import time
import os
import subprocess
import socket
import threading
import signal
import pytesseract
from PIL import Image
import cv2
import numpy as np
from pyzbar import pyzbar


VICE_BASE_PORT = 65501
assigned_window_ids = set()


base_dir = os.path.dirname(os.path.abspath(__file__))






def ascii_to_petscii_c128(ascii_str, addr_start=0x0287):
    petscii_bytes = []
    for ch in ascii_str:
        if 'a' <= ch <= 'z':
            ch = ch.upper()
        petscii_bytes.append(ord(ch))
    addr_end = addr_start + len(petscii_bytes) - 1
    byte_strs = ["{:02X}".format(b) for b in petscii_bytes]
    cmd = "f {:04X} {:04X} {}".format(addr_start, addr_end, " ".join(byte_strs))
    return cmd

def send_c128_command(context, name, cmd_str):
    # Convert to petscii and write to keyboard buffer
    petscii_cmd = ascii_to_petscii_c128(cmd_str + '\r')  # add carriage return
    petscii_cmd = ascii_to_petscii_cmd(cmd_str + '\r')  # add carriage return
    response1 = send_single_command(context, name, petscii_cmd)

    # write length of buffer to $00C6
    trigger_cmd = "f 00C6 00C6 {:02X}".format(len(cmd_str) + 1)
    response2 = send_single_command(context, name, trigger_cmd)
    return "\n".join([response1, response2])

def ascii_to_petscii_cmd(ascii_str, addr_start=0x0277):
    petscii_bytes = []
    for ch in ascii_str:
        if 'a' <= ch <= 'z':
            ch = ch.upper()
        petscii_bytes.append(ord(ch))

    addr_end = addr_start + len(petscii_bytes) - 1
    byte_strs = ["{:02X}".format(b) for b in petscii_bytes]

    cmd = "f {:04X} {:04X} {}".format(addr_start, addr_end, " ".join(byte_strs))
    return cmd

def wait_for_port(host, port, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except:
            time.sleep(0.1)
    return False

def send_single_command(context, name, cmd_str):
    if not isinstance(cmd_str, str):
        raise TypeError(f"cmd_str must be a string, got {type(cmd_str)}: {cmd_str}")

    instance = context.get(name)
    if not isinstance(instance, ViceInstance):
        raise ValueError(f"No ViceInstance named '{name}' in context")

    port = instance.port
    print(f"Connecting to VICE '{name}' on port {port} to send: {cmd_str.strip()}")
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        sock.sendall((cmd_str + "\n").encode('ascii'))
        sock.shutdown(socket.SHUT_WR)
        response = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
        print(f"VICE '{name}' response:\n", response.decode(errors='ignore'))
        return response.decode(errors='ignore')

def send_vice_command(context, name, string):
    string = string.replace('\n', '\r')
    i = 0
    log = []

    while i < len(string):
        chunk = string[i:i + 10]
        print(f"Sending to '{name}':", chunk)
        bits = ascii_to_petscii_cmd(chunk)
        log.append(send_single_command(context, name, bits))
        log.append(send_single_command(context, name, f"f 00c6 00c6 {len(chunk):02X}"))

        if i + 10 >= len(string):
            log.append(send_single_command(context, name, f"f 00c6 00c6 {len(chunk):02X}"))

        i += 10

    return True, "\n".join(log)

def next_vice_instance(context):
    if "_vice_count" not in context:
        context["_vice_count"] = 0

    index = context["_vice_count"]
    context["_vice_count"] += 1

    name = f"vice{index + 1}"
    port = VICE_BASE_PORT + index

    return name, port

def find_window_id_by_pid(pid):
    try:
        result = subprocess.check_output(["xdotool", "search", "--pid", str(pid)])
        for line in result.decode().splitlines():
            wid = line.strip()
            try:
                title = subprocess.check_output(["xdotool", "getwindowname", wid]).decode().strip()
                if "VICE" in title or "C64" in title:
                    return wid
            except subprocess.CalledProcessError:
                continue
    except subprocess.CalledProcessError:
        return None
    return None



# wrapper for putting logging around class start method
def launch_vice_instance(instance, boot_delay=3):
    log = []
    log.append(f"Launching {instance.name} on port {instance.port} with disk={instance.disk_path}")
    
    if not instance.start():
        log.append(f"{instance.name} failed to start (no window ID detected).")
        return False, log

    time.sleep(boot_delay)

    if not instance.wait_for_ready():
        log.append(f"{instance.name} did not become ready on port {instance.port}")
        log.append(f"{instance.name} stdout:\n{''.join(instance.get_output())}")
        return False, log

    log.append(f"{instance.name} is ready")
    log.append(f"{instance.name} stdout:\n{''.join(instance.get_output())}")
    return True, log


class ViceInstance:
    def __init__(self, name, port, archtype, config_path=None, disk_path=None, rom_path=None, autostart_path=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.name = name
        self.port = port
        self.archtype = archtype
        self.config_path = os.path.join(base_dir, config_path) if config_path and not os.path.isabs(config_path) else config_path
        self.disk_path = os.path.join(base_dir, disk_path) if disk_path and not os.path.isabs(disk_path) else disk_path
        self.autostart_path = os.path.join(base_dir, autostart_path) if autostart_path and not os.path.isabs(autostart_path) else autostart_path
        self.window_id = None
        self.screenshot_count = 0
        self.rom_path = os.path.join(base_dir, rom_path) if rom_path and not os.path.isabs(rom_path) else rom_path
        self.proc = None
        self.thread = None
        self.ready_event = threading.Event()
        self._output_lock = threading.Lock()
        self._output_lines = []
        self._stop_reading = threading.Event()
        

    seen_window_ids = set()

    def get_output(self):
        with self._output_lock:
            return list(self._output_lines)


    def _reader(self):
        with self.proc.stdout:
            for line in iter(self.proc.stdout.readline, ''):
                with self._output_lock:
                    self._output_lines.append(line)
                # print realtime output
                # print(f"[{self.name}] {line}", end='')
                if self._stop_reading.is_set():
                    break
        self.proc.stdout.close()
        self.proc.wait()

    def start(self):
        ViceInstance.seen_window_ids.clear()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env = os.environ.copy()
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":10"
        if "XAUTHORITY" in os.environ:
            env["XAUTHORITY"] = os.environ["XAUTHORITY"]

        if self.archtype == 'c64':
            cmd = ["x64"]
        elif self.archtype == 'c128':
            cmd = ["x128"]
        elif self.archtype == 'vic20':
            cmd = ["xvic"]
        else:
            raise ValueError(f"Unsupported archtype: {self.archtype}")

        if self.config_path:
            config_full_path = os.path.abspath(os.path.join(base_dir, self.config_path))
            cmd += ["-config", config_full_path]

        cmd += ["-remotemonitor", "-remotemonitoraddress", f"127.0.0.1:{self.port}"]

        if self.disk_path:
            cmd += ["-8", self.disk_path]
        if self.rom_path:
            cmd += ["-kernal", self.rom_path]
        if self.autostart_path:
            cmd += ["-autostart", self.autostart_path]

        print("Starting with command:", " ".join(f'"{arg}"' if ' ' in arg else arg for arg in cmd))

        self.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        # need to wait for window to be active, may need more time on a slower system
        time.sleep(1)

        # loop to find unique x64 vice window PIDs
        self.window_id = None
        for _ in range(10):
            time.sleep(0.5)
            self.window_id = self.find_window_id_by_pid(self.proc.pid)
            if self.window_id:
                break

        if not self.window_id:
            print(f"[{self.name}] Failed to get window ID, starting failed.")
            return False  # sets fail here

        print(f"[{self.name}] Window ID: {self.window_id}")

        self.ready_event.set()
        self._stop_reading.clear()
        self.thread = threading.Thread(target=self._reader, name=f"{self.name}-stdout-reader")
        self.thread.daemon = True
        self.thread.start()

        return True





    def wait_for_ready(self, timeout=15):
        self.ready_event.wait(timeout)
        return wait_for_port("127.0.0.1", self.port, timeout=timeout)

    def stop(self, timeout=5):
        if self.proc and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGINT)
            try:
                self.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self._stop_reading.set()
        if self.thread:
            self.thread.join(timeout=timeout)

    def take_screenshot(self, test_step=None, filename=None):
        if not self.proc or self.proc.poll() is not None:
            print(f"[{self.name}] VICE process not running.")
            return False

        if not self.window_id:
            print(f"[{self.name}] No window ID cached, cannot take screenshot.")
            return False

        base_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(base_dir, "reports")

        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        self.screenshot_count += 1

        if filename is None:
            if test_step:
                filename = f"screenshot-{self.name}-{test_step}-{self.screenshot_count}.png"
            else:
                filename = f"screenshot-{self.name}-{self.screenshot_count}.png"

        filepath = os.path.join(reports_dir, filename)

        try:
            subprocess.run(["xdotool", "windowmap", self.window_id], check=True)
            subprocess.run(["xdotool", "windowactivate", self.window_id], check=True)

            subprocess.run(["import", "-window", self.window_id, filepath], check=True)
            print(f"[{self.name}] Screenshot saved to {filepath}")

            if croptheimage(filepath):
                return True
            else:
                print(f"[{self.name}] Failed to crop screenshot")
                return False

        except subprocess.CalledProcessError as e:
            print(f"[{self.name}] Failed to take screenshot: {e}")
            return False
        
    def find_window_id_by_pid(self, pid):
        try:
            result = subprocess.check_output(["xdotool", "search", "--pid", str(pid)])
            for line in result.decode().splitlines():
                wid = line.strip()
                if wid in ViceInstance.seen_window_ids:
                    continue
                try:
                    title = subprocess.check_output(["xdotool", "getwindowname", wid]).decode().strip()
                    if "VICE" in title or "C64" in title:
                        ViceInstance.seen_window_ids.add(wid)
                        return wid
                except subprocess.CalledProcessError:
                    continue
        except subprocess.CalledProcessError:
            return None
        return None


def croptheimage(image_path):
    try:
        img = Image.open(image_path)
        width, height = img.size
        # Crop box: (left, upper, right, lower)
        crop_box = (0, 25, width, height - 75)
        cropped = img.crop(crop_box)
        cropped.save(image_path, format='PNG')
        print(f"Cropped image saved to {image_path}")
        return True
    except Exception as e:
        print(f"Failed to crop image {image_path}: {e}")
        return False

def ocr_word_find(instance, phrase, timeout=10, startx=None, starty=None, stopx=None, stopy=None, errorphrase=None):
    ocrlogdir = os.path.join(base_dir, "compile_logs")
    os.makedirs(ocrlogdir, exist_ok=True)
    print("OCR basedir var: base_dir ", ocrlogdir)
    print("OCR temp dir: ", ocrlogdir)
    log = []

    start_time = time.time()
    phrase_lower = phrase.lower()
    error_lower = errorphrase.lower() if errorphrase else None
    attempts = 0
    text = ""


    for i in range(timeout):
        attempts += 1
        iter_start = time.time()

        elapsed = int(iter_start - start_time)
        safe_phrase = phrase.replace(" ", "_")
        filename_base = f"{safe_phrase}_{elapsed}"
        screenshot_path = os.path.join(ocrlogdir, filename_base)

        png_path = screenshot_path + ".png"
        print("taking screenshot at path: ", png_path)
        txt_path = screenshot_path + ".txt"

        ok, msg = instance.take_screenshot(screenshot_path)
        print(f'OCR Screenshot Path: {screenshot_path}')
        if not ok:
            log.append(f"Screenshot failed: {msg}")
            continue

        try:
            print('processing screenshot OCR...')
            crop_start = time.time()

            img = Image.open(png_path)
            if None not in (startx, starty, stopx, stopy):
                img = img.crop((startx, starty, stopx, stopy))

            crop_duration = time.time() - crop_start
            log.append(f"Crop completed in {crop_duration:.2f} seconds")

            ocr_start = time.time()
            text = pytesseract.image_to_string(img)
            ocr_duration = time.time() - ocr_start
            log.append(f"OCR completed in {ocr_duration:.2f} seconds")

        except Exception as e:
            log.append(f"OCR failed on {png_path}: {e}")
            text = ""

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        iter_total = time.time() - iter_start
        log.append(f"Total time this pass: {iter_total:.2f} seconds\n")

        text_lower = text.lower()

        if phrase_lower in text_lower:
            return True, text, attempts, log
        if error_lower and error_lower in text_lower:
            log.append(f"Aborted early due to error phrase: '{errorphrase}' found in OCR text.")
            return False, text, attempts, log

        time.sleep(2)

    return False, text, attempts, log



# CC65 disk stuff #
def compile_cc65(source_file, output_file, archtype):
    source_path = os.path.join(base_dir, source_file)
    output_path = os.path.join(base_dir, output_file)
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)


    if not os.path.exists(source_path):
        return False, f"Source file not found: {source_path}"

    cmd = ['cc65', '-O', '-t', archtype, '-o', output_path, source_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def assemble_ca65(asm_file, obj_file, archtype):
    asm_path = os.path.join(base_dir, asm_file)
    obj_path = os.path.join(base_dir, obj_file)
    

    if not os.path.exists(asm_path):
        return False, f"Assembly file not found: {asm_path}"

    cmd = ['ca65', '-t', archtype, '-o', obj_path, asm_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def link_ld65(obj_file, output_file, archtype, linker_conf=None):
    cc65_lib_path = "/usr/share/cc65/lib"
    if isinstance(obj_file, (list, tuple)):
        obj_files = obj_file
    else:
        obj_files = [obj_file]

    obj_paths = [os.path.join(base_dir, f) for f in obj_files]
    output_path = os.path.join(base_dir, output_file)

    for p in obj_paths:
        if not os.path.exists(p):
            return False, f"Object file not found: {p}"

    cmd = ['ld65']
    cmd.extend(['-L', cc65_lib_path])
    if linker_conf is not None:
        conf_path = os.path.join(base_dir, linker_conf)
        if not os.path.exists(conf_path):
            return False, f"Linker config not found: {conf_path}"
        cmd.extend(['-C', conf_path])
    else:
        # If no custom config
        cmd.extend(['-t', archtype])

    cmd.extend(['-o', output_path])
    cmd.extend(obj_paths)

    if archtype == 'c64':
        cmd.append('c64.lib')
    elif archtype == 'c128':
        cmd.append('c128.lib')    
    elif archtype == 'vic20':
        cmd.append('vic20.lib')

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    if success and not os.path.exists(output_path):
        return False, f"Link failed, {output_path} not created"

    return success, proc.stdout


def create_blank_d64(d64_name, base_dir=base_dir):
    d64_path = os.path.join(base_dir, d64_name)
    os.makedirs(os.path.dirname(d64_path), exist_ok=True)

    try:
        with open(d64_path, 'wb') as f:
            f.write(b'\x00' * 174848)
    except Exception as e:
        return False, f"Failed to create empty d64: {e}"

    cmd = ['c1541', '-attach', d64_path, '-format', 'EMPTY,08']
    proc = subprocess.run(cmd, cwd=base_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    success = proc.returncode == 0
    return success, proc.stdout

def format_and_copyd64(d64_name, prg_file, base_dir=base_dir):
    d64_path = os.path.join(base_dir, d64_name)
    prg_path = os.path.join(base_dir, prg_file)

    if not os.path.exists(prg_path):
        return False, f"PRG file not found: {prg_path}"

    cmd = ['c1541', '-attach', d64_path, '-write', prg_path]
    proc = subprocess.run(cmd, cwd=base_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

C64_COLORS = {
    'black':    ((0, 0, 0), (40, 40, 40)),
    'white':    ((200, 200, 200), (255, 255, 255)),
    'red':      ((150, 0, 0), (255, 80, 80)),
    'cyan':     ((0, 150, 150), (80, 255, 255)),
    'purple':   ((150, 0, 150), (255, 80, 255)),
    'green':    ((0, 150, 0), (80, 255, 80)),
    'blue':     ((0, 0, 150), (80, 80, 255)),
    'yellow':   ((150, 150, 0), (255, 255, 80)),
    'orange':   ((200, 80, 0), (255, 150, 80)),
    'brown':    ((100, 50, 0), (160, 110, 50)),
    'lightred': ((255, 100, 100), (255, 170, 170)),
    'gray':     ((80, 80, 80), (160, 160, 160)),
} 

   


def assemble_object(ser_file, s_file, label, base_dir=base_dir):
    ser_file = os.path.abspath(os.path.join(base_dir, ser_file))
    s_file   = os.path.abspath(os.path.join(base_dir, s_file))

    cmd = [
        "co65",
        "--code-label",
        label,
        ser_file
    ]
    subprocess.check_call(cmd)

    # co65 outputs .s next to .ser by default
    generated_s = os.path.splitext(ser_file)[0] + ".s"
    if generated_s != s_file:
        os.rename(generated_s, s_file)

    return True, s_file

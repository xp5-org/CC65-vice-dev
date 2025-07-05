import time
import os
import subprocess
import socket
from PIL import Image
import subprocess
import time
import socket
import threading
import signal

import subprocess
import time

def start_vice(proc_container, ready_event, port):
    print(f"Starting VICE subprocess on port {port}...")

    proc = subprocess.Popen(
        ["x64", "-remotemonitor", f"-remotemonitoraddress", f"127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    proc_container["proc"] = proc
    proc_container["port"] = port
    print(f"VICE subprocess started, PID: {proc.pid}")
    time.sleep(1)  # give VICE time to bind to port
    ready_event.set()
    proc.wait()
    print("VICE subprocess exited.")






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





def find_vice_window_id():
    try:
        output = subprocess.check_output(["xwininfo", "-root", "-tree"]).decode()
        for line in output.splitlines():
            if "VICE" in line and line.strip().startswith("0x"):
                parts = line.strip().split()
                return parts[0]
    except subprocess.CalledProcessError:
        return None
    return None

def take_screenshot(output_path="/tmp/vice_screen.png"):
    win_id = find_vice_window_id()
    if not win_id:
        print("VICE window not found.")
        return
    try:
        subprocess.run(["import", "-window", win_id, output_path], check=True)
        print(f"Screenshot saved to {output_path}")
    except subprocess.CalledProcessError as e:
        print("Failed to take screenshot:", e)



# NEW #


VICE_BASE_PORT = 65501

def next_vice_instance(context):
    if "_vice_count" not in context:
        context["_vice_count"] = 0

    index = context["_vice_count"]
    context["_vice_count"] += 1

    name = f"vice{index + 1}"
    port = VICE_BASE_PORT + index

    return name, port







import threading
import signal

class ViceInstance:
    def __init__(self, name, port, config_path=None, disk_path=None, rom_path=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.name = name
        self.port = port
        self.config_path = os.path.join(base_dir, config_path) if config_path and not os.path.isabs(config_path) else config_path
        self.disk_path = os.path.join(base_dir, disk_path) if disk_path and not os.path.isabs(disk_path) else disk_path

        self.rom_path = os.path.join(base_dir, rom_path) if rom_path and not os.path.isabs(rom_path) else rom_path
        self.proc = None
        self.thread = None
        self.ready_event = threading.Event()
        self._output_lock = threading.Lock()
        self._output_lines = []
        self._stop_reading = threading.Event()

    def _reader(self):
        with self.proc.stdout:
            for line in iter(self.proc.stdout.readline, ''):
                with self._output_lock:
                    self._output_lines.append(line)
                # Optional: print realtime output if you want
                # print(f"[{self.name}] {line}", end='')
                if self._stop_reading.is_set():
                    break
        self.proc.stdout.close()
        self.proc.wait()

    def start(self):
        env = os.environ.copy()
        env["SDL_VIDEODRIVER"] = "x11"
        cmd = ["x64", "-remotemonitor", "-remotemonitoraddress", f"127.0.0.1:{self.port}"]
        if self.config_path:
            cmd += ["-config", self.config_path]
        if self.disk_path:
            cmd += ["-8", self.disk_path]
            print("disk path: ", self.disk_path)
        if self.rom_path:
            cmd += ["-kernal", self.rom_path]

        self.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        self.ready_event.set()
        self._stop_reading.clear()
        self.thread = threading.Thread(target=self._reader, name=f"{self.name}-stdout-reader")
        self.thread.daemon = True
        self.thread.start()

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

    @property
    def output(self):
        with self._output_lock:
            return "".join(self._output_lines)







def launch_vice_instance(context, name, port):
    log = []
    instance = ViceInstance(name, port)
    log.append(f"Launching VICE instance '{name}' on port {port}")
    instance.start()

    if not instance.wait_for_ready():
        log.append(f"Timeout waiting for VICE port {port}")
        return False, "\n".join(log)

    time.sleep(3)
    context[name] = instance
    log.append(f"VICE instance '{name}' is ready")
    return True, "\n".join(log)












# CC65 disk stuff #

import subprocess

import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))

def compile_cc65(source_file, output_file):
    source_path = os.path.join(base_dir, source_file)
    output_path = os.path.join(base_dir, output_file)
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)


    if not os.path.exists(source_path):
        return False, f"Source file not found: {source_path}"

    cmd = ['cc65', '-O', '-t', 'c64', '-o', output_path, source_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def assemble_ca65(asm_file, obj_file):
    asm_path = os.path.join(base_dir, asm_file)
    obj_path = os.path.join(base_dir, obj_file)
    

    if not os.path.exists(asm_path):
        return False, f"Assembly file not found: {asm_path}"

    cmd = ['ca65', '-t', 'c64', '-o', obj_path, asm_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def link_ld65(obj_file, output_file, library='c64.lib'):
    obj_path = os.path.join(base_dir, obj_file)
    output_path = os.path.join(base_dir, output_file)

    if not os.path.exists(obj_path):
        return False, f"Object file not found: {obj_path}"

    # Don't prepend base_dir to library, let ld65 find it
    cmd = ['ld65', '-o', output_path, '-t', 'c64', obj_path, library]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
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
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def format_and_copyd64(d64_name, prg_file, base_dir=base_dir):
    d64_path = os.path.join(base_dir, d64_name)
    prg_path = os.path.join(base_dir, prg_file)

    if not os.path.exists(prg_path):
        return False, f"PRG file not found: {prg_path}"

    cmd = ['c1541', '-attach', d64_path, '-write', prg_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

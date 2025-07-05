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





def send_single_command(cmd_str, port):
    if not isinstance(cmd_str, str):
        raise TypeError(f"cmd_str must be a string, got {type(cmd_str)}: {cmd_str}")

    print(f"Connecting to VICE remote monitor on port {port} to send: {cmd_str.strip()}")
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        sock.sendall((cmd_str + "\n").encode('ascii'))
        sock.shutdown(socket.SHUT_WR)
        response = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
        print("VICE response:\n", response.decode(errors='ignore'))
        return response.decode(errors='ignore')





def send_vice_command(string, port):
    string = string.replace('\n', '\r')
    i = 0
    log = []

    while i < len(string):
        chunk = string[i:i + 10]
        print("Sending this string chunk:", chunk)
        bits = ascii_to_petscii_cmd(chunk)
        log.append(send_single_command(bits, port))
        log.append(send_single_command(f"f 00c6 00c6 {len(chunk):02X}", port))

        if i + 10 >= len(string):
            log.append(send_single_command(f"f 00c6 00c6 {len(chunk):02X}", port))

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
        self.name = name
        self.port = port
        self.config_path = config_path
        self.disk_path = disk_path
        self.rom_path = rom_path
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

def compile_cc65(source_file, output_file):
    # Compile C source to assembly
    cmd = ['cc65', '-O', '-t', 'c64', '-o', output_file, source_file]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def assemble_ca65(asm_file, obj_file):
    # Assemble .s file to .o object
    cmd = ['ca65', '-t', 'c64', '-o', obj_file, asm_file]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def link_ld65(obj_file, output_file, library='c64.lib'):
    # Link object file to final executable .prg
    cmd = ['ld65', '-o', output_file, '-t', 'c64', obj_file, library]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def create_blank_d64(d64_name):
    # Create new blank disk image (empty d64)
    # Usually done with c1541 -format <name>,<id> <filename>
    # Here, just creating empty disk image with standard 1541 id "00"
    cmd = ['c1541', '-format', 'EMPTY', '00', d64_name]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

def format_and_copyd64(d64_name, prg_file):
    # Format and copy program to disk image
    # This command formats the disk and writes the file in one go:
    # c1541 -format diskname,id d64 test.d64 -attach test.d64 -write test.prg
    # But since you create blank d64 separately, you can just write the file:
    cmd = ['c1541', '-attach', d64_name, '-write', prg_file]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    success = proc.returncode == 0
    return success, proc.stdout

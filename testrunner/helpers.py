import os
import time
import subprocess
import socket
import tempfile
import threading
from PIL import Image
import pytesseract

RAW_IMAGE = "hdd.img"
QEMU_IMAGE = "hdd.qcow2"
MONITOR_PORT = 55555
PROGRESS_FILE = "progress.txt"
REPORT_DIR = "reports"
qemu_process = None
compile_logs_dir = "compile_logs"




testfile_registry = {}

def register_testfile(id, types, description=None, system=None, platform=None):
    def decorator(module=None):
        import inspect
        modname = module.__name__ if module else inspect.stack()[1][0].f_globals["__name__"]
        testfile_registry[modname] = {
            "id": id,
            "types": types,
            "description": description,
            "system": system,
            "platform": platform,
        }
        return module  # <-- must return module to preserve normal import behavior
    return decorator





def flush_monitor_banner(sock):
    sock.settimeout(1.0)
    try:
        banner = sock.recv(1024)
        print("[monitor banner]", banner.decode("utf-8", errors="replace").strip())
    except socket.timeout:
        print("[monitor banner] no banner received")
    except Exception as e:
        print(f"[monitor banner error] {e}")


def take_screenshots_to_gif(sock, interval, count, gif_name="screencap.gif", base_name="frame"):
    framerate = 10
    start_time = time.time()
    try:
        temp_dir = os.path.abspath("screens_tmp")
        os.makedirs(temp_dir, exist_ok=True)
        frames = []

        for i in range(count):
            name = f"{base_name}_{i}"
            ppm_path = os.path.join(temp_dir, name + ".ppm")
            png_path = os.path.join(temp_dir, name + ".png")

            # Trigger screenshot
            sock.sendall(f"screendump {ppm_path}\n".encode("utf-8"))
            time.sleep(0.5)

            # Wait for file
            wait_start = time.time()
            while not os.path.exists(ppm_path):
                if time.time() - wait_start > 5:
                    raise RuntimeError(f"Timed out waiting for screendump {ppm_path}")
                time.sleep(0.1)

            # Convert to PNG
            img = Image.open(ppm_path)
            img.save(png_path)
            frames.append(img.convert("RGB"))

            time.sleep(interval)

        # Save to animated GIF in REPORT_DIR
        gif_path = os.path.abspath(os.path.join(REPORT_DIR, gif_name))
        frame_duration = max(1, int(1000.0 / framerate))  # ms per frame

        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,
            loop=0
        )

        duration = time.time() - start_time
        gif_playback_time = count / framerate
        speedup = duration / gif_playback_time if gif_playback_time > 0 else 0

        info = (f"Captured {len(frames)} screenshots in {duration:.2f} seconds, "
                f"GIF plays back at {framerate} fps for {gif_playback_time:.2f} seconds, "
                f"approximate speedup: {speedup:.1f}x")

        return True, info

    except Exception as e:
        return False, f"Error: {e}"









def take_screenshot(sock, name="screenshot"):
    name = name.replace(" ", "_")  # replace spaces in filename
    ppm_path = os.path.abspath(name + ".ppm")
    png_path = os.path.abspath(name + ".png")
    time.sleep(0.5)
    sock.sendall(f"screendump {ppm_path}\n".encode("utf-8"))
    time.sleep(0.5)
    start = time.time()
    while not os.path.exists(ppm_path):
        if time.time() - start > 5:
            raise RuntimeError(f"Timed out waiting for screendump {ppm_path}")
        time.sleep(0.1)
    try:
        img = Image.open(ppm_path)
        img.save(png_path)
    except Exception as e:
        raise RuntimeError(f"Failed to convert {ppm_path} to PNG: {e}")

def copy_to_fat_image(src_dir, image_path):
    log = []
    mtools_config = f'drive h: file="{image_path}" offset=32256\n'
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(mtools_config)
        config_path = tmp.name

    try:
        try:
            result = subprocess.run(
                f'MTOOLSRC={config_path} mcopy -n -o -s {src_dir}/* h:/src/',
                shell=True,
                check=True,
                executable="/bin/bash",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            output = result.stdout.decode('utf-8', errors='replace')
            log.append(output)
            return True, output
        except subprocess.CalledProcessError as e:
            output = e.stdout.decode('utf-8', errors='replace') if e.stdout else ''
            log.append(output)
            return False, output
    finally:
        os.unlink(config_path)




def convert_raw_to_qcow2(raw_path=RAW_IMAGE, qcow2_path=QEMU_IMAGE):
    if not os.path.isfile(raw_path):
        return False, f"[error] Raw image not found: {raw_path}"

    if qcow2_path is None:
        qcow2_path = os.path.splitext(raw_path)[0] + ".qcow2"

    try:
        result = subprocess.run(
            ["qemu-img", "convert", "-O", "qcow2", raw_path, qcow2_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = result.stdout.decode("utf-8", errors="replace")
        return True, output
    except subprocess.CalledProcessError as e:
        output = e.stdout.decode("utf-8", errors="replace") if e.stdout else ''
        return False, output

    



def copy_from_fat_image(dst_dir, image_path):
    log = []
    os.makedirs(dst_dir, exist_ok=True)
    mtools_config = f'drive h: file="{image_path}" offset=32256\n'
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(mtools_config)
        config_path = tmp.name

    try:
        try:
            result = subprocess.run(
                f'MTOOLSRC={config_path} mcopy -n -o -s h:/src/ {dst_dir}/',
                shell=True,
                check=True,
                executable="/bin/bash",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            output = result.stdout.decode('utf-8', errors='replace')
            log.append(output)           
            return True, output
        except subprocess.CalledProcessError as e:
            output = e.stdout.decode('utf-8', errors='replace') if e.stdout else ''
            log.append(output)
            return False, output
    finally:
        os.unlink(config_path)

def send_monitor_key(sock, keyname, ctrl=False, alt=False, shift=False, delay=0.1):
    mods = []
    if ctrl: mods.append("ctrl")
    if alt: mods.append("alt")
    if shift: mods.append("shift")
    combo = "-".join(mods + [keyname]) if mods else keyname
    sock.sendall(f"sendkey {combo}\n".encode("utf-8"))
    time.sleep(delay)

def send_monitor_string(sock, text, delay=0.05):
    keymap = {
        'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f',
        'g': 'g', 'h': 'h', 'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l',
        'm': 'm', 'n': 'n', 'o': 'o', 'p': 'p', 'q': 'q', 'r': 'r',
        's': 's', 't': 't', 'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x',
        'y': 'y', 'z': 'z', '0': '0', '1': '1', '2': '2', '3': '3',
        '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
        ' ': 'spc', '.': 'dot', ',': 'comma', '-': 'minus',
        '/': 'slash', '\\': 'backslash', ':': 'semicolon',
        ';': 'semicolon', '\n': 'ret', '\r': 'ret',
        '*': '8'
    }



    # Characters that require SHIFT to produce correctly
    shift_required = {
        ':', '_', '+', '{', '}', '|', '<', '>', '"', '?',
        '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')'
    }

    for ch in text:
        key_char = ch.lower()
        if key_char in keymap:
            key = keymap[key_char]
            shift = ch.isupper() or ch in shift_required
            send_monitor_key(sock, key, shift=shift, delay=delay)
        else:
            print(f"[unsupported] {repr(ch)}")

sock_lock = threading.Lock()
def send_and_receive(sock, command):
    with sock_lock:
        # Flush old output
        try:
            sock.settimeout(0.2)
            while True:
                if not sock.recv(4096):
                    break
        except socket.timeout:
            pass
        except Exception:
            pass

        # Send the command
        sock.sendall((command + "\n").encode("utf-8"))
        sock.settimeout(2.0)

        data = ""
        start = time.time()
        prompt_count = 0

        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                decoded = chunk.decode("utf-8", errors="replace")
                data += decoded
                prompt_count += decoded.count("(qemu)")
                if prompt_count >= 1 and data.strip().endswith("(qemu)"):
                    break
            except socket.timeout:
                break
            if time.time() - start > 5:
                break

        return data.strip()

def save_snapshot(sock):
    print(f"[sending savevm] 'savevm snap1'")
    response = send_and_receive(sock, "savevm snap1")
    print(f"[monitor response]\n{response}\n--- end response ---")

    print(f"[sending info snapshots]")
    snapshot_list = send_and_receive(sock, "info snapshots")
    print(f"[snapshot list response]\n{snapshot_list}\n--- end snapshot list ---")

    if "snap1" in snapshot_list:
        print("[save_snapshot] Snapshot verified via monitor.")
        return True, snapshot_list
    else:
        print("[save_snapshot] Snapshot not found in monitor.")
        return False, snapshot_list

def ocr_word_find(sock, phrase, timeout=10, startx=None, starty=None, stopx=None, stopy=None, errorphrase=None):
    log_dir = "./compile_logs"
    os.makedirs(log_dir, exist_ok=True)
    log = []

    try:
        _ = pytesseract.get_tesseract_version()
    except Exception as e:
        log.append(f"Tesseract not available: {e}")
        return False, "", 0, log

    start_time = time.time()
    phrase_lower = phrase.lower()
    error_lower = errorphrase.lower() if errorphrase else None
    attempts = 0

    for i in range(timeout):
        attempts += 1
        iter_start = time.time()

        elapsed = int(iter_start - start_time)
        safe_phrase = phrase.replace(" ", "_")
        filename_base = f"{safe_phrase}_{elapsed}"
        screenshot_path = os.path.join(log_dir, filename_base)

        take_screenshot(sock, name=screenshot_path)

        png_path = screenshot_path + ".png"
        txt_path = screenshot_path + ".txt"

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
            return False, "", attempts, log

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


def ppdcompile(sock):
    log_dir = "./compile_logs"
    os.makedirs(log_dir, exist_ok=True)

    start_time = time.time()
    send_monitor_key(sock, "f3")
    time.sleep(1)
    send_monitor_key(sock, "ret")
    time.sleep(1)
    send_monitor_key(sock, "F")
    time.sleep(1)
    send_monitor_key(sock, "ret")
    time.sleep(1)
    send_monitor_key(sock, "ret")
    time.sleep(1)
    send_monitor_key(sock, "ret")
    time.sleep(1)

    return False

import socket
import time
MONITOR_PORT = 55555

def load_snapshot(sock, snapshot_name):
    print(f"[sending loadvm] 'loadvm {snapshot_name}'")
    response = send_and_receive(sock, f"loadvm {snapshot_name}")
    print(f"[monitor response]\n{response}\n--- end response ---")

    if "error" not in response.lower():
        print("[load_snapshot] Snapshot loaded successfully.")
        return True, response
    else:
        print("[load_snapshot] Failed to load snapshot.")
        return False, response



def make_floppy_image(path):
    size = 1474560  # 1.44 MB
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(b"\x00" * size)
        return True, "Created new 1.44MB floppy image"
    else:
        actual_size = os.path.getsize(path)
        if actual_size != size:
            return False, f"Floppy image exists but is {actual_size} bytes, expected 1474560"
        return True, "Floppy image already exists with correct size"


def attach_floppy_to_qemu(flop_img_path, monitor_host="127.0.0.1", monitor_port=MONITOR_PORT):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((monitor_host, monitor_port))
        sock.settimeout(2.0)

        # Flush initial monitor banner/output
        time.sleep(0.1)
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
        except socket.timeout:
            pass

        cmd = f'change floppy0 {flop_img_path}\n'
        sock.sendall(cmd.encode('utf-8'))

        # Optionally read the response
        response = b""
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
        except socket.timeout:
            pass

        sock.close()
        return True, response.decode('utf-8', errors='replace')
    except Exception as e:
        return False, str(e)
    




def detach_floppy_from_qemu(sock):
    #floppy image.img format blocks snap create
    #need to dismount floppy before snapshot take
    try:
        sock.settimeout(2.0)
        # Flush small amount of data if available, without blocking
        #try:
        #    while True:
        #        data = sock.recv(4096)
        #        if not data:
        #            break
        #except socket.timeout:
        #    pass

        sock.sendall(b"eject floppy0\n")

        # Optionally read a small response to avoid issues
        try:
            resp = sock.recv(4096)
        except socket.timeout:
            resp = b""

        return True, resp.decode('utf-8', errors='replace')
    except Exception as e:
        return False, str(e)








def start_playtest_qemu():
    global qemu_process
    dummy_floppy = "tmpfloppydisk.img"
    qemu_process = subprocess.Popen([
        "qemu-system-i386",
        "-hda", QEMU_IMAGE,
        "-m", "4M",
        "-vga", "std",
        "-monitor", f"tcp:127.0.0.1:{MONITOR_PORT},server,nowait",
        "-vga", "std"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return qemu_process


def start_buildtest_qemu():
    global qemu_process
    qemu_process = subprocess.Popen([
        "qemu-system-i386",
        "-hda", QEMU_IMAGE,
        "-m", "4M",
        "-monitor", "tcp:127.0.0.1:55555,server,nowait",
        "-vga", "std",
        "-fda", "tmpfloppydisk.img"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return qemu_process



def wait_for_monitor(timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return socket.create_connection(("127.0.0.1", MONITOR_PORT), timeout=1)
        except:
            time.sleep(0.2)
    raise RuntimeError("QEMU monitor timeout")



buildtest_registry = []
playtest_registry = []
packagetest_registry = []

def register_playtest(description):
    def decorator(func):
        func.test_description = description
        playtest_registry.append(func)
        return func
    return decorator

def register_buildtest(description):
    def decorator(func):
        func.test_description = description
        buildtest_registry.append(func)
        return func
    return decorator

def register_packagetest(description):
    def decorator(func):
        func.test_description = description
        packagetest_registry.append(func)
        return func
    return decorator
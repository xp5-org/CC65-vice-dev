import time
import os
import sys
import subprocess
import threading
import re

from appstate import process_registry

class HatariInstance:
    def __init__(self, name=None, port=None, archtype=None, config_path=None,
                 prg_filename=None, rom_path=None, mountpath=None, fastboot=None):
        self.name = name if name else "hatari1"
        self.port = port
        self.archtype = archtype
        self.prg_filename = prg_filename
        self.rom_path = rom_path
        self.mountpath = mountpath
        self.fastboot = fastboot
        self.ready_event = threading.Event()
        self._stop_reading = threading.Event()
        self.proc = None
        self.window_id = None
        self.screenshot_count = 0
        self.startup_error = ""
        self.cmd = []
        self._output_lines = []
        self._output_lock = threading.Lock()

    def start(self):
        env = os.environ.copy()
        
        tos_path = self.rom_path if self.rom_path else "/testsrc/etos256us.img"
        if not os.path.exists(tos_path):
            self.startup_error = f"TOS image not found: {tos_path}"
            return False

        self.cmd = [
            "hatari",
            "--machine", self.archtype or "st",
            "--monitor", "mono",
            "--tos", tos_path,
            "--fast-boot", "true" if self.fastboot else "false",
            "--memsize", "1",
            "--rs232-out", "/tmp/atariout.txt"
        ]

        has_drive = False
        if self.mountpath and os.path.exists(self.mountpath):
            self.cmd.extend(["--harddrive", self.mountpath])
            has_drive = True

        if self.prg_filename and has_drive:
            self.cmd.extend(["--auto", "C:\\" + self.prg_filename.upper()])


        self.proc = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )

        for _ in range(15):
            ret = self.proc.poll()
            if ret is not None:
                output = self.proc.stdout.read()
                self.startup_error = f"Exit code {ret}. Hatari Output: {output.strip()[:500]}"
                return False
            
            time.sleep(0.2)
            self.window_id = self.find_window_id_by_pid(self.proc.pid, env)
            if self.window_id:
                break

        if not self.window_id:
            self.startup_error = "Window ID not found (X11 connection or xdotool issue)"
            return False

        self.ready_event.set()
        threading.Thread(target=self._reader, daemon=True).start()
        process_registry.register(self.name, self.proc)
        return True
    
    
    def stop(self, timeout=5):
        if not self.proc:
            return True

        self._stop_reading.set()

        if self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()

        try:
            if self.proc.stdout:
                self.proc.stdout.close()
        except Exception:
            pass

        self.proc = None
        self.window_id = None
        process_registry.unregister(self.name)
        return True

    def get_output(self):
        with self._output_lock:
            return list(self._output_lines)

    def find_window_id_by_pid(self, pid, env):
        try:
            out = subprocess.check_output(["xdotool", "search", "--pid", str(pid)], text=True, env=env)
            ids = out.strip().splitlines()
            if ids: return ids[-1]
        except:
            pass
        return None

    def _reader(self):
        while not self._stop_reading.is_set() and self.proc:
            line = self.proc.stdout.readline()
            if not line: break
            print(f"[{self.name}] {line.strip()}")

    def take_screenshot(self, test_step=None, filename=None, window="default"):
        _helperdir = "/testrunnersrc/pyhelpers"
        if _helperdir not in sys.path:
            sys.path.insert(0, _helperdir)
        
        try:
            from appstate import progress_state
            stepnum = progress_state.step
            stepnum = re.match(r'\d+', stepnum).group(0)
            if not test_step:
                test_step = stepnum
        except Exception:
            if not test_step:
                test_step = "unknown"

        if not self.proc or self.proc.poll() is not None:
            return False, "Hatari process not running"

        win_id = getattr(self, "window_id", None)
        if not win_id:
            return False, "No window ID cached"

        screenshot_base_dir = "/testrunnerapp/"
        reports_dir = os.path.join(screenshot_base_dir, "reports")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        self.screenshot_count += 1
        if filename is None:
            filename = f"screenshot-{self.name}-{test_step}-{self.screenshot_count}.png"

        filepath = os.path.join(reports_dir, filename)

        try:
            subprocess.run(["xdotool", "windowmap", win_id], check=True)
            subprocess.run(["xdotool", "windowactivate", win_id], check=True)
            subprocess.run(["import", "-window", win_id, filepath], check=True)
            return True, filepath
        except subprocess.CalledProcessError as e:
            return False, f"Subprocess failed: {e}"
        except Exception as e:
            return False, str(e)

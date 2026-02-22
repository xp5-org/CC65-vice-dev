import os
import time
import subprocess
import threading
import re

def test_hatari_start(name=None, port=6502, config_path=None,
                      mountpath=None,
                      prg_filename=None,
                      romfile_path=None,
                      fastboot=True,
                      **kwargs):
    log = []
    context = kwargs.get("context", {})
    config = kwargs.get("config", {})
    
    name = name or config.get("instance_name") or "hatari1"
    
    rom_path = romfile_path or config.get("rom_path")
    mountpath = mountpath or config.get("mountpath")
    archtype = config.get("archtype", "st")

    instance = HatariInstance(
        name=name,
        port=port,
        archtype=archtype,
        rom_path=rom_path,
        mountpath=mountpath,
        fastboot=fastboot,
        prg_filename=prg_filename
    )

    started = instance.start()
    
    if not started:
        return False, f"Failed to start {name}: {instance.startup_error}"

    context[name] = instance
    time.sleep(0.5)
    log.append(f"Launched {name}")
    log.append("Command: " + " ".join(instance.cmd))
    return True, "\n".join(log)

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
            "--memsize", "1"
        ]

        if self.mountpath and os.path.exists(self.mountpath):
            self.cmd.extend(["--harddrive", self.mountpath])

        if self.prg_filename:
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
        return True

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



if __name__ == "__main__":
    test_config = {
        "instance_name": "hatari_test",
        "rom_path": "/testsrc/etos256us.img",
        "mountpath": "/testsrc/",
        "archtype": "st",
        "prg_filename": "AUTOEXEC.PRG"
    }

    success, log_output = test_hatari_start(config=test_config)
    
    print(f"Success: {success}")
    print("--- Log ---")
    print(log_output)
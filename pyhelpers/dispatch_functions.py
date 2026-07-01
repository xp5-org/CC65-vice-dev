from testsrc.pyhelpers.vicehelpers import send_vice_command, ViceInstance, send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from testsrc.pyhelpers.vicehelpers import send_single_command
from testsrc.pyhelpers.vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
import time
import os
import threading

from testsrc.pyhelpers.atarihelpers import HatariInstance
from testsrc.pyhelpers import ip232relayserver



# this is for returning only decorated def's found in this file
def dispatchtest_step(func):
    func._is_teststep = True
    return func


def resolve_path(path, config):
    if not path:
        return ""
    resolved = path
    atomic_keys = {k: v for k, v in config.items() if isinstance(v, (str, int))}
    while "{" in resolved:
        try:
            previous = resolved
            resolved = resolved.format(**atomic_keys)
            if previous == resolved:
                break
        except (KeyError, ValueError):
            break
    return resolved


@dispatchtest_step
def test_hatari_start(name=None, port=6502, config_path=None,
                      mountpath=None,
                      prg_filename=None,
                      romfile_path=None,
                      fastboot=True,
                      **kwargs):
    log = []
    context = kwargs.get("context", {})
    config = kwargs.get("config", {})
    
    config_path = resolve_path(config_path or config.get("hatari_config"), config)
    mountpath = resolve_path(mountpath or config.get("mountpath"), config)
    prg_filename = config.get("prg_filename")
    rom_path = resolve_path(romfile_path or config.get("rom_path"), config)
    archtype = config.get("archtype", "st")
    
    if not name:
        name = "hatari1"
    
    name = "hatari1"

    instance = HatariInstance(
        name=name,
        port=port,
        archtype=archtype,
        config_path=config_path,
        prg_filename=prg_filename,
        rom_path=rom_path,
        mountpath=mountpath,
        fastboot=fastboot
    )
    started = instance.start()
    
    log.append(f"Launching {name} mount={mountpath} rom={rom_path} config={config_path}")
    log.append("Command: " + " ".join(instance.cmd))
    
    stdout_lines = instance.get_output()
    if stdout_lines:
        log.append("Hatari stdout:")
        log.append("".join(stdout_lines))
        
    if not started:
        log.append(f"Failed to start {instance.name}: {instance.startup_error}")
        return False, "\n".join(log)
        
    context[name] = instance
    time.sleep(0.5)
    instance.take_screenshot()
    
    return True, "\n".join(log)


@dispatchtest_step
def test_wait30seconds(seconds=30, **kwargs):
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return False, f"Invalid seconds value: {seconds}"

    context = kwargs.get("context")
    if not context:
        return False, "No emulator instances in context"

    if not isinstance(context, dict):
        try:
            context = dict(context)
        except Exception:
            return False, f"Context is not iterable: {type(context)}"

    for name, instance in context.items():
        if not hasattr(instance, "take_screenshot") or not callable(instance.take_screenshot):
            continue

        success, info = instance.take_screenshot()
        if not success:
            err_msg = getattr(instance, "startup_error", None)
            reason = info or err_msg or "unknown"
            return False, f"Screenshot failed for {name}. Reason: {reason}"

    time.sleep(seconds)

    for name, instance in context.items():
        if not hasattr(instance, "take_screenshot") or not callable(instance.take_screenshot):
            continue

        success, info = instance.take_screenshot()
        if not success:
            err_msg = getattr(instance, "startup_error", None)
            reason = info or err_msg or "unknown"
            return False, f"Screenshot failed for {name}. Reason: {reason}"

    return True







@dispatchtest_step
def test_hatariterminate_all(**kwargs):
    log = []
    context = kwargs.get("context", {})
    
    stopped_names = []
    for name, instance in context.items():
        if hasattr(instance, "stop") and callable(instance.stop):
            log.append(f"Stopping {name}...")
            instance.take_screenshot()
            instance.stop()
            stopped_names.append(name)
            log.append(f"{name} has been terminated.")
    
    for name in stopped_names:
        del context[name]
        
    if not log:
        log.append("No active instances found to stop.")
        
    return True, "\n".join(log)


@dispatchtest_step
def test_emulator_start(name=None, port=6502, viceconf=None, disk8_path=None, disk9_path=None,
                        autostart_path=None, rom_path=None, warpmode=True, **kwargs):
    log = []
    context = kwargs.get("context", {})
    config = kwargs.get("config", {})

    disk8_path = resolve_path(disk8_path or config.get("d64_drive8_file"), config)
    disk9_path = resolve_path(disk9_path or config.get("d64_drive9_file"), config)
    viceconf = resolve_path(viceconf or config.get("viceconf"), config)
    autostart_path = resolve_path(autostart_path or "", config)
    rom_path = resolve_path(rom_path or "", config)

    # allocate a unique port using sequential counter
    auto_name, port = next_vice_instance(context)
    if name and str(name).strip() and str(name).strip().lower() not in ("none", "null"):
        name = str(name).strip()
    else:
        name = auto_name

    instance = ViceInstance(
        name,
        port,
        config.get("archtype"),
        config_path=viceconf,
        disk8_path=disk8_path,
        disk9_path=disk9_path,
        warpmode=warpmode,
        autostart_path=autostart_path,
        rom_path=rom_path
    )

    # record start order so the relay can correlate its connections
    context.setdefault("_vice_start_order", []).append(name)
    relay_running = ip232relayserver.server_running.is_set()
    relay_before = ip232relayserver.client_count() if relay_running else 0

    started = instance.start()
    context[name] = instance

    time.sleep(0.5)

    stdout_lines = instance.get_output()
    if stdout_lines:
        log.append("VICE stdout:")
        log.append("".join(stdout_lines))

    instance.take_screenshot()
    log.append(f"Launching {name} on port {port} with disk8={disk8_path} disk9={disk9_path} config={viceconf}")
    log.append("Command: " + " ".join(instance.cmd))

    # If the relay is up, wait for instance to connect before returning to prevent getting logging out of order
    # might need a better way to correlate relay to vice instance someday
    if relay_running:
        deadline = time.time() + 20
        while time.time() < deadline:
            if ip232relayserver.client_count() > relay_before:
                log.append(f"{name} connected to relay (client #{relay_before})")
                break
            time.sleep(0.5)
        else:
            log.append(f"WARNING: {name} did not connect to relay within timeout; "
                       f"relay correlation by connect-order may be unreliable")

    return True, "\n".join(log)






@dispatchtest_step
def test_compiletheprogram(out_dir=None, src_dir=None, d64_path=None, driver1_path=None, driver1_label=None,
                           driver2_path=None, driver2_label=None,
                           drivers=None, linkerconf=None,
                           prg_filepath=None, archtype=None, **kwargs):
    import os
    import glob
    import traceback

    def _nullify(v):
        """Convert string 'None'/'null'/'' to Python None."""
        if not v or str(v).strip().lower() in ("none", "null", ""):
            return None
        return v

    log = []
    context = None

    try:
        context = kwargs.get("context")
        config = kwargs.get("config")

        log.append(f"config present: {bool(config)}")
        log.append(f"context present: {bool(context)}")

        if not config:
            raise ValueError("Missing or empty config")

        archtype = _nullify(archtype) or _nullify(config.get("archtype", ""))
        log.append(f"archtype: {archtype!r}")

        # optional custom ld65 linker config
        linker_cfg = _nullify(linkerconf) or _nullify(config.get("linkerconf"))
        if linker_cfg:
            linker_cfg = resolve_path(linker_cfg, config)
            log.append(f"linker_cfg: {linker_cfg!r}")
            if not linker_cfg:
                raise ValueError("Could not resolve linkerconf")

        drivers_list = []
        if drivers:
            for drv in drivers:
                if isinstance(drv, dict):
                    drivers_list.append(drv)
                else:
                    log.append(f"Skipping invalid driver entry (not a dict): {drv!r}")

        for path_key, label_key, path_arg, label_arg in [
            ("linker_driver1", "driver1_label", driver1_path, driver1_label),
            ("linker_driver2", "driver2_label", driver2_path, driver2_label),
        ]:
            drv_path = _nullify(path_arg) or _nullify(config.get(path_key))
            drv_label = _nullify(label_arg) or _nullify(config.get(label_key))
            if drv_path and drv_label:
                drivers_list.append({"path": drv_path, "label": drv_label})

        res_out_dir = resolve_path(_nullify(out_dir) or _nullify(config.get("out_dir")), config)
        log.append(f"res_out_dir: {res_out_dir!r}")
        if not res_out_dir:
            raise ValueError("Invalid output directory")

        res_src_dir = resolve_path(_nullify(src_dir) or _nullify(config.get("src")), config)
        log.append(f"res_src_dir: {res_src_dir!r}")
        if not res_src_dir:
            raise ValueError("Invalid source directory")

        os.makedirs(res_out_dir, exist_ok=True)

        # Resolve drivers once — they are shared across every disk built here.
        resolved_drivers = []
        log.append(f"drivers: {len(drivers_list)}")
        for drv in drivers_list:
            drv_path = _nullify(drv.get("path"))
            drv_label = _nullify(drv.get("label"))
            if not drv_path or not drv_label:
                log.append(f"Skipping driver with missing path or label: {drv!r}")
                continue
            resolved_drv = resolve_path(drv_path, config)
            if not resolved_drv:
                raise ValueError(f"Could not resolve driver path: {drv_path!r}")
            resolved_label = resolve_path(drv_label, config)
            if not resolved_label:
                raise ValueError(f"Could not resolve driver label: {drv_label!r}")
            base = os.path.splitext(os.path.basename(resolved_drv))[0]
            resolved_drivers.append((base, resolved_drv, resolved_label))

        # if src_dir has subdirectories build each into its own disk image named after the subdir 
        # if no subdirs, collect every .c/.s directly in src_dir and link into a single disk
        # disk spec = (label, build_src, inter_dir, prg_file, d64_file)
        disk_specs = []
        subdirs = [
            entry for entry in sorted(os.listdir(res_src_dir))
            if os.path.isdir(os.path.join(res_src_dir, entry))
            and glob.glob(os.path.join(res_src_dir, entry, "*.c"))
        ]

        if subdirs:
            log.append(f"multi-disk mode: {len(subdirs)} client subdir(s): {subdirs}")
            for name in subdirs:
                build_src = os.path.join(res_src_dir, name)
                inter_dir = os.path.join(res_out_dir, name)
                prg_file = os.path.join(res_out_dir, name + ".prg")
                d64_file = os.path.join(res_out_dir, name + ".d64")
                disk_specs.append((name, build_src, inter_dir, prg_file, d64_file))
        else:
            res_prg_file = resolve_path(_nullify(prg_filepath) or _nullify(config.get("prg_filepath")), config)
            log.append(f"res_prg_file: {res_prg_file!r}")
            if not res_prg_file:
                raise ValueError("Invalid PRG output path")

            d64_filename = config.get("cmainfile", "disk") + ".d64"
            _d64_input = _nullify(d64_path) or os.path.join(res_out_dir, d64_filename)
            log.append(f"d64 input before resolve: {_d64_input!r}")
            res_d64_file = resolve_path(_d64_input, config)
            log.append(f"res_d64_file: {res_d64_file!r}")
            if not res_d64_file:
                raise ValueError("Invalid D64 output path")

            disk_label = config.get("cmainfile", "disk")
            log.append("flat mode: single disk from src_dir")
            disk_specs.append((disk_label, res_src_dir, res_out_dir, res_prg_file, res_d64_file))

        steps = []
        artifact_paths = []

        for disk_label, build_src, inter_dir, prg_file, d64_file in disk_specs:
            os.makedirs(inter_dir, exist_ok=True)
            link_objects = []

            c_files = glob.glob(os.path.join(build_src, "*.c"))
            log.append(f"[{disk_label}] c_files found: {len(c_files)}")
            for src_c in c_files:
                base_name = os.path.splitext(os.path.basename(src_c))[0]
                asm_file = os.path.join(inter_dir, f"{base_name}.s")
                obj_file = os.path.join(inter_dir, f"{base_name}.o")
                steps.extend([
                    (compile_cc65,  [src_c, asm_file, archtype], {"optimize": True}, f"[{disk_label}] Compile cc65 {base_name}"),
                    (assemble_ca65, [asm_file, obj_file, archtype], {},              f"[{disk_label}] Assemble ca65 {base_name}"),
                ])
                link_objects.append(obj_file)
                artifact_paths.extend([asm_file, obj_file])

            s_files = glob.glob(os.path.join(build_src, "*.s"))
            log.append(f"[{disk_label}] s_files found: {len(s_files)}")
            for src_s in s_files:
                base_name = os.path.splitext(os.path.basename(src_s))[0]
                obj_file = os.path.join(inter_dir, f"{base_name}_asm.o")
                steps.append(
                    (assemble_ca65, [src_s, obj_file, archtype], {}, f"[{disk_label}] Assemble ca65 {base_name} (source)")
                )
                link_objects.append(obj_file)
                artifact_paths.append(obj_file)

            for base, resolved_drv, resolved_label in resolved_drivers:
                driver_s = os.path.join(inter_dir, base + ".s")
                driver_o = os.path.join(inter_dir, base + ".o")
                steps.extend([
                    (assemble_object, [resolved_drv, driver_s, resolved_label], {}, f"[{disk_label}] Assemble driver object {base}"),
                    (assemble_ca65,   [driver_s, driver_o, archtype],            {}, f"[{disk_label}] Assemble driver ca65 {base}"),
                ])
                link_objects.append(driver_o)
                artifact_paths.extend([driver_s, driver_o])

            if not link_objects:
                raise RuntimeError(f"No linkable objects for disk '{disk_label}' — no .c or .s files found in {build_src}")

            steps.extend([
                (link_ld65,          [link_objects, prg_file, archtype, linker_cfg], {}, f"[{disk_label}] Link ld65"),
                (create_blank_d64,   [d64_file],                                     {}, f"[{disk_label}] Create blank d64"),
                (format_and_copyd64, [d64_file, prg_file],                           {}, f"[{disk_label}] Format and copy to d64"),
            ])
            artifact_paths.extend([prg_file, d64_file])

        log.append(f"steps to run: {len(steps)}")

        for func, args, kwargs_func, label in steps:
            log.append(f"Running: {label}")
            try:
                success, out = func(*args, **kwargs_func)
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                origin = tb[-1] if tb else None
                location = f"{origin.filename}:{origin.lineno} in {origin.name}" if origin else "unknown location"
                raise RuntimeError(f"Exception in step '{label}' [{location}]: {type(e).__name__}: {e}") from e
            log.append(f"{label}:\n{out}")
            if not success:
                raise RuntimeError(f"Step returned failure: {label}")

        for art in artifact_paths:
            log.append(f"ARTIFACT: {art}")

    except Exception as e:
        tb_lines = traceback.format_exc().splitlines()
        log.append(f"EXCEPTION ({type(e).__name__}): {e}")
        log.append(f"TRACEBACK:\n" + "\n".join(tb_lines))
        if isinstance(context, dict):
            context["abort"] = True
        return False, "\n".join(log)

    return True, "\n".join(log)


@dispatchtest_step
def test_compile4atari(out_dir=None, src_dir=None, prg_filepath=None, config=None, **kwargs):
    import os
    import subprocess
    context = kwargs.get("context", {})

    if not config:
        return False, "Missing config"

    res_out_dir = resolve_path(out_dir if out_dir != 'None' else config.get("out_dir"), config)
    res_src_dir = resolve_path(src_dir if src_dir != 'None' else config.get("src"), config)
    res_prg_path = resolve_path(prg_filepath if prg_filepath != 'None' else config.get("prg_filepath"), config)
    
    os.makedirs(res_out_dir, exist_ok=True)

    cmainfile = config.get("cmainfile", "")
    source_file = os.path.normpath(os.path.join(res_src_dir, cmainfile))

    log = []
    try:
        result = subprocess.run(
            ["m68k-atari-mintelf-gcc", source_file, "-lgem", "-o", res_prg_path],
            cwd=res_out_dir,
            capture_output=True,
            text=True
        )
        log.append(result.stdout)
        log.append(result.stderr)
        
        if result.returncode != 0:
            context["abort"] = True
            return False, "\n".join(log)
            
    except Exception as e:
        context["abort"] = True
        return False, str(e)

    if not os.path.exists(res_prg_path):
        context["abort"] = True
        log.append(f"Output file not found: {res_prg_path}")
        return False, "\n".join(log)

    log.append(f"ARTIFACT: {res_prg_path}")

    return True, "\n".join(log)




@dispatchtest_step
def test_sendrun(name="vice1", **kwargs):
    context = kwargs.get("context", {})
    target_name = name
    instance = context.get(target_name)

    if not isinstance(instance, ViceInstance):
        return False, f"No ViceInstance named '{target_name}' found in context"

    log = []
    try:
        success, output = send_vice_command(context, target_name, 'LOAD "*",8\n')
        time.sleep(3)
        success, output = send_vice_command(context, target_name, "RUN\n")
        
        instance.take_screenshot()
        
        log.append(f"Sent RUN to {target_name}:\n{output}")
        return True, "\n".join(log)
    except Exception as e:
        return False, f"Failed to send to {target_name}: {e}"


@dispatchtest_step
def test_basic_sendlistdisk(disk_idnum, name="vice1", **kwargs):
    context = kwargs.get("context", {})
    target_name = name
    instance = context.get(target_name)

    if not isinstance(instance, ViceInstance):
        return False, f"No ViceInstance named '{target_name}' found in context"

    log = []
    try:
        success, output = send_vice_command(context, target_name, f'load "$",{disk_idnum}\n')
        time.sleep(3)
        success, output = send_vice_command(context, target_name, "list\n")
        
        instance.take_screenshot()
        
        log.append(f"Sent RUN to {target_name}:\n{output}")
        return True, "\n".join(log)
    except Exception as e:
        return False, f"Failed to send to {target_name}: {e}"
    

@dispatchtest_step
def test_sendastring(inputkeyboardstring=None, name="vice1", **kwargs):
    context = kwargs.get("context", {})
    target_name = name
    instance = context.get(target_name)

    if not isinstance(instance, ViceInstance):
        return False, f"No ViceInstance named '{target_name}' found in context"

    log = []
    try:
        success, output = send_vice_command(context, target_name, inputkeyboardstring)
        instance.take_screenshot()

        log.append(f"Sent RUN to {target_name}:\n{output}")
        return True, "\n".join(log)
    except Exception as e:
        return False, f"Failed to send to {target_name}: {e}"


_KEY_PETSCII = {
    "up": 0x91, "down": 0x11, "left": 0x9D, "right": 0x1D,
    "return": 0x0D, "enter": 0x0D, "space": 0x20,
    "del": 0x14, "home": 0x13, "clear": 0x93,
    "f1": 0x85, "f3": 0x86, "f5": 0x87, "f7": 0x88,
}


@dispatchtest_step
def test_sendkey(key=None, name="vice1", **kwargs):
    """Inject a single keypress into a VICE instance's keyboard buffer.

    `key` may be a name (up/down/left/right/return/space/f1...) or a raw
    PETSCII code ("0x11", "17"). Targets context[name] (default 'vice1')."""
    context = kwargs.get("context", {})
    target_name = name
    instance = context.get(target_name)

    if not isinstance(instance, ViceInstance):
        return False, f"No ViceInstance named '{target_name}' found in context"

    if key is None or str(key).strip() == "":
        return False, "No key specified"

    k = str(key).strip().lower()
    if k in _KEY_PETSCII:
        raw = _KEY_PETSCII[k]
    else:
        try:
            raw = int(k, 0) & 0xFF
        except ValueError:
            return False, f"Unknown key: {key!r} (use a name or a PETSCII code like 0x11)"

    log = []
    try:
        # Place the PETSCII byte in KEYD ($0277) and set NDX ($00C6)=1.
        log.append(send_single_command(context, target_name, f"f 0277 0277 {raw:02X}"))
        log.append(send_single_command(context, target_name, "f 00c6 00c6 01"))
        time.sleep(0.5)
        instance.take_screenshot()
        log.append(f"Sent key {key!r} (PETSCII ${raw:02X}) to {target_name}")
        return True, "\n".join(log)
    except Exception as e:
        return False, f"Failed to send key to {target_name}: {e}"


# C64 colour palette index by name (for $D020/$D021 register checks).
_C64_COLORS = {
    "black": 0, "white": 1, "red": 2, "cyan": 3, "purple": 4, "green": 5,
    "blue": 6, "yellow": 7, "orange": 8, "brown": 9, "lightred": 10,
    "darkgrey": 11, "darkgray": 11, "grey": 12, "gray": 12, "lightgreen": 13,
    "lightblue": 14, "lightgrey": 15, "lightgray": 15,
}


@dispatchtest_step
def test_checkbordercolor(expected=None, name="vice1", numberofattempts=10, attemptdelay=1, **kwargs):
    """Confirm a VICE instance's border colour ($D020) over the monitor.

    Reads the VIC-II border register directly (low nibble = colour 0-15;
    bits 4-7 read back as 1, so they are masked off). `expected` may be a
    colour name (blue/red/...) or a numeric index. Targets context[name]
    (default 'vice1'). Aborts the run on mismatch."""
    import re as _re

    context = kwargs.get("context", {})
    target_name = name
    instance = context.get(target_name)

    if not isinstance(instance, ViceInstance):
        return False, f"No ViceInstance named '{target_name}' found in context"

    if expected is None or str(expected).strip() == "":
        return False, "No expected color specified"

    e = str(expected).strip().lower()
    if e in _C64_COLORS:
        want = _C64_COLORS[e]
    else:
        try:
            want = int(e, 0) & 0x0F
        except ValueError:
            return False, f"Unknown color: {expected!r}"

    numberofattempts = int(numberofattempts)
    attemptdelay = int(attemptdelay)

    # Memory-dump line for $D020 looks like ">C:d020  f6 ..": grab the first
    # 2-hex byte that follows the address (and is not part of a 4-hex address,
    # so the echoed 'm d020 d020' command can't be mis-parsed).
    pat = _re.compile(r"(?i)d020\s+([0-9a-f]{2})(?![0-9a-f])")

    log = []
    last = None
    for attempt in range(numberofattempts):
        resp = send_single_command(context, target_name, "m d020 d020")
        matches = pat.findall(resp or "")
        if matches:
            last = int(matches[-1], 16) & 0x0F
            log.append(f"attempt {attempt}: border=${last:02X} ({last}) want={want}")
            if last == want:
                instance.take_screenshot()
                log.append(f"{target_name} border color is {expected} ({want}) - OK")
                return True, "\n".join(log)
        else:
            log.append(f"attempt {attempt}: could not parse border from monitor response:\n{resp}")
        time.sleep(attemptdelay)

    instance.take_screenshot()
    log.append(f"{target_name} border never reached {expected} ({want}); last seen={last}")
    context["abort"] = True
    return False, "\n".join(log)


@dispatchtest_step
def test_terminate_all(**kwargs):
    log = []
    context = kwargs.get("context", {})
    
    to_stop = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            to_stop.append((name, instance))

    for name, instance in to_stop:
        log.append(f"Stopping {name} on port {instance.port}")
        instance.stop()
        log.append(f"{name} has exited.")
        
    if not log:
        log.append("No VICE instances found to stop.")
        
    return True, "\n".join(log)


@dispatchtest_step
def test_wordsearch(successphrase=None, failphrase=None, c128windowcolnum=None, numberofattempts=10, attemptdelay=3, **kwargs):
    # need to pass these args into function scanner later
    context = kwargs.get("context", {})

    # need to set things we expect to be numbers as ints
    numberofattempts = int(kwargs.get("numberofattempts", numberofattempts))
    attemptdelay = int(kwargs.get("attemptdelay", attemptdelay))
    # c128windowcolnum = "80col"
    # c128windowcolnum = "40col"
    log = []
    abort = False

    for name, instance in context.items():
        if not isinstance(instance, ViceInstance):
            continue

        attempt = 0
        screentext = ""
        found_status = False

        while attempt < numberofattempts:
            screentext = instance.screentextdump(context, window=c128windowcolnum)
            if screentext is None:
                log.append(f"{name} screentextdump returned None")
                return False, "\n".join(log)
            screentext = screentext.lower()


            if failphrase in screentext:
                log.append(f"{name} - failphrase {failphrase} found at attempt {attempt}.  ")
                abort = True
                found_status = True
                break

            if successphrase in screentext:
                log.append(f"{name} - successphrase {successphrase} found at attempt {attempt}.  ")
                found_status = True
                break

            time.sleep(attemptdelay)
            attempt += 1

        if not found_status:
            log.append(f"{name} did not report success or failure")
            abort = True

        log.append(f"{name} screentext:\n{screentext}")

        if instance.take_screenshot(window=c128windowcolnum):
            log.append(f"Screenshot for {name} taken")
        else:
            log.append(f"Screenshot for {name} failed")
            abort = True

    if not log:
        log.append("No ViceInstances found in context")

    if abort:
        context["abort"] = True
        for name, instance in context.items():
            if isinstance(instance, ViceInstance):
                log.append(f"Stopping {name} on port {instance.port}")
                instance.stop()
        return False, "\n".join(log)

    return True, "\n".join(log)


@dispatchtest_step
def test_relay_start(port=6501, **kwargs):
    log = []
    context = kwargs.get("context", {})
    name = "relay_server"

    relay_info = context.get(name)
    if relay_info and relay_info.get("started"):
        log.append(f"{name} was already started")
        return True, "\n".join(log)

    server_thread = threading.Thread(target=ip232relayserver.start_server, daemon=True)
    server_thread.start()
    context[name] = {"thread": server_thread, "started": True}
    log.append(f"{name} started on port {port}")

    return True, "\n".join(log)


@dispatchtest_step
def test_relay_reset(**kwargs):
    """Clear the relay's per-client sent/received capture buffers and symbol
    counts"""
    ip232relayserver.reset_client_stats()
    return True, "relay client stats reset"


@dispatchtest_step
def test_relay_stop(**kwargs):
    log = []
    context = kwargs.get("context", {})
    name = "relay_server"

    relay_info = context.get(name)
    if not relay_info or not relay_info.get("started"):
        return False, "error: relay server was not running"

    # Pass the instance start order so the relay labels each connection with
    # its Python-side instance name (vice1_rx / vice2_tx) instead of the
    # anonymous connect-order name.
    start_order = context.get("_vice_start_order", [])
    thread = relay_info.get("thread")
    logs = ip232relayserver.stop_server(instance_names=start_order)
    if thread:
        thread.join(timeout=5)
    relay_info["started"] = False

    log.append("relay stopped")
    log.extend(logs)

    return True, "\n".join(log)


def _phrase_in_screen(instance, context, phrase):
    """True if `phrase` (case-insensitive) appears in the instance's screen,
    read from screen RAM via the VICE monitor (screentextdump uses 'sc')."""
    try:
        screen = instance.screentextdump(context)
    except Exception as e:
        return False, f"screentextdump error: {e}"
    if screen is None:
        return False, "screentextdump returned None"
    return (phrase.lower() in screen.lower()), screen


@dispatchtest_step
def test_checkrelaytraffic(name="vice1", direction="recv", contains=None,
                           exact=False, check_screen=False,
                           numberofattempts=10, attemptdelay=1, **kwargs):
    """Validate what a named instance sent/received via the relay, and
    optionally cross-check the emulator screen.

    Correlates the relay connection to the instance by connect order, then:
      - direction "recv" (default) / "sent" selects which relay buffer to check
      - contains      — required phrase (case-insensitive)
      - exact=True    — the relay payload must equal `contains` exactly once
                        stripped (proves NO extra garbage chars on the wire)
      - check_screen  — also confirm the phrase is present on the instance's
                        screen (read from screen RAM via the remote monitor),
                        so relay and screen are validated to carry the same
                        basic phrase.
    Aborts on failure. Run while the relay is still up (before relay_stop)."""
    context = kwargs.get("context", {})
    start_order = context.get("_vice_start_order", [])
    direction = (direction or "recv").strip().lower()
    want = (contains or "")
    exact = str(exact).strip().lower() in ("1", "true", "yes")
    check_screen = str(check_screen).strip().lower() in ("1", "true", "yes")

    numberofattempts = int(numberofattempts)
    attemptdelay = int(attemptdelay)

    instance = context.get(name)

    log = []
    last = None
    for attempt in range(numberofattempts):
        sent, recv = ip232relayserver.get_client_traffic(start_order, name)
        if sent is None and recv is None:
            log.append(f"attempt {attempt}: no relay connection correlated to '{name}' yet")
            time.sleep(attemptdelay)
            continue

        hay = recv if direction == "recv" else sent
        last = hay
        log.append(f"attempt {attempt}: {name} relay {direction} chars = {hay!r}")

        if exact:
            relay_ok = (hay or "").strip().lower() == want.lower()
        else:
            relay_ok = (not want) or (want.lower() in (hay or "").lower())

        if not relay_ok:
            time.sleep(attemptdelay)
            continue

        # Relay side satisfied — optionally confirm the screen agrees.
        if check_screen and want:
            if not isinstance(instance, ViceInstance):
                log.append(f"check_screen requested but no ViceInstance '{name}' in context")
                context["abort"] = True
                return False, "\n".join(log)
            screen_ok, screen = _phrase_in_screen(instance, context, want)
            log.append(f"  screen contains {want!r}: {screen_ok}")
            if not screen_ok:
                log.append(f"  screen text:\n{screen}")
                time.sleep(attemptdelay)
                continue
            instance.take_screenshot()

        mode = "exact" if exact else "contains"
        log.append(f"{name} relay {direction} [{mode}] {want!r} OK"
                   + (" + screen match" if check_screen else ""))
        return True, "\n".join(log)

    log.append(f"{name} {direction} validation failed for {want!r} "
               f"(exact={exact}, check_screen={check_screen}); last relay={last!r}")
    context["abort"] = True
    return False, "\n".join(log)
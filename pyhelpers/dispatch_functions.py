from testsrc.pyhelpers.vicehelpers import send_vice_command, ViceInstance, send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from testsrc.pyhelpers.vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
import time
import os

from testsrc.pyhelpers.atarihelpers import HatariInstance



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
    context = kwargs.get("context")
    if not context:
        return False, "No emulator instances in context"

    # Ensure context is a dict
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

    name, port = next_vice_instance(context)

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

    started = instance.start()
    context[name] = instance

    import time
    time.sleep(0.5)

    stdout_lines = instance.get_output()
    if stdout_lines:
        log.append("VICE stdout:")
        log.append("".join(stdout_lines))

    instance.take_screenshot()
    log.append(f"Launching {name} on port {port} with disk8={disk8_path} disk9={disk9_path} config={viceconf}")
    log.append("Command: " + " ".join(instance.cmd))

    return True, "\n".join(log)





@dispatchtest_step
def test_compiletheprogram(out_dir=None, src_dir=None, cmainfile=None,
                           drv1_path=None, drv1_label=None,
                           prg_filepath=None, d64_file=None,
                           archtype=None, **kwargs):
    import os
    import glob
    context = kwargs.get("context")
    config = kwargs.get("config", {})

    if not config:
        return False, "Missing config"

    archtype = archtype or config.get("archtype", "")

    res_out_dir = resolve_path(out_dir or config.get("out_dir"), config)
    res_src_dir = resolve_path(src_dir or config.get("src"), config)
    res_prg_file = resolve_path(prg_filepath or config.get("prg_filepath"), config)

    d64_filename = config.get("cmainfile", "disk") + ".d64"
    res_d64_file = resolve_path(d64_file or os.path.join(res_out_dir, d64_filename), config)

    drv1_path = drv1_path or config.get("linker_driver1")
    drv1_label = drv1_label or config.get("driver1_label")

    os.makedirs(res_out_dir, exist_ok=True)
    log = []
    steps = []
    link_objects = []

    c_files = glob.glob(os.path.join(res_src_dir, "*.c"))
    
    for src_c in c_files:
        base_name = os.path.splitext(os.path.basename(src_c))[0]
        asm_file = os.path.join(res_out_dir, f"{base_name}.s")
        obj_file = os.path.join(res_out_dir, f"{base_name}.o")
        
        steps.extend([
            (compile_cc65, [src_c, asm_file, archtype], {"optimize": True}, f"Compile cc65 {base_name}"),
            (assemble_ca65, [asm_file, obj_file, archtype], {}, f"Assemble ca65 {base_name}")
        ])
        link_objects.append(obj_file)

    s_files = glob.glob(os.path.join(res_src_dir, "*.s"))
    
    for src_s in s_files:
        base_name = os.path.splitext(os.path.basename(src_s))[0]
        obj_file = os.path.join(res_out_dir, f"{base_name}_asm.o")
        
        steps.append(
            (assemble_ca65, [src_s, obj_file, archtype], {}, f"Assemble ca65 {base_name} (source)")
        )
        link_objects.append(obj_file)

    if drv1_path and drv1_label:
        driver_ser = resolve_path(drv1_path, config)
        driver_s = os.path.join(res_out_dir, os.path.basename(drv1_path) + ".s")
        driver_o = os.path.join(res_out_dir, os.path.basename(drv1_path) + ".o")

        steps.extend([
            (assemble_object, [driver_ser, driver_s, drv1_label], {}, "Assemble driver object"),
            (assemble_ca65, [driver_s, driver_o, archtype], {}, "Assemble driver ca65"),
        ])
        link_objects.append(driver_o)

    steps.extend([
        (link_ld65, [link_objects, res_prg_file, archtype], {}, "Link ld65"),
        (create_blank_d64, [res_d64_file], {}, "Create blank d64"),
        (format_and_copyd64, [res_d64_file, res_prg_file], {}, "Format and copy to d64")
    ])

    for func, args, kwargs_func, label in steps:
        success, out = func(*args, **kwargs_func)
        log.append(f"{label}:\n{out}")
        if not success:
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

    return True, "\n".join(log)




@dispatchtest_step
def test_sendrun(**kwargs):
    context = kwargs.get("context", {})
    target_name = kwargs.get("name", "vice1")
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
def test_basic_sendlistdisk(disk_idnum, **kwargs):
    context = kwargs.get("context", {})
    target_name = kwargs.get("name", "vice1")
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
def test_sendastring(inputkeyboardstring=None, **kwargs):
    context = kwargs.get("context", {})
    target_name = kwargs.get("name", "vice1")
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




from testsrc.pyhelpers.vicehelpers import send_vice_command, ViceInstance, send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from testsrc.pyhelpers.vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
import time
import os


# this is for returning only decorated def's found in this file
def dispatchtest_step(func):
    func._is_teststep = True
    return func


@dispatchtest_step
def test_emulator_start(name=None, port=6502, disk_path=None, warpmode=True, **kwargs):
    print("ppfft1")
    log = []

    context = kwargs.get("context")
    config = kwargs.get("config")

    if not config:
        return False, "Missing config"

    archtype = config.get("archtype")
    paths = config.get("paths", {})

    viceconf = paths.get("viceconf")
    d64_file = paths.get("d64file_abs")# if disk_path is None else disk_path

    name, port = next_vice_instance(context)

    instance = ViceInstance(
        name,
        port,
        archtype,
        config_path=viceconf,
        disk_path=d64_file
    )

    started = instance.start()
    context[name] = instance

    time.sleep(0.5)
    instance.take_screenshot()

    log.append(f"Launching {name} on port {port} with disk={d64_file} config={viceconf}")
    return True, "\n".join(log)


@dispatchtest_step
def test_compiletheprogram(**kwargs):
    # every test needs this vvv
    context = kwargs.get("context")
    config = kwargs.get("config")
    paths = config.get("paths", {})
    # every test needs this ^^^

    out_dir = paths.get("out")
    src_dir = paths.get("src")
    prg_file = paths.get("prg")
    d64_file = paths.get("d64file_abs")

    source_file = os.path.join(src_dir, config["cmainfile"] + ".c")
    asm_file = os.path.join(out_dir, config["cmainfile"] + ".s")
    obj_file = os.path.join(out_dir, config["cmainfile"] + ".o")

    os.makedirs(out_dir, exist_ok=True)
    log = []

    success, out = compile_cc65(source_file, asm_file, config["archtype"])
    log.append("Compile cc65:\n" + out)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    success, out = assemble_ca65(asm_file, obj_file, config["archtype"])
    log.append("Assemble ca65:\n" + out)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    success, out = link_ld65(obj_file, prg_file, config["archtype"])
    log.append("Link ld65:\n" + out)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    success, out = create_blank_d64(d64_file)
    log.append("Create blank d64:\n" + out)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    success, out = format_and_copyd64(d64_file, prg_file)
    log.append("Format and copy to d64:\n" + out)
    if not success:
        context["abort"] = True
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
def test_wordsearch(successphrase="saved", failphrase="failed", numberofattempts=10, attemptdelay=3, **kwargs):
    # need to pass these args into function scanner later
    context = kwargs.get("context", {})

    # need to set things we expect to be numbers as ints
    numberofattempts = int(kwargs.get("numberofattempts", numberofattempts))
    attemptdelay = int(kwargs.get("attemptdelay", attemptdelay))


    log = []
    abort = False

    for name, instance in context.items():
        if not isinstance(instance, ViceInstance):
            continue

        attempt = 0
        screentext = ""
        found_status = False

        while attempt < numberofattempts:
            screentext = instance.screentextdump(context).lower()

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

        if instance.take_screenshot():
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

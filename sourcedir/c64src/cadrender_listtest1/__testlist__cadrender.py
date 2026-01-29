import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "cadrender",
    "projdir": "cadrender_listtest1",            # projects main parent dir name, also used for testlist sorting
    "cmainfile": "main",                # c-file progname no extenion to give to compiler
    "testtype": "dirlisttest1",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "c64",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Graphics",             # 2nd tier sorting category
    "viceconf": "vice_nosound.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/c64src/"
}

PATHS = init_test_env(CONFIG, __name__)
testtype = CONFIG["testtype"]
archtype = CONFIG["archtype"]
progname = CONFIG["cmainfile"]
archtype = CONFIG["archtype"]
viceconf = os.path.join(CONFIG["projbasedir"], CONFIG["projdir"], CONFIG["viceconf"])
src_dir = PATHS["src"]
out_dir = PATHS["out"]
d64_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".d64")



@register_mytest(testtype, "Compile")
def cc65_c64compile(context):
    archtype = CONFIG["archtype"]
    os.makedirs(PATHS["out"], exist_ok=True)

    c_src_files = [os.path.join(PATHS["src"], f) 
                   for f in os.listdir(PATHS["src"]) 
                   if f.lower().endswith(".c")]

    obj_files = [os.path.join(PATHS["out"], os.path.splitext(os.path.basename(f))[0] + ".o")
                 for f in c_src_files]
    print("Found C files:", c_src_files, "in dir: ", PATHS["src"])
    log = []

    for src, obj in zip(c_src_files, obj_files):
        asm_file = os.path.splitext(obj)[0] + ".s"
        # add -Cl to the compile flags
        success, out = compile_cc65(src, asm_file, CONFIG["archtype"], extra_flags=["-Cl"])
        log.append(f"compile_cc65 {src}:\n{out}")
        if not success:
            context["abort"] = True
            return False, "\n".join(log)


        success, out = assemble_ca65(asm_file, obj, CONFIG["archtype"])
        log.append(f"assemble_ca65 {asm_file}:\n{out}")
        if not success:
            context["abort"] = True
            return False, "\n".join(log)

    prg_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".prg")
    success, out = link_ld65(obj_files, prg_file, CONFIG["archtype"])
    log.append(f"link_ld65:\n{out}")
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    d64_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".d64")
    success, out = create_blank_d64(d64_file)
    log.append(f"create_blank_d64:\n{out}")
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    success, out = format_and_copyd64(d64_file, prg_file)
    log.append(f"format_and_copyd64:\n{out}")
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    return True, "\n".join(log)


@register_mytest(testtype, "start vice instance")
def test_startviceemulator(context):
    name, port = next_vice_instance(context)
    log = []
    
    try:
        instance = ViceInstance(name, port, archtype, config_path=viceconf, autostart=d64_file)
        log.append(f"Launching {name} on port {port} with disk={d64_file} config={viceconf}")

        started = instance.start()
        if not started:
            log.append(f"{name} failed to start (no window ID detected).")
            context["abort"] = True
            return False, "\n".join(log)

    except Exception as e:
        log.append(f"CRITICAL: Python error during startup: {str(e)}")
        context["abort"] = True
        return False, "\n".join(log)

    time.sleep(3)

    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
        context["abort"] = True
        return False, "\n".join(log)

    context[name] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
    return True, "\n".join(log)


@register_mytest(testtype, "Screenshot after boot")
def screenshotboot(context):
    log = []
    abort = False

    for name, instance in context.items():
        if not isinstance(instance, ViceInstance):
            continue

        if instance.take_screenshot(test_step=3):
            log.append(f"Screenshot for {name} taken")
        else:
            log.append(f"Screenshot for {name} failed")
            abort = True

    if not log:
        log.append("No ViceInstances found in context")

    if abort:
        context["abort"] = True
        return False, "\n".join(log)

    return True, "\n".join(log)


@register_mytest(testtype, "Check for file write success")
def filewrite_check(context):
    log = []
    abort = False

    for name, instance in context.items():
        if not isinstance(instance, ViceInstance):
            continue

        attempt = 0
        screentext = ""
        found_status = False

        while attempt < 10:
            screentext = instance.screentextdump(context)
            #text = screentext.lower()

            if "FAILED" in screentext:
                log.append(f"{name} - save to disk failure")
                abort = True
                found_status = True
                break

            if "PASSED" in screentext:
                log.append(f"{name} reported success")
                found_status = True
                break

            time.sleep(3)
            attempt += 1

        if not found_status:
            log.append(f"{name} did not report success or failure")
            abort = True

        log.append(f"{name} screentext:\n{screentext}")

        if instance.take_screenshot(test_step=4):
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


@register_mytest(testtype, "terminate all")
def terminatevice(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    return True, "\n".join(log)

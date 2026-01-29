import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"


CONFIG = {
    "testname": "SID Music",            # projects main parent dir name, also used for testlist sorting
    "projdir": "sidplayer", 
    "cmainfile": "sidplayer",           # c-file progname no extenion to give to compiler
    "testtype": "build",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "c64",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Graphics",             # 2nd tier sorting category
    "viceconf": "vice_nosound.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
    "linkerconf": "c64-sid.cfg",        # linker conf filename, in proj basedir
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
def build1_compile(context):
    src_dir = PATHS["src"]
    progname = PATHS["cmainfile"]
    out_dir = PATHS["out"]
    config = PATHS["viceconf"]
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + "main.s")
    obj_file    = os.path.join(out_dir, progname + "main.o")
    prg_file    = os.path.join(out_dir, progname + "main.prg")
    d64_file    = os.path.join(out_dir, progname + ".d64")
    linkerconf  = os.path.join(src_dir, PATHS["linkerconf"])
    asm_include = os.path.join(src_dir, "sidplaysfx.s")
    asm_object  = os.path.join(out_dir, "sidplaysfx.o")

    helper_sources = [asm_include]  
    helper_objects = [asm_object]

    log = []
    steps = [
        (compile_cc65, source_file, asm_file, archtype),
        (assemble_ca65, asm_file, obj_file, archtype),
    ]

    for s, o in zip(helper_sources, helper_objects):
        steps.append((assemble_ca65, s, o, archtype))

    all_objects = [obj_file] + helper_objects
    steps.append((link_ld65, all_objects, prg_file, archtype, linkerconf))
    steps.append((create_blank_d64, d64_file))
    steps.append((format_and_copyd64, d64_file, prg_file))

    for func, *args in steps:
        success, out = func(*args)
        log.append(f"{func.__name__}:\n{out}")
        if not success:
            context["abort"] = True
            return False, "\n".join(log)

    return True, "\n".join(log)


@register_mytest(testtype, "start vice instance")
def test_startviceemulator(context):
    name, port = next_vice_instance(context)
    log = []
    
    try:
        instance = ViceInstance(name, port, archtype, config_path=viceconf, disk_path=d64_file)
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


@register_mytest(testtype, "screenshot after boot command")
def build3_screenshot_both(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            success = instance.take_screenshot(test_step=4)
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after program start")
def build4_screenshot_both(context):
    log = []
    time.sleep(15)  # takes a long time to laod the program
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            success = instance.take_screenshot(test_step=5)
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_mytest(testtype, "terminate all")
def build5_stopallvice(context):
    log = []
    time.sleep(1)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    return True, "\n".join(log)

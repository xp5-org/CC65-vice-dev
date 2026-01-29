import sys
import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_c128_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "C128-VDC2.tgi 640x480",            # nickname for 
    "projdir": "tgi_640x480", 
    "cmainfile": "main",                # c-file progname no extenion to give to compiler
    "testtype": "build",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "c128",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Graphics",             # 2nd tier sorting category
    "viceconf": "c128_viceconf.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/c128src/"
}

PATHS = init_test_env(CONFIG, __name__)
testtype = CONFIG["testtype"]
archtype = CONFIG["archtype"]
viceconf = os.path.join(CONFIG["projbasedir"], CONFIG["projdir"], CONFIG["viceconf"])
prg_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".prg")
d64_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".d64")
progname = CONFIG["cmainfile"]
src_dir = PATHS["src"]
out_dir = PATHS["out"]
d64_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".d64")



@register_mytest(testtype, "Compile")
def build1_compile(context):
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, "main.c")
    asm_file    = os.path.join(out_dir, progname + "main.s")
    obj_file    = os.path.join(out_dir, progname + "main.o")
    prg_file    = os.path.join(out_dir, progname + ".prg")
    d64_file    = os.path.join(out_dir, progname + ".d64")
    # driver path info
    driver_ser = os.path.join(src_dir, "c128-vdc2.tgi")
    driver_s   = os.path.join(out_dir, "c128-vdc2.s")
    driver_o   = os.path.join(out_dir, "c128-vdc2.o")
    driver_label = "_c128_640x480"

    log = []
    steps = [
        (compile_cc65, source_file, asm_file, archtype),
        (assemble_ca65, asm_file, obj_file, archtype),
        (assemble_object, driver_ser, driver_s, driver_label),
        (assemble_ca65, driver_s, driver_o, archtype),
        (link_ld65, [obj_file, driver_o], prg_file, archtype),
        (create_blank_d64, d64_file),
        (format_and_copyd64, d64_file, prg_file),
    ]

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


@register_mytest(testtype, "send RUN")
def test3_c128(context):
    log = []
    for name in ["vice1"]:
        try:
            success, output = send_c128_command(context, name, 'LOAD "*",8')
            time.sleep(3)
            success, output = send_c128_command(context, name, "RUN")
            log.append(f"Sent RUN to {name}:\n{output}")
        except Exception as e:
            log.append(f"Failed to send to {name}: {e}")
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after boot command")
def build4_screenshot_both(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            #print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshotc128(test_step=4, window="40col")
            success = instance.take_screenshotc128(test_step=4, window="80col")
            #print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        #print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after program start")
def build5_screenshot_both(context):
    name, port = next_vice_instance(context)
    log = []
    time.sleep(15)  # takes a long time to laod the program
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            #print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshotc128(test_step=5, window="40col")
            success = instance.take_screenshotc128(test_step=5, window="80col")
            #print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        #print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)


@register_mytest(testtype, "terminate all")
def build6_stopallvice(context):
    log = []
    #print("waiting 3s before teardown")
    time.sleep(3)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    return True, "\n".join(log)
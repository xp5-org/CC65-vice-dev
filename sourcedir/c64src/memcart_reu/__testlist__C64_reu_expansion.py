import sys
import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "reutest",            # nickname for 
    "projdir": "memcart_reu", 
    "cmainfile": "memcart_reu",                # c-file progname no extenion to give to compiler
    "testtype": "build",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "c64",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Devices",             # 2nd tier sorting category
    "viceconf": "vice_reu256k.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
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
def build1_compile(context):
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + "main.s")
    obj_file    = os.path.join(out_dir, progname + "main.o")
    prg_file    = os.path.join(out_dir, progname + ".prg")
    d64_file    = os.path.join(out_dir, progname + ".d64")
    
    driver_ser = os.path.join(src_dir, "c64-reu.emd")
    driver_s   = os.path.join(out_dir, "c64-reu.s")
    driver_o   = os.path.join(out_dir, "c64-reu.o")
    driver_label = "_c64_reu"

    print()

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
def startvice(context):
    name, port = next_vice_instance(context)    
    print("VICE CONF DEBUG: ", viceconf)
    instance = ViceInstance(name, port, archtype, config_path=viceconf, autostart_path=d64_file)
    log = [f"Launching {name} on port {port} with \n disk={d64_file} \n autostart_path={d64_file} \n config={viceconf}"]
    
    success, log = launch_vice_instance(instance)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after boot command")
def build4_screenshot_both(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot()
            print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
            screentextoutput = instance.screentextdump(context)
            log.append(f"adssdsdas{screentextoutput}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)



@register_mytest(testtype, "check for driver install success")
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

            if "failed" in screentext:
                log.append(f"PYTHON TEST: CHECK SCREEN: \n {name} REU install failure")
                abort = True
                found_status = True
                break

            if "successfully" in screentext:
                log.append(f"PYTHON TEST: CHECK SCREEN: \n {name} REU reported success")
                found_status = True
                break

            time.sleep(3)
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


@register_mytest(testtype, "screenshot after program start")
def build5_screenshot_both(context):
    log = []
    time.sleep(2)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=4)
            print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
            screentextoutput = instance.screentextdump(context)
            log.append(f"Screentext Output: {screentextoutput}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_mytest(testtype, "terminate all")
def build6_stopallvice(context):
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

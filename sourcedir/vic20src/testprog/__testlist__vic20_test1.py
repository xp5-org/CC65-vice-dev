import sys
import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "vic20 text pattern",            # nickname for 
    "projdir": "testprog", 
    "cmainfile": "testprog",                # c-file progname no extenion to give to compiler
    "testtype": "build",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "vic20",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Graphics",             # 2nd tier sorting category
    "viceconf": "vic20_viceconf.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/vic20src/"
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
def test1_vic20(context):
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, 'testprog.c')
    asm_file = os.path.join(out_dir, 'testprog.s')
    obj_file = os.path.join(out_dir, 'testprog.o')
    prg_file = os.path.join(out_dir, 'testprog.prg')
    d64_file = os.path.join(out_dir, 'testprog.d64')

    log = []

    success, out = compile_cc65(source_file, asm_file, archtype)
    log.append("Compile cc65:\n" + out)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    success, out = assemble_ca65(asm_file, obj_file, archtype)
    log.append("Assemble ca65:\n" + out)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    success, out = link_ld65(obj_file, prg_file, archtype)
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
def test3_vic20(context):
    log = []
    for name in ["vice1"]:
        try:
            success, output = send_vice_command(context, name, 'LOAD "*",8\n')
            time.sleep(3)
            success, output = send_vice_command(context, name, "RUN\n")
            log.append(f"Sent RUN to {name}:\n{output}")
        except Exception as e:
            log.append(f"Failed to send to {name}: {e}")
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after boot command")
def test4_vic20(context):
    log = []
    for name in ["vice1"]:
        instance = context.get(name)
        if instance:
            success = instance.take_screenshot()
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after program start")
def mytest_screenshot(context):
    log = []
    time.sleep(5) #replace with some OCR logic or something
    for name in ["vice1"]:
        instance = context.get(name)
        if instance:
            success = instance.take_screenshot()
            screentextoutput = instance.screentextdump(context)
            log.append(f"adssdsdas{screentextoutput}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)


@register_mytest(testtype, "terminate all")
def mytest_terminate(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    return True, "\n".join(log)
import sys
import os
import time

# auto import /mytests dir as modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 
TESTSRC_TESTLISTDIR = "/testsrc/mytests"
TESTSRC_BASEDIR = "/testsrc"
TESTSRC_HELPERDIR = "/testsrc/pyhelpers"

# make app helpers dir visible
if TESTSRC_HELPERDIR  not in sys.path:
    sys.path.insert(0, TESTSRC_HELPERDIR )


from apphelpers import register_testfile, register_buildtest
from vicehelpers import send_c128_command, ViceInstance, next_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"


register_testfile(
    id="C128 text print",
    types=["build"],
    system="C128",
    platform="Graphics",
)(sys.modules[__name__])


archtype = 'pet'
src_dir = '/testsrc/sourcedir/c128src/textprint'
out_dir = src_dir + '/output'


@register_buildtest("build 1 - testprog")
def test1_cbmpet(context):
    progname = "testprog"
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + "main.s")
    obj_file    = os.path.join(out_dir, progname + "main.o")
    prg_file    = os.path.join(out_dir, progname + "main.prg")
    d64_file    = os.path.join(out_dir, progname + ".d64")

    log = []
    steps = [
        (compile_cc65, source_file, asm_file, archtype),
        (assemble_ca65, asm_file, obj_file, archtype),
        (link_ld65, obj_file, prg_file, archtype),
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


@register_buildtest("Build 3 - start xpet vice instance")
def test2_cbmpet(context):
    archtype = 'c128'
    name, port = next_vice_instance(context)
    disk = out_dir + "/testprog.d64"
    config = src_dir + "/vice_c128.cfg"
    
    instance = ViceInstance(name, port, archtype, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]

    started = instance.start()
    if not started:
        log.append(f"{name} failed to start (no window ID detected). Abandoning test.")
        context["abort"] = True
        return False, "\n".join(log)

    time.sleep(3)  # wait for boot

    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
        return False, "\n".join(log)

    context[name] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
    return True, "\n".join(log)



@register_buildtest("Build 4 - send RUN")
def test3_vic20(context):
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


@register_buildtest("Build 5 - screenshot after boot command")
def test4_vic20(context):
    log = []
    for name in ["vice1"]:
        instance = context.get(name)
        if instance:
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=4)
            print(f"Screenshot for {name} taken: {success}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)


@register_buildtest("Build 6 - screenshot after program start")
def test5_vic20(context):
    log = []
    time.sleep(5) #replace with some OCR logic or something
    for name in ["vice1"]:
        instance = context.get(name)
        if instance:
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=5)
            print(f"Screenshot for {name} taken: {success}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)



@register_buildtest("Build 8 - terminate all")
def test6_vic20(context):
    log = []
    print("waiting 3s before teardown")
    time.sleep(1)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    return True, "\n".join(log)
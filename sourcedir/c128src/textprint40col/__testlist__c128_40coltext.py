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
    id="C128 Text 40 Col",
    types=["build"],
    system="C128",
    platform="Text Printing",
)(sys.modules[__name__])

progname = "text40col"
archtype = 'c128'
src_dir = '/testsrc/sourcedir/c128src/textprint40col'
out_dir = src_dir + "/output"
d64path = out_dir + "/" + progname + ".d64"
config = src_dir + "/c128_viceconf.cfg"


@register_buildtest("build 1 - testprog")
def test1_c128(context):
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


@register_buildtest("Build 2 - start c128 vice instance")
def test2_c128(context):
    name, port = next_vice_instance(context)
    instance = ViceInstance(name, port, archtype, config_path=config, disk_path=d64path)
    log = [f"Launching {name} on port {port} with disk={d64path} config={config}"]

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


@register_buildtest("Build 3 - send RUN")
def test3_c128(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            success, output = send_c128_command(context, name, 'LOAD "*",8')
            time.sleep(3)
            success, output = send_c128_command(context, name, "RUN")
            log.append(f"Sent RUN to {name}:\n{output}")
            screentextoutput = instance.screentextdump(context)
            log.append(f"adssdsdas{screentextoutput}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_buildtest("Build 4 - screenshot after boot command")
def test4_c128(context):
    log = []
    for name in ["vice1"]:
        instance = context.get(name)
        if instance:
            #print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshotc128(test_step=4, window="40col")
            success = instance.take_screenshotc128(test_step=4, window="80col")
            screentextoutput = instance.screentextdump(context)
            log.append(f"adssdsdas{screentextoutput}")
            #print(f"Screenshot for {name} taken: {success}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)


@register_buildtest("Build 5 - screenshot after program start")
def test5_c128(context):
    log = []
    time.sleep(5) #replace with some OCR logic or something
    for name in ["vice1"]:
        instance = context.get(name)
        if instance:
            #print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshotc128(test_step=5, window="40col")
            success = instance.take_screenshotc128(test_step=5, window="80col")
            screentextoutput = instance.screentextdump(context)
            log.append(f"adssdsdas{screentextoutput}")
            #print(f"Screenshot for {name} taken: {success}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)



@register_buildtest("Build 6 - terminate all")
def test6_c128(context):
    log = []
    #print("waiting 3s before teardown")
    time.sleep(1)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    return True, "\n".join(log)
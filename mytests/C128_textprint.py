import sys
import os
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) #auto import /mytests dir as modules
from helpers import register_testfile, register_buildtest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance, ascii_to_petscii_c128, send_c128_command
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
import ip232relayserver
VICE_IP = "127.0.0.1"


#this is to track if the relay server is already started or not
relay_started = False
relay_lock = threading.Lock()


register_testfile(
    id="textprint",
    types=["build"],
    system="C128",
    platform="VICE",
)(sys.modules[__name__])


# testing this out probably should put it in the testfile registry?
srcbasedir = 'mysource'
tgtbaseditr = 'myoutput'
progname = "c128text"
archtype = "c128"


@register_buildtest("build 1 - tezxtprint")
def build1_c128textprint(context):
    src_dir = os.path.join(srcbasedir, archtype, progname)
    out_dir = os.path.join(srcbasedir, archtype, progname)
    os.makedirs(out_dir, exist_ok=True)

    # need to come up with a way to handle multiple file programs
    source_file = os.path.join(src_dir, progname + "_main.c") 
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



@register_buildtest("Build 3 - start c128 vice instance")
def build3_launch_c128textprint(context):
    progname = "textprint"
    out_dir = 'C128output/' + progname
    d64_file    = os.path.join(out_dir, progname + ".d64")

    name, port = next_vice_instance(context)
    instance = ViceInstance(name, port, 'c128', disk_path="C128output/cuberotate/cuberotate.d64")
    
    success, log = launch_vice_instance(instance)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)



@register_buildtest("Build 4 - send RUN")
def buil4_send_run(context):
    """Send LOAD "*",8 and RUN commands to a C128."""
    log = []
    for name in ["vice1"]:  # add more instance names if needed
        try:
            log.append(send_c128_command(context, name, 'LOAD "*",8'))
            time.sleep(3)
            log.append(send_c128_command(context, name, 'RUN'))
        except Exception as e:
            log.append(f"Failed to send to {name}: {e}")
    return True, "\n".join(log)



@register_buildtest("Build 5 - screenshot after boot command")
def build5_screenshot_both(context):
    log = []
    for name in ["vice1"]:
        instance = context.get(name)
        if instance:
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=5)
            print(f"Screenshot for {name} taken: {success}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)


@register_buildtest("Build 6 - screenshot after program start")
def build6_screenshot_both(context):
    log = []
    time.sleep(15) #replace with some OCR logic or something
    for name in ["vice1"]:
        instance = context.get(name)
        if instance:
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=6)
            print(f"Screenshot for {name} taken: {success}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)



@register_buildtest("Build 8 - terminate all")
def build8_stopallvice(context):
    log = []
    print("waiting 3s before teardown")
    time.sleep(3)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    return True, "\n".join(log)


@register_buildtest("Build 9 - terminate relay & collect logs")
def build9_stoprelay(context):
    log = []
    name = "relay_server"

    with relay_lock:
        relay_info = context.get(name)
        if relay_info and relay_info.get("started"):
            thread = relay_info.get("thread")
            logs = ip232relayserver.stop_server()  # this returns the per-client log lines
            if thread:
                thread.join(timeout=5)
            relay_info["started"] = False
            log.append("relay stopped")
            log.extend(logs)
        else:
            log.append("error: relay server was not running")

    return True, "\n".join(log)

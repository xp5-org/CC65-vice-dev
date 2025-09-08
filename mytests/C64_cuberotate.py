import sys
import os
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) #auto import /mytests dir as modules
from helpers import register_testfile, register_buildtest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
import ip232relayserver
VICE_IP = "127.0.0.1"


#this is to track if the relay server is already started or not
relay_started = False
relay_lock = threading.Lock()


register_testfile(
    id="cuberotate",
    types=["build"],
    system="C64",
    platform="VICE",
)(sys.modules[__name__])





@register_buildtest("build 1 - Cuberotate")
def build1_cuberotate(context):
    progname = "cuberotate"
    archtype = 'c64'
    src_dir = 'c64src/' + progname
    out_dir = 'c64output/' + progname
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + "main.c")
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



@register_buildtest("Build 3 - start cuberotate vice instance")
def build3_launch_cuberotate(context):
    archtype = 'c64'
    name, port = next_vice_instance(context)
    disk = "c64output/cuberotate/cuberotate.d64"
    config = "vice_ip232_tx.cfg"
    
    instance = ViceInstance(name, port, archtype, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]
    
    success, log = launch_vice_instance(instance)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)




@register_buildtest("Build 4 - send RUN")
def buil4_send_run(context):
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


@register_buildtest("Build 5 - screenshot after boot command")
def build5_screenshot_both(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=5)
            print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)



@register_buildtest("Build 6 - screenshot after program start")
def build6_screenshot_both(context):
    log = []
    time.sleep(35)  # takes a long time to laod the program
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=6)
            print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
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

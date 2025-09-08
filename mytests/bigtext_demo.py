import sys
import os
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) #auto import /mytests dir as modules
from helpers import register_testfile, register_buildtest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
import ip232relayserver
VICE_IP = "127.0.0.1"


#this is to track if the relay server is already started or not
relay_started = False
relay_lock = threading.Lock()


register_testfile(
    id="bigtext",
    types=["build"],
    system="C64",
    platform="VICE",
)(sys.modules[__name__])





@register_buildtest("Build 3 - start cuberotate vice instance")
def build3_launch_rx(context):
    name, port = next_vice_instance(context)
    disk = "c64output/cuberotate/cuberotatemain.prg"
    config = "vice_ip232_tx.cfg"
    
    instance = ViceInstance(name, port, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]

    started = instance.start()
    if not started:
        log.append(f"{name} failed to start (no window ID detected). Abandoning test.")
        context["abort"] = True
        return False, "\n".join(log)

    time.sleep(3)  # wait for C64 to boot

    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
        return False, "\n".join(log)

    context[name] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
    return True, "\n".join(log)



@register_buildtest("Build 4 - send RUN")
def buil4_send_run(context):
    log = []
    for name in ["vice1"]:
        try:
            success, output = send_vice_command(context, name, 'long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text long text ')
            time.sleep(3)
            log.append(f"Sent RUN to {name}:\n{output}")
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
    time.sleep(35) #replace with some OCR logic or something
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

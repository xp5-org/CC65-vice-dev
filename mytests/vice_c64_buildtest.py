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
    id="C64",
    types=["build"],
    system="VICE",
    platform="VICE",
)(sys.modules[__name__])





@register_buildtest("build 1 - rx client")
def build1_rxclient(context):
    src_dir = 'cc65_rx_src'
    out_dir = 'cc65_rx_output'
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, 'rxtest.c')
    asm_file = os.path.join(out_dir, 'rxtest.s')
    obj_file = os.path.join(out_dir, 'rxtest.o')
    prg_file = os.path.join(out_dir, 'rxtest.prg')
    d64_file = os.path.join(out_dir, 'rxtest.d64')

    log = []

    success, out = compile_cc65(source_file, asm_file)
    log.append("Compile cc65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = assemble_ca65(asm_file, obj_file)
    log.append("Assemble ca65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = link_ld65(obj_file, prg_file)
    log.append("Link ld65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = create_blank_d64(d64_file)
    log.append("Create blank d64:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = format_and_copyd64(d64_file, prg_file)
    log.append("Format and copy to d64:\n" + out)
    if not success:
        return False, "\n".join(log)

    return True, "\n".join(log)



@register_buildtest("build 2 - tx client")
def build2_txclient(context):
    src_dir = 'cc65_tx_src'
    out_dir = 'cc65_tx_output'
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, 'txtest.c')
    asm_file = os.path.join(out_dir, 'txtest.s')
    obj_file = os.path.join(out_dir, 'txtest.o')
    prg_file = os.path.join(out_dir, 'txtest.prg')
    d64_file = os.path.join(out_dir, 'txtest.d64')

    log = []

    success, out = compile_cc65(source_file, asm_file)
    log.append("Compile cc65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = assemble_ca65(asm_file, obj_file)
    log.append("Assemble ca65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = link_ld65(obj_file, prg_file)
    log.append("Link ld65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = create_blank_d64(d64_file)
    log.append("Create blank d64:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = format_and_copyd64(d64_file, prg_file)
    log.append("Format and copy to d64:\n" + out)
    if not success:
        return False, "\n".join(log)

    return True, "\n".join(log)



@register_buildtest("Build 3 - start relay server")
def build3_launch_rx(context):
    print("ip232relayserver loaded:", __file__)
    print("Has start_server():", hasattr(ip232relayserver, 'start_server'))
    global relay_started
    log = []
    name = "relay_server"
    port = 6501

    with relay_lock:
        if not relay_started:
            server_thread = threading.Thread(target=ip232relayserver.start_server, daemon=True)
            server_thread.start()
            relay_started = True
            context[name] = {"thread": server_thread, "started": True}
            log.append(f"{name} started on port {port}")
        else:
            log.append(f"{name} was already started")

    return True, "\n".join(log)



@register_buildtest("Build 4 - start TX vice instance")
def build4_launch_tx(context):
    name, port = next_vice_instance(context)
    disk = "cc65_tx_output/txtest.d64"
    config = "vice_ip232_tx.cfg"
    instance = ViceInstance(name, port, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]
    

    instance.start()
    time.sleep(5) # wait for C64 to boot
    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{instance.output}")
        return False, "\n".join(log)
    context[name] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{instance.output}")
    return True, "\n".join(log)




@register_buildtest("Build 4 - start RX vice instance")
def build4_launch_rx(context):
    name, port = next_vice_instance(context)
    disk = "cc65_rx_output/rxtest.d64"
    config = "vice_ip232_rx.cfg"
    
    instance = ViceInstance(name, port, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]

    instance.start()
    time.sleep(5) # wait for C64 to boot
    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{instance.output}")
        return False, "\n".join(log)
    context[name] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{instance.output}")
    return True, "\n".join(log)



@register_buildtest("Build 5 - send RUN to both")
def build5_send_run(context):
    log = []
    for name in ["vice1", "vice2"]:
        try:
            success, output = send_vice_command(context, name, 'LOAD "*",8\n')
            time.sleep(3)
            success, output = send_vice_command(context, name, "RUN\n")
            log.append(f"Sent RUN to {name}:\n{output}")
        except Exception as e:
            log.append(f"Failed to send to {name}: {e}")
    return True, "\n".join(log)


@register_buildtest("Build 6 - screenshot after boot command")
def build6_screenshot_both(context):
    log = []
    for name in ["vice1", "vice2"]:
        instance = context.get(name)
        if instance:
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=7)
            print(f"Screenshot for {name} taken: {success}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)


@register_buildtest("Build 8 - screenshot after program start")
def build6_screenshot_both(context):
    log = []
    time.sleep(30) #replace with some OCR logic or something
    for name in ["vice1", "vice2"]:
        instance = context.get(name)
        if instance:
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=8)
            print(f"Screenshot for {name} taken: {success}")
        else:
            print(f"No ViceInstance found for {name}")
    return True, "\n".join(log)



@register_buildtest("Build 8 - terminate all")
def build8_stopallvice(context):
    log = []
    print("waiting 60s before teardown")
    time.sleep(3)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    
    with relay_lock:
        relay_info = context.get(name)
        if relay_info and relay_info.get("started"):
            # Call your server stop function here:
            ip232relayserver.stop_server()  # You must implement this to stop the server loop

            # Wait for thread to finish
            thread = relay_info.get("thread")
            if thread:
                thread.join(timeout=5)

            relay_info["started"] = False
            log.append(f"{name} stopped")
        else:
            log.append(f"{name} not running")

    return True, "\n".join(log)
import sys
import os
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) #auto import /mytests dir as modules
TESTSRC_TESTLISTDIR = "/testsrc/mytests"
TESTSRC_BASEDIR = "/testsrc"
TESTSRC_HELPERDIR = "/testsrc/helpers"

# make app helpers dir visible
if TESTSRC_HELPERDIR  not in sys.path:
    sys.path.insert(0, TESTSRC_HELPERDIR )


from apphelpers import register_testfile, register_buildtest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
import ip232relayserver
VICE_IP = "127.0.0.1"


#this is to track if the relay server is already started or not
relay_started = False
relay_lock = threading.Lock()


register_testfile(
    id="no-driver char rx-tx pair",
    types=["build"],
    system="C64",
    platform="SerialModem",
)(sys.modules[__name__])





@register_buildtest("build 1 - rx client")
def build1_cuberotate(context):
    progname = "randchar_rx"
    archtype = 'c64'
    src_dir = 'c64src/' + progname
    out_dir = 'c64output/' + progname
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + ".s")
    obj_file    = os.path.join(out_dir, progname + ".o")
    prg_file    = os.path.join(out_dir, progname + ".prg")
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



@register_buildtest("build 1 - tx client")
def build1_cuberotate(context):
    progname = "randchar_tx"
    archtype = 'c64'
    src_dir = 'c64src/' + progname
    out_dir = 'c64output/' + progname
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + ".s")
    obj_file    = os.path.join(out_dir, progname + ".o")
    prg_file    = os.path.join(out_dir, progname + ".prg")
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



@register_buildtest("Build 4 - start RX vice instance")
def build4_launch_rx(context):
    archtype = 'c64'
    name, port = next_vice_instance(context)
    disk = "c64output/randchar_rx/randchar_rx.d64"
    config = "c64src/randchar_tx/vice_ip232_rx_tx.cfg"
    
    instance = ViceInstance(name, port, archtype, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]

    started = instance.start()
    if not started:
        log.append(f"{name} failed to start (no window ID detected). Abandoning test.")
        context["abort"] = True
        return False, "\n".join(log)
    
    time.sleep(1) # wait for start

    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
        context["abort"] = True
        return False, "\n".join(log)

    context["rx_instance"] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
    return True, "\n".join(log)




@register_buildtest("Build 5 - start TX vice instance")
def build5_launch_tx(context):
    archtype = 'c64'
    name, port = next_vice_instance(context)
    disk = "c64output/randchar_tx/randchar_tx.d64"
    config = "c64src/randchar_tx/vice_ip232_rx_tx.cfg"
    instance = ViceInstance(name, port, archtype, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]
    
    

    started = instance.start()
    if not started:
        log.append(f"{name} failed to start (no window ID detected). Abandoning test.")
        context["abort"] = True
        return False, "\n".join(log)

    time.sleep(1) # wait for start
    
    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
        context["abort"] = True
        return False, "\n".join(log)

    context["tx_instance"] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
    return True, "\n".join(log)



@register_buildtest("Build 6 - send RUN to all instances")
def build6_send_run(context):
    time.sleep(5)
    log = []

    rx_instance = None
    tx_instance = None

    for name, instance in context.items():
        if not isinstance(instance, ViceInstance):
            continue
        if "rx" in name.lower():
            rx_instance = (name, instance)
        elif "tx" in name.lower():
            tx_instance = (name, instance)

    if rx_instance:
        name, instance = rx_instance
        success, output = send_vice_command(context, name, 'LOAD "*",8\n')
        time.sleep(1)
        success, output = send_vice_command(context, name, "RUN\n")
        log.append(f"Sent RUN to {name}:\n{output}")

        time.sleep(10)

    if tx_instance:
        name, instance = tx_instance
        success, output = send_vice_command(context, name, 'LOAD "*",8\n')
        time.sleep(1)
        success, output = send_vice_command(context, name, "RUN\n")
        log.append(f"Sent RUN to {name}:\n{output}")

    return True, "\n".join(log)




@register_buildtest("Build 7 - screenshot after boot command")
def build7_screenshot_both(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=7)
            print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_buildtest("Build 8 - screenshot after program start")
def build8_screenshot_both(context):
    log = []
    time.sleep(30)  # let test run for some time
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=8)
            print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)




@register_buildtest("Build 9 - terminate all")
def build9_stopallvice(context):
    log = []
    print("waiting 60s before teardown")
    time.sleep(30)
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
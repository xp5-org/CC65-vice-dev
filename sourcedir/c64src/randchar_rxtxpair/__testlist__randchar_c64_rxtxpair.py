import os
import time
import threading

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "no-driver char rx-tx pair",            # nickname for 
    "projdir": "randchar_rxtxpair", 
    "cmainfile": "other",                # c-file progname no extenion to give to compiler
    "testtype": "build",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "c64",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Devices",             # 2nd tier sorting category
    "viceconf": "vice_ip232_rxtx.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
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

#this is to track if the relay server is already started or not
import ip232relayserver
relay_started = False
relay_lock = threading.Lock()

# unique to this test
rxclient_d64_file  = out_dir + "/randchar_rx.d64"
txclient_d64_file = out_dir + "/randchar_tx.d64"




@register_mytest(testtype, "compile rx client")
def build1_buildrx(context):
    progname = "randchar_rx"
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + ".s")
    obj_file    = os.path.join(out_dir, progname + ".o")
    prg_file    = os.path.join(out_dir, progname + ".prg")

    log = []
    steps = [
        (compile_cc65, source_file, asm_file, archtype),
        (assemble_ca65, asm_file, obj_file, archtype),
        (link_ld65, obj_file, prg_file, archtype),
        (create_blank_d64, rxclient_d64_file),
        (format_and_copyd64, rxclient_d64_file, prg_file),
    ]

    for func, *args in steps:
        success, out = func(*args)
        log.append(f"{func.__name__}:\n{out}")
        if not success:
            context["abort"] = True
            return False, "\n".join(log)

    return True, "\n".join(log)


@register_mytest(testtype, "compile tx client")
def build1_buildtx(context):
    progname = "randchar_tx"
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + ".s")
    obj_file    = os.path.join(out_dir, progname + ".o")
    prg_file    = os.path.join(out_dir, progname + ".prg")

    log = []
    steps = [
        (compile_cc65, source_file, asm_file, archtype),
        (assemble_ca65, asm_file, obj_file, archtype),
        (link_ld65, obj_file, prg_file, archtype),
        (create_blank_d64, txclient_d64_file),
        (format_and_copyd64, txclient_d64_file, prg_file),
    ]

    for func, *args in steps:
        success, out = func(*args)
        log.append(f"{func.__name__}:\n{out}")
        if not success:
            context["abort"] = True
            return False, "\n".join(log)

    return True, "\n".join(log)


@register_mytest(testtype, "start relay server")
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


@register_mytest(testtype, "start RX vice instance")
def test_startviceemulator(context):
    # name, port = next_vice_instance(context)
    _, port = next_vice_instance(context)
    name = "rx_instance"
    log = []
    
    try:
        instance = ViceInstance(name, port, archtype, config_path=viceconf, disk_path=rxclient_d64_file)
        log.append(f"Launching {name} on port {port} with disk={rxclient_d64_file} config={viceconf}")

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


@register_mytest(testtype, "start TX vice instance")
def test_startviceemulator(context):
    # name, port = next_vice_instance(context)
    _, port = next_vice_instance(context)
    name = "tx_instance"
    log = []
    
    try:
        instance = ViceInstance(name, port, archtype, config_path=viceconf, disk_path=txclient_d64_file)
        log.append(f"Launching {name} on port {port} with disk={txclient_d64_file} config={viceconf}")

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


@register_mytest(testtype, "send RUN to all instances")
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


@register_mytest(testtype, "screenshot after boot command")
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


@register_mytest(testtype, "screenshot after program start")
def build8_screenshot_both(context):
    log = []
    time.sleep(30)  # let test run for some time
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


@register_mytest(testtype, "terminate all")
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


@register_mytest(testtype, "terminate relay & collect logs")
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
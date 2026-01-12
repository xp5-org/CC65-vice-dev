import sys
import os
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) #auto import /mytests dir as modules
TESTSRC_TESTLISTDIR = "/testsrc/mytests"
TESTSRC_BASEDIR = "/testsrc"
TESTSRC_HELPERDIR = "/testsrc/pyhelpers"

# make app helpers dir visible
if TESTSRC_HELPERDIR  not in sys.path:
    sys.path.insert(0, TESTSRC_HELPERDIR )


from apphelpers import register_testfile, register_buildtest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
from vicehelpers import assemble_object
VICE_IP = "127.0.0.1"



register_testfile(
    id="serialdriver",
    types=["build"],
    system="C64",
    platform="Devices",
)(sys.modules[__name__])



progname = "serial_driver"
archtype = 'c64'
src_dir = 'sourcedir/c64src/' + progname
out_dir = src_dir + "/output"



@register_buildtest("build 1 - serial")
def build1_compile(context):
    progname = "serial_driver"
    archtype = 'c64'
    src_dir = 'sourcedir/c64src/' + progname
    out_dir = src_dir + "/output"
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + "main.s")
    obj_file    = os.path.join(out_dir, progname + "main.o")
    prg_file    = os.path.join(out_dir, progname + ".prg")
    d64_file    = os.path.join(out_dir, progname + ".d64")
    # driver path info
    driver_ser = os.path.join(src_dir, "c64-swlink.ser")
    driver_s   = os.path.join(out_dir, "c64-swlink.s")
    driver_o   = os.path.join(out_dir, "c64-swlink.o")
    driver_label = "_c64_swlink"

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



@register_buildtest("Build 2 - serial_driver")
def build2_launch_serialtest(context):
    archtype = 'c64'
    name, port = next_vice_instance(context)
    disk = out_dir + "/serial_driver.d64"
    config = src_dir + "/vice_ip232_rx_tx.cfg"
    
    instance = ViceInstance(name, port, archtype, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]
    
    success, log = launch_vice_instance(instance)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)




@register_buildtest("Build 3 - send RUN")
def buil3_send_run(context):
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


@register_buildtest("Build 4 - screenshot after boot command")
def build4_screenshot_both(context):
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



@register_buildtest("Build 5 - screenshot after program start")
def build5_screenshot_both(context):
    name, port = next_vice_instance(context)
    log = []
    time.sleep(15)  # takes a long time to laod the program
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=6)
            print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)




@register_buildtest("Build 6 - terminate all")
def build6_stopallvice(context):
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
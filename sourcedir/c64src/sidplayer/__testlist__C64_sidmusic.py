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
VICE_IP = "127.0.0.1"

register_testfile(
    id="SID Music",
    types=["build"],
    system="C64",
    platform="Graphics",
)(sys.modules[__name__])



progname = "sidplayer"
archtype = 'c64'
src_dir = 'sourcedir/c64src/' + progname
out_dir = src_dir + "/output"


@register_buildtest("build 1 - Sid music")
def build1_cuberotate(context):

    os.makedirs(out_dir, exist_ok=True)

    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + "main.s")
    obj_file    = os.path.join(out_dir, progname + "main.o")
    prg_file    = os.path.join(out_dir, progname + "main.prg")
    d64_file    = os.path.join(out_dir, progname + ".d64")
    linkerconf  = os.path.join(src_dir, "c64-sid.cfg")
    asm_include = os.path.join(src_dir, "sidplaysfx.s")
    asm_object  = os.path.join(out_dir, "sidplaysfx.o")

    helper_sources = [asm_include]  
    helper_objects = [asm_object]

    log = []
    steps = [
        (compile_cc65, source_file, asm_file, archtype),
        (assemble_ca65, asm_file, obj_file, archtype),
    ]

    for s, o in zip(helper_sources, helper_objects):
        steps.append((assemble_ca65, s, o, archtype))

    all_objects = [obj_file] + helper_objects
    steps.append((link_ld65, all_objects, prg_file, archtype, linkerconf))

    steps.append((create_blank_d64, d64_file))
    steps.append((format_and_copyd64, d64_file, prg_file))

    for func, *args in steps:
        success, out = func(*args)
        log.append(f"{func.__name__}:\n{out}")
        if not success:
            context["abort"] = True
            return False, "\n".join(log)

    return True, "\n".join(log)




@register_buildtest("Build 2 - start cuberotate vice instance")
def build2_launch_cuberotate(context):
    archtype = 'c64'
    name, port = next_vice_instance(context)
    disk = out_dir + "/sidplayer.d64"
    config = "vice_ip232_tx.cfg"
    
    instance = ViceInstance(name, port, archtype, config_path=config, disk_path=None, autostart_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]
    
    success, log = launch_vice_instance(instance)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)




#@register_buildtest("Build 3 - send RUN")
#def buil3_send_run(context):
#    log = []
#    for name in ["vice1"]:
#        try:
#            success, output = send_vice_command(context, name, 'LOAD "*",8\n')
#            time.sleep(3)
#            success, output = send_vice_command(context, name, "RUN\n")
#            log.append(f"Sent RUN to {name}:\n{output}")
#        except Exception as e:
#            log.append(f"Failed to send to {name}: {e}")
#    return True, "\n".join(log)


@register_buildtest("Build 4 - screenshot after boot command")
def build4_screenshot_both(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=4)
            print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)



@register_buildtest("Build 5 - screenshot after program start")
def build5_screenshot_both(context):
    log = []
    time.sleep(5)  # takes a long time to laod the program
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




@register_buildtest("Build 6 - terminate all")
def build6_stopallvice(context):
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

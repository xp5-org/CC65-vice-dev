import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "ECM Text",            # nickname for 
    "projdir": "ecmtext", 
    "cmainfile": "ecmcharprint",                # c-file progname no extenion to give to compiler
    "testtype": "build",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "c64",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Text Printing",             # 2nd tier sorting category
    "viceconf": "vice_C64nosound.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/c64src/",
        "structure": {
        "project": {
            "_rel": "{projdir}",
            "viceconf": "{viceconf}",
            "src": {
                "_rel": "src"
            },
            "out": {
                "_rel": "output",
                "prg": "{cmainfile}.prg",
                "d64file_abs": "{cmainfile}.d64"
            }
        }
    },
}

PATHS = init_test_env(CONFIG, __name__)
testtype = CONFIG["testtype"]
archtype = CONFIG["archtype"]
progname = CONFIG["cmainfile"]
viceconf = PATHS["viceconf"]
src_dir = PATHS["src"]
out_dir = PATHS["out"]
prg_file = PATHS["prg"]
d64_file = PATHS["d64file_abs"]




@register_mytest(testtype, "Compile")
def build1_compile(context):
    os.makedirs(out_dir, exist_ok=True)
    source_file = os.path.join(src_dir, progname + ".c")
    asm_file    = os.path.join(out_dir, progname + "main.s")
    obj_file    = os.path.join(out_dir, progname + "main.o")
    prg_file    = os.path.join(out_dir, progname + ".prg")
    d64_file    = os.path.join(out_dir, progname + ".d64")
    
    log = []
    steps = [
        (compile_cc65, source_file, asm_file, archtype),
        (assemble_ca65, asm_file, obj_file, archtype),
        (link_ld65, [obj_file], prg_file, archtype),
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


@register_mytest(testtype, "start vice instance")
def startvice(context):
    name, port = next_vice_instance(context)    
    instance = ViceInstance(name, port, archtype, config_path=viceconf, disk_path=d64_file)
    log = [f"Launching {name} on port {port} with disk={d64_file} config={viceconf}"]
    
    success, log = launch_vice_instance(instance)
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)


@register_mytest(testtype, "send RUN")
def buil3_send_run(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            success, output = send_vice_command(context, name, 'LOAD "*",8\n')
            time.sleep(3)
            success, output = send_vice_command(context, name, "RUN\n")
            log.append(f"Sent RUN to {name}:\n{output}")
            screentextoutput = instance.screentextdump(context)
            log.append(f"{screentextoutput}")
        if not log:
            log.append(f"Failed to send to {name}")
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after boot command")
def build4_screenshot_both(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            #print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot()
            #print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        #print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after program start")
def build5_screenshot_both(context):
    name, port = next_vice_instance(context)
    log = []
    time.sleep(15)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            #print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot()
            #print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        #print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    if not success:
        context["abort"] = True
        return False, "\n".join(log)
    
    context[name] = instance
    return True, "\n".join(log)


@register_mytest(testtype, "terminate all")
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
import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "TGI cuberotate",            # nickname for 
    "projdir": "cuberotate", 
    "cmainfile": "cuberotatemain",                # c-file progname no extenion to give to compiler
    "testtype": "build",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "c64",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Graphics",             # 2nd tier sorting category
    "viceconf": "vice_nosound.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
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





@register_mytest(testtype, "Compile")
def cc65_c64compile(context):
    os.makedirs(PATHS["out"], exist_ok=True)

    c_src_files = [os.path.join(PATHS["src"], f) 
                   for f in os.listdir(PATHS["src"]) 
                   if f.lower().endswith(".c")]

    obj_files = [os.path.join(PATHS["out"], os.path.splitext(os.path.basename(f))[0] + ".o")
                 for f in c_src_files]
    print("Found C files:", c_src_files, "in dir: ", PATHS["src"])
    log = []

    for src, obj in zip(c_src_files, obj_files):
        asm_file = os.path.splitext(obj)[0] + ".s"
        # add -Cl to the compile flags
        success, out = compile_cc65(src, asm_file, archtype, extra_flags=["-Cl"])
        log.append(f"compile_cc65 {src}:\n{out}")
        if not success:
            context["abort"] = True
            return False, "\n".join(log)


        success, out = assemble_ca65(asm_file, obj, archtype)
        log.append(f"assemble_ca65 {asm_file}:\n{out}")
        if not success:
            context["abort"] = True
            return False, "\n".join(log)

    prg_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".prg")
    success, out = link_ld65(obj_files, prg_file, archtype)
    log.append(f"link_ld65:\n{out}")
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    d64_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".d64")
    success, out = create_blank_d64(d64_file)
    log.append(f"create_blank_d64:\n{out}")
    if not success:
        context["abort"] = True
        return False, "\n".join(log)

    success, out = format_and_copyd64(d64_file, prg_file)
    log.append(f"format_and_copyd64:\n{out}")
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
    for vice_name in ["vice1"]:
        try:
            success, output = send_vice_command(context, vice_name, 'LOAD "*",8\n')
            time.sleep(3)
            success, output = send_vice_command(context, vice_name, "RUN\n")
            log.append(f"Sent RUN to {vice_name}:\n{output}")

            for name, instance in context.items():
                if isinstance(instance, ViceInstance):
                    screentextoutput = instance.screentextdump(context)
                    log.append(f"adssdsdas{screentextoutput}")

        except Exception as e:
            log.append(f"Failed to send to {vice_name}: {e}")

    return True, "\n".join(log)



@register_mytest(testtype, "screenshot after boot command")
def build4_screenshot_both(context):
    log = []
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            #print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=4)
            #print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        #print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_mytest(testtype, "screenshot after program start")
def build5_screenshot_both(context):
    log = []
    time.sleep(35)  # takes a long time to laod the program
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            #print(f"{name} window_id: {instance.window_id}")
            success = instance.take_screenshot(test_step=5)
            #print(f"Screenshot for {name} taken: {success}")
            log.append(f"Screenshot for {name} taken: {success}")
    if not log:
        #print("No ViceInstances found in context")
        log.append("No ViceInstances found in context")
    return True, "\n".join(log)


@register_mytest(testtype, "terminate all")
def build6_stopallvice(context):
    log = []
    #print("waiting 3s before teardown")
    time.sleep(3)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")
    if not log:
        log.append("No VICE instances found to stop.")
    return True, "\n".join(log)

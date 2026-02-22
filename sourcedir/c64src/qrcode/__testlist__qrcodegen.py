import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "QR Code Sprites",
    "projdir": "qrcode",
    "cmainfile": "qrcodesprites.c",
    "testtype": "build",
    "archtype": "c64",
    "platform": "Graphics",
    "viceconf": "vice_C64nosound.cfg",
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/c64src/",
    "prg_filename": "qrcodesprites.prg",
    "d64_disk8_name": "qrcodesprites.d64",
    "d64_disk9_name": "",
    "cmainfile_path": "{src}{cmainfile}",
    "src": "{projbasedir}{projdir}/src/",
    "d64_drive8_file": "{projbasedir}{projdir}/output/{d64_disk8_name}",
    "d64_drive9_file": "{projbasedir}{projdir}/output/{d64_disk9_name}",
    "prg_filepath": "{projbasedir}{projdir}/output/{prg_filename}",
    "viceconf_filepath": "{projbasedir}{projdir}/{viceconf}",
    "out_dir": "{projbasedir}{projdir}/output",

"structure": {
    "project": {
        "_rel": "{projdir}",
        "out": {
            "_rel": "output",
            "d64file_abs": "{d64_disk8_name}",
            "prg": "{prg_filename}"
        },
        "src": {
            "_rel": "src"
        },
        "viceconf": "vice_C64dualdisk.cfg"
    }
},


    "steps": [
        {
            "action": "test_compiletheprogram",
            "param": {
                "archtype": "c64",
                "cmainfile": "{cmainfile_path}",
                "d64_file": "{d64_drive8_file}",
                "drv1_label": "",
                "drv1_path": "",
                "out_dir": "{out_dir}",
                "prg_filepath": "{prg_filepath}",
                "src_dir": "{src}"
            },
            "subaction": ""
        },
        {
            "action": "test_emulator_start",
            "param": {
                "autostart_path": "{d64_drive8_file}",
                "disk8_path": "",
                "disk9_path": "",
                "name": "",
                "port": "6502",
                "rom_path": "",
                "viceconf": "{viceconf_filepath}",
                "warpmode": "True"
            },
            "subaction": ""
        },
        {
            "action": "test_terminate_all",
            "param": {},
            "subaction": ""
        }
    ],
}

PATHS = init_test_env(CONFIG, __name__)
# testtype = CONFIG["testtype"]
# archtype = CONFIG["archtype"]
# progname = CONFIG["cmainfile"]
# viceconf = PATHS["viceconf"]
# src_dir = PATHS["src"]
# out_dir = PATHS["out"]
# prg_file = PATHS["prg"]
# d64_file = PATHS["d64file_abs"]




# @register_mytest(testtype, "Compile")
# def cc65_c64compile(context):
#     os.makedirs(PATHS["out"], exist_ok=True)

#     c_src_files = [os.path.join(PATHS["src"], f) 
#                    for f in os.listdir(PATHS["src"]) 
#                    if f.lower().endswith(".c")]

#     obj_files = [os.path.join(PATHS["out"], os.path.splitext(os.path.basename(f))[0] + ".o")
#                  for f in c_src_files]
#     print("Found C files:", c_src_files, "in dir: ", PATHS["src"])
#     log = []

#     for src, obj in zip(c_src_files, obj_files):
#         asm_file = os.path.splitext(obj)[0] + ".s"
#         # add -Cl to the compile flags
#         success, out = compile_cc65(src, asm_file, archtype, extra_flags=["-Cl"])
#         log.append(f"compile_cc65 {src}:\n{out}")
#         if not success:
#             context["abort"] = True
#             return False, "\n".join(log)


#         success, out = assemble_ca65(asm_file, obj, archtype)
#         log.append(f"assemble_ca65 {asm_file}:\n{out}")
#         if not success:
#             context["abort"] = True
#             return False, "\n".join(log)

#     prg_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".prg")
#     success, out = link_ld65(obj_files, prg_file, archtype)
#     log.append(f"link_ld65:\n{out}")
#     if not success:
#         context["abort"] = True
#         return False, "\n".join(log)

#     d64_file = os.path.join(PATHS["out"], CONFIG["cmainfile"] + ".d64")
#     success, out = create_blank_d64(d64_file)
#     log.append(f"create_blank_d64:\n{out}")
#     if not success:
#         context["abort"] = True
#         return False, "\n".join(log)

#     success, out = format_and_copyd64(d64_file, prg_file)
#     log.append(f"format_and_copyd64:\n{out}")
#     if not success:
#         context["abort"] = True
#         return False, "\n".join(log)

#     return True, "\n".join(log)


# @register_mytest(testtype, "start vice instance")
# def startvice(context):
#     name, port = next_vice_instance(context)    
#     instance = ViceInstance(name, port, archtype, config_path=viceconf, disk_path=d64_file, warpmode=True)
#     log = [f"Launching {name} on port {port} with disk={d64_file} config={viceconf}"]
    
#     success, log = launch_vice_instance(instance)
#     if not success:
#         context["abort"] = True
#         return False, "\n".join(log)
    
#     context[name] = instance
#     return True, "\n".join(log)


# @register_mytest(testtype, "send RUN")
# def buil3_send_run(context):
#     log = []
#     for name, instance in context.items():
#         if isinstance(instance, ViceInstance):
#             success, output = send_vice_command(context, name, 'LOAD "*",8\n')
#             time.sleep(3)
#             success, output = send_vice_command(context, name, "RUN\n")
#             log.append(f"Sent RUN to {name}:\n{output}")
#             screentextoutput = instance.screentextdump(context)
#             log.append(f"{screentextoutput}")
#         if not log:
#             log.append(f"Failed to send to {name}")
#     return True, "\n".join(log)


# @register_mytest(testtype, "screenshot after boot command")
# def build4_screenshot_both(context):
#     log = []
#     for name, instance in context.items():
#         if isinstance(instance, ViceInstance):
#             #print(f"{name} window_id: {instance.window_id}")
#             success = instance.take_screenshot()
#             #print(f"Screenshot for {name} taken: {success}")
#             log.append(f"Screenshot for {name} taken: {success}")
#     if not log:
#         #print("No ViceInstances found in context")
#         log.append("No ViceInstances found in context")
#     return True, "\n".join(log)


# @register_mytest(testtype, "screenshot after program start")
# def build5_screenshot_both(context):
#     name, port = next_vice_instance(context)
#     log = []
#     time.sleep(5)
#     for name, instance in context.items():
#         if isinstance(instance, ViceInstance):
#             #print(f"{name} window_id: {instance.window_id}")
#             success = instance.take_screenshot()
#             #print(f"Screenshot for {name} taken: {success}")
#             log.append(f"Screenshot for {name} taken: {success}")
#     if not log:
#         #print("No ViceInstances found in context")
#         log.append("No ViceInstances found in context")
#     if not success:
#         context["abort"] = True
#         return False, "\n".join(log)
    
#     context[name] = instance
#     return True, "\n".join(log)


# @register_mytest(testtype, "terminate all")
# def build6_stopallvice(context):
#     log = []
#     print("waiting 3s before teardown")
#     time.sleep(3)
#     for name, instance in context.items():
#         if isinstance(instance, ViceInstance):
#             log.append(f"Stopping {name} on port {instance.port}")
#             instance.stop()
#             log.append(f"{name} has exited.")
#     if not log:
#         log.append("No VICE instances found to stop.")
#     return True, "\n".join(log)
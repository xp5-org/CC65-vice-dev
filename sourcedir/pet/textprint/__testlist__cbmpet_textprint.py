import sys
import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_cbmpet_text, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "PET text print",            # nickname for 
    "projdir": "textprint", 
    "cmainfile": "pettestprog",                # c-file progname no extenion to give to compiler
    "testtype": "build",                # name for this test type, used to make new run-button of like-named tests
    "archtype": "pet",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
    "platform": "Text Printing",             # 2nd tier sorting category
    "viceconf": "vice_petconf.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/c64src/",
    "prg_filename": "diskformat.prg",
    "d64_disk8_name": "disk8main.d64",
    "d64_disk9_name": "disk9.d64",
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
                "out_dir": "{out_dir}",
                "prg_filepath": "{prg_filepath}",
                "src_dir": "{src}"
            },
            "subaction": ""
        },
        {
            "action": "test_emulator_start",
            "param": {
                "autostart_path": "",
                "disk8_path": "{d64_drive8_file}",
                "disk9_path": "{d64_drive8_file}",
                "name": "",
                "port": "6502",
                "rom_path": "",
                "viceconf": "{viceconf_filepath}",
                "warpmode": "True"
            },
            "subaction": ""
        },
        {
            "action": "test_wordsearch",
            "param": {
                "attemptdelay": "3",
                "failphrase": "failed",
                "numberofattempts": "10",
                "successphrase": "ready"
            },
            "subaction": ""
        },
        {
            "action": "test_sendrun",
            "param": {},
            "subaction": ""
        },
        {
            "action": "test_wordsearch",
            "param": {
                "attemptdelay": "3",
                "failphrase": "error",
                "numberofattempts": "10",
                "successphrase": "status: 00"
            },
            "subaction": ""
        },
        {
            "action": "test_basic_sendlistdisk",
            "param": {
                "disk_idnum": "8"
            },
            "subaction": ""
        },
        {
            "action": "test_wordsearch",
            "param": {
                "attemptdelay": "3",
                "failphrase": "error",
                "numberofattempts": "5",
                "successphrase": "itworks"
            },
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
# def test1_cbmpet(context):
#     os.makedirs(out_dir, exist_ok=True)
#     source_file = os.path.join(src_dir, progname + ".c")
#     asm_file    = os.path.join(out_dir, progname + "main.s")
#     obj_file    = os.path.join(out_dir, progname + "main.o")
#     prg_file    = os.path.join(out_dir, progname + "main.prg")
#     d64_file    = os.path.join(out_dir, progname + ".d64")

#     log = []
#     steps = [
#         (compile_cc65, source_file, asm_file, archtype),
#         (assemble_ca65, asm_file, obj_file, archtype),
#         (link_ld65, obj_file, prg_file, archtype),
#         (create_blank_d64, d64_file),
#         (format_and_copyd64, d64_file, prg_file),
#     ]

#     for func, *args in steps:
#         success, out = func(*args)
#         log.append(f"{func.__name__}:\n{out}")
#         if not success:
#             context["abort"] = True
#             return False, "\n".join(log)

#     return True, "\n".join(log)


# @register_mytest(testtype, "start vice instance")
# def test_startviceemulator(context):
#     name, port = next_vice_instance(context)
#     log = []
    
#     try:
#         instance = ViceInstance(name, port, archtype, config_path=viceconf, disk_path=d64_file)
#         log.append(f"Launching {name} on port {port} with disk={d64_file} config={viceconf}")

#         started = instance.start()
#         if not started:
#             log.append(f"{name} failed to start (no window ID detected).")
#             context["abort"] = True
#             return False, "\n".join(log)

#     except Exception as e:
#         log.append(f"CRITICAL: Python error during startup: {str(e)}")
#         context["abort"] = True
#         return False, "\n".join(log)

#     time.sleep(3)

#     if not instance.wait_for_ready():
#         log.append(f"{name} did not become ready on port {port}")
#         log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
#         context["abort"] = True
#         return False, "\n".join(log)

#     context[name] = instance
#     log.append(f"{name} is ready")
#     log.append(f"{name} stdout:\n{''.join(instance.get_output())}")
#     return True, "\n".join(log)


# @register_mytest(testtype, "send RUN")
# def test3_cbmpet(context):
#     log = []
#     for name in ["vice1"]:
#         try:
#             success, output = send_cbmpet_text(context, name, 'LOAD "*",8\n')
#             time.sleep(3)
#             success, output = send_cbmpet_text(context, name, "RUN\n")
#             log.append(f"Sent RUN to {name}:\n{output}")
#         except Exception as e:
#             log.append(f"Failed to send to {name}: {e}")
#     return True, "\n".join(log)


# @register_mytest(testtype, "screenshot after boot command")
# def test4_cbmpet(context):
#     log = []
#     for name in ["vice1"]:
#         instance = context.get(name)
#         if instance:
#             success = instance.take_screenshot()
#         else:
#             print(f"No ViceInstance found for {name}")
#     return True, "\n".join(log)


# @register_mytest(testtype, "screenshot after program start")
# def test5_cbmpet(context):
#     log = []
#     time.sleep(5) #replace with some OCR logic or something
#     for name in ["vice1"]:
#         instance = context.get(name)
#         if instance:
#             success = instance.take_screenshot()
#             screentextoutput = instance.screentextdump(context)
#             log.append(f"adssdsdas{screentextoutput}")
#         else:
#             print(f"No ViceInstance found for {name}")
#     return True, "\n".join(log)


# @register_mytest(testtype, "terminate all")
# def test6_cbmpet(context):
#     log = []
#     for name, instance in context.items():
#         if isinstance(instance, ViceInstance):
#             log.append(f"Stopping {name} on port {instance.port}")
#             instance.stop()
#             log.append(f"{name} has exited.")
#     if not log:
#         log.append("No VICE instances found to stop.")
#     return True, "\n".join(log)
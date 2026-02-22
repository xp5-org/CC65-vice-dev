import sys
import os
import time

# auto import /mytests dir as modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 
TESTSRC_TESTLISTDIR = "/testsrc/mytests"
TESTSRC_BASEDIR = "/testsrc"
TESTSRC_HELPERDIR = "/testsrc/pyhelpers"

# make app helpers dir visible
if TESTSRC_HELPERDIR  not in sys.path:
    sys.path.insert(0, TESTSRC_HELPERDIR )


from apphelpers import init_test_env, register_mytest
from vicehelpers import send_c128_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "C128 80 Column Text",
    "projdir": "textprint80col",
    "cmainfile": "text80col.c",
    "testtype": "build",
    "archtype": "c128",
    "platform": "Graphics",
    "viceconf": "c128_viceconf.cfg",
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/c128src/",
    "prg_filename": "text80colmain.prg",
    "d64_disk8_name": "text80col.d64",
    "d64_disk9_name": "",
    "cmainfile_path": "{src}{cmainfile}",
    "src": "{projbasedir}{projdir}/src/",
    "d64_drive8_file": "{out_dir}/{d64_disk8_name}",
    "d64_drive9_file": "{out_dir}/{d64_disk9_name}",
    "prg_filepath": "{out_dir}/{prg_filename}",
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
            "action": "test_wordsearch",
            "param": {
                "attemptdelay": "3",
                "c128windowcolnum": "80col",
                "failphrase": "failed",
                "numberofattempts": "3",
                "successphrase": "hello"
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





# @register_mytest(testtype, "compile")
# def test1_c128(context):
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
# def test3_c128(context):
#     log = []
#     for name in ["vice1"]:
#         try:
#             success, output = send_c128_command(context, name, 'LOAD "*",8')
#             time.sleep(3)
#             success, output = send_c128_command(context, name, "RUN")
#             log.append(f"Sent RUN to {name}:\n{output}")
#         except Exception as e:
#             log.append(f"Failed to send to {name}: {e}")
#     return True, "\n".join(log)


# @register_mytest(testtype, "screen text check")
# def filewrite_check(context):
#     log = []
#     abort = False

#     for name, instance in context.items():
#         if not isinstance(instance, ViceInstance):
#             continue

#         attempt = 0
#         screentext = ""
#         found_status = False

#         while attempt < 10:
#             screentext = instance.screentextdump(context, window="80col")
#             screentext = screentext.lower()

#             if "failed" in screentext:
#                 log.append(f"{name} - Screentext search in python - program start failure")
#                 abort = True
#                 found_status = True
#                 break

#             if "hello" in screentext:
#                 log.append(f"{name} - Screentext search in python reported success")
#                 found_status = True
#                 break

#             time.sleep(3)
#             attempt += 1

#         if not found_status:
#             log.append(f"{name} did not report success or failure")
#             abort = True

#         log.append(f"{name} screentext:\n{screentext}")

#         if instance.take_screenshot():
#             log.append(f"Screenshot for {name} taken")
#         else:
#             log.append(f"Screenshot for {name} failed")
#             abort = True

#     if not log:
#         log.append("No ViceInstances found in context")

#     if abort:
#         context["abort"] = True
#         for name, instance in context.items():
#             if isinstance(instance, ViceInstance):
#                 log.append(f"Stopping {name} on port {instance.port}")
#                 instance.stop()
#         return False, "\n".join(log)

#     return True, "\n".join(log)


# @register_mytest(testtype, "screenshot after program start")
# def test5_c128(context):
#     log = []
#     time.sleep(5) #replace with some OCR logic or something
#     for name in ["vice1"]:
#         instance = context.get(name)
#         if instance:
#             success = instance.take_screenshotc128(test_step=5, window="40col")
#             success = instance.take_screenshotc128(test_step=5, window="80col")
#             screentextoutput = instance.screentextdump(context)
#             log.append(f"adssdsdas{screentextoutput}")
#         else:
#             log.append("Screenshot Failed")
#     return True, "\n".join(log)



# @register_mytest(testtype, "terminate all")
# def test6_c128(context):
#     log = []
#     for name, instance in context.items():
#         if isinstance(instance, ViceInstance):
#             log.append(f"Stopping {name} on port {instance.port}")
#             instance.stop()
#             log.append(f"{name} has exited.")
#     if not log:
#         log.append("No VICE instances found to stop.")
#     return True, "\n".join(log)
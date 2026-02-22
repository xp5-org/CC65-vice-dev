import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"


CONFIG = {
    "testname": "qrcodetest2",
    "projdir": "qrcodenew",
    "cmainfile": "qrcodemain.c",
    "testtype": "build",
    "archtype": "c64",
    "platform": "Graphics",
    "viceconf": "vice_c64_printer.cfg",
    "linkerconf": "c64-sid.cfg",
    "projbasedir": "/testsrc/sourcedir/c64src/",
    "prg_filename": "qrcodemain.prg",
    "d64_disk8_name": "qrcodemain.d64",
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
            "action": "test_wordsearch",
            "param": {
                "attemptdelay": "3",
                "c128windowcolnum": "None",
                "failphrase": "error",
                "numberofattempts": "10",
                "successphrase": "qrgensuccess"
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



# @register_mytest(testtype, "clear old file")
# def test_startviceemulator(context):
#     log = []
#     with open("/tmp/viceprnt.txt", "r+") as f:
#         f.truncate(0)
    
#     return True, "\n".join(log)


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
# def test_startviceemulator(context):
#     name, port = next_vice_instance(context)
#     log = []
    
#     try:
#         instance = ViceInstance(name, port, archtype, config_path=viceconf, autostart_path=d64_file, warpmode=True)
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


# # @register_mytest(testtype, "sendbasicprog")
# # def buil3_send_run(context):
# #     log = []
# #     for vice_name in ["vice1"]:
# #         try:
# #             time.sleep(5)
# #             success, output = send_vice_command(context, vice_name, "10OPEN4,4\n")
# #             send_vice_command(context, vice_name, "20PRINT#4,\"TEST1\"\n")
# #             send_vice_command(context, vice_name, "30CLOSE4\n")
# #             #send_vice_command(context, vice_name, "40 goto 10\n")
# #             send_vice_command(context, vice_name, "run\n")
# #             send_vice_command(context, vice_name, "run\n")
# #             log.append(f"Sent RUN to {vice_name}:\n{output}")

# #             for name, instance in context.items():
# #                 if isinstance(instance, ViceInstance):
# #                     screentextoutput = instance.screentextdump(context)
# #                     log.append(f"adssdsdas{screentextoutput}")

# #         except Exception as e:
# #             log.append(f"Failed to send to {vice_name}: {e}")

# #     return True, "\n".join(log)

# @register_mytest(testtype, "screenshot after boot command")
# def build3_screenshot_both(context):
#     log = []
#     for name, instance in context.items():
#         if isinstance(instance, ViceInstance):
#             success = instance.take_screenshot()
#             log.append(f"Screenshot for {name} taken: {success}")
#     if not log:
#         log.append("No ViceInstances found in context")
#     return True, "\n".join(log)


# @register_mytest(testtype, "start prog word search")
# def filewrite_check(context):
#     log = []
#     abort = False

#     for name, instance in list(context.items()):
#         if not isinstance(instance, ViceInstance):
#             continue

#         attempt = 0
#         screentext = ""
#         found_status = False

#         while attempt < 3:
#             screentext = instance.screentextdump(context)
#             screentext = screentext.lower()

#             if "qrgenfailed" in screentext:
#                 log.append(f"{name} - Screentext search in python - save to disk failure")
#                 abort = True
#                 found_status = True
#                 break

#             if "testing numeric encoding" in screentext:
#                 log.append(f"{name} - Screentext search in python reported success")
#                 result_parts = []
#                 capturing = False

#                 for line in screentext.splitlines():
#                     if not capturing:
#                         if "input:" in line:
#                             part = line.split(":", 1)[1].strip()
#                             result_parts.append(part)
#                             capturing = True
#                     else:
#                         if line.strip() == "":  # stop at first empty line
#                             break
#                         result_parts.append(line.strip())

#                 # join all captured parts into a single string with no spaces/newlines
#                 captured_value = "".join(result_parts)
#                 context["captured_output"] = captured_value
#                 log.append(f"Captured output: {captured_value}")

#                 found_status = True
#                 break


#             time.sleep(2)
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






# @register_mytest(testtype, "QR generate runtime calc")
# def filewrite_check(context):
#     log = []
#     abort = False

#     for name, instance in context.items():
#         if not isinstance(instance, ViceInstance):
#             continue

#         attempt = 0
#         screentext = ""
#         found_status = False

#         while attempt < 30:
#             screentext = instance.screentextdump(context)
#             if screentext is None:
#                 screentext = ""
#             else:
#                 screentext = screentext.lower()


#             if "qrgenfailed" in screentext:
#                 log.append(f"{name} - Screentext search in python - save to disk failure")
#                 abort = True
#                 found_status = True
#                 break

#             if "qrgensuccess" in screentext:
#                 log.append(f"{name} - Screentext search in python reported success")
#                 found_status = True
#                 break

#             time.sleep(5)
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




# # @register_mytest(testtype, "QR size word search")
# # def filewrite_check(context):
# #     log = []
# #     abort = False

# #     for name, instance in context.items():
# #         if not isinstance(instance, ViceInstance):
# #             continue

# #         attempt = 0
# #         screentext = ""
# #         found_status = False

# #         while attempt < 3:
# #             screentext = instance.screentextdump(context)
# #             screentext = screentext.lower()

# #             if "qrgenfailed" in screentext:
# #                 log.append(f"{name} - Screentext search in python - save to disk failure")
# #                 abort = True
# #                 found_status = True
# #                 break

# #             if "qr size" in screentext:
# #                 log.append(f"{name} - Screentext search in python reported success")
# #                 found_status = True
# #                 break

# #             time.sleep(3)
# #             attempt += 1

# #         if not found_status:
# #             log.append(f"{name} did not report success or failure")
# #             abort = True

# #         log.append(f"{name} screentext:\n{screentext}")

# #         if instance.take_screenshot():
# #             log.append(f"Screenshot for {name} taken")
# #         else:
# #             log.append(f"Screenshot for {name} failed")
# #             abort = True

# #     if not log:
# #         log.append("No ViceInstances found in context")

# #     if abort:
# #         context["abort"] = True
# #         for name, instance in context.items():
# #             if isinstance(instance, ViceInstance):
# #                 log.append(f"Stopping {name} on port {instance.port}")
# #                 instance.stop()
# #         return False, "\n".join(log)

# #     return True, "\n".join(log)



# @register_mytest(testtype, "send anykey")
# def buil3_send_run(context):
#     log = []
#     for vice_name in ["vice1"]:
#         try:
#             success, output = send_vice_command(context, vice_name, 'L\n')
#             time.sleep(3)
#             log.append(f"Sent RUN to {vice_name}:\n{output}")

#             # for name, instance in context.items():
#             #     if isinstance(instance, ViceInstance):
#             #         screentextoutput = instance.screentextdump(context)
#             #         instance.take_screenshot()
#             #         log.append(f"adssdsdas{screentextoutput}")



#         except Exception as e:
#             log.append(f"Failed to send to {vice_name}: {e}")

#     return True, "\n".join(log)


# @register_mytest(testtype, "validate qrcode")
# def qrcodevalidate(context):
#     log = []
#     result = ""
#     abort = False
#     for vice_name, instance in context.items():
#         if not isinstance(instance, ViceInstance):
#             continue

#         qrstring1 = context.get("captured_output", "").strip().upper()
#         qrstring2 = instance.capture_qr_string().strip().upper()
#         print("QR code string:", qrstring2)
#         log.append(f"Detected QR code string from screenshot: {qrstring2}")

#         if qrstring2 == qrstring1:
#             log.append(f"qr {qrstring1} matches {qrstring2} taken")
#         else:
#             log.append(f"qr {qrstring1} NOT matches {qrstring2} taken")
#             abort = True

#     if abort:
#         context["abort"] = True

#     return not abort, "\n".join(log)

# @register_mytest(testtype, "terminate all")
# def build5_stopallvice(context):
#     log = []
#     time.sleep(1)
#     for name, instance in context.items():
#         if isinstance(instance, ViceInstance):
#             log.append(f"Stopping {name} on port {instance.port}")
#             instance.stop()
#             log.append(f"{name} has exited.")
#     if not log:
#         log.append("No VICE instances found to stop.")
#     return True, "\n".join(log)


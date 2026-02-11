import sys
import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"


CONFIG = {
    "testname": "vic20 text pattern",
    "projdir": "dispatchtest1",
    "cmainfile": "testprog",
    "testtype": "dispatchtest",
    "archtype": "vic20",
    "platform": "Graphics",
    "viceconf": "vic20_viceconf.cfg",
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/vic20src/",
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
    "steps": [
        {
            "action": "test_compiletheprogram",
            "param": {"string": ""},
            "subaction": ""
        },
        {
            "action": "test_emulator_start",
            "param": {
                "disk_path": None,
                "name": None,
                "port": 6502,
                "string": "",
                "warpmode": True
            },
            "subaction": "disk_path"
        },
        {
            "action": "test_wordsearch",
            "param": {
                "attemptdelay": "3",
                "failphrase": "fail",
                "numberofattempts": "2",
                "successphrase": "bytes"
            },
            "subaction": ""
        },
        {
            "action": "test_sendrun",
            "param": {"string": ""},
            "subaction": ""
        },
        {
            "action": "test_terminate_all",
            "param": {"string": ""},
            "subaction": ""
        }
    ],
}

CONFIG["paths"] = init_test_env(CONFIG, __name__)

# CONFIG = {
#     "testname": "vic20 text pattern",            # nickname for 
#     "projdir": "dispatchtest1", 
#     "cmainfile": "testprog",                # c-file progname no extenion to give to compiler
#     "testtype": "dispatchtest",                # name for this test type, used to make new run-button of like-named tests
#     "archtype": "vic20",                  # 1st tier sorting category. vice wants lowercase c64, vic20 or c128
#     "platform": "Graphics",             # 2nd tier sorting category
#     "viceconf": "vic20_viceconf.cfg",     # sound conf location, assume this starts at PATHS["projdir"]
#     "linkerconf": "",
#     "projbasedir": "/testsrc/sourcedir/vic20src/",
#     "steps": [
#         {
#                 "action": "test_compiletheprogram",
#                 "param": {
#                         "string": ""
#                 },
#                 "subaction": ""
#         },
#         {
#                 "action": "test_emulator_start",
#                 "param": {
#                         "disk_path": None,
#                         "name": None,
#                         "port": 6502,
#                         "string": "",
#                         "warpmode": True
#                 },
#                 "subaction": "disk_path"
#         },
#         {
#                 "action": "test_wordsearch",
#                 "param": {
#                         "attemptdelay": "3",
#                         "failphrase": "fail",
#                         "numberofattempts": "2",
#                         "successphrase": "bytes"
#                 },
#                 "subaction": ""
#         },
#         {
#                 "action": "test_sendrun",
#                 "param": {
#                         "string": ""
#                 },
#                 "subaction": ""
#         },
#         {
#                 "action": "test_terminate_all",
#                 "param": {
#                         "string": ""
#                 },
#                 "subaction": ""
#         }
# ],
# }

# computed paths, need to have abs path
PATHS = init_test_env(CONFIG, __name__)

base = os.path.join(CONFIG["projbasedir"], CONFIG["projdir"])

# CONFIG["paths"] = {
#     "src": PATHS["src"],
#     "out": PATHS["out"],
#     "viceconf": os.path.join(base, CONFIG["viceconf"]),
#     "prg": os.path.join(base, PATHS["out"], CONFIG["cmainfile"] + ".prg"),
#     "d64file_abs": os.path.join(base, PATHS["out"], CONFIG["cmainfile"] + ".d64"),
# }




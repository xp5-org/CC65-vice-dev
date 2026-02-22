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
            "out": {
                "_rel": "output",
                "d64file_abs": "{cmainfile}.d64",
                "prg": "{cmainfile}.prg"
            },
            "src": {
                "_rel": "src"
            },
            "viceconf": "{viceconf}"
        }
    },
    "steps": [
        {
            "action": "test_compiletheprogram",
            "param": {
                "string": "",
                "out_dir": None,
                "src_dir": None,
                "cmainfile": None,
                "drv1_path": None,
                "drv1_label": None,
                "prg_filepath": None,
                "d64_file": None,
                "archtype": None
            },
            "subaction": ""
        },
        {
            "action": "test_emulator_start",
            "param": {
                "disk_path": None,
                "name": None,
                "port": 6502,
                "string": "",
                "warpmode": True,
                "viceconf": None,
                "disk8_path": None,
                "disk9_path": None,
                "autostart_path": None,
                "rom_path": None
            },
            "subaction": "disk_path"
        },
        {
            "action": "test_wordsearch",
            "param": {
                "attemptdelay": "3",
                "failphrase": "fail",
                "numberofattempts": "2",
                "successphrase": "bytes",
                "c128windowcolnum": None
            },
            "subaction": ""
        },
        {
            "action": "test_sendrun",
            "param": {
                "string": ""
            },
            "subaction": ""
        },
        {
            "action": "test_wait30seconds",
            "param": {
                "seconds": "5"
            },
            "subaction": ""
        },
        {
            "action": "test_terminate_all",
            "param": {
                "string": ""
            },
            "subaction": ""
        }
    ],
}

PATHS = init_test_env(CONFIG, __name__)

base = os.path.join(CONFIG["projbasedir"], CONFIG["projdir"])

import sys
import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_c128_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "C128 MCM Gradient",
    "projdir": "mcmc128",
    "cmainfile": "mcmc128.c",
    "testtype": "build",
    "archtype": "c128",
    "platform": "Graphics",
    "viceconf": "c128_viceconf.cfg",
    "linkerconf": "",
    "projbasedir": "/testsrc/sourcedir/c128src/",
    "prg_filename": "mcmc128main.prg",
    "d64_disk8_name": "mcmc128.d64",
    "d64_disk9_name": "",
    "cmainfile_path": "{src}{cmainfile}",
    "src": "{projbasedir}{projdir}/src/",
    "d64_drive8_file": "{out_dir}/{d64_disk8_name}",
    "d64_drive9_file": "{out_dir}/{d64_disk9_name}",
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
                "archtype": None,
                "cmainfile": None,
                "d64_drive8_file": "{d64_drive8_file}",
                "d64_file": None,
                "out_dir": "{out_dir}",
                "prg_filepath": "{prg_filepath}",
                "src_dir": "{src}",
                "drv1_path": None,
                "drv1_label": None
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
                "c128windowcolnum": None,
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
                "c128windowcolnum": None,
                "failphrase": "error",
                "numberofattempts": "10",
                "successphrase": "status: 00"
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
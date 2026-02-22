import os
import time

from apphelpers import init_test_env, register_mytest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, assemble_object, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

CONFIG = {
    "testname": "diskrwlisttest",
    "projdir": "diskrwlist_format",
    "cmainfile": "diskformat.c",
    "testtype": "format",
    "archtype": "c64",
    "platform": "Disk IO",
    "viceconf": "vice_C64nosound.cfg",
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

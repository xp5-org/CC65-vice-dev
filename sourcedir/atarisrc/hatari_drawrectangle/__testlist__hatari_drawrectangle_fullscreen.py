import sys
import os
import time

from apphelpers import init_test_env, register_mytest
from atarihelpers import HatariInstance
VICE_IP = "127.0.0.1"


CONFIG = {
    "testname": "hatari rectangle draw",
    "projdir": "hatari_drawrectangle",
    "cmainfile": "rectangle_fullscreen.c",
    "prg_filename": "rectangle_fullscreen.prg",
    "testtype": "fullscreen",
    "archtype": "st",
    "romfile": "etos256us.img",
    "platform": "Graphics",
    "mountpath": "{out_dir}",
    "projbasedir": "/testsrc/sourcedir/atarisrc/",
    "src": "{projbasedir}{projdir}/src/",
    "cmainfile_path": "{src}{cmainfile}",
    "romfilefile_path": "{src}{romfile}",
    "out_dir": "{projbasedir}{projdir}/output",
    "prg_filepath": "{projbasedir}{projdir}/output/{prg_filename}",
    "structure": {},
    "steps": [
        {
            "action": "test_compile4atari",
            "param": {
                "out_dir": "{out_dir}",
                "prg_filepath": "{prg_filepath}",
                "src_dir": "{src}"
            },
            "subaction": ""
        },
        {
            "action": "test_hatari_start",
            "param": {
                "config_path": "",
                "fastboot": "True",
                "mountpath": "{out_dir}",
                "name": "",
                "port": "",
                "prg_filename": "{prg_filename}",
                "romfile_path": "{romfilefile_path}"
            },
            "subaction": ""
        },
        {
            "action": "test_wait30seconds",
            "param": {
                "seconds": "45"
            },
            "subaction": ""
        },
        {
            "action": "test_hatariterminate_all",
            "param": {},
            "subaction": ""
        }
    ],
}

PATHS = init_test_env(CONFIG, __name__)

base = os.path.join(CONFIG["projbasedir"], CONFIG["projdir"])

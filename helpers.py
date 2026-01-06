import os
import time
import subprocess
import socket
import tempfile
import threading
from PIL import Image
import pytesseract

PROGRESS_FILE = "progress.txt"
REPORT_DIR = "reports"
compile_logs_dir = "compile_logs"

testfile_registry = {}
buildtest_registry = []
playtest_registry = []
packagetest_registry = []

def clear_registries():
    buildtest_registry[:] = []
    playtest_registry[:] = []
    packagetest_registry[:] = []
    testfile_registry.clear()




def register_testfile(id, types, description=None, system=None, platform=None):
    def decorator(module=None):
        import inspect
        modname = module.__name__ if module else inspect.stack()[1][0].f_globals["__name__"]
        testfile_registry[modname] = {
            "id": id,
            "types": types,
            "description": description,
            "system": system,
            "platform": platform,
        }
        return module  # <-- must return module to preserve normal import behavior
    return decorator

def register_playtest(description):
    def decorator(func):
        func.test_description = description
        playtest_registry.append(func)
        return func
    return decorator

def register_buildtest(description):
    def decorator(func):
        func.test_description = description
        buildtest_registry.append(func)
        return func
    return decorator

def register_packagetest(description):
    def decorator(func):
        func.test_description = description
        packagetest_registry.append(func)
        return func
    return decorator
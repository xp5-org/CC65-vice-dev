import sys
import os
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) #auto import /mytests dir as modules
from helpers import register_testfile, register_buildtest
from vicehelpers import send_vice_command, ViceInstance, next_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
import ip232relayserver
VICE_IP = "127.0.0.1"


#this is to track if the relay server is already started or not
relay_started = False
relay_lock = threading.Lock()


register_testfile(
    id="ip232 debug",
    types=["build"],
    system="C64",
    platform="ip232debug",
)(sys.modules[__name__])







@register_buildtest("Build 3 - start relay server")
def build3_launch_rx(context):
    print("ip232relayserver loaded:", __file__)
    print("Has start_server():", hasattr(ip232relayserver, 'start_server'))
    global relay_started
    log = []
    name = "relay_server"
    port = 6501

    with relay_lock:
        if not relay_started:
            server_thread = threading.Thread(target=ip232relayserver.start_server, daemon=True)
            server_thread.start()
            relay_started = True
            context[name] = {"thread": server_thread, "started": True}
            log.append(f"{name} started on port {port}")
        else:
            log.append(f"{name} was already started")

    return True, "\n".join(log)



@register_buildtest("Build 9 - terminate relay & collect logs")
def build9_stoprelay(context):
    log = []
    name = "relay_server"

    with relay_lock:
        relay_info = context.get(name)
        if relay_info and relay_info.get("started"):
            thread = relay_info.get("thread")
            logs = ip232relayserver.stop_server()  # this returns the per-client log lines
            if thread:
                thread.join(timeout=5)
            relay_info["started"] = False
            log.append("relay stopped")
            log.extend(logs)
        else:
            log.append("error: relay server was not running")

    return True, "\n".join(log)
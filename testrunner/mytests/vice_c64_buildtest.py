import sys
import os
import time
import threading
import socket

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers import register_testfile, register_buildtest
from vicehelpers import start_vice, wait_for_port, send_vice_command, ViceInstance, next_vice_instance, launch_vice_instance
from vicehelpers import compile_cc65, assemble_ca65, link_ld65, create_blank_d64, format_and_copyd64
VICE_IP = "127.0.0.1"

register_testfile(
    id="C64",
    types=["build"],
    system="VICE",
    platform="VICE",
)(sys.modules[__name__])



import os

@register_buildtest("build 1 - rx client")
def build1_rxclient(context):
    src_dir = './cc65_rx_src'
    out_dir = './cc65_rx_output'
    os.makedirs(out_dir, exist_ok=True)

    source_file = os.path.join(src_dir, 'main.c')
    asm_file = os.path.join(out_dir, 'main.s')
    obj_file = os.path.join(out_dir, 'main.o')
    prg_file = os.path.join(out_dir, 'main.prg')
    d64_file = os.path.join(out_dir, 'test.d64')

    log = []

    success, out = compile_cc65(source_file, asm_file)
    log.append("Compile cc65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = assemble_ca65(asm_file, obj_file)
    log.append("Assemble ca65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = link_ld65(obj_file, prg_file)
    log.append("Link ld65:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = create_blank_d64(d64_file)
    log.append("Create blank d64:\n" + out)
    if not success:
        return False, "\n".join(log)

    success, out = format_and_copyd64(d64_file, prg_file)
    log.append("Format and copy to d64:\n" + out)
    if not success:
        return False, "\n".join(log)

    return True, "\n".join(log)



@register_buildtest("Build 3 - start TX vice instance")
def build1_launch_tx(context):
    name, port = next_vice_instance(context)
    disk = "/path/to/my.d64"
    config = "/path/to/vice.cfg"
    
    instance = ViceInstance(name, port, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]
    

    instance.start()
    time.sleep(5) # wait for C64 to boot
    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{instance.output}")
        return False, "\n".join(log)

    context[name] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{instance.output}")
    return True, "\n".join(log)


@register_buildtest("Build 2 - start RX vice instance")
def build2_launch_rx(context):
    name, port = next_vice_instance(context)
    disk = "/path/to/my.d64"
    config = "/path/to/vice.cfg"
    
    instance = ViceInstance(name, port, config_path=config, disk_path=disk)
    log = [f"Launching {name} on port {port} with disk={disk} config={config}"]

    instance.start()
    time.sleep(5) # wait for C64 to boot
    if not instance.wait_for_ready():
        log.append(f"{name} did not become ready on port {port}")
        log.append(f"{name} stdout:\n{instance.output}")
        return False, "\n".join(log)

    context[name] = instance
    log.append(f"{name} is ready")
    log.append(f"{name} stdout:\n{instance.output}")
    return True, "\n".join(log)

@register_buildtest("Build 3 - terminate all")
def build3_stopallvice(context):
    log = []
    time.sleep(5)
    for name, instance in context.items():
        if isinstance(instance, ViceInstance):
            log.append(f"Stopping {name} on port {instance.port}")
            instance.stop()
            log.append(f"{name} has exited.")

    if not log:
        return False, "No VICE instances found to stop."

    return True, "\n".join(log)

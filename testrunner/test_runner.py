import os
import time
import re
import datetime
from PIL import Image
import shutil
#import mytests.buildtest
#import mytests.playtest

import os
import shutil
import re
import datetime

import helpers

QEMU_IMAGE = "hdd.qcow2"
MONITOR_PORT = 55555
PROGRESS_FILE = "progress.txt"
REPORT_DIR = "reports"
qemu_process = None
compile_logs_dir = "compile_logs"



context = {
    "sock": None,
    "qemu_process": None,
    "abort": False
}




import importlib
import sys
import os



def reload_tests():
    helpers.clear_registries()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(base_dir, "mytests")
    for fname in os.listdir(test_dir):
        if fname.endswith(".py") and not fname.startswith("__"):
            modname = f"mytests.{fname[:-3]}"
            if modname in sys.modules:
                importlib.reload(sys.modules[modname])
            else:
                __import__(modname)

import datetime
import importlib


def run_testfile(module_name):
    import importlib
    full_module_name = f"mytests.{module_name}"

    try:
        importlib.import_module(full_module_name)
    except ImportError as e:
        print(f"Failed to import {full_module_name}: {e}")
        return []

    # Lookup testfile metadata by full module name
    meta = helpers.testfile_registry.get(full_module_name)
    if not meta:
        print(f"No metadata found for module '{full_module_name}' in helpers.testfile_registry")
        return []

    test_types = meta.get("types", [])
    results = []
    context = {"sock": None, "qemu_process": None}

    # Map test types to global registries
    registry_map = {
        "build": helpers.buildtest_registry,
        "play": helpers.playtest_registry,
        "package": helpers.packagetest_registry,  # fix spelling if possible
    }

    for t in test_types:
        registry = registry_map.get(t)
        if not registry:
            print(f"No registry found for test type '{t}'")
            continue

        # Filter tests defined in this module only
        tests = [f for f in registry if f.__module__ == full_module_name]

        if not tests:
            print(f"No tests found in registry '{t}' for module '{full_module_name}'")
            continue

        test_cases = [f.test_description for f in tests]
        results.extend(run_tests(test_cases, tests, context))

    if context.get("qemu_process"):
        context["qemu_process"].terminate()
        context["qemu_process"].wait(timeout=5)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir_path = os.path.join(REPORT_DIR, timestamp)
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path, exist_ok=True)
    report_path = os.path.join(subdir_path, f"{module_name}.html")
    generate_report(results, report_path)

    return results





def run_registered_test(name, registry, context):
    for test_func in registry:
        if test_func.test_description == name:
            try:
                print(f"Running {name}")
                start_time = time.time()
                result = test_func(context)
                duration = time.time() - start_time
                if len(result) == 3:
                    success, log_output, stdout_output = result
                else:
                    success, log_output = result
                    stdout_output = ""
                status = "PASS" if success else "FAIL"
                color = "green" if success else "red"
            except Exception as e:
                status = "ERROR"
                log_output = str(e)
                stdout_output = ""
                color = "gray"
                duration = 0.0
            return (name, status, color, log_output, stdout_output, duration)
    return (name, "NOT FOUND", "gray", "No matching test found", "", 0.0)



def run_tests(test_descriptions, registry, context):
    reload_tests()
    results = []
    total = len(test_descriptions)

    with open(PROGRESS_FILE + ".tmp", "w") as pf:
        pf.write(f"0/{total}|Starting")
    os.replace(PROGRESS_FILE + ".tmp", PROGRESS_FILE)

    for index, name in enumerate(test_descriptions, start=1):
        with open(PROGRESS_FILE + ".tmp", "w") as pf:
            pf.write(f"{index-1}/{total}|{name}")
        os.replace(PROGRESS_FILE + ".tmp", PROGRESS_FILE)

        print(f"Running test {index}/{total}: {name}")

        if context.get("abort"):
            print(f"Skipping {name} due to previous failure")
            results.append((name, "SKIPPED", "gray", "Skipped due to earlier failure", "", 0.0))
            continue

        result = run_registered_test(name, registry, context)
        if result:
            results.append(result)

    print(f"Completed {len(results)}/{total}")
    time.sleep(1)
    return results



def generate_report(results, report_path):
    subdir_path = os.path.dirname(report_path)
    print(f"Creating directory: '{subdir_path}'")
    if subdir_path and not os.path.exists(subdir_path):
        os.makedirs(subdir_path, exist_ok=True)

    # Move compile logs into report subdir
    if os.path.exists(compile_logs_dir):
        for filename in os.listdir(compile_logs_dir):
            shutil.move(os.path.join(compile_logs_dir, filename), subdir_path)

    # Move images (.png, .ppm) from REPORT_DIR to report subdir
    # Move images (.png, .ppm, .gif) from REPORT_DIR to report subdir
    for filename in os.listdir(REPORT_DIR):
        if re.match(r"test\d+\.(png|ppm|gif)$", filename):
            shutil.move(os.path.join(REPORT_DIR, filename), subdir_path)


    with open(report_path, "w") as f:
        f.write("""<html>
<head>
<title>Test Report</title>
<style>
body { font-family: sans-serif; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
.green { background-color: #c8f7c5; }
.red { background-color: #f7c5c5; }
.gray { background-color: #eeeeee; }

.flex-container {
    display: flex;
    gap: 20px;
    flex-wrap: nowrap;
    max-width: 100%;
}

.output-column {
    flex: 1;
    min-width: 0;
    max-width: 50%;
    overflow: hidden;
    background-color: #f0f0f0;
    padding: 10px;
}

.image-column {
    flex: 1;
    max-width: 50%;
}

pre {
    background-color: #eee;
    padding: 10px;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
    max-width: 100%;
    overflow-x: auto;
}
hr { margin: 40px 0; }
</style>


</head>
<body>
<h1>Test Report</h1>
<table>
<tr><th>Test Name</th><th>Duration (s)</th><th>Result</th></tr>
""")

        for name, status, color, _, _, duration in results:
            f.write(f'<tr><td>{name}</td><td>{duration:.2f}</td><td class="{color}">{status}</td></tr>\n')

        f.write("</table><h2>Detailed Output</h2>\n")

        # Map screenshots by test index (expects files like test1.png, test2.png, ...)
        screenshot_map = {}
        for fname in os.listdir(subdir_path):
            m_png = re.match(r"test(\d+)\.png$", fname)
            m_gif = re.match(r"test(\d+)\.gif$", fname)
            if m_gif:
                idx = int(m_gif.group(1))
                screenshot_map[idx] = fname  # store GIF with priority
            elif m_png:
                idx = int(m_png.group(1))
                # Only add PNG if GIF not already present for this index
                if idx not in screenshot_map:
                    screenshot_map[idx] = fname

        for idx, (name, status, color, output, stdout, duration) in enumerate(results):
            img_index = idx + 1
            if img_index in screenshot_map:
                img_file = screenshot_map[img_index]
                img_tag = f'<img src="{img_file}" alt="{img_file}" style="max-width: 100%; border: 1px solid #ccc;">'
            else:
                img_tag = "<p>No screenshot available.</p>"

            f.write(f"""
<hr>
<div class="flex-container">
    <div class="output-column">
        <h3>{name}</h3>
        <p><strong>Duration:</strong> {duration:.2f} seconds</p>
        <pre>
        OUTPUT:\n{output}\n\n
        STDOUT:\n{stdout}\n\n</pre>
    </div>
    <div class="image-column">
        <h4>Screenshot</h4>
        {img_tag}
    </div>
</div>

""")

        f.write("</body></html>")
    print(f"Wrote report to {report_path}")

            


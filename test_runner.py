import os
import time
import re
import datetime
import shutil
import datetime
import helpers
import datetime
import importlib
import sys
from collections import defaultdict



PROGRESS_FILE = "progress.txt"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
compile_logs_dir = os.path.join(BASE_DIR, "compile_logs")




context = {
    "sock": None,
    "abort": False
}

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


def run_testfile(module_name):
    reload_tests() 

    full_module_name = f"mytests.{module_name}"

    try:
        importlib.import_module(full_module_name)
    except ImportError as e:
        print(f"Failed to import {full_module_name}: {e}")
        return []

    meta = helpers.testfile_registry.get(full_module_name)
    if not meta:
        print(f"No metadata found for module '{full_module_name}' in helpers.testfile_registry")
        return []

    test_types = meta.get("types", [])
    results = []
    context = {"sock": None}

    registry_map = {
        "build": helpers.buildtest_registry,
        "play": helpers.playtest_registry,
        "package": helpers.packagetest_registry,
    }

    for t in test_types:
        registry = registry_map.get(t)
        if not registry:
            print(f"No registry found for test type '{t}'")
            continue

        tests = [f for f in registry if f.__module__ == full_module_name]
        if not tests:
            print(f"No tests found in registry '{t}' for module '{full_module_name}'")
            continue

        test_cases = [f.test_description for f in tests]
        results.extend(run_tests(test_cases, tests, context))


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

    # Move screenshots from REPORT_DIR into subdir
    for filename in os.listdir(REPORT_DIR):
        if (re.match(r"test\d+\.(png|ppm|gif)$", filename) or
            filename.startswith("screenshot-")):
            shutil.move(os.path.join(REPORT_DIR, filename), subdir_path)
            print("moved image to ", REPORT_DIR, filename)

    # Collect screenshots by integer test step
    screenshot_map = defaultdict(list)
    for fname in os.listdir(subdir_path):
        if fname.endswith((".png", ".gif")):
            # Match filenames like screenshot-vice1-6-1.png or screenshot-vice2-6.png
            m = re.match(r"screenshot-[^-]+-(\d+)(?:-\d+)?\.(png|gif)$", fname)
            if m:
                step_num = int(m.group(1))
                screenshot_map[step_num].append(fname)

    # Write HTML report
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

        # Summary table
        for name, status, color, _, _, duration in results:
            f.write(f'<tr><td>{name}</td><td>{duration:.2f}</td><td class="{color}">{status}</td></tr>\n')

        f.write("</table><h2>Detailed Output</h2>\n")

        # Detailed sections with screenshots linked by index (starting at 1)
        for idx, (name, status, color, output, stdout, duration) in enumerate(results, start=1):
            matching_images = screenshot_map.get(idx, [])
            if matching_images:
                img_tags = "\n".join(
                    f'<img src="{img}" alt="{img}" style="max-width: 100%; border: 1px solid #ccc;">'
                    for img in matching_images
                )
            else:
                img_tags = "<p>No screenshot available.</p>"

            f.write(f"""<hr>
    <div class="flex-container">
    <div class="output-column">
        <h3>{name}</h3>
        <p><strong>Duration:</strong> {duration:.2f} seconds</p>
        <pre>OUTPUT:
        {output}

    STDOUT:
    {stdout}</pre>
        </div>
        <div class="image-column">
            <h4>Screenshot</h4>
            {img_tags}
        </div>
        </div>
        """)

        f.write("</body></html>")

    print(f"Wrote report to {report_path}")

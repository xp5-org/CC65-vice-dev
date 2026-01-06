import os
import datetime
from flask import Flask, render_template, send_from_directory
from bs4 import BeautifulSoup
import test_runner
import threading
import helpers
from flask import jsonify
import importlib
import pkgutil
import mytests
from collections import defaultdict

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
build_REPORT_DIR = REPORT_DIR
play_REPORT_DIR = REPORT_DIR



@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


def get_report_summaries():
    if not os.path.exists(build_REPORT_DIR):
        return []

    summaries = []
    reports = []
    for subdir in sorted(os.listdir(build_REPORT_DIR), reverse=True):
        subdir_path = os.path.join(build_REPORT_DIR, subdir)
        if os.path.isdir(subdir_path):
            for f in os.listdir(subdir_path):
                if f.endswith(".html"):
                    reports.append(os.path.join(subdir, f))

    for report in reports:
        path = os.path.join(build_REPORT_DIR, report)
        try:
            with open(path, "r") as f:
                content = f.read()
                soup = BeautifulSoup(content, "html.parser")
                table = soup.find("table")
                if not table:
                    status = "UNKNOWN"
                    duration_total = ""
                else:
                    status = "PASS"
                    duration_total = 0.0
                    for row in table.find_all("tr")[1:]:
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            duration_text = cols[1].get_text(strip=True)
                            test_status = cols[2].get_text(strip=True).upper()

                            try:
                                duration = float(duration_text.rstrip("s"))
                                duration_total += duration
                            except ValueError:
                                pass

                            if "FAIL" in test_status:
                                status = "FAIL"

                    duration_total = f"{duration_total:.2f}s" if duration_total else ""

                summaries.append((report, duration_total, status))
        except Exception:
            summaries.append((report, "", "ERROR"))

    return summaries


@app.route("/testfile_list")
def testfile_list():
    for _, modname, _ in pkgutil.iter_modules(mytests.__path__):
        importlib.import_module(f"mytests.{modname}")

    grouped = defaultdict(lambda: {
        "types": {},
        "files": [],
        "description": None,
        "system": None,
        "platform": None,
    })

    for modname, meta in helpers.testfile_registry.items():
        file = modname.split('.')[-1]
        for t in meta["types"]:
            grouped[meta["id"]]["types"][t] = file
        grouped[meta["id"]]["files"].append(file)
        # Only set description, system, platform if not set yet
        if grouped[meta["id"]]["description"] is None:
            grouped[meta["id"]]["description"] = meta.get("description")
        if grouped[meta["id"]]["system"] is None:
            grouped[meta["id"]]["system"] = meta.get("system")
        if grouped[meta["id"]]["platform"] is None:
            grouped[meta["id"]]["platform"] = meta.get("platform")

    result = []
    for test_id, info in grouped.items():
        result.append({
            "id": test_id,
            "types": info["types"],
            "description": info["description"],
            "system": info["system"],
            "platform": info["platform"],
        })

    print("Returning testfile list:", result)  # debug print
    return jsonify(result)


def get_latest_report_summary():
    if not os.path.exists(build_REPORT_DIR):
        return []

    all_reports = []
    for subdir in sorted(os.listdir(build_REPORT_DIR), reverse=True):
        subdir_path = os.path.join(build_REPORT_DIR, subdir)
        if os.path.isdir(subdir_path):
            for f in os.listdir(subdir_path):
                if f.endswith(".html"):
                    all_reports.append((subdir, f))

    if not all_reports:
        return []

    # sort timestamp dir
    all_reports.sort(reverse=True)
    latest_subdir, latest_file = all_reports[0]
    latest_path = os.path.join(build_REPORT_DIR, latest_subdir, latest_file)

    with open(latest_path, "r") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    summary = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 3:
            test_name = cols[0].get_text(strip=True)
            duration_text = cols[1].get_text(strip=True)
            status_text = cols[2].get_text(strip=True).upper()

            if "PASS" in status_text:
                status = "PASS"
            elif "FAIL" in status_text:
                status = "FAIL"
            else:
                status = status_text
            summary.append((test_name, duration_text, status))
    return summary


@app.route("/")
def index():
    if not os.path.exists(build_REPORT_DIR):
        os.makedirs(build_REPORT_DIR)
    summaries = get_report_summaries()
    latest_summary = get_latest_report_summary()
    return render_template("index.html", summaries=summaries, latest_summary=latest_summary)


@app.route("/run/<testname>")
def run_named_tests(testname):
    print(f"run {testname} called")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.html"
    path = os.path.join(REPORT_DIR, filename)

    def run():
        test_runner.run_testfile(testname)
        with open("progress.txt", "w") as pf:
            pf.write("Done")

    with open("progress.txt", "w") as pf:
        pf.write("0/0")

    threading.Thread(target=run).start()
    return "Started"


@app.route("/progress")
def progress():
    try:
        with open("progress.txt", "r") as f:
            data = f.read().strip()
            if "|" in data:
                step, test_name = data.split("|", 1)
            else:
                step, test_name = data, ""
            return jsonify({
                "step": step,
                "test_name": test_name
            })
    except FileNotFoundError:
        return jsonify({"step": "Done", "test_name": ""})


@app.route("/reports/<path:filepath>")
def view_report(filepath):
    # filepath could be "timestamp/filename.html" or "filename.html"
    full_path = os.path.join(build_REPORT_DIR, filepath)
    if not os.path.isfile(full_path):
        return "File not found", 404
    directory, filename = os.path.split(full_path)
    return send_from_directory(directory, filename)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

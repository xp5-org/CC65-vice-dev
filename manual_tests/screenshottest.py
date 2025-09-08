import subprocess
import time

def find_window_id(name="c64"):
    try:
        output = subprocess.check_output(["xdotool", "search", "--name", name])
        return output.decode().splitlines()[0]
    except subprocess.CalledProcessError:
        return None

def main():
    # Start x64
    proc = subprocess.Popen(["x64"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Started x64 with PID {proc.pid}")

    # Wait for window to appear
    time.sleep(5)

    # Find window ID
    winid = find_window_id()
    if not winid:
        print("Window not found.")
        proc.terminate()
        return

    print(f"Found window ID: {winid}")

    # Focus (unminimize and activate) the window
    subprocess.run(["xdotool", "windowmap", winid])
    subprocess.run(["xdotool", "windowactivate", winid])

    # Take screenshot
    screenshot_file = "screenshot.png"
    try:
        subprocess.run(["import", "-window", winid, screenshot_file], check=True)
        print(f"Screenshot saved to {screenshot_file}")
    except subprocess.CalledProcessError:
        print("Failed to take screenshot")

    # Cleanup
    proc.terminate()
    proc.wait()

if __name__ == "__main__":
    main()


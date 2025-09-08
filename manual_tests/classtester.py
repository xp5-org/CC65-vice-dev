import time
from vicehelpers import ViceInstance  # adjust the module name if needed

def main():
    name = "vice1"
    port = 65501

    instance = ViceInstance(name, port)
    instance.start()

    print(f"Started VICE instance '{name}' on port {port}, waiting 5 seconds...")
    time.sleep(5)

    success = instance.take_screenshot()
    if success:
        print(f"Screenshot taken for {name}")
    else:
        print(f"Failed to take screenshot for {name}")

    print("Stopping VICE instance...")
    instance.stop()

if __name__ == "__main__":
    main()

import time
import ip232relayserver  # replace with the filename of your server code, without .py

if __name__ == "__main__":
    ip232relayserver.start_server()  # start the server with default HOST and PORT

    try:
        while True:
            time.sleep(1)  # keep the main thread alive so the server threads keep running
    except KeyboardInterrupt:
        print("\nServer stopped by user")

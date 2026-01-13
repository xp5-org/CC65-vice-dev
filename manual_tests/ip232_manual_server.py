import time
import ip232relayserver

if __name__ == "__main__":
    ip232relayserver.start_server()  # start the server with default HOST and PORT

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")

import socket
import threading
import time

HOST = '0.0.0.0'
PORT = 6501

IP232_CMD_SET_DTR = 0x01
IP232_CMD_SET_RTS = 0x02
IP232_CMD_QUERY_LINES = 0x0E
IP232_CMD_LINE_STATUS = 0x0F

LINE_DTR = 0x01
LINE_RTS = 0x02
LINE_CTS = 0x04
LINE_DSR = 0x08
LINE_CD  = 0x10

def petscii_to_ascii(b):
    if 0xC1 <= b <= 0xDA:
        return chr(b - 0xC1 + ord('A'))
    elif 0x30 <= b <= 0x39:
        return chr(b)
    elif b == 0x0D:
        return '\n'
    elif 0x20 <= b <= 0x3F:
        return chr(b)
    else:
        return '.'

def print_petscii_line(data):
    line = ''.join(petscii_to_ascii(b) for b in data)
    hex_line = ' '.join(f'{b:02X}' for b in data)
    print(f"{line}    {hex_line}")

class IP232Server:
    clients_lock = threading.Lock()
    clients = []

    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.lines_out = 0
        self.lines_in = LINE_CTS | LINE_DSR | LINE_CD
        self.lock = threading.Lock()
        self.buffer = bytearray()
        self.state = 'normal'
        self.cmd_byte = None
        self.running = True

    def send_control(self, cmd, val=0):
        try:
            self.conn.sendall(bytes([0xFF, cmd, val]))
        except Exception:
            pass

    def handle_control_command(self, cmd, val):
        with self.lock:
            if cmd == IP232_CMD_SET_DTR:
                old = self.lines_out & LINE_DTR
                if val:
                    self.lines_out |= LINE_DTR
                else:
                    self.lines_out &= ~LINE_DTR
                if old != (self.lines_out & LINE_DTR):
                    print(f"DTR set to {bool(val)} from {self.addr}")

            elif cmd == IP232_CMD_SET_RTS:
                old = self.lines_out & LINE_RTS
                if val:
                    self.lines_out |= LINE_RTS
                else:
                    self.lines_out &= ~LINE_RTS
                if old != (self.lines_out & LINE_RTS):
                    print(f"RTS set to {bool(val)} from {self.addr}")

            elif cmd == IP232_CMD_QUERY_LINES:
                print(f"Client {self.addr} requested line status")
                self.send_control(IP232_CMD_LINE_STATUS, self.lines_in)

            else:
                print(f"Unknown control command: {cmd} {val} from {self.addr}")

    def process_data(self, data):
        self.buffer.extend(data)
        i = 0
        out_bytes = bytearray()

        while i < len(self.buffer):
            b = self.buffer[i]
            if self.state == 'normal':
                if b == 0xFF:
                    self.state = 'got_0xFF'
                else:
                    out_bytes.append(b)
                i += 1
            elif self.state == 'got_0xFF':
                if b == 0xFF:
                    out_bytes.append(0xFF)
                    self.state = 'normal'
                    i += 1
                else:
                    self.cmd_byte = b
                    self.state = 'got_cmd'
                    i += 1
            elif self.state == 'got_cmd':
                val = b
                self.handle_control_command(self.cmd_byte, val)
                self.state = 'normal'
                i += 1

        self.buffer.clear()

        if out_bytes:
            print_petscii_line(out_bytes)
            self.broadcast(out_bytes)

    def broadcast(self, data):
        with IP232Server.clients_lock:
            for client in IP232Server.clients:
                if client is not self:
                    try:
                        client.conn.sendall(data)
                    except Exception:
                        # Ignore send errors; client cleanup will handle
                        pass

    def keep_alive(self):
        while self.running:
            try:
                self.send_control(IP232_CMD_LINE_STATUS, self.lines_in)
                time.sleep(5)
            except Exception:
                break

    def close(self):
        self.running = False
        try:
            self.conn.close()
        except Exception:
            pass

def client_thread(conn, addr):
    server = IP232Server(conn, addr)
    with IP232Server.clients_lock:
        IP232Server.clients.append(server)

    threading.Thread(target=server.keep_alive, daemon=True).start()

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"Connection closed from {addr}")
                break
            server.process_data(data)
    except Exception as e:
        print(f"Connection error from {addr}: {e}")

    server.close()
    with IP232Server.clients_lock:
        if server in IP232Server.clients:
            IP232Server.clients.remove(server)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"IP232 RX server listening on {HOST}:{PORT}...")

        while True:
            conn, addr = s.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=client_thread, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    main()


import socket
import threading
import time
import struct

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


server_socket = None
accept_thread = None
server_running = threading.Event()


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

        self.rx_symbols = 0
        self.tx_symbols = 0
        self.name = None

        # Correlation back to the Python-side VICE instance. connect_index is
        # the 0-based accept order; instance_name is filled in by correlation
        # against the context's instance start order (see correlate_instances).
        self.connect_index = None
        self.connected_at = time.time()
        self.instance_name = None

        # Captured payload bytes for per-instance validation/logging:
        #   sent_text — bytes this client transmitted (relay received from it)
        #   recv_text — bytes this client received (relay forwarded to it)
        self.sent_text = bytearray()
        self.recv_text = bytearray()


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
            self.rx_symbols += len(out_bytes)
            self.sent_text.extend(out_bytes)
            print_petscii_line(out_bytes, sender=self.name or str(self.addr))
            self.broadcast(out_bytes)


    def broadcast(self, data):
        with IP232Server.clients_lock:
            for client in IP232Server.clients:
                if client is not self:
                    try:
                        client.conn.sendall(data)
                        client.tx_symbols += len(data)
                        client.recv_text.extend(data)
                    except Exception:
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


def petscii_to_ascii(b):
    if 0x41 <= b <= 0x5A:
        # PETSCII uppercase A-Z (what typed/unshifted letters send on the wire)
        return chr(b)
    elif 0xC1 <= b <= 0xDA:
        # Shifted-mode letters map to the same A-Z
        return chr(b - 0xC1 + ord('A'))
    elif 0x30 <= b <= 0x39:
        return chr(b)
    elif b == 0x0D:
        return '\n'
    elif 0x20 <= b <= 0x3F:
        return chr(b)
    else:
        return '.'

def petscii_bytes_to_str(data):
    return ''.join(petscii_to_ascii(b) for b in data)


def print_petscii_line(data, sender=None):
    line = petscii_bytes_to_str(data)
    hex_line = ' '.join(f'{b:02X}' for b in data)
    prefix = f"[{sender}] " if sender else ""
    print(f"{prefix}{line}    {hex_line}")

def client_thread(conn, addr, name):
    server = IP232Server(conn, addr)
    server.name = name
    with IP232Server.clients_lock:
        server.connect_index = len(IP232Server.clients)   # 0-based accept order
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
    #with IP232Server.clients_lock:
        #if server in IP232Server.clients:
            #IP232Server.clients.remove(server)

def start_server(host=HOST, port=PORT):
    global server_socket, accept_thread

    if server_running.is_set():
        print("Server is already running")
        return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Enable SO_REUSEADDR to allow binding to a recently-used port
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Set SO_LINGER to send RST on close (no lingering)
    linger_struct = struct.pack('ii', 1, 0)  # l_onoff=1, l_linger=0
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger_struct)
    server_socket.bind((host, port))
    server_socket.listen()
    server_socket.settimeout(2.0)
    server_running.set()

    print(f"IP232 RX server listening on {host}:{port}...")

    client_counter = 0  # global or nonlocal

    def accept_loop():
        nonlocal client_counter
        while server_running.is_set():
            try:
                conn, addr = server_socket.accept()
                client_name = f"vice{client_counter + 1}"
                print(f"Connection from {addr} assigned name {client_name}")
                client_counter += 1
                threading.Thread(target=client_thread, args=(conn, addr, client_name), daemon=True).start()
            except socket.timeout:
                # print("accept-thread socket timeout")
                # short timeout so the test closes fast when terminated
                continue
            except OSError:
                print("accept-thread oserr")
                # Socket closed or other OS error, exit loop
                break


    accept_thread = threading.Thread(target=accept_loop, daemon=True)
    accept_thread.start()

def client_count():
    """Number of clients currently connected to the relay."""
    with IP232Server.clients_lock:
        return len(IP232Server.clients)


def correlate_instances(instance_names):
    """Map relay connections to Python-side VICE instance names by connect order.

    `instance_names` is the ordered list of instance names as they were
    started (e.g. ["vice1_rx", "vice2_tx"]). The Nth client to connect is
    assumed to be the Nth instance started — test_emulator_start enforces this
    by waiting for each instance's relay connection before starting the next.
    Returns a list of (connect_index, instance_name, addr) for logging.
    """
    mapping = []
    if not instance_names:
        return mapping
    with IP232Server.clients_lock:
        ordered = sorted(IP232Server.clients,
                         key=lambda c: (c.connect_index if c.connect_index is not None else 0))
        for c in ordered:
            i = c.connect_index if c.connect_index is not None else 0
            if 0 <= i < len(instance_names):
                c.instance_name = instance_names[i]
                mapping.append((i, c.instance_name, c.addr))
    return mapping


def get_client_traffic(instance_names, target_name):
    """Return (sent_str, recv_str) for the named VICE instance, or (None, None).

    Correlates connections to instance names by connect order (see
    correlate_instances) and returns the decoded chars that instance
    transmitted (sent) and received (recv). Safe to call while running.
    """
    correlate_instances(instance_names)
    with IP232Server.clients_lock:
        for c in IP232Server.clients:
            if c.instance_name == target_name:
                return (petscii_bytes_to_str(c.sent_text),
                        petscii_bytes_to_str(c.recv_text))
    return None, None


def stop_server(instance_names=None):
    global server_socket, accept_thread
    logs = []

    # Correlate connections to named VICE instances (by connect order) so the
    # log identifies which instance sent/received what, not just "vice1/vice2".
    correlate_instances(instance_names)

    # Close all client connections and clear client list
    with IP232Server.clients_lock:
        logs.append(f"number of clients: {len(IP232Server.clients)}")
        for idx, client in enumerate(IP232Server.clients):
            cname = client.instance_name or client.name or f"client{idx}"
            sent_str = petscii_bytes_to_str(client.sent_text)
            recv_str = petscii_bytes_to_str(client.recv_text)
            # "sent"/"received" are from the VICE instance's point of view:
            # sent  = chars it transmitted out its serial port (relay rx)
            # recv  = chars it received on its serial port (relay tx to it)
            logs.append(f"{cname} (conn#{client.connect_index} {client.addr[0]}:{client.addr[1]}):")
            logs.append(f"  symbols sent: {client.rx_symbols}")
            logs.append(f"  symbols recv: {client.tx_symbols}")
            logs.append(f"  sent chars: {sent_str!r}")
            logs.append(f"  recv chars: {recv_str!r}")
            client.close()
        IP232Server.clients.clear()

    if server_running.is_set():
        # Close server socket first so accept() unblocks
        try:
            print("server socket closed")
            server_socket.close()
            server_socket = None
        except Exception as e:
            logs.append(f"Error closing server socket: {e}")

        server_running.clear()

        if accept_thread:
            print("accept thread found, trying to join it")
            accept_thread.join(timeout=5)
            logs.append("accept thread terminated")

    # Small delay to allow OS to fully release the socket
    time.sleep(0.2)

    return logs

def reset_client_stats():
    with IP232Server.clients_lock:
        for client in IP232Server.clients:
            client.rx_symbols = 0
            client.tx_symbols = 0
            client.sent_text = bytearray()
            client.recv_text = bytearray()

def get_clients():
    with IP232Server.clients_lock:
        return list(IP232Server.clients)

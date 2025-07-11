<h1 align="center">Vice & CC65 build and test automation</h1>

```
git clone https://github.com/xp5-org/CC65-vice-dev.git
cd CC65-vice-dev
docker build ./ -t vicedev
docker run -it --rm -p 3389:3389 -p 8080:8080 -e USERPASSWORD=a -v "$(pwd)":/testrunnerapp -e USERNAME=user vicedev:latest
```

This is built off the QEMU automation framework
It's also a Dockerfile of ubuntu:25.04 with XRDP, VICE, CC65, and OpenCBM built

The current demo is of multiple C64 RX & TX instances using the ACIA RS232 feature in the VICE emulator, with an IP232 relay server as the backend.

### this tool will:
- take an input src directory with C89 compliant C code, build the PRG using CC65, copy it to a D64
- start multiple VICE instances and track the X window ID using the D64
- take screenshots against the VICE instance name

<br>

### Rx/Tx demo:
- builds separate RX & TX src dirs
- starts one TX VICE instance with TX disk.D64
- starts one or many RX VICE instances with RX disk.D64
- connects ACIA-RS232 (Swiftlink) to IP232 Python relay server
- RX: sends 1 byte (single char) at set interval
- TX: checks buffer for byte at set interval

<br>




  ## Rx & Tx single pair demo
it uses python to connect to the vice remote monitor and send key codes to memory remotely
  <img width="862" height="1063" alt="image" src="https://github.com/user-attachments/assets/1ea5b93d-ba5a-465d-a90b-0cea21790702" />

<br>

example output from running the Rx & Tx demo. two vice instances are started and RS232 connects. One client sends a byte, and the other checks the ACIA interface for its buffer contents. occasionally a $1C is received which seems to be the keepalive equivalent
  <img width="1016" height="783" alt="image" src="https://github.com/user-attachments/assets/f33ed406-5aec-4f39-8daf-b59cbbe97d9b" />

<br>


  ## 1x Rx & 3 Tx - 4x C64 demo
  taking screenshots is slow, so there is different chars shown for the 3 RX windows due to how long it takes, 1 second per screenshot) 
  <img width="833" height="1243" alt="image" src="https://github.com/user-attachments/assets/b2af669b-6d9d-42ff-a65c-5bbf07ba1b8c" />

relay server also has statistics reset & collect before shutdown

once the clients are connected the stats can be cleared, and start tracking how many Rx/TX chars were seen from each client.
<img width="694" height="469" alt="image" src="https://github.com/user-attachments/assets/7da9e244-783c-4c17-8f7c-a04ceed22f76" />

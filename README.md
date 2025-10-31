<h1 align="center">Vice & CC65 build and test automation</h1>

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

## Setup and use
I built this with docker in mind. I have a linux host (can be a virtual machine) with SMB, NFS available so that the dirs/files inside of the cc65-vice-dev container can be accessed from another computer

docker isnt needed to use this, can clone the git repo, set up your venv and run pip against requirements.txt and start it locally. 

i have the dir ```/bigpool/data/code_projects/``` shared out, and navigated here , downloaded the GIT link, built the docker image, and ran the container from here
```
$ cd /bigpool/data/code_projects/
$ cd CC65-vice-dev
$ git clone https://github.com/xp5-org/CC65-vice-dev.git
$ docker build -t cc65vicedev ./
[+] Building 251.6s (18/18) FINISHED

$ docker image ls
REPOSITORY                        TAG       IMAGE ID       CREATED          SIZE
cc65vicedev                       latest    4fa1328959a2   46 seconds ago   1.89GB
```

once the image is built, run the container

-v can be omitted if you dont need to make the testrunnerapp visible outside of the container, but it will make code-edits and file copying more challenging without it

```
$ docker run -it -d \
  -p 3389:3389 \
  -p 8088:8080 \
  -e USERPASSWORD=a \
  -e USERNAME=user \
  -v /bigpool/data/code_projects/CC65-vice-dev:/testrunnerapp \
  cc65vicedev
```

it takes some time to set up & start - so if xrdp rejects right away check docker logs or try again in a minute


<img width="1614" height="707" alt="image" src="https://github.com/user-attachments/assets/d34e71f0-971f-49f8-b25c-532e0ef9f39e" />

| RDP connect | Manually starting the app |
|---------|---------|
| ![Image 1](https://github.com/user-attachments/assets/f5e9780a-89b8-4769-88bb-52c9dce4a048) | ![Image 2](https://github.com/user-attachments/assets/04ec44c2-d061-41ab-bc65-f347746019a6) |

<br>

| Connecting to the app with a web browser from any computer |
|------------------------------------------------------------|
| <img src="https://github.com/user-attachments/assets/50e28150-18d9-406a-9e9d-b0408d39cdc0" width="600"> |

<br>

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

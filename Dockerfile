FROM ubuntu:25.04
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        xfce4 \
        xfce4-clipman-plugin \
        xfce4-cpugraph-plugin \
        xfce4-netload-plugin \
        xserver-xorg-legacy \
        xdg-utils \
        dbus-x11 \
        xfce4-screenshooter \
        xfce4-taskmanager \
        xfce4-terminal \
        xfce4-xkb-plugin \
        xorgxrdp \
        xrdp \
        sudo \
        wget \
        bzip2 \
        python3 \
        python3-pip \
        python3-venv \
        build-essential \
        # xterm for runme.sh debug
        xterm \
        git \
        vim \
        python3-venv \
        # for vice & c1541 tool
        linux-headers-generic \
        libusb-1.0 pkg-config ncurses-dev \
        cc65 \
        vice && \
        # for vice make
        #build-essential flex bison \
        #libgtk-3-dev libreadline-dev libpng-dev \
        #libasound2-dev libsdl2-dev \
        #libxrandr-dev libxinerama-dev libxi-dev libglew-dev \
        #wget tar dos2unix libcurl4-openssl-dev file && \
    apt-get remove -y light-locker xscreensaver && \
    apt-get autoremove -y && \
    rm -rf /var/cache/apt /var/lib/apt/lists/*

# install Firefox
RUN wget -O /tmp/firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US" --no-check-certificate && \
    tar xvf /tmp/firefox.tar.bz2 -C /opt && \
    ln -s /opt/firefox/firefox /usr/local/bin/firefox && \
    rm /tmp/firefox.tar.bz2

# fix XRDP/X11 setup
RUN mkdir -p /var/run/dbus && \
    cp /etc/X11/xrdp/xorg.conf /etc/X11 || true && \
    sed -i "s/console/anybody/g" /etc/X11/Xwrapper.config && \
    sed -i "s|xrdp/xorg|xorg|g" /etc/xrdp/sesman.ini && \
    echo "xfce4-session" >> /etc/skel/.Xsession


    




WORKDIR /root

# get & copy VICE roms
RUN wget -O /tmp/vice-3.8.tar.gz "https://sourceforge.net/projects/vice-emu/files/releases/vice-3.8.tar.gz/download" --no-check-certificate && \
   tar -xvf /tmp/vice-3.8.tar.gz -C /tmp && \
    mkdir -p /usr/share/vice/C64 /usr/share/vice/C128 /usr/share/vice/PET /usr/share/vice/CBM-II /usr/share/vice/PLUS4 /usr/share/vice/C64DTV /usr/share/vice/VIC20 /usr/share/vice/DRIVES && \
   cp /tmp/vice-3.8/data/C64/*.bin /usr/share/vice/C64 && \
    cp /tmp/vice-3.8/data/C128/*.bin /usr/share/vice/C128 && \
    cp /tmp/vice-3.8/data/C128/kern* /usr/share/vice/C128 && \
    cp /tmp/vice-3.8/data/PET/*.bin /usr/share/vice/PET && \
    cp /tmp/vice-3.8/data/CBM-II/*.bin /usr/share/vice/CBM-II && \
    cp /tmp/vice-3.8/data/PLUS4/*.bin /usr/share/vice/PLUS4 && \
    cp /tmp/vice-3.8/data/C64DTV/*.bin /usr/share/vice/C64DTV && \
    cp /tmp/vice-3.8/data/VIC20/*.bin /usr/share/vice/VIC20 && \
    cp /tmp/vice-3.8/data/DRIVES/*.bin /usr/share/vice/DRIVES && \
    rm -rf /tmp/vice-3.8 /tmp/vice-3.8.tar.gz

# build and install xa assembler
#RUN wget -O /tmp/xa-2.4.1.tar.gz https://www.floodgap.com/retrotech/xa/dists/xa-2.4.1.tar.gz && \
#   tar -xzf /tmp/xa-2.4.1.tar.gz -C /tmp && \
#    cd /tmp/xa-2.4.1 && \
#    make && \
#    cp xa /usr/local/bin && \
#    cd / && rm -rf /tmp/xa-2.4.1 /tmp/xa-2.4.1.tar.gz


# build VICE (currently broken fix later)
#RUN wget -O /tmp/vice-3.8.tar.gz "https://sourceforge.net/projects/vice-emu/files/releases/vice-3.8.tar.gz/download" --no-check-certificate && \
#    tar -xzf /tmp/vice-3.8.tar.gz -C /tmp && \
#    cd /tmp/vice-3.8 && \
#    ./configure --prefix=/usr && \
#    make -j$(nproc) && \
#    make install && \
#    rm -rf /tmp/vice-3.8 /tmp/vice-3.8.tar.gz

WORKDIR /root

# build cc65
#RUN git clone https://github.com/cc65/cc65.git && \
#    cd cc65 && \
#    make && \
#    make install

# build OpenCBM
RUN git clone https://github.com/OpenCBM/OpenCBM.git && \
    cd OpenCBM && \
    pkg-config --modversion libusb-1.0 && \
    make -f LINUX/Makefile USB_LIBS="$(pkg-config --libs libusb-1.0)" USB_CFLAGS="$(pkg-config --cflags libusb-1.0)" opencbm && \
    make -f LINUX/Makefile install && \
    make -f LINUX/Makefile ldconfig

#WORKDIR /root/cc65
#RUN make && make avail

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

RUN mkdir /testrunnerapp
COPY ./testrunner /testrunnerapp


# create venv
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r /testrunnerapp/requirements.txt
ENV VENV_PATH=/opt/venv

EXPOSE 3389 8080
ENTRYPOINT ["/app/entrypoint.sh"]
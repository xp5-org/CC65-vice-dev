# syntax=docker/dockerfile:1
FROM ubuntu:25.04
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
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
        xvfb \
        sudo \
        wget \
        curl \
        bzip2 \
        python3 \
        python3-pip \
        python3-venv \
        build-essential \
        supervisor \
        # xterm for runme.sh debug
        xterm \
        git \
        vim \
        python3-venv \
        libzbar0 \
        # for vice & c1541 tool
        linux-headers-generic \
        libusb-1.0 pkg-config ncurses-dev \
        cc65 \
        libsdl2-dev \
        #vice \
        xdotool imagemagick \
        # for pipewire
        pipewire \
        pipewire-pulse wireplumber \
        pipewire-audio-client-libraries \
        dbus-user-session alsa-utils \
        pipewire-module-xrdp \
        pulseaudio-utils \
        autoconf \
        automake \
        libtool \
        pkg-config \
        libpipewire-0.3-dev \
        libspa-0.2-dev \
        cmake \
        # for vice make
        libgtk-3-dev \
        libglew-dev \
        libevdev-dev \
        libpulse-dev \
        libasound2-dev \
        libsdl2-dev \
        libcurl4-openssl-dev \
        libreadline-dev \
        libxaw7-dev \
        build-essential flex bison \
        libgtk-3-dev libreadline-dev libpng-dev \
        libasound2-dev libsdl2-dev \
        libxrandr-dev libxinerama-dev libxi-dev libglew-dev \
        wget tar dos2unix libcurl4-openssl-dev file
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

# build and install xa assembler
RUN wget -O /tmp/xa-2.4.1.tar.gz https://www.floodgap.com/retrotech/xa/dists/xa-2.4.1.tar.gz && \
   tar -xzf /tmp/xa-2.4.1.tar.gz -C /tmp && \
    cd /tmp/xa-2.4.1 && \
    make && \
    cp xa /usr/local/bin && \
    cd / && rm -rf /tmp/xa-2.4.1 /tmp/xa-2.4.1.tar.gz

# Build VICE
RUN export VICE_URL=$(python3 -c "import urllib.request, re; html = urllib.request.urlopen('https://vice-emu.sourceforge.io/index.html').read().decode('utf-8'); print(re.search(r'href=\"(https://sourceforge.net/projects/vice-emu/files/releases/vice-[\d\.]+\.tar\.gz/download)\"', html).group(1))") && \
    curl -L -o /tmp/vice.tar.gz "$VICE_URL" && \
    tar -xzf /tmp/vice.tar.gz -C /tmp && \
    cd /tmp/vice-* && \
    ./configure --prefix=/usr --enable-native-gtk3ui --with-sdlsound && \
    make -j$(($(nproc) / 2)) && \
    make install && \
    mkdir -p /usr/share/vice/C64 /usr/share/vice/C128 /usr/share/vice/PET /usr/share/vice/CBM-II /usr/share/vice/PLUS4 /usr/share/vice/C64DTV /usr/share/vice/VIC20 /usr/share/vice/DRIVES && \
    cp /tmp/vice-*/data/C64/*.bin /usr/share/vice/C64 && \
    cp /tmp/vice-*/data/C128/*.bin /usr/share/vice/C128 && \
    cp /tmp/vice-*/data/C128/kern* /usr/share/vice/C128 && \
    cp /tmp/vice-*/data/PET/*.bin /usr/share/vice/PET && \
    cp /tmp/vice-*/data/CBM-II/*.bin /usr/share/vice/CBM-II && \
    cp /tmp/vice-*/data/PLUS4/*.bin /usr/share/vice/PLUS4 && \
    cp /tmp/vice-*/data/C64DTV/*.bin /usr/share/vice/C64DTV && \
    cp /tmp/vice-*/data/VIC20/*.bin /usr/share/vice/VIC20 && \
    cp /tmp/vice-*/data/DRIVES/*.bin /usr/share/vice/DRIVES && \
    rm -rf /tmp/vice*




WORKDIR /root

# build cc65 , not needed can get it from apt-get
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


# create venv
COPY requirements.txt /app/
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r /app/requirements.txt && \
    chgrp -R users /opt/venv && \
    chmod -R g+rwX /opt/venv && \
    find /opt/venv -type d -exec chmod g+s {} \;
ENV VENV_PATH=/opt/venv


# set up supervisord to run flask app
COPY services.conf /etc/supervisor/conf.d/services.conf
RUN mkdir -p /var/log && touch /var/log/flaskapp.out.log /var/log/flaskapp.err.log




# build the pipewire module for xrdp audio
RUN mkdir -p /app/pipewire-module && \
    git clone https://github.com/neutrinolabs/pipewire-module-xrdp.git /app/pipewire-module && \
    cd /app/pipewire-module && \
    ./bootstrap && \
    ./configure --with-module-dir=/usr/lib/x86_64-linux-gnu/pipewire-0.3 && \
    make && \
    make install && \
    ldconfig


COPY startaudio.sh /app/
RUN chmod +x /app/startaudio.sh
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh


# need at least these 2 ports
EXPOSE 3389 8080
ENTRYPOINT ["/app/entrypoint.sh"]

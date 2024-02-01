FROM xp5org/ubuntu23-xrdp


#TZ fix for no console/headless
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    #Emulator and CC65 stuff
    build-essential \
    vim \
    git \
    vice 
RUN apt remove -y light-locker xscreensaver && \
    apt autoremove -y && \
    rm -rf /var/cache/apt /var/lib/apt/lists

WORKDIR /app
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN git clone https://github.com/cc65/cc65.git && \
    cd cc65 && \
    make && \
    make avail

# set up roms
RUN wget -O vice-3.8.tar.gz "https://sourceforge.net/projects/vice-emu/files/releases/vice-3.8.tar.gz/download" --no-check-certificate && \
tar -xvf vice-3.8.tar.gz && \
cp vice-3.8/data/C64/*.bin /usr/share/vice/C64 && \
cp vice-3.8/data/C128/*.bin /usr/share/vice/C128 && \
cp vice-3.8/data/C128/kern* /usr/share/vice/C128 && \
cp vice-3.8/data/PET/*.bin /usr/share/vice/PET && \
cp vice-3.8/data/CBM-II/*.bin /usr/share/vice/CBM-II && \
cp vice-3.8/data/PLUS4/*.bin /usr/share/vice/PLUS4 && \
cp vice-3.8/data/C64DTV/*.bin /usr/share/vice/C64DTV && \
cp vice-3.8/data/VIC20/*.bin /usr/share/vice/VIC20 && \
cp vice-3.8/data/DRIVES/*.bin /usr/share/vice/DRIVES

ENTRYPOINT ["/app/entrypoint.sh"]
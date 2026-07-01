#!/bin/bash

DESKTOP="$USERHOME/Desktop"

if [ -n "$USERPASSWORD" ]; then
  echo ''
  echo "USERPASSWORD: $USERPASSWORD" # print password to docker log console
  # echo "$USERPASSWORD" > passwordoutput.txt  #save
else
  # Generate a random 10-character password with mixed case letters and numbers
  USERPASSWORD=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 10 ; echo '')
  echo "Generated Password: $USERPASSWORD"  
  # echo "$USERPASSWORD" > passwordoutput.txt         #save
fi

if [ -n "$USERNAME" ]; then
  echo "USERNAME: $USERNAME" #debug
 # echo "$USERNAME" > usernameoutput.txt  #save
else
  USERNAME="user"
fi

# Set up users from command line input positions
addgroup "$USERNAME"
useradd -m -s /bin/bash -g "$USERNAME" "$USERNAME"
echo "$USERNAME:$USERPASSWORD" | chpasswd 
usermod -aG sudo "$USERNAME"
echo "debug1"

# SSH setup
SSH_KEY_DIR="${SSH_KEY_DIR:-/keys}"
SSH_KEY_NAME="${SSH_KEY_NAME:-agent_${USERNAME}_id_ed25519}"
mkdir -p /run/sshd

# save sshd's HOST keys
HOST_KEY_DIR="$SSH_KEY_DIR/ssh_host_keys"
mkdir -p "$HOST_KEY_DIR" 2>/dev/null
if ls "$HOST_KEY_DIR"/ssh_host_*_key >/dev/null 2>&1; then
  echo "Reusing existing sshd host keys from $HOST_KEY_DIR"
  cp "$HOST_KEY_DIR"/ssh_host_* /etc/ssh/
  chmod 600 /etc/ssh/ssh_host_*_key
  chmod 644 /etc/ssh/ssh_host_*_key.pub
else
  echo "No existing sshd host keys found in $HOST_KEY_DIR; generating"
  ssh-keygen -A
  cp /etc/ssh/ssh_host_* "$HOST_KEY_DIR/"
fi

mkdir -p /etc/ssh/sshd_config.d
cat <<EOF > /etc/ssh/sshd_config.d/99-password-auth.conf
PasswordAuthentication yes
KbdInteractiveAuthentication yes
PermitRootLogin no
EOF

USER_SSH="/home/$USERNAME/.ssh"
mkdir -p "$USER_SSH"

# save keypair in the bind-mounted host dir
mkdir -p "$SSH_KEY_DIR" 2>/dev/null
PERSIST_PRIV="$SSH_KEY_DIR/$SSH_KEY_NAME"
PERSIST_PUB="$PERSIST_PRIV.pub"

if [ -f "$PERSIST_PRIV" ] && [ -f "$PERSIST_PUB" ]; then
  echo "Reusing existing agent SSH keypair from $PERSIST_PRIV"
  cp "$PERSIST_PRIV" "$USER_SSH/agentkey"
  cp "$PERSIST_PUB" "$USER_SSH/agentkey.pub"
else
  echo "No existing agent keypair found in $SSH_KEY_DIR; generating one"
  ssh-keygen -t ed25519 -N "" -C "agent@${USERNAME}" -f "$USER_SSH/agentkey"
  cp "$USER_SSH/agentkey" "$PERSIST_PRIV"
  cp "$USER_SSH/agentkey.pub" "$PERSIST_PUB"
  chmod 644 "$PERSIST_PRIV" "$PERSIST_PUB"
fi

cat "$USER_SSH/agentkey.pub" > "$USER_SSH/authorized_keys"
chmod 700 "$USER_SSH"
chmod 600 "$USER_SSH/authorized_keys" "$USER_SSH/agentkey"
chown -R "$USERNAME:$USERNAME" "$USER_SSH"

/usr/sbin/sshd
echo "sshd started on port 22 (password auth + agent key both enabled for $USERNAME)"
# ---- end SSH ----

mkdir -p /home/$USERNAME/Desktop/
cat <<EOF > /home/$USERNAME/Desktop/runme.sh
#!/bin/bash
xfce4-terminal --hold --command="bash -c 'source /opt/venv/bin/activate && python3 /testrunnerapp/app.py'"
EOF

cat <<'EOF' > /home/$USERNAME/Desktop/sound_en.sh
#!/bin/bash
export XDG_RUNTIME_DIR=/run/user/1001
export PULSE_SERVER=unix:$XDG_RUNTIME_DIR/pulse/native
#/app/startaudio.sh >$HOME/pipewire_output.log 2>&1 &
( /app/startaudio.sh >$HOME/pipewire_output.log 2>&1 & ) && disown
xfce4-terminal --hold --command="tail -f $HOME/pipewire_output.log"
EOF
chmod +x /home/$USERNAME/Desktop/sound_en.sh


cat <<'EOF' > /home/$USERNAME/Desktop/soundlog.sh
#!/bin/bash
xfce4-terminal --hold --command="tail -f $HOME/pipewire_output.log"
EOF


echo "debug2"
chmod +x /home/$USERNAME/Desktop/runme.sh
chmod +x /home/$USERNAME/Desktop/soundlog.sh
chmod +x /home/$USERNAME/Desktop/sound_en.sh
chmod +x /home/$USERNAME/Desktop/startaudio.sh
echo "debug2.1"
#sudo chown -R $USERNAME:user /opt/venv
echo "debug2.2"
sudo chown -R $USERNAME:user /app
echo "debug2.3"
sudo chown -R $USERNAME:user /testrunnerapp
echo "debug2.4"
sudo chown -R $USERNAME:user /home/user
echo "debug3"

# clear stale x session state
echo "clearing stale session state from previous run..."
pkill -f Xorg        2>/dev/null || true
pkill -f xrdp-sesman 2>/dev/null || true
pkill -f xrdp        2>/dev/null || true
rm -f /tmp/.X11-unix/X10 /tmp/.X10-lock 2>/dev/null || true
rm -f /var/run/xrdp/*.pid /run/xrdp/*.pid 2>/dev/null || true
rm -f /var/run/xrdp/sockdir/* /run/xrdp/sockdir/* 2>/dev/null || true
rm -f /home/$USERNAME/.Xauthority 2>/dev/null || true

# start xorg as user
sudo -u "$USERNAME" Xorg :10 -noreset -nolisten tcp -ac &


# force software GL inside RDP session
cat <<'GLEOF' > /etc/profile.d/99-xrdp-software-gl.sh
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
GLEOF
chmod 0644 /etc/profile.d/99-xrdp-software-gl.sh

# for rdp pulseaudio
echo 'export XDG_RUNTIME_DIR=/run/user/1001' >> /home/user/.bashrc
echo 'export XDG_RUNTIME_DIR=/run/user/1001' >> /home/user/.profile
sed -i 's/rdpsnd=false/rdpsnd=true/' /etc/xrdp/xrdp.ini
USER_ID=$(id -u "$USERNAME")
mkdir -p /run/user/$USER_ID
chown "$USERNAME:$USERNAME" /run/user/$USER_ID
chmod 700 /run/user/$USER_ID

# wait for x to start
while [ ! -e /tmp/.X11-unix/X10 ]; do sleep 1; done
chown "$USERNAME":"$USERNAME" /tmp/.X11-unix/X10


# start xrdp service
echo -e "starting xrdp services...\n"
trap "pkill -f xrdp" SIGKILL SIGTERM SIGHUP SIGINT EXIT
rm -rf /var/run/xrdp*.pid
xrdp-sesman
exec xrdp -n

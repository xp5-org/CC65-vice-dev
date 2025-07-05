#!/bin/bash

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
  echo "$USERNAME" > usernameoutput.txt  #save
else
  USERNAME="user"
fi

# Set up users from command line input positions
addgroup "$USERNAME"
useradd -m -s /bin/bash -g "$USERNAME" "$USERNAME"
echo "$USERNAME:$USERPASSWORD" | chpasswd 
usermod -aG sudo "$USERNAME"


mkdir -p /home/$USERNAME/Desktop/
cat <<EOF > /home/$USERNAME/Desktop/runme.sh
#!/bin/bash
xfce4-terminal --hold --command="bash -c '. /opt/venv/bin/activate && python3 /testrunnerapp/app.py'"
EOF

chmod +x /home/$USERNAME/Desktop/runme.sh
sudo chown -R user:user /opt/venv
sudo chown -R user:user /app

# Start and stop scripts
echo -e "starting xrdp services...\n"
trap "pkill -f xrdp" SIGKILL SIGTERM SIGHUP SIGINT EXIT

# start xrdp desktop
rm -rf /var/run/xrdp*.pid
rm -rf /var/run/xrdp/xrdp*.pid
xrdp-sesman && exec xrdp -n
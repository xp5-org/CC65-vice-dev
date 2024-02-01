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

# Add firefox to default browser menu icon
target_dir="/home/$USERNAME/.config/xfce4/panel/launcher-19/"
check_directory() {
    while true; do
        if [ -d "$target_dir" ]; then
            echo "XFCE Menu Directory found, adding firefox path"
            sleep 3
            grep -rl '^Exec' /home/$USERNAME/.config/xfce4/panel/launcher-19/ | xargs sed -i 's/^Exec=.*/Exec=firefox/'
            break
        else
            echo "XFCE Menu Directory not found. Waiting to add firefox..."
            sleep 3
        fi
    done
}

# Run the Firefox-fix function in the background
check_directory &

# Start and stop scripts
echo -e "starting xrdp services...\n"
trap "pkill -f xrdp" SIGKILL SIGTERM SIGHUP SIGINT EXIT

# start xrdp desktop
rm -rf /var/run/xrdp*.pid
rm -rf /var/run/xrdp/xrdp*.pid
xrdp-sesman && exec xrdp -n
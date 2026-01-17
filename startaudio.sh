export XDG_RUNTIME_DIR=/run/user/1001
export PULSE_SERVER=unix:$XDG_RUNTIME_DIR/pulse/native

mkdir -p $XDG_RUNTIME_DIR
chown $USER:$USER $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR

pkill -9 -f "pipewire|wireplumber|pw-cli"
rm /run/user/1001/pulse/native
rm /run/user/1001/pipewire-0.lock

sleep 2

LOG_DIR="/home/user/pwxrdplogs"
mkdir -p "$LOG_DIR"

pipewire > "$LOG_DIR/pipewire.log" 2>&1 &
pipewire-pulse > "$LOG_DIR/pipewire-pulse.log" 2>&1 &
wireplumber > "$LOG_DIR/wireplumber.log" 2>&1 &

sleep 1

pw-cli -m load-module libpipewire-module-xrdp \
    sink.stream.props={node.name=xrdp-sink} \
    source.stream.props={node.name=xrdp-source} >/dev/null &

sleep 1
pactl set-default-sink xrdp-sink
pactl set-default-source xrdp-source

OUT=$(pactl list sinks short)

if echo "$OUT" | grep -q "xrdp-sink"; then
    echo "Success: XRDP Audio ready"
else
    echo "Failed: no xrdp-sink"
    echo "Current Sinks:"
    echo "$OUT"
    
    # Restarting/Logging because it failed
    pipewire > "$LOG_DIR/pipewire.log" 2>&1 &
    pipewire-pulse > "$LOG_DIR/pipewire-pulse.log" 2>&1 &
    wireplumber > "$LOG_DIR/wireplumber.log" 2>&1 &

    sleep 2

    echo "--- scanning logs for errors ---"
    # Failed to connect to system bus - ignorable
    grep -Ei "error|fail|failure|failed" "$LOG_DIR"/*.log
fi

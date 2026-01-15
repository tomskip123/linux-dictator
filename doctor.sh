#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }

# Handle commands
case "$1" in
    restart)
        echo "Restarting services..."
        systemctl --user restart ydotoold
        sleep 1
        systemctl --user restart dictation
        echo "Done."
        exit 0
        ;;
    stop)
        echo "Stopping services..."
        systemctl --user stop dictation
        systemctl --user stop ydotoold
        echo "Done."
        exit 0
        ;;
    start)
        echo "Starting services..."
        systemctl --user start ydotoold
        sleep 1
        systemctl --user start dictation
        echo "Done."
        exit 0
        ;;
    logs)
        echo "=== ydotoold ==="
        journalctl --user -u ydotoold -n 20 --no-pager
        echo
        echo "=== dictation ==="
        journalctl --user -u dictation -n 20 --no-pager
        exit 0
        ;;
    config)
        CONFIG_DIR="$HOME/.config/dictation"
        CONFIG_FILE="$CONFIG_DIR/config.json"
        mkdir -p "$CONFIG_DIR"
        cat > "$CONFIG_FILE" << 'EOF'
{
  "device": "cpu",
  "model": "small",
  "language": "auto",
  "hotkey": ["F10"],
  "mode": "toggle",
  "streaming": true,
  "streaming_interval": 3.0,
  "auto_punctuation": true
}
EOF
        echo "Config generated at: $CONFIG_FILE"
        cat "$CONFIG_FILE"
        exit 0
        ;;
    help|--help|-h)
        echo "Usage: ./doctor.sh [command]"
        echo
        echo "Commands:"
        echo "  (none)    Run diagnostics"
        echo "  restart   Restart all services"
        echo "  start     Start all services"
        echo "  stop      Stop all services"
        echo "  logs      Show recent logs"
        echo "  config    Generate default config file"
        exit 0
        ;;
esac

echo "=== Dictation Doctor ==="
echo

# Check dependencies
echo "Dependencies:"
command -v ydotool >/dev/null && pass "ydotool installed" || fail "ydotool not installed (sudo pacman -S ydotool)"
command -v dictation >/dev/null && pass "dictation installed" || fail "dictation not installed (run ./install.sh)"
command -v notify-send >/dev/null && pass "notify-send installed" || warn "notify-send not installed (optional, for notifications)"

echo
echo "Services:"
systemctl --user is-active --quiet ydotoold && pass "ydotoold running" || fail "ydotoold not running (systemctl --user start ydotoold)"
systemctl --user is-active --quiet dictation && pass "dictation running" || fail "dictation not running (systemctl --user start dictation)"

echo
echo "Permissions:"
if groups | grep -q '\binput\b'; then
    pass "User in 'input' group"
else
    fail "User not in 'input' group (sudo usermod -aG input \$USER, then reboot)"
fi

if [ -r /dev/input/event0 ]; then
    pass "Can read input devices"
else
    fail "Cannot read input devices (check 'input' group membership)"
fi

echo
echo "Socket:"
SOCKET="${YDOTOOL_SOCKET:-/run/user/$UID/.ydotool_socket}"
if [ -S "$SOCKET" ]; then
    pass "ydotool socket exists ($SOCKET)"
else
    fail "ydotool socket missing ($SOCKET)"
fi

echo
echo "Config:"
CONFIG_FILE="$HOME/.config/dictation/config.json"
if [ -f "$CONFIG_FILE" ]; then
    pass "Config file exists"
    echo "    $(cat "$CONFIG_FILE" | tr -d '\n' | head -c 80)..."
else
    warn "No config file (will use defaults)"
fi

echo
echo "CUDA:"
if command -v python3 >/dev/null; then
    CUDA=$(python3 -c "import torch; print('available' if torch.cuda.is_available() else 'not available')" 2>/dev/null || echo "torch not installed")
    if [ "$CUDA" = "available" ]; then
        pass "CUDA $CUDA"
        GPU=$(python3 -c "import torch; print(torch.cuda.get_device_name(0))" 2>/dev/null)
        echo "    GPU: $GPU"
    else
        warn "CUDA $CUDA (will use CPU)"
    fi
fi

echo
echo "Logs (last 10 lines):"
echo "--- ydotoold ---"
journalctl --user -u ydotoold -n 5 --no-pager 2>/dev/null || echo "No logs"
echo "--- dictation ---"
journalctl --user -u dictation -n 5 --no-pager 2>/dev/null || echo "No logs"

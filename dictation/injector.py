"""Text injection for Wayland."""

import shutil
import subprocess
import time


def ydotool_available() -> bool:
    return shutil.which("ydotool") is not None


def wlcopy_available() -> bool:
    return shutil.which("wl-copy") is not None


def delete_chars(count: int) -> bool:
    if count <= 0:
        return True

    if ydotool_available():
        try:
            # Key code 14 is backspace
            for _ in range(count):
                subprocess.run(
                    ["ydotool", "key", "14:1", "14:0"],
                    check=True,
                    capture_output=True,
                    timeout=2,
                )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
    return False


def inject_text(text: str) -> bool:
    if not text:
        return True

    # Try ydotool first (requires ydotoold daemon running)
    if ydotool_available():
        try:
            result = subprocess.run(
                ["ydotool", "type", "--", text],
                check=True,
                capture_output=True,
                timeout=5,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"ydotool error: {e.stderr.decode()}")
        except subprocess.TimeoutExpired:
            print("ydotool timed out")

    # Fallback: copy to clipboard and paste
    if wlcopy_available():
        try:
            subprocess.run(
                ["wl-copy", "--", text],
                check=True,
                capture_output=True,
            )
            print("Text copied to clipboard. Press Ctrl+V to paste.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"wl-copy error: {e.stderr.decode()}")
            return False

    print("Error: No text injection method available.")
    print("Install one of: ydotool (+ run ydotoold), wl-copy")
    return False

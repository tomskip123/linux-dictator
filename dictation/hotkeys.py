"""Global hotkey handling using evdev for Wayland compatibility."""

import threading
from pathlib import Path
from typing import Callable
from evdev import InputDevice, ecodes, list_devices, categorize

KEY_MAP = {
    "Super_L": ecodes.KEY_LEFTMETA,
    "Super_R": ecodes.KEY_RIGHTMETA,
    "Control_L": ecodes.KEY_LEFTCTRL,
    "Control_R": ecodes.KEY_RIGHTCTRL,
    "Alt_L": ecodes.KEY_LEFTALT,
    "Alt_R": ecodes.KEY_RIGHTALT,
    "Shift_L": ecodes.KEY_LEFTSHIFT,
    "Shift_R": ecodes.KEY_RIGHTSHIFT,
}

for i in range(1, 13):
    KEY_MAP[f"F{i}"] = getattr(ecodes, f"KEY_F{i}")

for c in "abcdefghijklmnopqrstuvwxyz":
    KEY_MAP[c] = getattr(ecodes, f"KEY_{c.upper()}")
for n in "0123456789":
    KEY_MAP[n] = getattr(ecodes, f"KEY_{n}")


def find_keyboards(debug: bool = False) -> list[InputDevice]:
    keyboards = []
    if debug:
        print("All input devices:")

    # Get all event devices directly
    from pathlib import Path
    event_paths = sorted(Path("/dev/input").glob("event*"), key=lambda p: int(p.name[5:]))

    for path in event_paths:
        try:
            device = InputDevice(str(path))
            caps = device.capabilities()
            has_keys = ecodes.EV_KEY in caps
            has_letters = False
            if has_keys:
                keys = caps[ecodes.EV_KEY]
                has_letters = ecodes.KEY_A in keys and ecodes.KEY_Z in keys
            if debug:
                print(f"  {device.path}: {device.name} [keys={has_keys}, letters={has_letters}]")
            if has_letters:
                keyboards.append(device)
        except PermissionError:
            if debug:
                print(f"  {path}: PERMISSION DENIED")
            continue
        except OSError:
            continue
    return keyboards


class HotkeyListener:
    def __init__(
        self,
        hotkey: list[str],
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ):
        self.hotkey_codes = set(KEY_MAP.get(k, 0) for k in hotkey)
        self.on_press = on_press
        self.on_release = on_release
        self._pressed_keys: set[int] = set()
        self._hotkey_active = False
        self._running = False
        self._threads: list[threading.Thread] = []

    def _handle_event(self, device: InputDevice) -> None:
        try:
            for event in device.read_loop():
                if not self._running:
                    break
                if event.type != ecodes.EV_KEY:
                    continue

                key_event = categorize(event)
                code = key_event.scancode

                if key_event.keystate == key_event.key_down:
                    self._pressed_keys.add(code)
                    if self._debug:
                        print(f"Key down: {code}, pressed: {self._pressed_keys}, need: {self.hotkey_codes}")
                    if not self._hotkey_active and self.hotkey_codes <= self._pressed_keys:
                        self._hotkey_active = True
                        self.on_press()
                elif key_event.keystate == key_event.key_up:
                    self._pressed_keys.discard(code)
                    if self._hotkey_active and code in self.hotkey_codes:
                        self._hotkey_active = False
                        self.on_release()
        except OSError:
            pass

    def start(self, debug: bool = False) -> bool:
        self._debug = debug
        print("Scanning input devices...")
        keyboards = find_keyboards(debug=debug)
        if not keyboards:
            print("No keyboards found. Ensure user is in 'input' group:")
            print("  sudo usermod -aG input $USER")
            print("Then log out and back in.")
            return False

        print(f"Found {len(keyboards)} keyboard(s): {[kb.name for kb in keyboards]}")
        print(f"Listening for hotkey codes: {self.hotkey_codes}")

        self._running = True
        for kb in keyboards:
            thread = threading.Thread(target=self._handle_event, args=(kb,), daemon=True)
            thread.start()
            self._threads.append(thread)
        return True

    def stop(self) -> None:
        self._running = False
        self._threads.clear()

    def update_hotkey(self, hotkey: list[str]) -> None:
        self.hotkey_codes = set(KEY_MAP.get(k, 0) for k in hotkey)

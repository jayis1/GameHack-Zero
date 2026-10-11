#!/usr/bin/env python3
"""Run Crispy Doom as hacker with a controller-to-keyboard input bridge."""
import argparse
from contextlib import ExitStack, closing
import select
import shutil
import subprocess
import time
from pathlib import Path

from evdev import InputDevice, UInput, ecodes as E

BUTTON_KEYS = {
    E.BTN_DPAD_UP: E.KEY_UP, E.BTN_DPAD_DOWN: E.KEY_DOWN,
    E.BTN_DPAD_LEFT: E.KEY_LEFT, E.BTN_DPAD_RIGHT: E.KEY_RIGHT,
    E.BTN_EAST: E.KEY_SPACE, E.BTN_SOUTH: E.KEY_LEFTCTRL,
    E.BTN_NORTH: E.KEY_TAB, E.BTN_TL: E.KEY_A, E.BTN_TR: E.KEY_D,
    E.BTN_TL2: E.KEY_ESC, E.BTN_TR2: E.KEY_ENTER,
    E.BTN_START: E.KEY_ESC, E.BTN_SELECT: E.KEY_ENTER,
    E.BTN_TRIGGER_HAPPY1: E.KEY_ESC, E.BTN_TRIGGER_HAPPY2: E.KEY_ENTER,
}


def axis_direction(value, minimum, maximum):
    center = (minimum + maximum) / 2
    deadzone = max(0.25, (maximum - minimum) * 0.25)
    return -1 if value < center - deadzone else 1 if value > center + deadzone else 0


def controller():
    for path in sorted(Path("/dev/input").glob("event*")):
        device = InputDevice(str(path))
        if any(word in device.name.lower() for word in ("odroidgo3", "go-super", "joypad", "gamepad")):
            return device
        device.close()
    raise RuntimeError("No handheld controller detected.")


def wad_path(phase):
    external = Path(f"/data/external/roms/doom/freedoom{phase}.wad")
    return external if external.is_file() else Path(f"/opt/freedoom/freedoom{phase}.wad")


def play(phase):
    engine = shutil.which("crispy-doom") or ("/usr/games/crispy-doom" if Path("/usr/games/crispy-doom").exists() else None)
    wad = wad_path(phase)
    if not engine or not wad.is_file():
        raise RuntimeError("Crispy Doom / Freedoom data not installed.")
    save = Path("/data/gamehack-zero/freedoom") / f"phase{phase}"
    save.mkdir(parents=True, exist_ok=True)
    config = save / "doom.cfg"
    if not config.exists():
        config.write_text('use_mouse 0\nuse_joystick 0\nkey_strafeleft 97\nkey_straferight 100\njoyb_speed 29\n')
    with ExitStack() as cleanup:
        # Debian 12's evdev InputDevice/UInput have close(), but no __enter__.
        device = cleanup.enter_context(closing(controller()))
        keyboard = cleanup.enter_context(closing(UInput({E.EV_KEY: sorted(set(BUTTON_KEYS.values()) | {E.KEY_1, E.KEY_2, E.KEY_3, E.KEY_4, E.KEY_5, E.KEY_6, E.KEY_7})}, name="GameHack Freedoom keyboard")))
        device.grab()
        cleanup.callback(device.ungrab)
        time.sleep(0.3)
        process = subprocess.Popen([engine, "-iwad", str(wad), "-savedir", str(save),
                                    "-config", str(config), "-fullscreen", "-width", "640", "-height", "480"])
        pressed, axes, sources = set(), {}, {}
        weapon = 1
        try:
            while process.poll() is None:
                if not select.select([device.fd], [], [], 0.1)[0]:
                    continue
                for event in device.read():
                    if event.type == E.EV_KEY:
                        if event.value == 2:
                            continue
                        if event.value:
                            pressed.add(event.code)
                        else:
                            pressed.discard(event.code)
                        if {E.BTN_START, E.BTN_SELECT} <= pressed or {E.BTN_TL2, E.BTN_TR2} <= pressed:
                            process.terminate()
                            break
                        if event.code == E.BTN_WEST and event.value == 1:
                            weapon = weapon % 7 + 1
                            key = getattr(E, f"KEY_{weapon}")
                            keyboard.write(E.EV_KEY, key, 1)
                            keyboard.syn()
                            keyboard.write(E.EV_KEY, key, 0)
                            keyboard.syn()
                        elif event.code in BUTTON_KEYS:
                            key = BUTTON_KEYS[event.code]
                            old = key in sources.values()
                            if event.value:
                                sources[("button", event.code)] = key
                            else:
                                sources.pop(("button", event.code), None)
                            new = key in sources.values()
                            if old != new:
                                keyboard.write(E.EV_KEY, key, int(new))
                                keyboard.syn()
                    elif event.type == E.EV_ABS and event.code in (E.ABS_X, E.ABS_Y, E.ABS_HAT0X, E.ABS_HAT0Y):
                        info = device.absinfo(event.code)
                        direction = axis_direction(event.value, info.min, info.max)
                        keys = (E.KEY_LEFT, E.KEY_RIGHT) if event.code in (E.ABS_X, E.ABS_HAT0X) else (E.KEY_UP, E.KEY_DOWN)
                        old_key = axes.get(event.code)
                        new_key = keys[0] if direction < 0 else keys[1] if direction > 0 else None
                        if old_key != new_key:
                            old_pressed = set(sources.values())
                            sources.pop(("axis", event.code), None)
                            if new_key is not None:
                                sources[("axis", event.code)] = new_key
                            axes[event.code] = new_key
                            new_pressed = set(sources.values())
                            for key in old_pressed - new_pressed:
                                keyboard.write(E.EV_KEY, key, 0)
                            for key in new_pressed - old_pressed:
                                keyboard.write(E.EV_KEY, key, 1)
                            keyboard.syn()
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        return process.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", type=int, choices=(1, 2))
    args = parser.parse_args()
    raise SystemExit(play(args.phase))

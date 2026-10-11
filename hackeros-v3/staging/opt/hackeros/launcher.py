#!/usr/bin/env python3

import glob
import json
import os
import queue
import re
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "alsa")

import pygame
from evdev import InputDevice, ecodes
from customization import Preferences, load_themes, search_files
from wifi_tools import parse_networks, split_fields
from prompt_job import PromptJob

VERSION = "4.2.0"
RESULTS = Path("/data/gamehack-zero")
BG = (3, 10, 13)
PANEL = (8, 25, 29)
PANEL_ACTIVE = (12, 54, 57)
CYAN = (49, 232, 220)
GREEN = (96, 255, 155)
TEXT = (225, 245, 242)
MUTED = (119, 156, 157)
RED = (255, 99, 110)

CATEGORIES = [
    ("QUICK", [
        ("Find & connect Wi-Fi", "wifi"),
        ("Favorite actions", "favorites"),
        ("Recent actions", "recent"),
        ("Appearance / theme", "theme"),
        ("About / compatibility", "about"),
    ]),
    ("STATUS", [
        ("System dashboard", "dashboard"),
        ("Network dashboard", "network"),
        ("Hardware inventory", "hardware"),
        ("Installed tools", "tools"),
    ]),
    ("CONNECT", [
        ("Find & connect Wi-Fi", "wifi"),
        ("Wi-Fi connection status", "wifi-status"),
        ("External Wi-Fi monitor", "wifi-monitor"),
        ("Raspberry Pi worker", "pi-worker"),
        ("SanDisk / optional field node", "nimbus-fieldkit"),
        ("Wi-Fi survey", "wifi-survey"),
        ("Bluetooth discovery", "bluetooth"),
        ("OTG link status", "otg-status"),
    ]),
    ("INFRARED", [
        ("IR hardware", "ir-status"),
        ("Learn remote button", "ir-learn"),
        ("Send saved signal", "ir-send"),
        ("Browse remote library", "ir-library"),
        ("Adapter / format guide", "ir-guide"),
    ]),
    ("AUDIT", [
        ("Discover local hosts", "discover"),
        ("TCP port audit", "ports"),
        ("DNS / TLS / HTTP", "diagnostics"),
        ("Bounded packet capture", "capture"),
    ]),
    ("FILES", [
        ("Browse workspace", "browse-workspace"),
        ("Browse expansion card", "browse-external"),
        ("Browse SD2 debug logs", "browse-debug"),
        ("Search filenames", "search-files"),
        ("Storage status", "storage"),
        ("Safely eject expansion", "eject"),
    ]),
    ("DEVELOP", [
        ("OpenCode / local coding TUI", "opencode-local"),
        ("Local coding terminal", "coding-terminal"),
        ("OpenCode / quick prompt", "opencode-prompt"),
        ("Zero-Day feature map", "zeroday-features"),
        ("SSH instructions", "ssh"),
        ("Development workspace", "workspace"),
        ("OpenCode status", "opencode"),
        ("Service warnings", "warnings"),
    ]),
    ("PLAY", [
        ("Freedoom Phase 1", "freedoom-1"),
        ("Freedoom Phase 2", "freedoom-2"),
        ("Freedoom controls", "freedoom-controls"),
        ("Browse SD2 ROMs", "browse-roms"),
    ]),
    ("SYSTEM", [
        ("Balanced power", "power-balanced"),
        ("Performance power", "power-performance"),
        ("Switch OTG to USB host", "usb-host"),
        ("Switch OTG to PC network", "usb-gadget"),
        ("Reboot", "reboot"),
        ("Power off", "poweroff"),
    ]),
]

BUTTONS = {
    ecodes.BTN_DPAD_UP: "up",
    ecodes.BTN_DPAD_DOWN: "down",
    ecodes.BTN_DPAD_LEFT: "left",
    ecodes.BTN_DPAD_RIGHT: "right",
    ecodes.BTN_EAST: "confirm",       # Physical A
    ecodes.BTN_SOUTH: "back",         # Physical B
    ecodes.BTN_NORTH: "status",       # Physical X
    ecodes.BTN_WEST: "details",       # Physical Y
    ecodes.BTN_TL: "left",
    ecodes.BTN_TR: "right",
    ecodes.BTN_TL2: "back",
    ecodes.BTN_TR2: "confirm",
    ecodes.BTN_TRIGGER_HAPPY1: "back",
    ecodes.BTN_TRIGGER_HAPPY2: "confirm",
    ecodes.BTN_TRIGGER_HAPPY3: "status",
}


def run(command, timeout=45):
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        output = (result.stdout + result.stderr).strip()
        return output or f"Command finished with status {result.returncode}."
    except subprocess.TimeoutExpired:
        return f"Timed out after {timeout} seconds."
    except Exception as exc:
        return f"Unable to run command: {exc}"


def first_interface():
    route = run(["ip", "-4", "route", "show", "default"], 5)
    match = re.search(r"\bdev\s+(\S+)", route)
    if match:
        return match.group(1)
    for path in Path("/sys/class/net").glob("*"):
        if path.name not in ("lo", "usb0"):
            return path.name
    return ""


def local_cidr():
    output = run(["ip", "-4", "route", "show", "scope", "link"], 5)
    match = re.search(r"(^|\n)(\d+\.\d+\.\d+\.\d+/\d+)", output)
    return match.group(2) if match else ""


class Gamepad(threading.Thread):
    def __init__(self, events):
        super().__init__(daemon=True)
        self.events = events

    def run(self):
        while True:
            device = self.find_device()
            if not device:
                time.sleep(2)
                continue
            try:
                for event in device.read_loop():
                    if event.type == ecodes.EV_KEY and event.value == 1:
                        action = BUTTONS.get(event.code)
                        if action:
                            self.events.put(action)
                    elif event.type == ecodes.EV_ABS:
                        if event.code in (ecodes.ABS_HAT0X, ecodes.ABS_X):
                            if event.value < -1000 or event.value == -1:
                                self.events.put("left")
                            elif event.value > 1000 or event.value == 1:
                                self.events.put("right")
                        elif event.code in (ecodes.ABS_HAT0Y, ecodes.ABS_Y):
                            if event.value < -1000 or event.value == -1:
                                self.events.put("up")
                            elif event.value > 1000 or event.value == 1:
                                self.events.put("down")
            except OSError:
                time.sleep(1)

    @staticmethod
    def find_device():
        for path in glob.glob("/dev/input/event*"):
            try:
                device = InputDevice(path)
                name = device.name.lower()
                if any(word in name for word in ("go-super", "odroidgo3", "gamepad", "joypad")):
                    return device
            except OSError:
                pass
        return None


class GameHackZero:
    def __init__(self):
        # The launcher is silent. pygame.init() also opens ALSA through the
        # mixer and prevents Crispy Doom from acquiring the handheld audio.
        pygame.display.init()
        pygame.font.init()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption(f"GameHack Zero {VERSION}")
        self.title_font = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", max(24, self.height // 15))
        self.font = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", max(16, self.height // 25))
        self.small = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", max(13, self.height // 32))
        self.events = queue.Queue()
        Gamepad(self.events).start()
        self.category = 0
        self.item = 0
        self.home = True
        self.message = "R2/A select  L2/B back  Y favorite  L1/R1 tabs"
        RESULTS.mkdir(parents=True, exist_ok=True)
        self.preferences = Preferences(RESULTS / "settings.json")
        self.themes = load_themes(RESULTS / "asset_packs")
        self.apply_theme(self.preferences.theme)
        self.status_line = "Checking system status..."
        threading.Thread(target=self.refresh_status, daemon=True).start()

    def refresh_status(self):
        while True:
            battery = "--"
            for path in Path("/sys/class/power_supply").glob("*/capacity"):
                try:
                    battery = path.read_text().strip() + "%"
                    break
                except OSError:
                    pass
            wifi = "Wi-Fi offline"
            output = run(["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "dev", "status"], 5)
            for line in output.splitlines():
                fields = split_fields(line)
                if len(fields) == 3 and fields[0] == "wifi" and fields[1] == "connected":
                    wifi = "Wi-Fi " + fields[2]
                    break
            self.status_line = f"BAT {battery}   {wifi}   {time.strftime('%H:%M')}"
            time.sleep(15)

    def fit_text(self, text, font, color, width):
        text = str(text)
        if font.size(text)[0] > width:
            while text and font.size(text + "...")[0] > width:
                text = text[:-1]
            text += "..."
        return font.render(text, True, color)

    def busy(self, title, message):
        self.page_header(title, "WORKING / PLEASE WAIT")
        self.screen.blit(self.fit_text(message, self.font, TEXT, self.width - 48), (24, 125))
        pygame.display.flip()

    def apply_theme(self, name):
        global BG, PANEL, PANEL_ACTIVE, CYAN, GREEN, TEXT, MUTED, RED
        colors = self.themes.get(name, self.themes["Momentum amber"])
        BG, PANEL, PANEL_ACTIVE = colors["bg"], colors["panel"], colors["active"]
        CYAN, GREEN = colors["accent"], colors["focus"]
        TEXT, MUTED, RED = colors["text"], colors["muted"], colors["error"]

    def quick_actions(self, actions, title):
        available = {action: name for _, items in CATEGORIES for name, action in items}
        entries = {available[action]: action for action in actions if action in available and action not in ("favorites", "recent")}
        chosen = self.select(title, list(entries))
        if chosen:
            self.execute(entries[chosen])

    def draw(self):
        self.page_header("GAMEHACK ZERO", self.status_line)
        if self.home:
            self.draw_home()
        else:
            self.draw_category()
        self.footer("D-pad navigate   R2/A open   X status" if self.home else "R2/A select  L2/B home  Y favorite  L1/R1 tabs")
        pygame.display.flip()

    def page_header(self, title, subtitle=""):
        self.screen.fill(BG)
        for x in range(16, self.width, 32):
            for y in range(90, self.height - 40, 32):
                pygame.draw.circle(self.screen, PANEL, (x, y), 1)
        pygame.draw.rect(self.screen, PANEL, (0, 0, self.width, 76))
        pygame.draw.rect(self.screen, CYAN, (20, 16, 4, 31), border_radius=2)
        self.screen.blit(self.fit_text(title, self.title_font, TEXT, self.width - 152), (34, 8))
        self.screen.blit(self.fit_text(subtitle, self.small, MUTED, self.width - 54), (24, 53))
        badge = pygame.Rect(self.width - 108, 17, 86, 25)
        pygame.draw.rect(self.screen, PANEL_ACTIVE, badge, border_radius=6)
        label = self.fit_text(VERSION, self.small, CYAN, 78)
        self.screen.blit(label, label.get_rect(center=badge.center))
        pygame.draw.line(self.screen, CYAN, (20, 75), (self.width - 20, 75), 1)

    def footer(self, text):
        pygame.draw.rect(self.screen, PANEL, (0, self.height - 36, self.width, 36))
        self.screen.blit(self.fit_text(text, self.small, MUTED, self.width - 36), (18, self.height - 26))

    def category_icon(self, name, rect, color):
        x, y = rect.center
        if name == "CONNECT":
            for radius in (10, 18, 26):
                pygame.draw.arc(self.screen, color, (x - radius, y - radius, radius * 2, radius * 2), 0.6, 2.54, 2)
            pygame.draw.circle(self.screen, color, (x, y + 4), 3)
        elif name == "PLAY":
            pygame.draw.rect(self.screen, color, (x - 25, y - 14, 50, 28), 2, border_radius=8)
            pygame.draw.line(self.screen, color, (x - 18, y), (x - 6, y), 2)
            pygame.draw.line(self.screen, color, (x - 12, y - 6), (x - 12, y + 6), 2)
            pygame.draw.circle(self.screen, color, (x + 11, y + 3), 3)
            pygame.draw.circle(self.screen, color, (x + 18, y - 4), 3)
        elif name == "FILES":
            pygame.draw.lines(self.screen, color, True, [(x-24,y-14),(x-4,y-14),(x+2,y-8),(x+24,y-8),(x+24,y+16),(x-24,y+16)], 2)
        elif name == "SYSTEM":
            pygame.draw.arc(self.screen, color, (x-18,y-18,36,36), 2.0, 7.4, 3)
            pygame.draw.line(self.screen, color, (x,y-24),(x,y-2),3)
        else:
            symbols = {"QUICK": ">>", "STATUS": "i", "INFRARED": "IR", "AUDIT": ">_", "DEVELOP": "{}"}
            pygame.draw.rect(self.screen, color, (x-25,y-19,50,38), 2, border_radius=7)
            label = self.font.render(symbols.get(name, ">"), True, color)
            self.screen.blit(label, label.get_rect(center=(x,y)))

    def draw_home(self):
        cols = 3
        rows = (len(CATEGORIES) + cols - 1) // cols
        gap = 10
        tile_w = (self.width - 40 - gap * (cols - 1)) // cols
        tile_h = (self.height - 126 - gap * (rows - 1)) // rows
        for index, (name, items) in enumerate(CATEGORIES):
            rect = pygame.Rect(20 + (index % cols) * (tile_w + gap), 88 + (index // cols) * (tile_h + gap), tile_w, tile_h)
            active = index == self.category
            pygame.draw.rect(self.screen, PANEL_ACTIVE if active else PANEL, rect, border_radius=12)
            pygame.draw.rect(self.screen, CYAN if active else PANEL_ACTIVE, rect, 2 if active else 1, border_radius=12)
            if active:
                pygame.draw.rect(self.screen, GREEN, (rect.x + 12, rect.y + 10, 24, 3), border_radius=1)
            self.category_icon(name, pygame.Rect(rect.x, rect.y + 10, rect.width, 42), CYAN if active else MUTED)
            label = self.small.render(name, True, TEXT if active else MUTED)
            self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.bottom - 35)))
            count = self.small.render(f"{len(items)} actions", True, MUTED)
            self.screen.blit(count, count.get_rect(center=(rect.centerx, rect.bottom - 15)))

    def draw_category(self):
        sidebar = max(112, self.width // 5)
        row_h = min(36, (self.height - 132) // len(CATEGORIES))
        for index, (name, _) in enumerate(CATEGORIES):
            rect = pygame.Rect(16, 90 + index * row_h, sidebar - 20, row_h - 4)
            active = index == self.category
            pygame.draw.rect(self.screen, PANEL_ACTIVE if active else PANEL, rect, border_radius=6)
            if active:
                pygame.draw.rect(self.screen, CYAN, (rect.x, rect.y + 5, 3, rect.height - 10))
            self.screen.blit(self.fit_text(name, self.small, CYAN if active else MUTED, rect.width - 16), (rect.x + 10, rect.y + 7))
        left = sidebar + 10
        items = CATEGORIES[self.category][1]
        heading = f"{CATEGORIES[self.category][0]} / {self.item + 1:02}/{len(items):02}"
        self.screen.blit(self.small.render(heading, True, CYAN), (left, 90))
        visible = max(1, (self.height - 216) // 48)
        start = max(0, min(self.item - visible // 2, len(items) - visible))
        y = 117
        for index, (name, action) in enumerate(items[start:start + visible], start):
            active = index == self.item
            rect = pygame.Rect(left, y, self.width - left - 24, 42)
            pygame.draw.rect(self.screen, PANEL_ACTIVE if active else PANEL, rect, border_radius=8)
            if active:
                pygame.draw.rect(self.screen, CYAN, rect, 2, border_radius=8)
            number = self.small.render(f"{index + 1:02}", True, CYAN if active else MUTED)
            self.screen.blit(number, (left + 12, y + 13))
            favorite = "* " if action in self.preferences.favorites else ""
            self.screen.blit(self.fit_text(favorite + name, self.font, TEXT if active else MUTED, rect.width - 58), (left + 48, y + 10))
            y += 48
        if len(items) > visible:
            rail = pygame.Rect(self.width - 15, 117, 3, visible * 48 - 6)
            pygame.draw.rect(self.screen, PANEL_ACTIVE, rail)
            knob_h = max(12, rail.height * visible // len(items))
            pygame.draw.rect(self.screen, CYAN, (rail.x, rail.y + (rail.height - knob_h) * start // max(1, len(items) - visible), 3, knob_h))
        action = items[self.item][1]
        descriptions = {
            "wifi": "Scan nearby networks and connect on-device.", "favorites": "Your pinned tools, all in one place.",
            "recent": "Jump back into recently used actions.", "theme": "Choose a color theme or custom palette.",
            "opencode-prompt": "Write a coding prompt using the controller.", "freedoom-1": "Single-player campaign / four episodes.",
            "opencode-local": "Local interactive OpenCode with a flat coding keyboard; no SSH.",
            "coding-terminal": "Local workspace shell with controller keyboard and coding symbols.",
            "zeroday-features": "Upstream feature inventory with honest port/hardware status.",
            "freedoom-2": "Single-player campaign / 32 levels.", "ir-learn": "Capture a button from your own remote.",
            "ir-send": "Replay a saved infrared signal.", "poweroff": "Safely shut down before removing the card.",
        }
        rect = pygame.Rect(left, self.height - 100, self.width - left - 24, 54)
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=8)
        self.screen.blit(self.small.render("SELECTED TOOL", True, CYAN), (left + 12, rect.y + 8))
        description = descriptions.get(action, "R2 opens this tool. L2 returns to the home screen.")
        self.screen.blit(self.fit_text(description, self.small, MUTED, rect.width - 24), (left + 12, rect.y + 30))

    def get_action(self):
        try:
            return self.events.get_nowait()
        except queue.Empty:
            pass
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                return {
                    pygame.K_UP: "up", pygame.K_DOWN: "down", pygame.K_LEFT: "left",
                    pygame.K_RIGHT: "right", pygame.K_RETURN: "confirm", pygame.K_ESCAPE: "back",
                    pygame.K_x: "status", pygame.K_y: "details",
                }.get(event.key)
        return None

    def wait_action(self):
        while True:
            action = self.get_action()
            if action:
                return action
            time.sleep(0.02)

    def text_view(self, title, text):
        lines = []
        limit = max(32, self.width // max(8, self.small.get_height() // 2))
        for raw in str(text).splitlines() or [""]:
            while len(raw) > limit:
                lines.append(raw[:limit])
                raw = raw[limit:]
            lines.append(raw)
        offset = 0
        visible = max(1, (self.height - 136) // self.small.get_height())
        while True:
            self.page_header(title, "OUTPUT / D-PAD TO SCROLL")
            for index, line in enumerate(lines[offset:offset + visible]):
                self.screen.blit(self.small.render(line, True, TEXT), (20, 87 + index * self.small.get_height()))
            footer = f"{offset + 1}-{min(offset + visible, len(lines))}/{len(lines)}   D-pad scroll   L2/B close"
            self.footer(footer)
            pygame.display.flip()
            action = self.wait_action()
            if action == "back":
                return
            if action in ("down", "pagedown"):
                offset = min(max(0, len(lines) - visible), offset + (visible if action == "pagedown" else 1))
            if action in ("up", "pageup"):
                offset = max(0, offset - (visible if action == "pageup" else 1))

    def confirm(self, title, message):
        choice = 0
        while True:
            self.page_header(title, "CONFIRM ACTION / CANCEL IS THE DEFAULT")
            y = 110
            for line in message.splitlines():
                self.screen.blit(self.font.render(line, True, TEXT), (30, y))
                y += self.font.get_height() + 6
            labels = ["CANCEL", "CONFIRM"]
            for index, label in enumerate(labels):
                rect = pygame.Rect(self.width // 4 * (1 + index * 2) - 90, self.height - 100, 180, 55)
                pygame.draw.rect(self.screen, PANEL_ACTIVE if index == choice else PANEL, rect, border_radius=8)
                pygame.draw.rect(self.screen, RED if index == 1 else CYAN, rect, 2, border_radius=8)
                text = self.font.render(label, True, TEXT)
                self.screen.blit(text, text.get_rect(center=rect.center))
            self.footer("Left/right choose   R2/A confirm   L2/B cancel")
            pygame.display.flip()
            action = self.wait_action()
            if action in ("left", "right"):
                choice = 1 - choice
            elif action == "confirm":
                return choice == 1
            elif action == "back":
                return False

    def keyboard(self, title, secret=False):
        layouts = [
            ["1234567890", "qwertyuiop", "asdfghjkl-", "zxcvbnm._@"],
            ["1234567890", "QWERTYUIOP", "ASDFGHJKL-", "ZXCVBNM._@"],
            ["!@#$%^&*()", "[]{}<>/\\|", "_+-=:;\"'`~", ",.?0123456"],
        ]
        layout = 0
        row = col = 0
        value = ""
        while True:
            rows = layouts[layout] + [""]
            self.page_header(title, "CONTROLLER KEYBOARD / " + ["abc", "ABC", "symbols"][layout])
            shown = "*" * len(value) if secret else value
            pygame.draw.rect(self.screen, PANEL, (20, 86, self.width - 40, 48), border_radius=6)
            self.screen.blit(self.fit_text(shown[-48:], self.font, TEXT, self.width - 60), (30, 98))
            y = 145
            for r, chars in enumerate(rows):
                cells = ["SHIFT", "SPACE", "DEL", "OK"] if r == 4 else list(chars)
                cell_w = (self.width - 40) // len(cells)
                for c, char in enumerate(cells):
                    rect = pygame.Rect(20 + c * cell_w, y, cell_w - 4, 48)
                    active = r == row and c == col
                    pygame.draw.rect(self.screen, PANEL_ACTIVE if active else PANEL, rect, border_radius=5)
                    if active:
                        pygame.draw.rect(self.screen, GREEN, rect, 2, border_radius=5)
                    label = self.small.render(char, True, TEXT if active else MUTED)
                    self.screen.blit(label, label.get_rect(center=rect.center))
                y += max(48, (self.height - 175) // 5)
            self.footer("R2/A type   Y case/symbols   L2/B cancel   OK submits")
            pygame.display.flip()
            action = self.wait_action()
            cells = ["SHIFT", "SPACE", "DEL", "OK"] if row == 4 else list(rows[row])
            if action == "left":
                col = (col - 1) % len(cells)
            elif action == "right":
                col = (col + 1) % len(cells)
            elif action == "up":
                row = (row - 1) % len(rows)
                col = min(col, len(["SHIFT", "SPACE", "DEL", "OK"] if row == 4 else rows[row]) - 1)
            elif action == "down":
                row = (row + 1) % len(rows)
                col = min(col, len(["SHIFT", "SPACE", "DEL", "OK"] if row == 4 else rows[row]) - 1)
            elif action == "details":
                layout = (layout + 1) % len(layouts)
                col = min(col, 3 if row == 4 else len(layouts[layout][row]) - 1)
            elif action == "back":
                return None
            elif action == "confirm":
                key = cells[col]
                if key == "SHIFT":
                    layout = (layout + 1) % len(layouts)
                elif key == "SPACE":
                    value += " "
                elif key == "DEL":
                    value = value[:-1]
                elif key == "OK":
                    return value
                else:
                    value += key

    def select(self, title, values):
        if not values:
            self.text_view(title, "No entries found.")
            return None
        index = 0
        while True:
            self.page_header(title, f"CHOOSE AN ENTRY / {index + 1} OF {len(values)}")
            visible = max(1, (self.height - 130) // 45)
            start = max(0, min(index - visible // 2, len(values) - visible))
            for row, value in enumerate(values[start:start + visible]):
                actual = start + row
                rect = pygame.Rect(22, 88 + row * 45, self.width - 44, 39)
                pygame.draw.rect(self.screen, PANEL_ACTIVE if actual == index else PANEL, rect, border_radius=6)
                if actual == index:
                    pygame.draw.rect(self.screen, CYAN, rect, 2, border_radius=6)
                self.screen.blit(self.fit_text(value, self.small, TEXT if actual == index else MUTED, self.width - 70), (35, rect.y + 10))
            self.footer("D-pad choose   R2/A select   L2/B back")
            pygame.display.flip()
            action = self.wait_action()
            if action == "up":
                index = (index - 1) % len(values)
            elif action == "down":
                index = (index + 1) % len(values)
            elif action == "confirm":
                return values[index]
            elif action == "back":
                return None

    def dashboard(self):
        battery = "unknown"
        for capacity in Path("/sys/class/power_supply").glob("*/capacity"):
            try:
                battery = capacity.read_text().strip() + "%"
                break
            except OSError:
                pass
        temp = "unknown"
        for sensor in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
            try:
                temp = f"{int(sensor.read_text()) / 1000:.1f} C"
                break
            except (OSError, ValueError):
                pass
        text = "\n".join([
            f"GameHack Zero V{VERSION}", "Zero-Day OS for R36XX", f"Kernel: {os.uname().release}", f"Uptime: {run(['uptime', '-p'], 5)}",
            f"Battery: {battery}", f"Temperature: {temp}", "", run(["free", "-h"], 5), "", run(["df", "-h", "/", "/data"], 5)
        ])
        self.text_view("SYSTEM DASHBOARD", text)

    def wifi_setup(self):
        self.busy("WI-FI", "Enabling radio and checking hardware...")
        enabled = run(["sudo", "-n", "/usr/local/sbin/hackeros-action", "wifi-enable"], 15)
        devices = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "dev", "status"], 10)
        if not any(len(fields) == 3 and fields[1] == "wifi"
                   for fields in (split_fields(line) for line in devices.splitlines())):
            diagnostics = run(["sudo", "-n", "/usr/local/sbin/hackeros-action", "wifi-diagnostics"], 45)
            self.text_view("WI-FI HARDWARE", "No Wi-Fi interface detected by Linux.\nThis does not automatically mean a missing driver.\n\n" + diagnostics + "\n\n" + devices + "\n\n" + enabled)
            return
        while True:
            self.busy("FIND WI-FI", "Scanning nearby networks... please wait")
            output = run(["nmcli", "-t", "--escape", "yes", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "yes"], 30)
            networks = parse_networks(output)
            labels = [f"{'*' if item['active'] else ' '} {item['signal']:3}%  {item['ssid']}  [{item['security'] or 'OPEN'}]" for item in networks]
            options = labels + ["Rescan networks", "Join hidden network", "Connection / hardware status"]
            if not networks:
                self.text_view("WI-FI SCAN", "No visible networks found. Try rescan or check hardware status.\n\n" + output)
            chosen = self.select("NEARBY WI-FI", options)
            if chosen is None:
                return
            if chosen == "Rescan networks":
                continue
            if chosen == "Connection / hardware status":
                self.wifi_status()
                continue
            hidden = chosen == "Join hidden network"
            if hidden:
                ssid = self.keyboard("Hidden network SSID")
                if not ssid:
                    continue
                security = "unknown"
            else:
                selected = networks[labels.index(chosen)]
                if selected["active"]:
                    self.wifi_status()
                    continue
                ssid, security = selected["ssid"], selected["security"]
            if "802.1X" in security or "EAP" in security:
                self.text_view("ENTERPRISE WI-FI", "This network needs enterprise credentials. Configure its profile over SSH; the handheld password dialog supports personal and open networks.")
                continue
            password = ""
            if security and security != "--":
                password = self.keyboard("Wi-Fi password", secret=True)
                if password is None:
                    continue
            self.busy("CONNECTING", "Joining " + ssid)
            command = ["nmcli", "--wait", "30", "dev", "wifi", "connect", ssid]
            if password:
                command += ["password", password]
            if hidden:
                command += ["hidden", "yes"]
            self.text_view("WI-FI RESULT", run(command, 40))

    def wifi_status(self):
        self.busy("WI-FI STATUS", "Checking connections...")
        self.text_view("WI-FI STATUS", run(["nmcli", "dev", "status"], 10) + "\n\n" + run(["nmcli", "-f", "GENERAL,IP4", "dev", "show"], 10) + "\n\n" + run(["rfkill", "list"], 5))

    def pi_worker(self):
        actions = {"USB link diagnostics": "link", "Worker status": "status", "Run task on Pi": "task", "List shared files": "files", "Shut down Pi": "shutdown", "Restart Pi": "reboot"}
        while True:
            chosen = self.select("PI WORKER / GAMEHACK CONTROLS", list(actions) + ["Connection help"])
            if chosen is None:
                return
            if chosen == "Connection help":
                self.text_view("PI WORKER CONNECTION", "GameHack = USB host/controller.\nPi = USB Ethernet device/worker.\nDo not select PC gadget mode.\n\nPi: 192.168.77.1\nGameHack link: 192.168.77.2\nWi-Fi stays the internet route.\n\nPi must use its USB/data port.\nIf Wi-Fi disappears with USB error -71, check shared USB wiring, cable and power.\nA converter is not a hub.\n\nTasks run as companion, not root.\nShared files: /home/companion/shared\nTask output/connection limit: 35 seconds.")
                continue
            action = actions[chosen]
            command = ["/usr/bin/python3", "/opt/hackeros/pi_worker.py", action]
            if action == "task":
                task = self.keyboard("Pi worker task command")
                if not task:
                    continue
                command.append(task)
            elif action in ("shutdown", "reboot") and not self.confirm("PI WORKER", chosen + "?"):
                continue
            self.busy("PI WORKER", "Sending request to the paired Pi...")
            self.text_view("PI WORKER RESULT", run(command, 40))

    def wifi_monitor(self):
        self.busy("USB WI-FI MONITOR", "Checking adapter and driver capabilities...")
        output = run(["sudo", "-n", "/usr/local/sbin/hackeros-action", "monitor-list"], 15)
        try:
            devices = json.loads(output)
            if not isinstance(devices, list):
                raise ValueError("Unexpected adapter report")
        except ValueError:
            self.text_view("MONITOR STATUS", output)
            return
        candidates = [device for device in devices if device.get("supported") and device.get("monitor")]
        if not candidates:
            self.text_view("USB WI-FI MONITOR", "No supported external monitor adapter detected.\n\nRequired: RTL8821CU 0bda:c820 via a data/OTG adapter. USB host mode must be active.\nThe driver must load and advertise monitor support.\n\nDetected wireless devices:\n" + json.dumps(devices, indent=2) + "\n\n" + run(["lsusb"], 5))
            return
        labels = [f"{device['interface']} / {device['usb']} / {device['driver']}" for device in candidates]
        chosen = self.select("SELECT USB ADAPTER", labels)
        if chosen is None:
            return
        interface = candidates[labels.index(chosen)]["interface"]
        while True:
            choice = self.select("EXTERNAL DONGLE", ["Scan permitted access points", "Disconnect dongle from Wi-Fi", "Show adapter details"])
            if choice is None:
                return
            if choice == "Scan permitted access points":
                break
            if choice == "Show adapter details":
                self.text_view("ADAPTER DETAILS", json.dumps(candidates[labels.index(chosen)], indent=2))
            elif self.confirm("DISCONNECT DONGLE?", "Disconnect only the external adapter?\nBuilt-in Wi-Fi stays connected."):
                self.text_view("DONGLE CONNECTION", run(["sudo", "-n", "/usr/local/sbin/hackeros-action", "monitor-disconnect", interface], 15))
        self.busy("SELECT PERMITTED NETWORK", "Scanning with " + interface + "...")
        output = run(["nmcli", "-t", "--escape", "yes", "-f", "BSSID,SSID,FREQ,SIGNAL,SECURITY", "dev", "wifi", "list", "ifname", interface, "--rescan", "yes"], 30)
        networks = []
        for line in output.splitlines():
            fields = split_fields(line)
            frequency = re.fullmatch(r"(\d+)(?:\s*MHz)?", fields[2]) if len(fields) == 5 else None
            if frequency:
                fields[2] = frequency[1]
                networks.append(fields)
        if not networks:
            self.text_view("MONITOR SCAN", output or "No access points found.")
            return
        labels = [f"{ssid or '(hidden)'} / {bssid} / {signal}% / {freq}MHz" for bssid, ssid, freq, signal, security in networks]
        chosen = self.select("SELECT PERMITTED AP", labels)
        if chosen is None:
            return
        bssid, ssid, frequency, signal, security = networks[labels.index(chosen)]
        duration = self.select("PASSIVE CAPTURE DURATION", ["15 seconds", "30 seconds", "60 seconds"])
        if duration is None:
            return
        seconds = int(duration.split()[0])
        if not self.confirm("AUTHORIZED CAPTURE?", "Only networks you own or may monitor.\nPassive, BSSID-filtered packet capture.\nNo injection or deauthentication.\nExternal adapter must be disconnected."):
            return
        self.busy("PASSIVE CAPTURE", f"{interface}: up to {seconds}s; please wait")
        result = run(["sudo", "-n", "/usr/local/sbin/hackeros-action", "monitor-capture", interface, bssid, frequency, str(seconds)], seconds + 35)
        self.text_view("MONITOR RESULT", result)

    def local_coding(self, opencode=True):
        executable = shutil.which("opencode" if opencode else "bash")
        if not executable:
            self.text_view("LOCAL CODING", "Required executable is not installed.")
            return
        try:
            from local_terminal import run_terminal
            import pyte
        except ImportError:
            self.text_view("LOCAL CODING", "Terminal dependency missing: install python3-pyte with the local coding update.")
            return
        directory = RESULTS / "projects"
        directory.mkdir(parents=True, exist_ok=True)
        if not self.confirm("LOCAL CODING", "Runs directly on GameHack as hacker.\nFiles/commands stay on this Linux device.\nAI prompts may go to your selected provider.\nR2 types/selects; L2 leaves.\nY hides keyboard; X opens shortcuts."):
            return
        try:
            run_terminal(self, [executable] if opencode else [executable, "--noprofile", "--norc"], directory, "OPENCODE" if opencode else "GAMEHACK TERMINAL")
        except (OSError, ValueError) as exc:
            self.text_view("LOCAL TERMINAL ERROR", str(exc))

    def zeroday_features(self):
        try:
            catalog = json.loads(Path('/opt/hackeros/zeroday-features.json').read_text())
        except (OSError, ValueError) as exc:
            self.text_view("FEATURE MAP", str(exc))
            return
        categories = sorted({item['category'] for item in catalog['scripts']})
        chosen = self.select("ZERO-DAY PORT STATUS", categories)
        if chosen:
            entries = [f"{item['name']}: {item['status']}\n{item['note']}" for item in catalog['scripts'] if item['category'] == chosen]
            self.text_view("ZERO-DAY / " + chosen.upper(), '\n\n'.join(entries))

    def opencode_prompt(self):
        executable = shutil.which("opencode")
        if not executable:
            self.text_view("OPENCODE", "OpenCode binary is not installed yet. Deploy the handheld update first.")
            return
        prompt = self.keyboard("OpenCode prompt")
        if not prompt:
            return
        if not self.confirm("RUN OPENCODE?", "Uses your configured AI provider.\nMay edit files or run commands.\nWorkspace: gamehack-zero/projects\nB during execution cancels the job."):
            return
        directory = RESULTS / "projects"
        directory.mkdir(parents=True, exist_ok=True)
        try:
            job = PromptJob([executable, "run", prompt], directory)
        except OSError as exc:
            self.text_view("OPENCODE ERROR", str(exc))
            return
        canceled = False
        try:
            while not job.done.is_set():
                elapsed = int(time.monotonic() - job.started)
                self.busy("OPENCODE", f"Working... {elapsed}s   B: cancel")
                preview = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", job.output)
                lines = preview.splitlines()[-8:]
                for index, line in enumerate(lines):
                    self.screen.blit(self.fit_text(line, self.small, TEXT, self.width - 48), (24, 180 + index * (self.small.get_height() + 4)))
                pygame.display.flip()
                if self.get_action() == "back" or elapsed >= 180:
                    canceled = True
                    break
                time.sleep(0.1)
        finally:
            if not job.done.is_set():
                job.cancel()
        output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", job.output)
        self.text_view("OPENCODE RESULT", ("Canceled / timed out.\n" if canceled else f"Exit status: {job.process.returncode}\n") + (output or "No output. Provider setup may be required.") + "\n\nProvider setup: open the local OpenCode TUI and use /connect. No SSH or PC credentials required. OAuth providers may require opening a sign-in URL in a browser.")

    def freedoom(self, phase):
        if not Path(f"/opt/freedoom/freedoom{phase}.wad").is_file() or not Path("/usr/games/crispy-doom").is_file():
            self.text_view("FREEDOOM", "Game data or Crispy Doom is not installed yet.")
            return
        log = RESULTS / "freedoom-last-run.log"
        status = None
        try:
            # Release DRM before the engine opens the same display.
            pygame.mixer.quit()
            pygame.display.quit()
            with log.open("w") as output:
                status = subprocess.call(["/usr/bin/python3", "/opt/hackeros/freedoom_runner.py", str(phase)], stdout=output, stderr=subprocess.STDOUT)
        finally:
            pygame.display.init()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
            while not self.events.empty():
                try:
                    self.events.get_nowait()
                except queue.Empty:
                    break
        if status not in (0, -15):
            self.text_view("FREEDOOM LOG", log.read_text(errors="replace")[-12000:])

    def ir_remote(self, path):
        from ir_library import buttons, waveform
        try:
            signals = buttons(path)
            if not signals:
                if self.confirm('IR TRANSMIT', f'Transmit {path.name}?\nFixed carrier ~36.6 kHz.'):
                    self.text_view('IR TRANSMIT', run(['sudo', '/usr/local/sbin/hackeros-action', 'ir-send', str(path)], 20))
                return
            labels = []
            for index, signal in enumerate(signals):
                try:
                    carrier, _ = waveform(signal)
                    state = signal.get('protocol', 'raw')
                    if not 35000 <= carrier <= 40000:
                        state += f'; {carrier}Hz carrier mismatch'
                except (ValueError, KeyError) as exc:
                    state = 'UNSUPPORTED: ' + str(exc)
                labels.append(f'{index + 1}. {signal["name"]} [{state}]')
            while True:
                chosen = self.select(path.stem, labels)
                if chosen is None:
                    return
                index = labels.index(chosen)
                try:
                    carrier, _ = waveform(signals[index])
                except (ValueError, KeyError) as exc:
                    self.text_view('IR UNSUPPORTED', str(exc))
                    continue
                if self.confirm('IR TRANSMIT', f'{signals[index]["name"]}\nRequested {carrier} Hz; fixed ~36.6 kHz.\nSend once to your device?'):
                    self.text_view('IR TRANSMIT', run(['sudo', '/usr/local/sbin/hackeros-action', 'ir-send', str(path), str(index)], 20))
        except (OSError, ValueError) as exc:
            self.text_view('IR LIBRARY', str(exc))

    def ir_library(self):
        from ir_library import DATABASE, entries, search
        saved = RESULTS / 'ir'
        saved.mkdir(parents=True, exist_ok=True)
        while True:
            mode = self.select('GAMEHACK ZERO IR', ['Browse database', 'Search model / brand', 'Saved / learned remotes'])
            if mode is None:
                return
            root = saved if mode == 'Saved / learned remotes' else DATABASE
            if not root.is_dir():
                self.text_view('IR LIBRARY', 'Database not installed yet. Reconnect the system card for the IR update.')
                continue
            try:
                if mode == 'Search model / brand':
                    query = self.keyboard('IR model / brand')
                    if query and query.strip():
                        found = search(root, query)
                        names = [str(p.relative_to(root)) for p in found]
                        chosen = self.select('IR SEARCH (MAX 200)', names)
                        if chosen:
                            self.ir_remote(found[names.index(chosen)])
                    continue
                folder = root
                while True:
                    paths = entries(folder)
                    labels = [('DIR: ' if p.is_dir() else '') + p.name for p in paths]
                    chosen = self.select('IR: ' + folder.name, labels)
                    if chosen is None:
                        if folder == root:
                            break
                        folder = folder.parent
                        continue
                    path = paths[labels.index(chosen)]
                    if path.is_dir():
                        folder = path
                    else:
                        self.ir_remote(path)
            except (OSError, ValueError) as exc:
                self.text_view('IR LIBRARY', str(exc))

    def browse(self, start):
        current = Path(start)
        while True:
            if not current.exists():
                self.text_view("FILES", f"Not available: {current}")
                return
            entries = ["../"] + sorted([p.name + ("/" if p.is_dir() else "") for p in current.iterdir()], key=str.lower)
            selected = self.select(str(current), entries)
            if selected is None:
                return
            if selected == "../":
                if current == Path(start):
                    return
                current = current.parent
            else:
                target = current / selected.rstrip("/")
                if target.is_dir():
                    current = target
                elif target.stat().st_size <= 1024 * 1024:
                    try:
                        self.text_view(target.name, target.read_text(errors="replace"))
                    except OSError as exc:
                        self.text_view("FILES", str(exc))
                else:
                    self.text_view("FILES", f"{target}\n\n{target.stat().st_size} bytes\nPreview limited to files under 1 MiB.")

    def execute(self, action):
        if action not in ("favorites", "recent"):
            try:
                self.preferences.record(action)
            except OSError:
                self.message = "Settings could not be saved; check storage."
        if action == "favorites":
            self.quick_actions(self.preferences.favorites, "FAVORITES")
        elif action == "recent":
            self.quick_actions(self.preferences.recent, "RECENT ACTIONS")
        elif action == "theme":
            self.themes = load_themes(RESULTS / "asset_packs")
            chosen = self.select("APPEARANCE", list(self.themes))
            if chosen:
                self.apply_theme(chosen)
                self.preferences.theme = chosen
                try:
                    self.preferences.save()
                except OSError as exc:
                    self.text_view("SETTINGS", str(exc))
        elif action == "about":
            self.text_view("GAMEHACK ZERO", f"GameHack Zero {VERSION}\nZero-Day OS concept adapted for R36XX.\n\nController launcher, local coding, Pi worker, Freedoom and IR library.\nOriginal independent Linux implementation; not Flipper firmware.\n\nNFC and Sub-GHz are excluded.\nTF2 detection and native IR/provider operation still need validation.\nSee /opt/hackeros/RELEASE-4.2.0.md for release status.")
        elif action == "search-files":
            query = self.keyboard("Search filename")
            if query:
                chosen = self.select("SEARCH RESULTS (MAX 200)", search_files([RESULTS, "/data/external"], query))
                if chosen:
                    self.browse(str(Path(chosen).parent))
        elif action == "ir-library":
            self.ir_library()
        elif action == "ir-guide":
            self.text_view("INFRARED GUIDE", "GameHack Zero IR library\nTiqiaa Tview 10c4:8468; USB host mode.\n\nBrowse category, brand, remote and button, or search by model. L2: back; R2: select.\nSupported: raw, NEC and NECext. Other parsed protocols are marked unsupported.\nSaved remotes: /data/gamehack-zero/ir.\n\nFixed carrier ~36.6 kHz, not adjustable. Other frequencies may not work. Transmission needs hardware testing.\nDatabase: Lucaslhm/Flipper-IRDB; upstream license/provenance included.\nOnly control devices you own or may operate.")
        elif action in ("freedoom-1", "freedoom-2"):
            self.freedoom(int(action[-1]))
        elif action == "freedoom-controls":
            self.text_view("FREEDOOM CONTROLS", "D-pad / left stick: move and turn\nA: use / open door\nB: fire\nX: map\nY: cycle weapon slots\nL1 / R1: strafe\nL2: back / pause menu\nR2: OK / select in menus\nSTART: pause / menu\nSELECT: confirm menu item\nL2 + R2 or START + SELECT: exit game\n\nSaves: /data/gamehack-zero/freedoom\nControls and display need on-device testing.")
        elif action == "dashboard":
            self.dashboard()
        elif action == "network":
            self.text_view("NETWORK", run(["/usr/local/sbin/hackeros-report", "network"], 15))
        elif action == "hardware":
            self.text_view("HARDWARE", run(["/usr/local/sbin/hackeros-report", "hardware"], 15))
        elif action == "tools":
            self.text_view("TOOL ARSENAL", run(["/usr/local/sbin/hackeros-report", "tools"], 10))
        elif action == "wifi":
            self.wifi_setup()
        elif action == "wifi-status":
            self.wifi_status()
        elif action == "wifi-monitor":
            self.wifi_monitor()
        elif action == "pi-worker":
            self.pi_worker()
        elif action == "nimbus-fieldkit":
            from nimbus_fieldkit import menu
            menu(self, run)
        elif action == "wifi-survey":
            self.text_view("WI-FI SURVEY", run(["nmcli", "-f", "SSID,SIGNAL,CHAN,RATE,SECURITY", "dev", "wifi", "list", "--rescan", "yes"], 30))
        elif action == "bluetooth":
            self.text_view("BLUETOOTH", run(["sudo", "/usr/local/sbin/hackeros-action", "bluetooth-scan"], 25))
        elif action == "ir-status":
            self.text_view("INFRARED", run(["/usr/local/sbin/hackeros-report", "ir"], 15))
        elif action == "ir-learn":
            if self.confirm("IR LEARN", "Aim a remote at the adapter.\nCapture for up to 30 seconds?"):
                self.text_view("IR LEARN", run(["sudo", "/usr/local/sbin/hackeros-action", "ir-learn"], 40))
        elif action == "ir-send":
            roots = [RESULTS / "ir", Path("/data/external")]
            files = []
            for root in roots:
                if root.exists():
                    files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in (".ir", ".txt", ".mode2"))
            labels = [str(path) for path in sorted(files)]
            selected = self.select("SELECT IR SIGNAL", labels)
            if selected:
                self.ir_remote(Path(selected))
        elif action == "otg-status":
            self.text_view("OTG LINK", run(["/usr/local/sbin/hackeros-report", "otg"], 10))
        elif action == "discover":
            cidr = local_cidr()
            if not cidr:
                self.text_view("DISCOVERY", "No connected IPv4 network was found.")
            elif self.confirm("AUTHORIZED USE", f"Scan local network {cidr}?\nOnly continue with permission."):
                self.text_view("LOCAL HOSTS", run(["nmap", "-sn", "--", cidr], 120))
        elif action == "ports":
            target = self.keyboard("Authorized target")
            if target and re.fullmatch(r"[A-Za-z0-9._:-]+", target) and not target.startswith("-"):
                if self.confirm("AUTHORIZED USE", f"Audit top 100 TCP ports on\n{target}?"):
                    self.text_view("TCP PORT AUDIT", run(["nmap", "-sT", "-T3", "--top-ports", "100", "--", target], 180))
            elif target:
                self.text_view("TCP PORT AUDIT", "Invalid target.")
        elif action == "diagnostics":
            host = self.keyboard("Hostname")
            if host and re.fullmatch(r"[A-Za-z0-9.-]+", host):
                self.text_view("DIAGNOSTICS", run(["/usr/local/sbin/hackeros-report", "diagnostics", host], 35))
        elif action == "capture":
            if self.confirm("AUTHORIZED USE", "Capture up to 250 packets?\nOnly capture traffic you may inspect."):
                self.text_view("PACKET CAPTURE", run(["sudo", "/usr/local/sbin/hackeros-action", "capture"], 75))
        elif action == "browse-workspace":
            self.browse("/data/gamehack-zero")
        elif action == "browse-external":
            self.browse("/data/external")
        elif action == "browse-debug":
            self.browse("/data/debug/sessions")
        elif action == "browse-roms":
            self.browse("/data/external/roms")
        elif action == "storage":
            self.text_view("STORAGE", run(["/usr/local/sbin/hackeros-report", "storage"], 10))
        elif action == "eject":
            if self.confirm("SAFE EJECT", "Unmount the expansion card?"):
                self.text_view("SAFE EJECT", run(["sudo", "/usr/local/sbin/hackeros-action", "eject"], 20))
        elif action == "ssh":
            password_file = Path("/etc/hackeros/bootstrap-password")
            password = password_file.read_text().strip() if password_file.exists() else "your configured password"
            self.text_view("SSH ACCESS", f"USB host address: 10.55.0.1\nGameHack Zero: 10.55.0.2\n\nssh hacker@10.55.0.2\nInitial password: {password}\n\nYou must change it on first login.")
        elif action == "workspace":
            self.browse("/home/hacker/workspace")
        elif action == "opencode-local":
            self.local_coding()
        elif action == "coding-terminal":
            self.local_coding(False)
        elif action == "zeroday-features":
            self.zeroday_features()
        elif action == "opencode-prompt":
            self.opencode_prompt()
        elif action == "opencode":
            path = shutil.which("opencode")
            self.text_view("OPENCODE", f"Binary: {path or 'not installed'}\n\nUse OpenCode over SSH for a full keyboard-driven session.")
        elif action == "warnings":
            self.text_view("SYSTEM WARNINGS", run(["journalctl", "-p", "warning", "-n", "120", "--no-pager"], 15))
        elif action.startswith("power-"):
            profile = action.split("-", 1)[1]
            self.text_view("POWER PROFILE", run(["sudo", "/usr/local/sbin/hackeros-action", "power", profile], 15))
        elif action == "usb-host":
            if self.confirm("USB ROLE", "Unplug the PC OTG cable first.\nSwitch to USB host and reboot?\nUSB remote access stops."):
                run(["sudo", "/usr/local/sbin/hackeros-action", "usb-mode", "host"], 10)
        elif action == "usb-gadget":
            if self.confirm("USB ROLE", "Switch OTG to PC network and reboot?\nWi-Fi on a shared USB bus may stop.\nConnect the PC after reboot."):
                run(["sudo", "/usr/local/sbin/hackeros-action", "usb-mode", "gadget"], 10)
        elif action == "reboot":
            if self.confirm("REBOOT", "Restart GameHack Zero now?"):
                run(["sudo", "/usr/local/sbin/hackeros-action", "reboot"], 5)
        elif action == "poweroff":
            if self.confirm("POWER OFF", "Shut down GameHack Zero now?"):
                run(["sudo", "/usr/local/sbin/hackeros-action", "poweroff"], 5)

    def navigate(self, action):
        if self.home:
            if action in ("left", "right", "up", "down"):
                delta = {"left": -1, "right": 1, "up": -3, "down": 3}[action]
                self.category = (self.category + delta) % len(CATEGORIES)
            elif action == "confirm":
                self.home = False
                self.item = 0
            return
        if action in ("left", "right"):
            self.category = (self.category + (-1 if action == "left" else 1)) % len(CATEGORIES)
            self.item = 0
        elif action in ("up", "down"):
            self.item = (self.item + (-1 if action == "up" else 1)) % len(CATEGORIES[self.category][1])
        elif action == "back":
            self.home = True
        elif action == "confirm":
            self.execute(CATEGORIES[self.category][1][self.item][1])
        elif action == "details":
            selected = CATEGORIES[self.category][1][self.item][1]
            try:
                self.preferences.toggle_favorite(selected)
            except OSError as exc:
                self.text_view("FAVORITES", str(exc))

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.draw()
            action = self.get_action()
            if action == "quit":
                return
            if action == "status":
                self.dashboard()
            else:
                self.navigate(action)
            clock.tick(30)


if __name__ == "__main__":
    GameHackZero().run()

"""Native ttk styling and original, dependency-free pixel icons."""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import font, ttk

BG = "#101720"
PANEL = "#17212d"
CARD = "#1e2b39"
TEXT = "#edf4fa"
MUTED = "#99aebf"
ACCENT = "#58dfc5"
DANGER = "#ff8890"
BORDER = "#33495d"


def rounded_image(master, fill, outline, width=32, height=32, radius=8):
    """Nine-slice surface; transparent corners work on any parent panel."""
    image = tk.PhotoImage(master=master, width=width, height=height)
    for y in range(height):
        for x in range(width):
            dx = max(radius - x - .5, x + .5 - (width - radius), 0)
            dy = max(radius - y - .5, y + .5 - (height - radius), 0)
            if dx * dx + dy * dy <= radius * radius:
                edge = (min(x, y, width - x - 1, height - y - 1) < 1
                        or dx * dx + dy * dy > (radius - 1) ** 2)
                image.put(outline if edge else fill, (x, y))
    return image


class Appearance:
    def __init__(self, root):
        self.root = root
        self.images = []  # Tk images must stay alive for the entire window lifetime.
        self.icons = {}
        families = {name.casefold(): name for name in font.families(root)}
        self.family = next((families[name.casefold()] for name in ("Segoe UI", "DejaVu Sans", "Arial")
                            if name.casefold() in families), font.nametofont("TkDefaultFont", root=root).actual("family"))
        self.mono = next((families[name.casefold()] for name in ("Consolas", "DejaVu Sans Mono", "Courier")
                          if name.casefold() in families), self.family)
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            font.nametofont(name, root=root).configure(family=self.family, size=10)
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.configure()

    def keep(self, image):
        self.images.append(image)
        return image

    def button_style(self, name, normal, hover, pressed, foreground, outline):
        s = self.style
        states = [self.keep(rounded_image(self.root, fill, stroke)) for fill, stroke in (
            (normal, outline), (hover, outline), (pressed, ACCENT),
            ("#1b2631", "#293846"), (normal, ACCENT))]
        element = name + ".surface"
        s.element_create(element, "image", states[0],
                         ("disabled", states[3]), ("pressed", states[2]),
                         ("focus", states[4]), ("active", states[1]),
                         border=8, sticky="nsew")
        s.layout(name, [(element, {"sticky": "nsew", "children": [
            ("Button.padding", {"sticky": "nsew", "children": [
                ("Button.label", {"sticky": "nsew"})]})]})])
        s.configure(name, font=(self.family, 10, "bold"), foreground=foreground,
                    padding=(10, 4), anchor="center", borderwidth=0, background=BG)
        s.map(name, foreground=[("disabled", "#697c8b")], background=[("disabled", BG), ("active", BG)])

    def configure(self):
        s = self.style
        for name, color in (("TFrame", BG), ("Panel.TFrame", PANEL), ("Card.TFrame", CARD)):
            s.configure(name, background=color)
        for name, bg, fg, size, weight in (
            ("TLabel", BG, TEXT, 10, "normal"),
            ("Panel.TLabel", PANEL, TEXT, 10, "normal"),
            ("Muted.TLabel", BG, MUTED, 9, "normal"),
            ("CardMuted.TLabel", CARD, MUTED, 9, "normal"),
            ("Title.TLabel", BG, TEXT, 18, "bold"),
            ("Section.TLabel", PANEL, TEXT, 12, "bold"),
            ("TimerName.TLabel", CARD, TEXT, 11, "bold"),
        ):
            s.configure(name, background=bg, foreground=fg, font=(self.family, size, weight))
        s.configure("Clock.TLabel", background=BG, foreground=ACCENT,
                    font=(self.mono, 15, "bold"))
        s.configure("TimerClock.TLabel", background=CARD, foreground=TEXT,
                    font=(self.mono, 18, "bold"))
        self.button_style("TButton", "#223344", "#2b4256", "#193e42", TEXT, BORDER)
        self.button_style("Accent.TButton", ACCENT, "#80ebd7", "#36bba5", "#09251f", ACCENT)
        self.button_style("Danger.TButton", "#302630", "#46303a", "#522e39", DANGER, "#65404b")
        s.configure("TEntry", fieldbackground=BG, foreground=TEXT, insertcolor=ACCENT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    padding=(10, 7), borderwidth=1, selectbackground="#245749")
        s.map("TEntry", bordercolor=[("focus", ACCENT)],
              lightcolor=[("focus", ACCENT)], darkcolor=[("focus", ACCENT)])
        s.configure("TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT,
                    arrowcolor=MUTED, bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, padding=(8, 6))
        s.map("TCombobox", fieldbackground=[("readonly", CARD)],
              foreground=[("readonly", TEXT)], selectbackground=[("readonly", CARD)],
              selectforeground=[("readonly", TEXT)], bordercolor=[("focus", ACCENT)])
        self.root.option_add("*TCombobox*Listbox.background", CARD)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#25534f")
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                    font=(self.family, 10), rowheight=40, borderwidth=0,
                    lightcolor=PANEL, darkcolor=PANEL)
        s.layout("Treeview", [("Treeview.treearea", {"sticky": "nsew"})])
        s.configure("Treeview.Heading", background=CARD, foreground=MUTED,
                    font=(self.family, 9, "bold"), relief="flat", padding=(8, 7))
        s.map("Treeview", background=[("selected", "#234e4c")],
              foreground=[("selected", "#ffffff")])
        s.map("Treeview.Heading", background=[("active", "#293c4d")])
        s.configure("Horizontal.TProgressbar", troughcolor="#334556", background=ACCENT,
                    borderwidth=0, lightcolor=ACCENT, darkcolor=ACCENT, thickness=5)
        for element, fill in (("Hunt.trough", "#334556"), ("Hunt.pbar", ACCENT)):
            surface = self.keep(rounded_image(self.root, fill, fill, 12, 6, 3))
            s.element_create(element, "image", surface, border=(3, 0, 3, 0), sticky="nsew")
        s.layout("Horizontal.TProgressbar", [("Hunt.trough", {"sticky": "ew", "children": [
            ("Hunt.pbar", {"side": "left", "sticky": "ns"})]})])
        s.configure("Vertical.TScrollbar", background=BORDER, troughcolor=PANEL,
                    arrowcolor=MUTED, borderwidth=0, arrowsize=12)
        s.map("Vertical.TScrollbar", background=[("active", "#56748a")])
        switches = []
        for selected, focused in ((False, False), (True, False), (False, True), (True, True)):
            fill = ACCENT if selected else BORDER
            image = rounded_image(self.root, fill, TEXT if focused else fill, 34, 20, 10)
            cx = 24 if selected else 10
            for y in range(3, 17):
                for x in range(cx - 7, cx + 7):
                    if (x + .5 - cx) ** 2 + (y + .5 - 10) ** 2 <= 49:
                        image.put("#f4fafc", (x, y))
            switches.append(self.keep(image))
        s.element_create("Hunt.toggle", "image", switches[0],
                         ("selected", "focus", switches[3]), ("selected", switches[1]),
                         ("focus", switches[2]), sticky="w")
        s.layout("TCheckbutton", [("Checkbutton.padding", {"sticky": "nsew", "children": [
            ("Hunt.toggle", {"side": "left", "sticky": "w"}),
            ("Checkbutton.label", {"side": "left", "sticky": "w"})]})])
        s.configure("TCheckbutton", background=BG, foreground=TEXT, padding=(0, 4),
                    font=(self.family, 9))
        s.map("TCheckbutton", background=[("active", BG)])
        s.configure("Panel.TCheckbutton", background=PANEL)
        s.map("Panel.TCheckbutton", background=[("active", PANEL)])

    def reset_icon(self):
        if "reset" not in self.icons:
            image = tk.PhotoImage(master=self.root, width=20, height=20)
            for y in range(20):
                for x in range(20):
                    distance = math.hypot(x - 10, y - 10)
                    if (5 <= distance <= 7 and not (x < 9 and y < 6)) or (
                            2 <= x <= 7 and 2 <= y <= 7 and x + y >= 9):
                        image.put(TEXT, (x, y))
            self.icons["reset"] = image
        return self.icons["reset"]

    def icon(self, entry):
        """Original category symbols, not official game sprites."""
        name = entry.name.casefold()
        category = entry.item_category or ""
        if entry.entity_type != "spell":
            kind = "ring" if "ring" in category or "ring" in name else "amulet"
        elif "shield" in name:
            kind = "shield"
        elif "recovery" in name or "heal" in name:
            kind = "recovery"
        else:
            kind = "spell"
        if kind in self.icons:
            return self.icons[kind]
        image = tk.PhotoImage(master=self.root, width=32, height=32)
        colors = {"ring": "#edc96d", "amulet": "#f3b66e", "shield": "#74b9ff",
                  "recovery": "#78e6ad", "spell": "#bda0ff"}
        color = colors[kind]
        for y in range(16):
            for x in range(16):
                dx, dy = x - 7.5, y - 8
                pixel = None
                if kind == "ring":
                    radius = math.hypot(dx, dy)
                    if 4 <= radius <= 6:
                        pixel = color if y < 10 else "#9b7c42"
                    if 6 <= x <= 9 and 1 <= y <= 4:
                        pixel = "#74dfd0" if x < 8 else "#329b96"
                elif kind == "amulet":
                    if 2 <= y <= 9 and abs(abs(dx) - (10 - y) * .65) < 1:
                        pixel = color
                    if abs(dx) + abs(y - 11) <= 3:
                        pixel = color if x < 8 else "#c27451"
                    if abs(dx) < 1.5 and 9 <= y <= 12:
                        pixel = "#e77485"
                elif kind == "shield":
                    limit = 5 if y < 9 else 14 - y
                    if 2 <= y <= 13 and abs(dx) <= limit:
                        pixel = color if abs(dx) > limit - 1.5 or y < 4 else "#2b6399"
                        if abs(dx) < 1 or y == 7:
                            pixel = "#c7e5ff"
                else:
                    cx, cy = (7, 8) if kind == "recovery" else (8, 7)
                    if ((abs(x - cx) <= 1 and abs(y - cy) <= 5)
                            or (abs(y - cy) <= 1 and abs(x - cx) <= 5)):
                        pixel = color
                    if abs(x - cx) <= 1 and abs(y - cy) <= 1:
                        pixel = "#edfff5"
                    if (x, y) in ((2, 2), (13, 3), (12, 13)):
                        pixel = color
                if pixel:
                    image.put(pixel, (x * 2, y * 2, x * 2 + 2, y * 2 + 2))
        self.icons[kind] = image
        return image

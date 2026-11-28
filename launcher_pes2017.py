#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRO EVOLUTION SOCCER 2017 — PC Launcher Oficial (PRO17PORT)
Diseño Sports Broadcast · Bento Grid con barra lateral de iconos,
detección independiente de Carpeta Base (CUSA04957) y Parche (CUSA04957-patch),
soporte nativo de Option Files (WEPES) y ajustes gráficos/audio Vulkan.
"""
import ctypes
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pes2017_lang import UI_LANGUAGES, normalize_language, translate

# Activar DPI awareness en Windows para textos y bordes ultra nítidos
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Konami.PES2017.PCLauncher")
    except Exception:
        pass


def attach_stdio():
    """Garantiza que existan sys.stdout y sys.stderr al ejecutarse con pythonw.exe sin consola."""
    if sys.platform != "win32":
        return
    import msvcrt
    for name, std in (("stdout", -11), ("stderr", -12)):
        if getattr(sys, name) is not None:
            continue
        stream = None
        try:
            handle = ctypes.windll.kernel32.GetStdHandle(std)
            if handle and handle != ctypes.c_void_p(-1).value:
                stream = open(
                    msvcrt.open_osfhandle(handle, os.O_WRONLY),
                    "w",
                    encoding="utf-8",
                    errors="replace",
                    buffering=1,
                )
        except Exception:
            stream = None
        setattr(sys, name, stream or open(os.devnull, "w", encoding="utf-8"))


attach_stdio()

BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
if (BASE_DIR / "PRO17PORT").is_dir():
    ENGINE_DIR = BASE_DIR / "PRO17PORT"
elif (BASE_DIR / "out").is_dir():
    ENGINE_DIR = BASE_DIR
elif (BASE_DIR / "src").is_dir():
    ENGINE_DIR = BASE_DIR
else:
    ENGINE_DIR = BASE_DIR

OUT_DIR = ENGINE_DIR / "out"
SETTINGS_FILE = BASE_DIR / "pes2017_launcher.json"
INI_FILE = ENGINE_DIR / "pes2017.ini"
LEGACY_INI_FILE = ENGINE_DIR / "pes2017.ini"
MSYS2_BIN = Path(r"D:\MSYS2\clang64\bin")
MSYS2_USR = Path(r"D:\MSYS2\usr\bin")

# ============================================================================
# Paleta Sports Broadcast · Bento Grid (Grafito / Azul Marino / Carmesí / Oro)
# ============================================================================
BG_ROOT = "#0a0c10"
BG_SIDEBAR = "#090b0f"
BG_MAIN = "#0d0f14"
BG_CARD = "#141821"
BG_CARD_HI = "#1b212e"
BG_CARD_HOVER = "#232b3c"
BG_INPUT = "#0c0f16"
BG_PILL = "#1a202d"
BORDER_COLOR = "#242c3d"
BORDER_SUBTLE = "#1a202e"

FG_WHITE = "#f8fafc"
FG_TEXT = "#e2e8f0"
FG_MUTED = "#94a3b8"
FG_DIM = "#64748b"

ACCENT = "#f5c518"        # Dorado metálico PES 2017
ACCENT_HOVER = "#fde047"
ACCENT_DARK = "#b4860b"
CRIMSON = "#be123c"
CRIMSON_HI = "#e11d48"
NAVY_DEEP = "#0c172b"
GREEN_OK = "#22c55e"
GREEN_BG = "#0e2a1d"
GREEN_BORDER = "#166534"
BLUE_ACCENT = "#38bdf8"
WARN_COLOR = "#f59e0b"
ERR_COLOR = "#ef4444"

DISPLAY_MODES = [
    ("windowed", "Ventana (Windowed)"),
    ("borderless", "Ventana sin bordes (Borderless)"),
    ("fullscreen", "Pantalla completa (Fullscreen)"),
]

RESOLUTIONS = [
    ("720p", "1280 × 720 (HD 720p)"),
    ("900p", "1600 × 900 (HD+ 900p)"),
    ("native", "1920 × 1080 (Full HD 1080p)"),
    ("1440p", "2560 × 1440 (QHD 2K)"),
    ("4K", "3840 × 2160 (Ultra HD 4K)"),
    ("2560x1080", "2560 × 1080 (Ultrawide 21:9)"),
    ("3440x1440", "3440 × 1440 (Ultrawide 21:9)"),
]

RES_SHORT = {
    "720p": "1280×720",
    "900p": "1600×900",
    "native": "1920×1080",
    "1440p": "2560×1440",
    "4K": "3840×2160",
    "2560x1080": "2560×1080",
    "3440x1440": "3440×1440",
}

UPSCALERS = [
    ("off", "Desactivado (Nativo puro)"),
    ("taa", "TAA + RCAS (Suavizado temporal + Nitidez)"),
    ("fsr3", "AMD FSR (EASU Upscaling + RCAS Nitidez)"),
]

FPS_LIMITS = [
    ("60", "60 FPS (Recomendado — Velocidad oficial PES)"),
    ("120", "120 FPS (⚠ Acelera el partido — Experimental)"),
    ("144", "144 FPS (⚠ Acelera el partido — Experimental)"),
    ("0", "Sin límite (⚠ Acelera si el monitor es >60 Hz)"),
]

ANISO_OPTIONS = [
    ("0", "Por defecto del juego"),
    ("2", "2x Anisotrópico"),
    ("4", "4x Anisotrópico"),
    ("8", "8x Anisotrópico (Recomendado)"),
    ("16", "16x Anisotrópico (Máxima nitidez)"),
]

AUDIO_CHANNELS = [
    ("auto", "Automático (Windows)"),
    ("stereo", "Estéreo (2.0)"),
    ("5.1", "Envolvente 5.1"),
    ("7.1", "Envolvente 7.1"),
]

LANGUAGES = [
    ("17", "Español (Latinoamérica)"),
    ("3", "Español (España)"),
    ("1", "Inglés (EE.UU.)"),
    ("18", "Inglés (Reino Unido)"),
    ("2", "Francés"),
    ("4", "Alemán"),
    ("5", "Italiano"),
    ("7", "Portugués (Portugal)"),
    ("16", "Portugués (Brasil)"),
    ("0", "Japonés"),
]


def read_sfo(path: Path) -> dict:
    """Lee un archivo param.sfo y devuelve sus metadatos."""
    try:
        data = path.read_bytes()
        if len(data) < 20 or data[:4] != b"\x00PSF":
            return {}
        _, _, keys_off, vals_off, count = struct.unpack_from("<4sIIII", data, 0)
        out = {}
        for i in range(count):
            k_off, fmt, size, _, v_off = struct.unpack_from("<HHIII", data, 20 + i * 16)
            end_k = data.index(0, keys_off + k_off)
            key = data[keys_off + k_off : end_k].decode("ascii", errors="ignore")
            val_bytes = data[vals_off + v_off : vals_off + v_off + size]
            if fmt == 0x0404 and len(val_bytes) == 4:
                out[key] = struct.unpack("<I", val_bytes)[0]
            else:
                out[key] = val_bytes.rstrip(b"\x00").decode("utf-8", errors="ignore")
        return out
    except Exception:
        return {}


def read_dpfilelist(path: Path) -> list:
    """Lee la lista de paquetes CPK activos en DpFileList.bin."""
    try:
        data = path.read_bytes()
        cpks = []
        for i in range(0, len(data), 48):
            chunk = data[i : i + 48]
            if len(chunk) == 48:
                name = chunk[16:48].split(b"\x00")[0].decode("ascii", errors="ignore").strip()
                if name.endswith(".cpk"):
                    cpks.append(name)
        return cpks
    except Exception:
        return []


def auto_detect_folders():
    """Detecta automáticamente la carpeta del juego base y la carpeta de actualización."""
    base_candidates = [
        BASE_DIR / "CUSA04957",
        BASE_DIR.parent / "CUSA04957",
        ENGINE_DIR.parent / "CUSA04957",
        BASE_DIR / "PES2017byZC" / "CUSA04957",
        BASE_DIR.parent / "PES2017byZC" / "CUSA04957",
    ]
    patch_candidates = [
        BASE_DIR / "CUSA04957-patch",
        BASE_DIR.parent / "CUSA04957-patch",
        ENGINE_DIR.parent / "CUSA04957-patch",
        BASE_DIR / "PES2017byZC" / "CUSA04957-patch",
        BASE_DIR.parent / "PES2017byZC" / "CUSA04957-patch",
        BASE_DIR / "CUSA04957-update",
        BASE_DIR / "patch",
    ]
    found_base = next((str(p) for p in base_candidates if (p / "eboot.bin").is_file()), "")
    found_patch = next((str(p) for p in patch_candidates if (p / "eboot.bin").is_file()), "")
    return found_base, found_patch


def find_sibling_patch(game_dir: str) -> str:
    """Busca carpetas hermanas de parche automáticamente al elegir la carpeta base."""
    if not game_dir:
        return ""
    g = Path(game_dir)
    candidates = [
        g.parent / f"{g.name}-patch",
        g.parent / f"{g.name}-update",
        g.parent / "PES2017byZC" / f"{g.name}-patch",
        BASE_DIR / "CUSA04957-patch",
        BASE_DIR.parent / "CUSA04957-patch",
    ]
    for c in candidates:
        if c.is_dir() and c != g and (c / "eboot.bin").is_file():
            return str(c)
    return ""


def read_ini(path: Path) -> dict:
    values = {}
    target = path if path.is_file() else (LEGACY_INI_FILE if LEGACY_INI_FILE.is_file() else None)
    if not target:
        return values
    try:
        for line in target.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    except Exception:
        pass
    return values


def write_ini(path: Path, updates: dict):
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines() if path.is_file() else [
            "# Configuración gráfica de Pro Evolution Soccer 2017"
        ]
    except Exception:
        lines = ["# Configuración gráfica de Pro Evolution Soccer 2017"]
    done = set()
    out = []
    for line in lines:
        if line.startswith("# Configuración gráfica de PES 2017"):
            out.append("# Configuración gráfica de Pro Evolution Soccer 2017")
            continue
        key = line.split("=", 1)[0].strip() if ("=" in line and not line.lstrip().startswith("#")) else None
        if key in updates:
            out.append(f"{key}={updates[key]}")
            done.add(key)
        else:
            out.append(line)
    for k, v in updates.items():
        if k not in done:
            out.append(f"{k}={v}")
    content = "\n".join(out) + "\n"
    path.write_text(content, encoding="utf-8")
    try:
        LEGACY_INI_FILE.write_text(content, encoding="utf-8")
    except Exception:
        pass


def enable_dark_titlebar(window: tk.Tk):
    """Activa la barra de título oscura nativa en Windows 10/11."""
    if sys.platform != "win32":
        return
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        dark = ctypes.c_int(1)
        for attr in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(dark), ctypes.sizeof(dark))
        caption_color = ctypes.c_int(0x00100C0A)  # #0a0c10
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(caption_color), ctypes.sizeof(caption_color))
    except Exception:
        pass


def draw_rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, r=12, **kwargs):
    """Dibuja un rectángulo con esquinas redondeadas suaves en un tk.Canvas."""
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def bind_hover(widget, normal_bg, hover_bg, normal_fg=None, hover_fg=None):
    def on_enter(_e):
        if str(widget.cget("state")) != "disabled":
            widget.configure(bg=hover_bg)
            if hover_fg is not None:
                widget.configure(fg=hover_fg)

    def on_leave(_e):
        widget.configure(bg=normal_bg)
        if normal_fg is not None:
            widget.configure(fg=normal_fg)

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


class ToolTip:
    """Tooltip minimalista oscuro para los iconos de la barra lateral."""
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _e=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 8
        y = self.widget.winfo_rooty() + (self.widget.winfo_height() // 2) - 13
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg=BORDER_COLOR)
        lbl = tk.Label(
            tw,
            text=self.text,
            bg="#121620",
            fg=FG_WHITE,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
        )
        lbl.pack(padx=1, pady=1)

    def _hide(self, _e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ModernToggle(tk.Canvas):
    """Interruptor moderno redondeado (verde esmeralda / dorado)."""
    def __init__(self, parent, variable: tk.BooleanVar, command=None, bg=BG_CARD, active_color=GREEN_OK):
        super().__init__(parent, width=52, height=28, bg=bg, highlightthickness=0, cursor="hand2")
        self.variable = variable
        self.command = command
        self.active_color = active_color
        self.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *_: self._draw())
        self._draw()

    def _toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _draw(self):
        self.delete("all")
        on = bool(self.variable.get())
        track = self.active_color if on else "#262e40"
        border = "#4ade80" if (on and self.active_color == GREEN_OK) else (ACCENT_HOVER if on else "#344058")
        knob = "#0b111c" if on else "#cbd5e1"
        # Pista redondeada
        self.create_oval(2, 2, 26, 26, fill=border, outline="")
        self.create_oval(26, 2, 50, 26, fill=border, outline="")
        self.create_rectangle(14, 2, 38, 26, fill=border, outline="")
        self.create_oval(3, 3, 25, 25, fill=track, outline="")
        self.create_oval(27, 3, 49, 25, fill=track, outline="")
        self.create_rectangle(14, 3, 38, 25, fill=track, outline="")
        # Círculo móvil
        cx = 28 if on else 6
        self.create_oval(cx, 6, cx + 18, 22, fill=knob, outline="")


class ModernSlider(tk.Canvas):
    """Deslizador personalizado moderno en Canvas para el volumen maestro."""
    def __init__(self, parent, variable: tk.IntVar, from_=0, to=200, bg=BG_CARD, label_var=None):
        super().__init__(parent, height=34, bg=bg, highlightthickness=0, cursor="hand2")
        self.variable = variable
        self.from_ = from_
        self.to = to
        self.label_var = label_var
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Button-1>", self._on_drag)
        self.bind("<B1-Motion>", self._on_drag)
        self.variable.trace_add("write", lambda *_: self._draw())

    def _on_drag(self, event):
        w = max(self.winfo_width(), 60)
        pad = 12
        ratio = max(0.0, min(1.0, (event.x - pad) / max(1, w - 2 * pad)))
        val = int(round(self.from_ + ratio * (self.to - self.from_)))
        self.variable.set(val)

    def _draw(self):
        self.delete("all")
        w = max(self.winfo_width(), 60)
        cy = 17
        pad = 12
        val = max(self.from_, min(self.to, int(self.variable.get())))
        ratio = (val - self.from_) / max(1, (self.to - self.from_))
        tx = pad + ratio * (w - 2 * pad)
        if self.label_var is not None:
            self.label_var.set(f"{val}%")

        self.create_line(pad, cy, w - pad, cy, fill="#242c3d", width=6, capstyle="round")
        if self.from_ < 100 < self.to:
            x100 = pad + ((100 - self.from_) / (self.to - self.from_)) * (w - 2 * pad)
            self.create_line(x100, cy - 8, x100, cy + 8, fill="#38445e", width=1)
        if tx > pad:
            self.create_line(pad, cy, tx, cy, fill=ACCENT, width=6, capstyle="round")
        self.create_oval(tx - 10, cy - 10, tx + 10, cy + 10, fill="#1f2738", outline=ACCENT, width=2)
        self.create_oval(tx - 5, cy - 5, tx + 5, cy + 5, fill=FG_WHITE, outline="")


class PES2017Launcher:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PRO EVOLUTION SOCCER 2017 — PRO17PORT")
        self.root.geometry("1040x660")
        self.root.minsize(940, 610)
        self.root.configure(bg=BG_ROOT)

        self.icon_img = None
        self.settings = self.load_settings()
        self.ui_language = self.settings["ui_language"]
        self.launch_in_progress = False
        self.active_page = "home"
        self.play_enabled = True
        self.play_hover = False
        self.play_label = self.tr("▶   JUGAR PES 2017")
        self.hero_badge_text = self.tr("DETECTANDO...")
        self.hero_badge_color = ACCENT
        self.hero_btn_box = (0, 0, 0, 0)

        self.load_brand_images()
        self.setup_styles()
        self.build_ui()
        enable_dark_titlebar(self.root)
        self.refresh_detection()

    def tr(self, text):
        return translate(text, self.ui_language)

    def load_brand_images(self):
        game_dir = Path(self.settings.get("game_dir", "")) if self.settings.get("game_dir") else BASE_DIR / "CUSA04957"
        if not (game_dir / "sce_sys").is_dir():
            game_dir = BASE_DIR.parent / "CUSA04957"
        icon_path = game_dir / "sce_sys" / "icon0.png"
        if icon_path.is_file():
            try:
                full_icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, full_icon)
                self.icon_img = full_icon
            except Exception:
                pass

    def load_settings(self) -> dict:
        auto_base, auto_patch = auto_detect_folders()
        ini = read_ini(INI_FILE)
        defaults = {
            "ui_language": "es",
            "game_dir": auto_base,
            "patch_dir": auto_patch,
            "use_patch": bool(auto_patch),
            "user_dir": str(OUT_DIR / "user"),
            "display_mode": ini.get("display_mode", "windowed"),
            "render_resolution": ini.get("render_resolution", "native"),
            "upscaler": ini.get("upscaler", "off"),
            "vsync": ini.get("vsync", "1") == "1",
            "fps_limit": ini.get("fps_limit", "60"),
            "show_fps": ini.get("show_fps", "0") == "1",
            "anisotropy": ini.get("anisotropy", "8"),
            "master_volume": int(ini.get("master_volume", "100") or 100),
            "audio_channels": ini.get("audio_channels", "auto"),
            "language": "17",
            "close_on_launch": False,
        }
        if SETTINGS_FILE.is_file():
            try:
                saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    defaults.update(saved)
            except Exception:
                pass
        if "\\PRO17PORT\\out\\user" in defaults.get("user_dir", "") and not (ENGINE_DIR / "PRO17PORT").is_dir():
            defaults["user_dir"] = str(OUT_DIR / "user")
        if not defaults["game_dir"] and auto_base:
            defaults["game_dir"] = auto_base
        if not defaults["patch_dir"]:
            sib = find_sibling_patch(defaults["game_dir"])
            if sib:
                defaults["patch_dir"] = sib
        defaults["ui_language"] = normalize_language(defaults["ui_language"])
        return defaults

    def save_settings(self):
        data = {
            "ui_language": self.get_combo_key(self.cb_ui_lang, UI_LANGUAGES, "es"),
            "game_dir": self.var_game_dir.get().strip(),
            "patch_dir": self.var_patch_dir.get().strip(),
            "use_patch": bool(self.var_use_patch.get()),
            "user_dir": self.var_user_dir.get().strip() or str(OUT_DIR / "user"),
            "display_mode": self.get_combo_key(self.cb_display_mode, DISPLAY_MODES, "windowed"),
            "render_resolution": self.get_combo_key(self.cb_resolution, RESOLUTIONS, "native"),
            "upscaler": self.get_combo_key(self.cb_upscaler, UPSCALERS, "off"),
            "vsync": bool(self.var_vsync.get()),
            "fps_limit": self.get_combo_key(self.cb_fps, FPS_LIMITS, "60"),
            "show_fps": bool(self.var_show_fps.get()),
            "anisotropy": self.get_combo_key(self.cb_aniso, ANISO_OPTIONS, "8"),
            "master_volume": int(self.var_volume.get()),
            "audio_channels": self.get_combo_key(self.cb_audio, AUDIO_CHANNELS, "auto"),
            "language": self.get_combo_key(self.cb_lang, LANGUAGES, "17"),
            "close_on_launch": bool(self.var_close_on_launch.get()),
        }
        SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self.settings = data

        res_key = data["render_resolution"]
        out_res_map = {
            "720p": "1280x720",
            "900p": "1920x1080",
            "native": "1920x1080",
            "1440p": "2560x1440",
            "4K": "3840x2160",
        }
        upscaler_key = data["upscaler"]
        fsr_on = "1" if upscaler_key in ("fsr3", "taa") else "0"
        rcas_strength = "90" if upscaler_key == "fsr3" else ("40" if upscaler_key == "taa" else "0")
        write_ini(INI_FILE, {
            "display_mode": data["display_mode"],
            "render_resolution": res_key,
            "output_res": out_res_map.get(res_key, "1920x1080"),
            "upscaler": upscaler_key,
            "fsr1": fsr_on,
            "rcas": fsr_on,
            "rcas_strength": rcas_strength,
            "vsync": "1" if data["vsync"] else "0",
            "fps_limit": data["fps_limit"],
            "show_fps": "1" if data["show_fps"] else "0",
            "anisotropy": data["anisotropy"] if str(data["anisotropy"]).isdigit() else "0",
            "master_volume": str(data["master_volume"]),
            "audio_channels": data["audio_channels"],
            "deferred_readback": "1",
            "stale_readback": "0",
        })
        self.refresh_graphics_summary()
        return data

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=BG_CARD, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure(
            "TCombobox",
            fieldbackground=BG_INPUT,
            background=BG_CARD_HI,
            foreground=FG_WHITE,
            arrowcolor=ACCENT,
            bordercolor=BORDER_COLOR,
            lightcolor=BORDER_COLOR,
            darkcolor=BORDER_COLOR,
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", BG_INPUT)],
            foreground=[("readonly", FG_WHITE)],
            selectbackground=[("readonly", BG_INPUT)],
            selectforeground=[("readonly", FG_WHITE)],
        )
        self.root.option_add("*TCombobox*Listbox.background", BG_INPUT)
        self.root.option_add("*TCombobox*Listbox.foreground", FG_WHITE)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#090b0f")
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

    def make_btn(self, parent, text, command, fg=FG_WHITE, bg=BG_CARD_HI, hover=BG_CARD_HOVER, padx=14, pady=7):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=ACCENT,
            activeforeground="#090b0f",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            font=("Segoe UI", 9, "bold"),
            padx=padx,
            pady=pady,
            cursor="hand2",
        )
        bind_hover(btn, bg, hover, fg, FG_WHITE)
        return btn

    def build_ui(self):
        main_wrap = tk.Frame(self.root, bg=BG_ROOT)
        self.main_wrap = main_wrap
        main_wrap.pack(fill="both", expand=True)

        # ================= SLIM ICON-ONLY SIDEBAR (66px) =================
        sidebar = tk.Frame(main_wrap, bg=BG_SIDEBAR, width=66)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Frame(main_wrap, bg=BORDER_SUBTLE, width=1).pack(side="left", fill="y")

        self.nav_buttons = {}
        self.nav_bars = {}
        self.pages = {}

        top_nav = [
            ("home", "⌂", self.tr("Inicio (Panel Bento)")),
            ("gfx",  "🖥", self.tr("Pantalla y Gráficos")),
            ("aud",  "🔊", self.tr("Audio e Idioma")),
            ("dirs", "📁", self.tr("Carpetas, Parche y Option Files")),
        ]
        tk.Frame(sidebar, bg=BG_SIDEBAR, height=18).pack(fill="x")

        for key, icon, tip in top_nav:
            row = tk.Frame(sidebar, bg=BG_SIDEBAR, height=54)
            row.pack(fill="x", pady=4)
            row.pack_propagate(False)

            bar = tk.Frame(row, bg=BG_SIDEBAR, width=4)
            bar.pack(side="left", fill="y", pady=8)

            btn = tk.Button(
                row,
                text=icon,
                bg=BG_SIDEBAR,
                fg=FG_MUTED,
                activebackground=BG_CARD_HI,
                activeforeground=ACCENT,
                relief="flat",
                bd=0,
                font=("Segoe UI Symbol", 17),
                cursor="hand2",
                command=lambda k=key: self.switch_page(k),
            )
            btn.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=4)
            ToolTip(btn, tip)

            def _bind(k=key, b=btn):
                b.bind("<Enter>", lambda _e: b.configure(bg=BG_CARD, fg=FG_WHITE) if self.active_page != k else None, add="+")
                b.bind("<Leave>", lambda _e: b.configure(bg=BG_SIDEBAR, fg=FG_MUTED) if self.active_page != k else None, add="+")
            _bind()

            self.nav_buttons[key] = btn
            self.nav_bars[key] = bar

        # Botón inferior de Guardar / Ajustes rápidos en el sidebar
        save_row = tk.Frame(sidebar, bg=BG_SIDEBAR, height=54)
        save_row.pack(side="bottom", fill="x", pady=12)
        save_row.pack_propagate(False)
        btn_save_ico = tk.Button(
            save_row,
            text="⚙",
            bg=BG_SIDEBAR,
            fg=FG_MUTED,
            activebackground=BG_CARD_HI,
            activeforeground=ACCENT,
            relief="flat",
            bd=0,
            font=("Segoe UI Symbol", 17),
            cursor="hand2",
            command=lambda: self.switch_page("dirs"),
        )
        btn_save_ico.pack(fill="both", expand=True, padx=10, pady=4)
        ToolTip(btn_save_ico, self.tr("Rutas y Opciones del Launcher"))
        bind_hover(btn_save_ico, BG_SIDEBAR, BG_CARD, FG_MUTED, FG_WHITE)

        # ================= ÁREA DERECHA (HERO + BENTO CONTENT + MINI STATUS) =================
        right_area = tk.Frame(main_wrap, bg=BG_MAIN)
        right_area.pack(side="left", fill="both", expand=True)

        content_pad = tk.Frame(right_area, bg=BG_MAIN, padx=24, pady=18)
        content_pad.pack(fill="both", expand=True)

        # --- HERO BANNER DEPORTIVO (NAVY → CRIMSON + BOTÓN DORADO METÁLICO) ---
        self.hero_h = 176
        self.hero = tk.Canvas(content_pad, height=self.hero_h, bg=BG_MAIN, highlightthickness=0)
        self.hero.pack(fill="x", pady=(0, 18))
        self.hero.bind("<Configure>", lambda _e: self.draw_hero())
        self.hero.bind("<Motion>", self._on_hero_motion)
        self.hero.bind("<Leave>", self._on_hero_leave)
        self.hero.bind("<Button-1>", self._on_hero_click)

        # --- CONTENEDOR DE PÁGINAS ---
        self.page_container = tk.Frame(content_pad, bg=BG_MAIN)
        self.page_container.pack(fill="both", expand=True)

        # Construir todas las variables y páginas (primero dirs/gfx/aud para tener vars listas)
        self.build_page_dirs()
        self.build_page_graphics()
        self.build_page_audio()
        self.build_page_home()

        # --- MINI BARRA DE ESTADO INFERIOR ---
        status_strip = tk.Frame(right_area, bg=BG_SIDEBAR, height=36)
        status_strip.pack(fill="x", side="bottom")
        status_strip.pack_propagate(False)
        tk.Frame(right_area, bg=BORDER_SUBTLE, height=1).pack(fill="x", side="bottom")

        self.lbl_status_bar = tk.Label(
            status_strip,
            text=self.tr("●  Listo para jugar."),
            bg=BG_SIDEBAR,
            fg=FG_MUTED,
            font=("Segoe UI", 9),
        )
        self.lbl_status_bar.pack(side="left", padx=24)

        btn_quick_save = tk.Button(
            status_strip,
            text=self.tr("💾 Guardar Ajustes"),
            command=self.on_save_clicked,
            bg=BG_SIDEBAR,
            fg=ACCENT,
            activebackground=BG_CARD_HI,
            activeforeground=ACCENT_HOVER,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=12,
            pady=4,
            cursor="hand2",
        )
        btn_quick_save.pack(side="right", padx=18)
        bind_hover(btn_quick_save, BG_SIDEBAR, BG_CARD, ACCENT, ACCENT_HOVER)

        self.switch_page("home")
        self.refresh_graphics_summary()

    # -------------------- HERO BANNER CANVAS --------------------
    def draw_hero(self):
        c = self.hero
        c.delete("all")
        w = max(c.winfo_width(), 720)
        h = self.hero_h

        # Fondo base redondeado azul marino profundo
        draw_rounded_rect(c, 1, 1, w - 1, h - 1, r=16, fill=NAVY_DEEP, outline="")

        # Franjas diagonales deportivas azul → carmesí (estilo Broadcast PES 2017)
        split = int(w * 0.48)
        c.create_polygon(split + 50, 2, w - 12, 2, w - 2, 12, w - 2, h - 12, w - 12, h - 2, split - 65, h - 2, fill="#580e24", outline="")
        c.create_polygon(split + 85, 2, w - 12, 2, w - 2, 12, w - 2, h - 12, w - 12, h - 2, split - 30, h - 2, fill="#881337", outline="")
        c.create_polygon(split + 150, 2, w - 12, 2, w - 2, 12, w - 2, h - 12, w - 12, h - 2, split + 45, h - 2, fill="#a91237", outline="")
        c.create_polygon(split + 240, 2, w - 12, 2, w - 2, 12, w - 2, h - 12, w - 12, h - 2, split + 140, h - 2, fill="#7f102c", outline="")

        # Detalles geométricos sutiles de estadio y cancha
        c.create_line(split + 30, 2, split - 85, h - 2, fill="#1f355c", width=3)
        c.create_line(split + 58, 2, split - 57, h - 2, fill=CRIMSON_HI, width=4)
        c.create_line(split + 72, 2, split - 43, h - 2, fill=ACCENT, width=1)
        # Área táctica sutil a la derecha
        c.create_rectangle(w - 115, 22, w - 8, h - 22, outline="#c0264c", width=1)
        c.create_rectangle(w - 58, 52, w - 8, h - 52, outline="#c0264c", width=1)
        c.create_oval(w - 140, h // 2 - 28, w - 90, h // 2 + 28, outline="#c0264c", width=1)
        # Rejilla sutil de focos de estadio en la zona azul
        for row in range(3):
            for col in range(6):
                fx = int(w * 0.34) + col * 10 - row * 4
                fy = 20 + row * 9 + col * 2
                c.create_oval(fx, fy, fx + 3, fy + 3, fill="#28426e", outline="")

        # Borde exterior redondeado limpio
        draw_rounded_rect(c, 1, 1, w - 1, h - 1, r=16, fill="", outline="#2c3952", width=1)

        # Pill de estado arriba a la izquierda (● v01.07 LISTO)
        bx, by = 28, 22
        pill_w = max(132, len(self.hero_badge_text) * 8 + 38)
        draw_rounded_rect(c, bx, by, bx + pill_w, by + 28, r=14, fill="#141e33", outline="#2d3b59", width=1)
        c.create_oval(bx + 12, by + 9, bx + 22, by + 19, fill=self.hero_badge_color, outline="")
        c.create_text(bx + 30, by + 14, anchor="w", text=self.hero_badge_text, fill=FG_WHITE, font=("Segoe UI", 9, "bold"))

        # Título metálico PES (blanco) + 2017 (dorado)
        tx, ty = 28, 58
        c.create_text(tx, ty, anchor="nw", text="PES", fill=FG_WHITE, font=("Segoe UI Black", 36, "bold"))
        c.create_text(tx + 114, ty, anchor="nw", text="2017", fill=ACCENT, font=("Segoe UI Black", 36, "bold"))

        # Subtítulo
        c.create_text(
            tx + 2, ty + 68,
            anchor="nw",
            text="PC EDITION  ·  FOX ENGINE VULKAN",
            fill="#cbd5e1",
            font=("Segoe UI", 10, "bold"),
        )

        # Botón dorado metálico "▶  JUGAR PES 2017" a la derecha
        bw, bh = 258, 62
        x1 = w - bw - 34
        y1 = (h - bh) // 2
        x2 = x1 + bw
        y2 = y1 + bh
        self.hero_btn_box = (x1, y1, x2, y2)

        if not self.play_enabled:
            draw_rounded_rect(c, x1, y1, x2, y2, r=12, fill="#283040", outline="#3c465c", width=1)
            c.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=self.play_label, fill="#64748b", font=("Segoe UI", 13, "bold"))
        else:
            # Sombra/brillo dorado sutil detrás
            if self.play_hover:
                draw_rounded_rect(c, x1 - 3, y1 - 3, x2 + 3, y2 + 3, r=14, fill="", outline=ACCENT_HOVER, width=2)
            # Cuerpo del botón con efecto metálico de 2 tonos
            top_col = "#fde047" if self.play_hover else "#f7ce3b"
            bot_col = "#eab308" if self.play_hover else "#d49b12"
            draw_rounded_rect(c, x1, y1, x2, y2, r=12, fill=bot_col, outline="#fef08a", width=1)
            draw_rounded_rect(c, x1 + 2, y1 + 2, x2 - 2, (y1 + y2) // 2 + 4, r=10, fill=top_col, outline="")
            c.create_text(
                (x1 + x2) // 2, (y1 + y2) // 2,
                text=self.play_label,
                fill="#0b0e14",
                font=("Segoe UI", 13, "bold"),
            )

    def _in_hero_btn(self, x, y) -> bool:
        x1, y1, x2, y2 = self.hero_btn_box
        return x1 <= x <= x2 and y1 <= y <= y2

    def _on_hero_motion(self, event):
        over = self.play_enabled and self._in_hero_btn(event.x, event.y)
        self.hero.configure(cursor="hand2" if over else "")
        if over != self.play_hover:
            self.play_hover = over
            self.draw_hero()

    def _on_hero_leave(self, _event=None):
        if self.play_hover:
            self.play_hover = False
            self.draw_hero()

    def _on_hero_click(self, event):
        if self.play_enabled and self._in_hero_btn(event.x, event.y):
            self.on_play_clicked()

    # -------------------- TARJETA BENTO --------------------
    def create_bento_card(self, parent, icon: str, title: str, subtitle: str = "") -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=BG_CARD,
            padx=20,
            pady=16,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
        )
        hdr = tk.Frame(card, bg=BG_CARD)
        hdr.pack(fill="x", pady=(0, 12))
        tk.Label(hdr, text=icon, bg=BG_CARD, fg=FG_MUTED, font=("Segoe UI Symbol", 13)).pack(side="left", padx=(0, 8))
        tk.Label(hdr, text=title, bg=BG_CARD, fg=FG_WHITE, font=("Segoe UI", 12, "bold")).pack(side="left")
        if subtitle:
            tk.Label(hdr, text=subtitle, bg=BG_CARD, fg=FG_DIM, font=("Segoe UI", 8)).pack(side="right")
        return card

    # -------------------- PÁGINA 1: BENTO HOME (2x2) --------------------
    def build_page_home(self):
        page = tk.Frame(self.page_container, bg=BG_MAIN)
        self.pages["home"] = page
        page.columnconfigure(0, weight=1, uniform="bento")
        page.columnconfigure(1, weight=1, uniform="bento")
        page.rowconfigure(0, weight=1, uniform="bento_row")
        page.rowconfigure(1, weight=1, uniform="bento_row")

        # --- BENTO 1 (Arriba Izquierda): Archivos del Juego ---
        c1 = self.create_bento_card(page, "📁", self.tr("Archivos del Juego"))
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 9), pady=(0, 9))

        b1_body = tk.Frame(c1, bg=BG_CARD)
        b1_body.pack(fill="both", expand=True)

        left_f = tk.Frame(b1_body, bg=BG_CARD)
        left_f.pack(side="left", fill="both", expand=True)
        self.lbl_home_base = tk.Label(left_f, text="CUSA04957", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_home_base.pack(anchor="w", pady=(2, 4))
        self.lbl_home_patch = tk.Label(left_f, text="CUSA04957-patch", bg=BG_CARD, fg=FG_MUTED, font=("Segoe UI", 9), anchor="w")
        self.lbl_home_patch.pack(anchor="w")

        right_f = tk.Frame(b1_body, bg=BG_CARD)
        right_f.pack(side="right", padx=(10, 0))
        ModernToggle(right_f, self.var_use_patch, command=self.refresh_detection, bg=BG_CARD, active_color=GREEN_OK).pack(anchor="e")
        tk.Label(right_f, text=self.tr("Parche v01.07"), bg=BG_CARD, fg=FG_DIM, font=("Segoe UI", 8)).pack(anchor="e", pady=(4, 0))

        # --- BENTO 2 (Arriba Derecha): Perfil Gráfico ---
        c2 = self.create_bento_card(page, "🖥", self.tr("Perfil Gráfico"))
        c2.grid(row=0, column=1, sticky="nsew", padx=(9, 0), pady=(0, 9))

        self.gfx_pills_frame = tk.Frame(c2, bg=BG_CARD)
        self.gfx_pills_frame.pack(fill="x", pady=(6, 10))
        self.gfx_pill_labels = []
        for _ in range(4):
            lbl = tk.Label(
                self.gfx_pills_frame,
                text="",
                bg=BG_PILL,
                fg=FG_WHITE,
                font=("Segoe UI", 9, "bold"),
                padx=12,
                pady=6,
                highlightthickness=1,
                highlightbackground=BORDER_COLOR,
            )
            lbl.pack(side="left", padx=(0, 8))
            self.gfx_pill_labels.append(lbl)

        link_gfx = tk.Label(c2, text=self.tr("Personalizar gráficos →"), bg=BG_CARD, fg=ACCENT, font=("Segoe UI", 8, "bold"), cursor="hand2")
        link_gfx.pack(anchor="w")
        link_gfx.bind("<Button-1>", lambda _e: self.switch_page("gfx"))

        # --- BENTO 3 (Abajo Izquierda): Option Files (WEPES) ---
        c3 = self.create_bento_card(page, "📄", "Option Files (WEPES)")
        c3.grid(row=1, column=0, sticky="nsew", padx=(0, 9), pady=(9, 0))

        b3_row = tk.Frame(c3, bg=BG_CARD)
        b3_row.pack(fill="x", pady=(8, 0))

        tk.Label(
            b3_row,
            text=self.tr("USB Virtual Listo"),
            bg=GREEN_BG,
            fg=GREEN_OK,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=6,
            highlightthickness=1,
            highlightbackground=GREEN_BORDER,
        ).pack(side="left", padx=(0, 12))

        self.make_btn(b3_row, self.tr("Abrir carpeta WEPES"), self.open_wepes_dir, fg=FG_WHITE, padx=16, pady=6).pack(side="left")

        tk.Label(
            c3,
            text=self.tr("Coloca tus archivos .ted / .png en WEPES e impórtalos en Editar → Gestión de datos."),
            bg=BG_CARD,
            fg=FG_DIM,
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(12, 0))

        # --- BENTO 4 (Abajo Derecha): Atajos de Mando ---
        c4 = self.create_bento_card(page, "🎮", self.tr("Atajos de Mando"))
        c4.grid(row=1, column=1, sticky="nsew", padx=(9, 0), pady=(9, 0))

        keys_row = tk.Frame(c4, bg=BG_CARD)
        keys_row.pack(fill="x", pady=(8, 10))
        for k_text, k_desc in [
            ("Insert", self.tr("Menú")),
            ("L2+R3", self.tr("Mando")),
            ("Select", self.tr("Cámara BAL")),
            ("F12", self.tr("Captura")),
        ]:
            chip = tk.Frame(keys_row, bg=BG_PILL, padx=10, pady=6, highlightthickness=1, highlightbackground=BORDER_COLOR)
            chip.pack(side="left", padx=(0, 8))
            tk.Label(chip, text=k_text, bg=BG_PILL, fg=FG_WHITE, font=("Consolas", 9, "bold")).pack()
            tk.Label(chip, text=k_desc, bg=BG_PILL, fg=FG_DIM, font=("Segoe UI", 7)).pack()

    # -------------------- PÁGINA 2: GRÁFICOS --------------------
    def build_page_graphics(self):
        page = tk.Frame(self.page_container, bg=BG_MAIN)
        self.pages["gfx"] = page

        c1 = self.create_bento_card(page, "🖥", self.tr("Pantalla y Resolución"), "Vulkan 1.3")
        c1.pack(fill="x", pady=(0, 14))

        g1 = tk.Frame(c1, bg=BG_CARD)
        g1.pack(fill="x")
        g1.columnconfigure(1, weight=1)
        g1.columnconfigure(3, weight=1)

        tk.Label(g1, text=self.tr("Modo de pantalla:"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=7, padx=(0, 12))
        self.cb_display_mode = ttk.Combobox(g1, state="readonly", values=[self.tr(v) for _, v in DISPLAY_MODES])
        self.set_combo_by_key(self.cb_display_mode, DISPLAY_MODES, self.settings["display_mode"])
        self.cb_display_mode.grid(row=0, column=1, sticky="ew", pady=7, padx=(0, 20))

        tk.Label(g1, text=self.tr("Resolución interna:"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", pady=7, padx=(0, 12))
        self.cb_resolution = ttk.Combobox(g1, state="readonly", values=[self.tr(v) for _, v in RESOLUTIONS])
        self.set_combo_by_key(self.cb_resolution, RESOLUTIONS, self.settings["render_resolution"])
        self.cb_resolution.grid(row=0, column=3, sticky="ew", pady=7)
        self.cb_resolution.bind("<<ComboboxSelected>>", lambda _e: self.refresh_graphics_summary())

        tk.Label(g1, text=self.tr("Límite de FPS:"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=7, padx=(0, 12))
        self.cb_fps = ttk.Combobox(g1, state="readonly", values=[self.tr(v) for _, v in FPS_LIMITS])
        self.set_combo_by_key(self.cb_fps, FPS_LIMITS, str(self.settings["fps_limit"]))
        self.cb_fps.grid(row=1, column=1, sticky="ew", pady=7, padx=(0, 20))
        self.cb_fps.bind("<<ComboboxSelected>>", lambda _e: self.refresh_graphics_summary())

        tk.Label(g1, text=self.tr("Filtro anisotrópico:"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=1, column=2, sticky="w", pady=7, padx=(0, 12))
        self.cb_aniso = ttk.Combobox(g1, state="readonly", values=[self.tr(v) for _, v in ANISO_OPTIONS])
        self.set_combo_by_key(self.cb_aniso, ANISO_OPTIONS, str(self.settings["anisotropy"]))
        self.cb_aniso.grid(row=1, column=3, sticky="ew", pady=7)

        c2 = self.create_bento_card(page, "✨", self.tr("Suavizado, Escalado y Sincronización"))
        c2.pack(fill="x")

        g2 = tk.Frame(c2, bg=BG_CARD)
        g2.pack(fill="x")
        g2.columnconfigure(1, weight=1)
        tk.Label(g2, text="Antialiasing / Upscaler:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4, padx=(0, 14))
        self.cb_upscaler = ttk.Combobox(g2, state="readonly", values=[self.tr(v) for _, v in UPSCALERS])
        self.set_combo_by_key(self.cb_upscaler, UPSCALERS, self.settings["upscaler"])
        self.cb_upscaler.grid(row=0, column=1, sticky="ew", pady=4)

        t_row = tk.Frame(c2, bg=BG_CARD)
        t_row.pack(fill="x", pady=(12, 0))

        vs_box = tk.Frame(t_row, bg=BG_CARD_HI, padx=14, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        vs_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.var_vsync = tk.BooleanVar(value=self.settings["vsync"])
        ModernToggle(vs_box, self.var_vsync, command=self.refresh_graphics_summary, bg=BG_CARD_HI, active_color=GREEN_OK).pack(side="left", padx=(0, 12))
        vs_t = tk.Frame(vs_box, bg=BG_CARD_HI)
        vs_t.pack(side="left")
        tk.Label(vs_t, text=self.tr("Sincronización Vertical (VSync)"), bg=BG_CARD_HI, fg=FG_WHITE, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(vs_t, text=self.tr("Evita cortes horizontales de imagen"), bg=BG_CARD_HI, fg=FG_MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        fps_box = tk.Frame(t_row, bg=BG_CARD_HI, padx=14, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        fps_box.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.var_show_fps = tk.BooleanVar(value=self.settings["show_fps"])
        ModernToggle(fps_box, self.var_show_fps, bg=BG_CARD_HI, active_color=ACCENT).pack(side="left", padx=(0, 12))
        fps_t = tk.Frame(fps_box, bg=BG_CARD_HI)
        fps_t.pack(side="left")
        tk.Label(fps_t, text=self.tr("Overlay de Rendimiento"), bg=BG_CARD_HI, fg=FG_WHITE, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(fps_t, text=self.tr("FPS, Frametime y uso de GPU/VRAM"), bg=BG_CARD_HI, fg=FG_MUTED, font=("Segoe UI", 8)).pack(anchor="w")

    # -------------------- PÁGINA 3: AUDIO E IDIOMA --------------------
    def build_page_audio(self):
        page = tk.Frame(self.page_container, bg=BG_MAIN)
        self.pages["aud"] = page

        c1 = self.create_bento_card(page, "🔊", self.tr("Audio e Idioma del Juego"), self.tr("Mezcla multicanal"))
        c1.pack(fill="x", pady=(0, 14))

        g1 = tk.Frame(c1, bg=BG_CARD)
        g1.pack(fill="x")
        g1.columnconfigure(1, weight=1)
        g1.columnconfigure(3, weight=1)

        tk.Label(g1, text=self.tr("Idioma del juego:"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 12))
        self.cb_lang = ttk.Combobox(g1, state="readonly", values=[self.tr(v) for _, v in LANGUAGES])
        self.set_combo_by_key(self.cb_lang, LANGUAGES, str(self.settings["language"]))
        self.cb_lang.grid(row=0, column=1, sticky="ew", pady=8, padx=(0, 20))

        tk.Label(g1, text=self.tr("Canales de salida:"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", pady=8, padx=(0, 12))
        self.cb_audio = ttk.Combobox(g1, state="readonly", values=[self.tr(v) for _, v in AUDIO_CHANNELS])
        self.set_combo_by_key(self.cb_audio, AUDIO_CHANNELS, self.settings["audio_channels"])
        self.cb_audio.grid(row=0, column=3, sticky="ew", pady=8)

        tk.Label(g1, text=self.tr("Volumen maestro:"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=10, padx=(0, 12))
        vol_wrap = tk.Frame(g1, bg=BG_CARD)
        vol_wrap.grid(row=1, column=1, columnspan=3, sticky="ew", pady=6)
        self.var_volume = tk.IntVar(value=int(self.settings["master_volume"]))
        self.var_volume_text = tk.StringVar(value=f"{self.var_volume.get()}%")
        ModernSlider(vol_wrap, self.var_volume, from_=0, to=200, bg=BG_CARD, label_var=self.var_volume_text).pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(
            vol_wrap,
            textvariable=self.var_volume_text,
            bg=BG_INPUT,
            fg=ACCENT,
            font=("Consolas", 10, "bold"),
            width=5,
            pady=4,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
        ).pack(side="right")

        c2 = self.create_bento_card(page, "⚙", self.tr("Comportamiento del Launcher"))
        c2.pack(fill="x")
        language_row = tk.Frame(c2, bg=BG_CARD)
        language_row.pack(fill="x", pady=(0, 8))
        tk.Label(language_row, text=self.tr("Idioma del launcher:"), bg=BG_CARD,
                 fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 12))
        self.cb_ui_lang = ttk.Combobox(language_row, state="readonly", width=18,
                                      values=[label for _, label in UI_LANGUAGES])
        self.set_combo_by_key(self.cb_ui_lang, UI_LANGUAGES, self.ui_language)
        self.cb_ui_lang.pack(side="left")
        self.cb_ui_lang.bind("<<ComboboxSelected>>", self.on_ui_language_changed)
        close_row = tk.Frame(c2, bg=BG_CARD)
        close_row.pack(fill="x", pady=4)
        self.var_close_on_launch = tk.BooleanVar(value=self.settings["close_on_launch"])
        ModernToggle(close_row, self.var_close_on_launch, bg=BG_CARD, active_color=ACCENT).pack(side="left", padx=(0, 12))
        tk.Label(
            close_row,
            text=self.tr("Cerrar launcher automáticamente al iniciar PES 2017"),
            bg=BG_CARD,
            fg=FG_TEXT,
            font=("Segoe UI", 10),
        ).pack(side="left")

    # -------------------- PÁGINA 4: CARPETAS Y RUTAS --------------------
    def build_page_dirs(self):
        page = tk.Frame(self.page_container, bg=BG_MAIN)
        self.pages["dirs"] = page

        c1 = self.create_bento_card(page, "📁", self.tr("Rutas del Juego Base y Parche"), self.tr("Sin fusionar archivos"))
        c1.pack(fill="x", pady=(0, 14))

        tk.Label(c1, text=self.tr("Carpeta Juego Base (CUSA04957):"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        r1 = tk.Frame(c1, bg=BG_CARD)
        r1.pack(fill="x", pady=(4, 10))
        self.var_game_dir = tk.StringVar(value=self.settings["game_dir"])
        ent_game = tk.Entry(r1, textvariable=self.var_game_dir, bg=BG_INPUT, fg=FG_WHITE, insertbackground=ACCENT, relief="flat", font=("Consolas", 10), highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT)
        ent_game.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        ent_game.bind("<FocusOut>", lambda _e: self.on_game_dir_changed())
        self.make_btn(r1, self.tr("Examinar..."), self.browse_game_dir).pack(side="right")

        tk.Label(c1, text=self.tr("Carpeta Parche / DataPacks (CUSA04957-patch):"), bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        r2 = tk.Frame(c1, bg=BG_CARD)
        r2.pack(fill="x", pady=(4, 8))
        self.var_patch_dir = tk.StringVar(value=self.settings["patch_dir"])
        ent_patch = tk.Entry(r2, textvariable=self.var_patch_dir, bg=BG_INPUT, fg=FG_WHITE, insertbackground=ACCENT, relief="flat", font=("Consolas", 10), highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT)
        ent_patch.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        ent_patch.bind("<FocusOut>", lambda _e: self.refresh_detection())
        self.make_btn(r2, self.tr("Examinar..."), self.browse_patch_dir).pack(side="right")

        self.var_use_patch = tk.BooleanVar(value=self.settings["use_patch"])
        self.lbl_base_status = tk.Label(c1, text="", bg=BG_CARD, fg=GREEN_OK, font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_base_status.pack(anchor="w", pady=(2, 1))
        self.lbl_patch_status = tk.Label(c1, text="", bg=BG_CARD, fg=ACCENT, font=("Segoe UI", 9), anchor="w")
        self.lbl_patch_status.pack(anchor="w")

        c2 = self.create_bento_card(page, "💾", self.tr("Savedata y Option Files (WEPES)"))
        c2.pack(fill="x")
        r3 = tk.Frame(c2, bg=BG_CARD)
        r3.pack(fill="x", pady=4)
        self.var_user_dir = tk.StringVar(value=self.settings["user_dir"])
        ent_user = tk.Entry(r3, textvariable=self.var_user_dir, bg=BG_INPUT, fg=FG_WHITE, insertbackground=ACCENT, relief="flat", font=("Consolas", 10), highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT)
        ent_user.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        self.make_btn(r3, self.tr("💾 Savedata"), self.open_user_dir).pack(side="right")
        self.make_btn(r3, self.tr("📂 Carpeta WEPES"), self.open_wepes_dir, fg=ACCENT).pack(side="right", padx=(0, 8))

    def switch_page(self, key: str):
        self.active_page = key
        for k, p in self.pages.items():
            p.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(bg=BG_CARD_HI, fg=ACCENT)
                self.nav_bars[k].configure(bg=ACCENT)
            else:
                btn.configure(bg=BG_SIDEBAR, fg=FG_MUTED)
                self.nav_bars[k].configure(bg=BG_SIDEBAR)
        if key == "home":
            self.refresh_graphics_summary()

    def refresh_graphics_summary(self):
        if not hasattr(self, "gfx_pill_labels"):
            return
        res_k = self.get_combo_key(self.cb_resolution, RESOLUTIONS, "native")
        fps_k = self.get_combo_key(self.cb_fps, FPS_LIMITS, "60")
        vsync = bool(self.var_vsync.get())
        vals = [
            RES_SHORT.get(res_k, "1920×1080"),
            self.tr("Sin límite") if fps_k == "0" else f"{fps_k} FPS",
            "Vulkan",
            "VSync ON" if vsync else "VSync OFF",
        ]
        for lbl, txt in zip(self.gfx_pill_labels, vals):
            lbl.configure(text=txt)

    def open_user_dir(self):
        p = Path(self.var_user_dir.get().strip() or str(OUT_DIR / "user"))
        p.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(p))

    def open_wepes_dir(self):
        p = ENGINE_DIR / "WEPES"
        p.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(p))

    @staticmethod
    def set_combo_by_key(combo: ttk.Combobox, pairs: list, key: str):
        for index, (k, _label) in enumerate(pairs):
            if k == key:
                combo.current(index)
                return
        if pairs:
            combo.current(0)

    @staticmethod
    def get_combo_key(combo: ttk.Combobox, pairs: list, default: str) -> str:
        index = combo.current()
        return pairs[index][0] if 0 <= index < len(pairs) else default

    def on_ui_language_changed(self, _event=None):
        language = self.get_combo_key(self.cb_ui_lang, UI_LANGUAGES, "es")
        if self.launch_in_progress or language == self.ui_language:
            self.set_combo_by_key(self.cb_ui_lang, UI_LANGUAGES, self.ui_language)
            return
        # Save every current control before rebuilding so pending edits survive.
        self.save_settings()
        self.ui_language = language
        page = self.active_page
        self.main_wrap.destroy()
        self.play_label = self.tr("▶   JUGAR PES 2017")
        self.build_ui()
        self.switch_page(page)
        self.refresh_detection()

    def browse_game_dir(self):
        chosen = filedialog.askdirectory(
            title=self.tr("Selecciona la carpeta del juego base (CUSA04957)"),
            initialdir=self.var_game_dir.get() or str(BASE_DIR),
        )
        if chosen:
            self.var_game_dir.set(chosen)
            self.on_game_dir_changed()

    def browse_patch_dir(self):
        chosen = filedialog.askdirectory(
            title=self.tr("Selecciona la carpeta del Parche / Update (CUSA04957-patch)"),
            initialdir=self.var_patch_dir.get() or str(BASE_DIR),
        )
        if chosen:
            self.var_patch_dir.set(chosen)
            self.var_use_patch.set(True)
            self.refresh_detection()

    def on_game_dir_changed(self):
        game_dir = self.var_game_dir.get().strip()
        if game_dir and not self.var_patch_dir.get().strip():
            sib = find_sibling_patch(game_dir)
            if sib:
                self.var_patch_dir.set(sib)
                self.var_use_patch.set(True)
        self.refresh_detection()

    def refresh_detection(self):
        game_path = Path(self.var_game_dir.get().strip()) if self.var_game_dir.get().strip() else None
        patch_path = Path(self.var_patch_dir.get().strip()) if self.var_patch_dir.get().strip() else None
        use_patch = bool(self.var_use_patch.get())

        base_ok = bool(game_path and (game_path / "eboot.bin").is_file() and (game_path / "sce_module" / "libc.prx").is_file())
        if base_ok:
            sfo = read_sfo(game_path / "sce_sys" / "param.sfo")
            tid = sfo.get("TITLE_ID", "CUSA04957")
            ver = sfo.get("APP_VER", "01.00")
            self.lbl_base_status.configure(text=self.tr("✔ Juego Base listo: [{tid}] · v{ver}").format(tid=tid, ver=ver), fg=GREEN_OK)
            self.lbl_home_base.configure(text=f"✔  {game_path.name}  (v{ver})", fg=FG_WHITE)
        else:
            self.lbl_base_status.configure(text=self.tr("✖ Carpeta base no válida (falta eboot.bin / libc.prx)"), fg=ERR_COLOR)
            self.lbl_home_base.configure(text=self.tr("✖  Falta carpeta CUSA04957"), fg=ERR_COLOR)

        patch_ok = bool(patch_path and (patch_path / "eboot.bin").is_file())
        if patch_ok:
            psfo = read_sfo(patch_path / "sce_sys" / "param.sfo")
            pver = psfo.get("APP_VER", "01.07")
            cpks = read_dpfilelist(patch_path / "DpFileList.bin")
            cpk_info = f" · {len(cpks)} DataPacks" if cpks else ""
            if use_patch:
                self.lbl_patch_status.configure(text=self.tr("✔ Parche ACTIVO: v{version}{cpk_info}").format(version=pver, cpk_info=cpk_info), fg=ACCENT)
                self.lbl_home_patch.configure(text=self.tr("{name}  ·  Activo (v{version}{cpk_info})").format(name=patch_path.name, version=pver, cpk_info=cpk_info), fg=GREEN_OK)
            else:
                self.lbl_patch_status.configure(text=self.tr("ℹ Parche v{version} desactivado (modo base)").format(version=pver), fg=FG_MUTED)
                self.lbl_home_patch.configure(text=self.tr("{name}  ·  Desactivado").format(name=patch_path.name), fg=FG_MUTED)
        else:
            self.lbl_patch_status.configure(text=self.tr("ℹ Sin parche externo seleccionado"), fg=FG_MUTED)
            self.lbl_home_patch.configure(text=self.tr("Sin parche externo"), fg=FG_DIM)

        if not base_ok:
            self.hero_badge_text = self.tr("FALTA BASE")
            self.hero_badge_color = ERR_COLOR
            self.play_enabled = False
        elif patch_ok and use_patch:
            psfo = read_sfo(patch_path / "sce_sys" / "param.sfo")
            pver = psfo.get("APP_VER", "01.07")
            self.hero_badge_text = self.tr("v{version} LISTO").format(version=pver)
            self.hero_badge_color = GREEN_OK
            self.play_enabled = True
        else:
            sfo = read_sfo(game_path / "sce_sys" / "param.sfo")
            ver = sfo.get("APP_VER", "01.00")
            self.hero_badge_text = self.tr("v{version} LISTO").format(version=ver)
            self.hero_badge_color = GREEN_OK
            self.play_enabled = True
        self.draw_hero()

    def on_save_clicked(self):
        self.save_settings()
        self.lbl_status_bar.configure(text=self.tr("✔  Ajustes guardados en pes2017.ini"), fg=GREEN_OK)

    def ensure_boot_image(self, game_dir: Path, patch_dir: Path | None) -> Path:
        active_eboot = (patch_dir / "eboot.bin") if (patch_dir and (patch_dir / "eboot.bin").is_file()) else (game_dir / "eboot.bin")
        stat = active_eboot.stat()
        stamp_file = OUT_DIR / "active_eboot_stamp.json"
        target_boot = OUT_DIR / "boot-linked.bin"

        if target_boot.is_file() and stamp_file.is_file():
            try:
                stamp = json.loads(stamp_file.read_text(encoding="utf-8"))
                if stamp.get("path") == str(active_eboot) and stamp.get("size") == stat.st_size and stamp.get("mtime") == stat.st_mtime_ns:
                    return target_boot
            except Exception:
                pass

        sfo_dir = patch_dir if (patch_dir and (patch_dir / "sce_sys" / "param.sfo").is_file()) else game_dir
        ver = read_sfo(sfo_dir / "sce_sys" / "param.sfo").get("APP_VER", "")
        cached_boot = OUT_DIR / f"boot-linked-{ver}.bin"

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        scripts_dir = ENGINE_DIR / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        import prepare as prep_mod
        import link_modules as link_mod

        prep_mod.prepare(game_dir, OUT_DIR, eboot_override=patch_dir)
        link_mod.link(game_dir, OUT_DIR, patch_dir=patch_dir)

        if ver:
            try:
                import shutil
                shutil.copy2(target_boot, cached_boot)
            except Exception:
                pass

        stamp_file.write_text(
            json.dumps({"path": str(active_eboot), "size": stat.st_size, "mtime": stat.st_mtime_ns, "ver": ver}),
            encoding="utf-8",
        )
        return target_boot

    def on_play_clicked(self):
        cfg = self.save_settings()
        game_dir = Path(cfg["game_dir"])
        if not (game_dir / "eboot.bin").is_file():
            messagebox.showerror("Error", self.tr("No se encontró eboot.bin en la carpeta del juego base."))
            return

        patch_dir = Path(cfg["patch_dir"]) if (cfg["use_patch"] and cfg["patch_dir"]) else None
        if patch_dir and not (patch_dir / "eboot.bin").is_file():
            patch_dir = None

        self.play_enabled = False
        self.launch_in_progress = True
        self.cb_ui_lang.configure(state="disabled")
        self.play_label = self.tr("INICIANDO...")
        self.draw_hero()
        self.lbl_status_bar.configure(text=self.tr("●  Preparando módulos de Pro Evolution Soccer 2017..."), fg=ACCENT)
        self.root.update_idletasks()

        def worker():
            try:
                boot_bin = self.ensure_boot_image(game_dir, patch_dir)
                content_bin = OUT_DIR / "content.bin"
                if not content_bin.is_file():
                    scripts_dir = ENGINE_DIR / "scripts"
                    if str(scripts_dir) not in sys.path:
                        sys.path.insert(0, str(scripts_dir))
                    import content_profile as cp_mod
                    cp_mod.prepare(game_dir, OUT_DIR)

                env = os.environ.copy()
                env["PATH"] = f"{OUT_DIR};{env.get('PATH', '')}"
                if MSYS2_BIN.is_dir():
                    env["PATH"] = f"{MSYS2_BIN};{MSYS2_USR};{env['PATH']}"
                env["SPARTAN_CONFIG"] = str(INI_FILE)
                env.setdefault("SPARTAN_PARTIAL_HEIGHT_VIEWS", "0")
                env.setdefault("SPARTAN_DEFERRED_READBACK", "1")
                env.setdefault("SPARTAN_STALE_READBACK", "0")
                env["SPARTAN_LANGUAGE"] = str(cfg["language"])
                env["SPARTAN_AUDIO_VOLUME"] = str(cfg["master_volume"])
                env["SPARTAN_AUDIO_CHANNELS"] = str(cfg["audio_channels"])
                env["SPARTAN_ANISOTROPY"] = str(cfg["anisotropy"])
                env["SPARTAN_UPSCALER"] = str(cfg["upscaler"])
                env["SPARTAN_FSR1"] = "1" if cfg["upscaler"] in ("fsr3", "taa") else "0"
                env["SPARTAN_RCAS"] = "1" if cfg["upscaler"] in ("fsr3", "taa") else "0"

                icon_png = game_dir / "sce_sys" / "icon0.png"
                if icon_png.is_file():
                    env["SPARTAN_WINDOW_ICON"] = str(icon_png).replace("\\", "/")

                if patch_dir:
                    env["SPARTAN_PATCH_DIR"] = str(patch_dir).replace("\\", "/")
                else:
                    env.pop("SPARTAN_PATCH_DIR", None)

                game_exe = OUT_DIR / "PES2017.exe"
                if not game_exe.is_file():
                    raise FileNotFoundError(self.tr("No se encontró el ejecutable principal PES2017.exe en {path}").format(path=OUT_DIR))

                user_dir = Path(cfg["user_dir"])
                if "\\PRO17PORT\\out\\user" in str(user_dir) and not user_dir.parent.is_dir():
                    user_dir = OUT_DIR / "user"
                user_dir.mkdir(parents=True, exist_ok=True)

                cmd = [
                    str(game_exe),
                    str(boot_bin),
                    "--content-profile",
                    str(content_bin),
                    "--app0",
                    str(game_dir).replace("\\", "/"),
                    "--user",
                    str(user_dir).replace("\\", "/"),
                ]

                creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                subprocess.Popen(cmd, cwd=str(ENGINE_DIR), env=env, creationflags=creation_flags)
                self.root.after(0, self.on_launch_success)
            except Exception as exc:
                self.root.after(0, lambda error=str(exc): self.on_launch_error(error))

        threading.Thread(target=worker, daemon=True).start()

    def on_launch_success(self):
        self.launch_in_progress = False
        self.cb_ui_lang.configure(state="readonly")
        self.play_enabled = True
        self.play_label = self.tr("▶   JUGAR PES 2017")
        self.draw_hero()
        self.lbl_status_bar.configure(text=self.tr("✔  ¡Pro Evolution Soccer 2017 en ejecución!"), fg=GREEN_OK)
        if self.var_close_on_launch.get():
            self.root.destroy()

    def on_launch_error(self, err_msg: str):
        self.launch_in_progress = False
        self.cb_ui_lang.configure(state="readonly")
        self.play_enabled = True
        self.play_label = self.tr("▶   JUGAR PES 2017")
        self.draw_hero()
        self.lbl_status_bar.configure(text=self.tr("✖  Error al iniciar: {error}").format(error=err_msg), fg=ERR_COLOR)
        messagebox.showerror(self.tr("Error al lanzar PES 2017"), err_msg)


def main():
    root = tk.Tk()
    PES2017Launcher(root)
    root.mainloop()


if __name__ == "__main__":
    main()

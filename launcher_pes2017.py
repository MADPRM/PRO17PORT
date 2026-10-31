#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRO EVOLUTION SOCCER 2017 — PC Launcher Oficial
Interfaz moderna con barra lateral, portada oficial de PES 2017, detección
inteligente de Carpeta Base (CUSA04957) y Parche/DataPacks (CUSA04957-patch)
por separado sin fusionar carpetas, y ajustes gráficos/audio.
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

BASE_DIR = Path(__file__).resolve().parent
if (BASE_DIR / "PRO17PORT").is_dir():
    ENGINE_DIR = BASE_DIR / "PRO17PORT"
elif (BASE_DIR / "src").is_dir():
    ENGINE_DIR = BASE_DIR
else:
    ENGINE_DIR = BASE_DIR / "PRO17PORT" 
OUT_DIR = ENGINE_DIR / "out"
SETTINGS_FILE = BASE_DIR / "pes2017_launcher.json"
INI_FILE = ENGINE_DIR / "pes2017.ini"
LEGACY_INI_FILE = ENGINE_DIR / "pes2017.ini"
MSYS2_BIN = Path(r"D:\MSYS2\clang64\bin")
MSYS2_USR = Path(r"D:\MSYS2\usr\bin")

# Paleta de colores inspirada en la interfaz oficial de PES 2017 (Navy / Pitch Dark / Gold)
BG_ROOT = "#070a10"
BG_SIDEBAR = "#0b101b"
BG_HERO = "#0d1424"
BG_MAIN = "#0f172a"
BG_CARD = "#162033"
BG_CARD_HI = "#1e2c46"
BG_INPUT = "#0c1322"
BORDER_COLOR = "#263554"
BORDER_GOLD = "#eab308"

FG_WHITE = "#f8fafc"
FG_TEXT = "#e2e8f0"
FG_MUTED = "#94a3b8"
FG_DIM = "#64748b"

ACCENT = "#facc15"        # Amarillo/Dorado icónico de PES 2017
ACCENT_HOVER = "#fde047"
ACCENT_DARK = "#ca8a04"
BLUE_ACCENT = "#38bdf8"
GREEN_OK = "#22c55e"
WARN_COLOR = "#f59e0b"
ERR_COLOR = "#ef4444"

DISPLAY_MODES = [
    ("windowed", "Ventana (Windowed)"),
    ("borderless", "Ventana sin bordes (Borderless Fullscreen)"),
    ("fullscreen", "Pantalla completa exclusiva (Fullscreen)"),
]

RESOLUTIONS = [
    ("720p", "1280 × 720 (HD 720p)"),
    ("900p", "1600 × 900 (HD+ 900p)"),
    ("native", "1920 × 1080 (Full HD 1080p · Nativo)"),
    ("1440p", "2560 × 1440 (QHD 2K)"),
    ("4K", "3840 × 2160 (Ultra HD 4K)"),
    ("2560x1080", "2560 × 1080 (Ultrawide 21:9)"),
    ("3440x1440", "3440 × 1440 (Ultrawide 21:9)"),
]

UPSCALERS = [
    ("off", "Desactivado (Nativo puro)"),
    ("taa", "TAA + RCAS (Suavizado de bordes temporal + Nitidez)"),
    ("fsr3", "AMD FSR (EASU Upscaling + RCAS Nitidez alta)"),
]

FPS_LIMITS = [
    ("60", "60 FPS (Velocidad oficial de simulación PES)"),
    ("120", "120 FPS"),
    ("144", "144 FPS"),
    ("0", "Sin límite (Controlado por VSync)"),
]

ANISO_OPTIONS = [
    ("0", "Por defecto del juego"),
    ("2", "2x Anisotrópico"),
    ("4", "4x Anisotrópico"),
    ("8", "8x Anisotrópico (Recomendado)"),
    ("16", "16x Anisotrópico (Máxima nitidez de césped)"),
]

AUDIO_CHANNELS = [
    ("auto", "Automático (según dispositivo de Windows)"),
    ("stereo", "Estéreo (2.0)"),
    ("5.1", "Sonido Envolvente 5.1"),
    ("7.1", "Sonido Envolvente 7.1"),
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
        BASE_DIR / "PES2017byZC" / "CUSA04957-patch",
        BASE_DIR.parent / "PES2017byZC" / "CUSA04957-patch",
        BASE_DIR / "CUSA04957-patch",
        BASE_DIR.parent / "CUSA04957-patch",
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
        BASE_DIR / "PES2017byZC" / "CUSA04957-patch",
        BASE_DIR / "CUSA04957-patch",
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
    # Mantener sincronizado el archivo legado por si alguna herramienta lo consulta
    try:
        LEGACY_INI_FILE.write_text(content, encoding="utf-8")
    except Exception:
        pass


class ModernToggle(tk.Canvas):
    """Interruptor moderno estilo switch (On/Off) animado."""
    def __init__(self, parent, variable: tk.BooleanVar, command=None, bg=BG_CARD):
        super().__init__(parent, width=46, height=24, bg=bg, highlightthickness=0, cursor="hand2")
        self.variable = variable
        self.command = command
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
        track_color = ACCENT if on else "#334155"
        knob_color = "#090d14" if on else "#cbd5e1"
        # Pista redondeada (dos círculos + rectángulo central)
        self.create_oval(2, 2, 22, 22, fill=track_color, outline="")
        self.create_oval(24, 2, 44, 22, fill=track_color, outline="")
        self.create_rectangle(12, 2, 34, 22, fill=track_color, outline="")
        # Círculo móvil
        cx = 25 if on else 5
        self.create_oval(cx, 4, cx + 16, 20, fill=knob_color, outline="")


class PES2017Launcher:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pro Evolution Soccer 2017 — PC Launcher")
        self.root.geometry("980x690")
        self.root.minsize(920, 640)
        self.root.configure(bg=BG_ROOT)

        self.icon_img = None
        self.logo_small = None
        self.hero_bg_img = None

        self.settings = self.load_settings()
        self.load_brand_images()
        self.setup_styles()
        self.build_ui()
        self.refresh_detection()

    def load_brand_images(self):
        """Carga el icono y arte oficial desde sce_sys/icon0.png y pic1.png."""
        game_dir = Path(self.settings.get("game_dir", "")) if self.settings.get("game_dir") else BASE_DIR / "CUSA04957"
        if not (game_dir / "sce_sys").is_dir():
            game_dir = BASE_DIR / "CUSA04957"

        icon_path = game_dir / "sce_sys" / "icon0.png"
        if icon_path.is_file():
            try:
                full_icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, full_icon)
                self.icon_img = full_icon.subsample(5, 5)   # ~102x102 para el Hero
                self.logo_small = full_icon.subsample(9, 9) # ~56x56 para la barra lateral
            except Exception:
                pass

        pic_path = game_dir / "sce_sys" / "pic0.png"
        if pic_path.is_file():
            try:
                full_pic = tk.PhotoImage(file=str(pic_path))
                self.hero_bg_img = full_pic.subsample(3, 3)
            except Exception:
                pass

    def load_settings(self) -> dict:
        auto_base, auto_patch = auto_detect_folders()
        ini = read_ini(INI_FILE)
        defaults = {
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
                defaults.update(saved)
            except Exception:
                pass
        if not defaults["game_dir"] and auto_base:
            defaults["game_dir"] = auto_base
        if not defaults["patch_dir"]:
            sib = find_sibling_patch(defaults["game_dir"])
            if sib:
                defaults["patch_dir"] = sib
        return defaults

    def save_settings(self):
        data = {
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
            "stale_readback": "1",
        })
        return data

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=BG_CARD, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("TCombobox",
                        fieldbackground=BG_INPUT,
                        background=BG_CARD_HI,
                        foreground=FG_WHITE,
                        arrowcolor=ACCENT,
                        bordercolor=BORDER_COLOR,
                        lightcolor=BORDER_COLOR,
                        darkcolor=BORDER_COLOR,
                        padding=6)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG_INPUT)],
                  foreground=[("readonly", FG_WHITE)],
                  selectbackground=[("readonly", BG_INPUT)],
                  selectforeground=[("readonly", FG_WHITE)])
        self.root.option_add("*TCombobox*Listbox.background", BG_INPUT)
        self.root.option_add("*TCombobox*Listbox.foreground", FG_WHITE)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#090d14")
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

    def build_ui(self):
        # Layout principal: Barra lateral izquierda (230px) + Área principal derecha
        main_wrap = tk.Frame(self.root, bg=BG_ROOT)
        main_wrap.pack(fill="both", expand=True)

        # ================= BARRA LATERAL (SIDEBAR) =================
        sidebar = tk.Frame(main_wrap, bg=BG_SIDEBAR, width=235, highlightthickness=1, highlightbackground=BORDER_COLOR)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Cabecera de marca en la barra lateral
        brand_box = tk.Frame(sidebar, bg=BG_SIDEBAR, pady=22, padx=18)
        brand_box.pack(fill="x")
        if self.logo_small:
            tk.Label(brand_box, image=self.logo_small, bg=BG_SIDEBAR).pack(side="left", padx=(0, 12))
        title_col = tk.Frame(brand_box, bg=BG_SIDEBAR)
        title_col.pack(side="left", fill="x")
        tk.Label(title_col, text="PES 2017", bg=BG_SIDEBAR, fg=ACCENT, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        tk.Label(title_col, text="PC EDITION", bg=BG_SIDEBAR, fg=FG_MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")

        tk.Frame(sidebar, bg=BORDER_COLOR, height=1).pack(fill="x", padx=16, pady=(0, 14))

        # Botones de navegación
        self.nav_buttons = {}
        self.pages = {}
        nav_items = [
            ("home", "⚽   Inicio y Carpetas"),
            ("gfx",  "🖥   Pantalla y Gráficos"),
            ("aud",  "🔊   Audio e Idioma"),
        ]
        for key, label in nav_items:
            btn = tk.Button(
                sidebar,
                text=label,
                anchor="w",
                 padx=20,
                pady=12,
                bg=BG_SIDEBAR,
                fg=FG_MUTED,
                activebackground=BG_CARD,
                activeforeground=FG_WHITE,
                relief="flat",
                bd=0,
                font=("Segoe UI", 10, "bold"),
                cursor="hand2",
                command=lambda k=key: self.switch_page(k),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[key] = btn

        # Tarjeta de atajos útiles en la parte baja del sidebar
        info_card = tk.Frame(sidebar, bg=BG_CARD, padx=14, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        info_card.pack(side="bottom", fill="x", padx=14, pady=16)
        tk.Label(info_card, text="ATAJOS EN PARTIDO", bg=BG_CARD, fg=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 6))
        for shortcut, desc in [("Insert", "Menú en el juego"), ("R3 + L2", "Menú desde mando"), ("F12", "Captura de pantalla")]:
            row = tk.Frame(info_card, bg=BG_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=shortcut, bg=BG_INPUT, fg=FG_WHITE, font=("Consolas", 8, "bold"), padx=6, pady=1).pack(side="left")
            tk.Label(row, text=desc, bg=BG_CARD, fg=FG_MUTED, font=("Segoe UI", 8)).pack(side="right")

        # ================= ÁREA DERECHA (HERO + PÁGINAS + FOOTER) =================
        right_area = tk.Frame(main_wrap, bg=BG_MAIN)
        right_area.pack(side="left", fill="both", expand=True)

        # --- HERO BANNER CON ARTE DE PES 2017 ---
        hero = tk.Canvas(right_area, height=132, bg=BG_HERO, highlightthickness=0)
        hero.pack(fill="x", side="top")

        def draw_hero(event=None):
            hero.delete("all")
            w = event.width if event else 745
            if self.hero_bg_img:
                hero.create_image(w // 2, 66, image=self.hero_bg_img)
            # Superposición oscura elegante para legibilidad perfecta
            hero.create_rectangle(0, 0, w, 132, fill="#080d1a", stipple="gray75", outline="")
            hero.create_line(0, 131, w, 131, fill=BORDER_GOLD, width=2)

            x_text = 26
            if self.icon_img:
                hero.create_image(68, 66, image=self.icon_img)
                x_text = 132

            hero.create_text(
                x_text, 40,
                anchor="nw",
                text="PRO EVOLUTION SOCCER 2017",
                fill=FG_WHITE,
                font=("Segoe UI", 18, "bold"),
            )
            hero.create_text(
                x_text, 70,
                anchor="nw",
                text="KONAMI DIGITAL ENTERTAINMENT  ·  MOTOR GRÁFICO FOX ENGINE (VULKAN)",
                fill=ACCENT,
                font=("Segoe UI", 9, "bold"),
            )
            hero.create_text(
                x_text, 92,
                anchor="nw",
                text="Soporte de Carpeta Base + Parche Separado (DataPacks en vivo) sin fusionar archivos",
                fill=FG_MUTED,
                font=("Segoe UI", 9),
            )

        hero.bind("<Configure>", draw_hero)

        # Insignia de estado flotante en el Hero
        self.badge_lbl = tk.Label(
            hero,
            text="Detectando...",
            bg=BG_CARD_HI,
            fg=ACCENT,
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=6,
            highlightthickness=1,
            highlightbackground=BORDER_GOLD,
        )
        self.badge_lbl.place(relx=0.97, rely=0.25, anchor="ne")

        # --- CONTENEDOR DE PÁGINAS ---
        self.page_container = tk.Frame(right_area, bg=BG_MAIN, padx=24, pady=18)
        self.page_container.pack(fill="both", expand=True)

        self.build_page_home()
        self.build_page_graphics()
        self.build_page_audio()

        # --- FOOTER DE ACCIÓN ---
        footer = tk.Frame(right_area, bg=BG_SIDEBAR, height=78, highlightthickness=1, highlightbackground=BORDER_COLOR)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        left_foot = tk.Frame(footer, bg=BG_SIDEBAR)
        left_foot.pack(side="left", padx=22, pady=12)

        close_row = tk.Frame(left_foot, bg=BG_SIDEBAR)
        close_row.pack(anchor="w")
        self.var_close_on_launch = tk.BooleanVar(value=self.settings["close_on_launch"])
        ModernToggle(close_row, self.var_close_on_launch, bg=BG_SIDEBAR).pack(side="left", padx=(0, 8))
        tk.Label(
            close_row,
            text="Cerrar launcher automáticamente al abrir el juego",
            bg=BG_SIDEBAR,
            fg=FG_TEXT,
            font=("Segoe UI", 9),
        ).pack(side="left")

        self.lbl_status_bar = tk.Label(
            left_foot,
            text="Listo para jugar.",
            bg=BG_SIDEBAR,
            fg=FG_MUTED,
            font=("Segoe UI", 9),
        )
        self.lbl_status_bar.pack(anchor="w", pady=(4, 0))

        self.btn_play = tk.Button(
            footer,
            text="▶   JUGAR PES 2017",
            command=self.on_play_clicked,
            bg=ACCENT,
            fg="#090d14",
            activebackground=ACCENT_HOVER,
            activeforeground="#090d14",
            relief="flat",
            bd=0,
            font=("Segoe UI", 12, "bold"),
            padx=28,
            pady=12,
            cursor="hand2",
        )
        self.btn_play.pack(side="right", padx=(10, 22), pady=14)

        btn_save = tk.Button(
            footer,
            text="Guardar Ajustes",
            command=self.on_save_clicked,
            bg=BG_CARD,
            fg=FG_WHITE,
            activebackground=BG_CARD_HI,
            activeforeground=FG_WHITE,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=12,
            cursor="hand2",
        )
        btn_save.pack(side="right", padx=4, pady=14)

        self.switch_page("home")

    def create_card(self, parent, title: str, subtitle: str = "") -> tk.Frame:
        card = tk.Frame(parent, bg=BG_CARD, padx=18, pady=14, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 14))
        hdr = tk.Frame(card, bg=BG_CARD)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text=title, bg=BG_CARD, fg=ACCENT, font=("Segoe UI", 11, "bold")).pack(side="left")
        if subtitle:
            tk.Label(hdr, text=subtitle, bg=BG_CARD, fg=FG_MUTED, font=("Segoe UI", 9)).pack(side="right")
        return card

    def build_page_home(self):
        page = tk.Frame(self.page_container, bg=BG_MAIN)
        self.pages["home"] = page

        # Tarjeta 1: Carpetas del juego y parche
        c1 = self.create_card(
            page,
            "CARPETAS DEL JUEGO Y PARCHE",
            "Detección independiente sin mezclar ni sobrescribir archivos",
        )

        # Fila Juego Base
        tk.Label(c1, text="Carpeta del Juego Base (CUSA04957):", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        r_base = tk.Frame(c1, bg=BG_CARD)
        r_base.pack(fill="x", pady=(4, 10))
        self.var_game_dir = tk.StringVar(value=self.settings["game_dir"])
        ent_game = tk.Entry(
            r_base,
            textvariable=self.var_game_dir,
            bg=BG_INPUT,
            fg=FG_WHITE,
            insertbackground=FG_WHITE,
            relief="flat",
            font=("Consolas", 10),
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT,
        )
        ent_game.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        ent_game.bind("<FocusOut>", lambda _e: self.on_game_dir_changed())
        tk.Button(
            r_base,
            text="Examinar...",
            command=self.browse_game_dir,
            bg=BG_CARD_HI,
            fg=FG_WHITE,
            activebackground=ACCENT,
            activeforeground="#090d14",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=5,
            cursor="hand2",
        ).pack(side="right")

        # Fila Carpeta Patch
        tk.Label(c1, text="Carpeta de Actualización / Patch (CUSA04957-patch):", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        r_patch = tk.Frame(c1, bg=BG_CARD)
        r_patch.pack(fill="x", pady=(4, 6))
        self.var_patch_dir = tk.StringVar(value=self.settings["patch_dir"])
        ent_patch = tk.Entry(
            r_patch,
            textvariable=self.var_patch_dir,
            bg=BG_INPUT,
            fg=FG_WHITE,
            insertbackground=FG_WHITE,
            relief="flat",
            font=("Consolas", 10),
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT,
        )
        ent_patch.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        ent_patch.bind("<FocusOut>", lambda _e: self.refresh_detection())
        tk.Button(
            r_patch,
            text="Examinar...",
            command=self.browse_patch_dir,
            bg=BG_CARD_HI,
            fg=FG_WHITE,
            activebackground=ACCENT,
            activeforeground="#090d14",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=5,
            cursor="hand2",
        ).pack(side="right")

        # Tarjeta 2: Estado de activación del Patch y diagnóstico
        c2 = self.create_card(
            page,
            "ESTADO DE VERSIÓN Y DATAPACKS",
            "Puedes jugar con el juego base o activar el parche al vuelo",
        )

        toggle_row = tk.Frame(c2, bg=BG_CARD_HI, padx=14, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        toggle_row.pack(fill="x", pady=(0, 10))
        self.var_use_patch = tk.BooleanVar(value=self.settings["use_patch"])
        ModernToggle(toggle_row, self.var_use_patch, command=self.refresh_detection, bg=BG_CARD_HI).pack(side="left", padx=(0, 12))
        lbl_t = tk.Frame(toggle_row, bg=BG_CARD_HI)
        lbl_t.pack(side="left", fill="x")
        tk.Label(
            lbl_t,
            text="Cargar Parche y DataPacks (v01.07) en superposición virtual",
            bg=BG_CARD_HI,
            fg=FG_WHITE,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        tk.Label(
            lbl_t,
            text="Mantiene intactas las carpetas CUSA04957 y CUSA04957-patch por separado",
            bg=BG_CARD_HI,
            fg=FG_MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor="w")

        self.lbl_base_status = tk.Label(c2, text="", bg=BG_CARD, fg=GREEN_OK, font=("Segoe UI", 9, "bold"))
        self.lbl_base_status.pack(anchor="w", pady=(2, 2))

        self.lbl_patch_status = tk.Label(c2, text="", bg=BG_CARD, fg=ACCENT, font=("Segoe UI", 9))
        self.lbl_patch_status.pack(anchor="w", pady=(2, 0))

    def build_page_graphics(self):
        page = tk.Frame(self.page_container, bg=BG_MAIN)
        self.pages["gfx"] = page

        c1 = self.create_card(page, "PANTALLA Y RESOLUCIÓN", "Ajustes del renderizador Vulkan")
        g1 = tk.Frame(c1, bg=BG_CARD)
        g1.pack(fill="x")
        g1.columnconfigure(1, weight=1)
        g1.columnconfigure(3, weight=1)

        tk.Label(g1, text="Modo de pantalla:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 12))
        self.cb_display_mode = ttk.Combobox(g1, state="readonly", values=[v for _, v in DISPLAY_MODES])
        self.set_combo_by_key(self.cb_display_mode, DISPLAY_MODES, self.settings["display_mode"])
        self.cb_display_mode.grid(row=0, column=1, sticky="ew", pady=8, padx=(0, 20))

        tk.Label(g1, text="Resolución interna:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", pady=8, padx=(0, 12))
        self.cb_resolution = ttk.Combobox(g1, state="readonly", values=[v for _, v in RESOLUTIONS])
        self.set_combo_by_key(self.cb_resolution, RESOLUTIONS, self.settings["render_resolution"])
        self.cb_resolution.grid(row=0, column=3, sticky="ew", pady=8)

        tk.Label(g1, text="Límite de FPS:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 12))
        self.cb_fps = ttk.Combobox(g1, state="readonly", values=[v for _, v in FPS_LIMITS])
        self.set_combo_by_key(self.cb_fps, FPS_LIMITS, str(self.settings["fps_limit"]))
        self.cb_fps.grid(row=1, column=1, sticky="ew", pady=8, padx=(0, 20))

        tk.Label(g1, text="Filtro anisotrópico:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=1, column=2, sticky="w", pady=8, padx=(0, 12))
        self.cb_aniso = ttk.Combobox(g1, state="readonly", values=[v for _, v in ANISO_OPTIONS])
        self.set_combo_by_key(self.cb_aniso, ANISO_OPTIONS, str(self.settings["anisotropy"]))
        self.cb_aniso.grid(row=1, column=3, sticky="ew", pady=8)

        c2 = self.create_card(page, "ESCALADO, ANTIALIASING Y SINCRONIZACIÓN", "Suavizado de bordes y estabilidad de imagen")
        g2 = tk.Frame(c2, bg=BG_CARD)
        g2.pack(fill="x")
        g2.columnconfigure(1, weight=1)

        tk.Label(g2, text="Tecnología de suavizado / escalado:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=6, padx=(0, 14))
        self.cb_upscaler = ttk.Combobox(g2, state="readonly", values=[v for _, v in UPSCALERS])
        self.set_combo_by_key(self.cb_upscaler, UPSCALERS, self.settings["upscaler"])
        self.cb_upscaler.grid(row=0, column=1, sticky="ew", pady=6)

        toggles_frame = tk.Frame(c2, bg=BG_CARD)
        toggles_frame.pack(fill="x", pady=(12, 2))

        # Toggle VSync
        vs_box = tk.Frame(toggles_frame, bg=BG_CARD_HI, padx=14, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        vs_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.var_vsync = tk.BooleanVar(value=self.settings["vsync"])
        ModernToggle(vs_box, self.var_vsync, bg=BG_CARD_HI).pack(side="left", padx=(0, 10))
        tk.Label(vs_box, text="Sincronización Vertical (VSync)\nEvita cortes de imagen (tearing)", justify="left", bg=BG_CARD_HI, fg=FG_TEXT, font=("Segoe UI", 9)).pack(side="left")

        # Toggle FPS Overlay
        fps_box = tk.Frame(toggles_frame, bg=BG_CARD_HI, padx=14, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        fps_box.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.var_show_fps = tk.BooleanVar(value=self.settings["show_fps"])
        ModernToggle(fps_box, self.var_show_fps, bg=BG_CARD_HI).pack(side="left", padx=(0, 10))
        tk.Label(fps_box, text="Mostrar Overlay de Rendimiento\nFPS, Frametime y uso de GPU/VRAM", justify="left", bg=BG_CARD_HI, fg=FG_TEXT, font=("Segoe UI", 9)).pack(side="left")

    def build_page_audio(self):
        page = tk.Frame(self.page_container, bg=BG_MAIN)
        self.pages["aud"] = page

        c1 = self.create_card(page, "AUDIO E IDIOMA DEL JUEGO", "Configuración de sonido y región")
        g1 = tk.Frame(c1, bg=BG_CARD)
        g1.pack(fill="x")
        g1.columnconfigure(1, weight=1)
        g1.columnconfigure(3, weight=1)

        tk.Label(g1, text="Idioma predeterminado:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 12))
        self.cb_lang = ttk.Combobox(g1, state="readonly", values=[v for _, v in LANGUAGES])
        self.set_combo_by_key(self.cb_lang, LANGUAGES, str(self.settings["language"]))
        self.cb_lang.grid(row=0, column=1, sticky="ew", pady=8, padx=(0, 20))

        tk.Label(g1, text="Canales de salida:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", pady=8, padx=(0, 12))
        self.cb_audio = ttk.Combobox(g1, state="readonly", values=[v for _, v in AUDIO_CHANNELS])
        self.set_combo_by_key(self.cb_audio, AUDIO_CHANNELS, self.settings["audio_channels"])
        self.cb_audio.grid(row=0, column=3, sticky="ew", pady=8)

        tk.Label(g1, text="Volumen maestro (%):", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 12))
        self.var_volume = tk.IntVar(value=int(self.settings["master_volume"]))
        sc_vol = tk.Scale(
            g1,
            from_=0,
            to=200,
            orient="horizontal",
            variable=self.var_volume,
            bg=BG_CARD,
            fg=ACCENT,
            highlightthickness=0,
            troughcolor=BG_INPUT,
            activebackground=ACCENT_HOVER,
            font=("Segoe UI", 8, "bold"),
        )
        sc_vol.grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)

        c2 = self.create_card(page, "DATOS GUARDADOS (SAVEDATA)", "Ubicación de tus partidas, repeticiones y datos de edición")
        r_user = tk.Frame(c2, bg=BG_CARD)
        r_user.pack(fill="x", pady=4)
        self.var_user_dir = tk.StringVar(value=self.settings["user_dir"])
        ent_user = tk.Entry(
            r_user,
            textvariable=self.var_user_dir,
            bg=BG_INPUT,
            fg=FG_WHITE,
            insertbackground=FG_WHITE,
            relief="flat",
            font=("Consolas", 10),
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT,
        )
        ent_user.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        tk.Button(
            r_user,
            text="Abrir Carpeta",
            command=self.open_user_dir,
            bg=BG_CARD_HI,
            fg=FG_WHITE,
            activebackground=ACCENT,
            activeforeground="#090d14",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=5,
            cursor="hand2",
        ).pack(side="right")

    def switch_page(self, key: str):
        for k, p in self.pages.items():
            p.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(bg=BG_CARD_HI, fg=ACCENT)
            else:
                btn.configure(bg=BG_SIDEBAR, fg=FG_MUTED)

    def open_user_dir(self):
        p = Path(self.var_user_dir.get().strip() or str(OUT_DIR / "user"))
        p.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(p))

    @staticmethod
    def set_combo_by_key(combo: ttk.Combobox, pairs: list, key: str):
        for k, label in pairs:
            if k == key:
                combo.set(label)
                return
        if pairs:
            combo.set(pairs[0][1])

    @staticmethod
    def get_combo_key(combo: ttk.Combobox, pairs: list, default: str) -> str:
        val = combo.get()
        for k, label in pairs:
            if label == val:
                return k
        return default

    def browse_game_dir(self):
        chosen = filedialog.askdirectory(
            title="Selecciona la carpeta del juego base (donde está eboot.bin y sce_module)",
            initialdir=self.var_game_dir.get() or str(BASE_DIR),
        )
        if chosen:
            self.var_game_dir.set(chosen)
            self.on_game_dir_changed()

    def browse_patch_dir(self):
        chosen = filedialog.askdirectory(
            title="Selecciona la carpeta del Parche / Update (CUSA04957-patch)",
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
            title = sfo.get("TITLE", "Pro Evolution Soccer 2017")
            tid = sfo.get("TITLE_ID", "CUSA04957")
            ver = sfo.get("APP_VER", "01.00")
            self.lbl_base_status.configure(
                text=f"✔ Juego Base listo: {title} [{tid}] · Versión base v{ver}",
                fg=GREEN_OK,
            )
        else:
            self.lbl_base_status.configure(
                text="✖ Carpeta de juego base no válida (debe contener eboot.bin y sce_module/libc.prx)",
                fg=ERR_COLOR,
            )

        patch_ok = bool(patch_path and (patch_path / "eboot.bin").is_file())
        if patch_ok:
            psfo = read_sfo(patch_path / "sce_sys" / "param.sfo")
            pver = psfo.get("APP_VER", "01.07")
            cpks = read_dpfilelist(patch_path / "DpFileList.bin")
            cpk_info = f" · {len(cpks)} DataPacks ({', '.join(cpks)})" if cpks else ""
            if use_patch:
                self.lbl_patch_status.configure(
                    text=f"✔ Parche ACTIVO (sin fusionar): Actualización v{pver}{cpk_info}",
                    fg=ACCENT,
                )
            else:
                self.lbl_patch_status.configure(
                    text=f"ℹ Parche detectado (v{pver}), desactivado: se ejecutará la versión base v01.00.",
                    fg=FG_MUTED,
                )
        else:
            if self.var_patch_dir.get().strip():
                self.lbl_patch_status.configure(
                    text="⚠ La carpeta de parche indicada no contiene eboot.bin (se iniciará sin parche).",
                    fg=WARN_COLOR,
                )
            else:
                self.lbl_patch_status.configure(
                    text="ℹ Sin carpeta de parche externa seleccionada (modo juego base).",
                    fg=FG_MUTED,
                )

        if not base_ok:
            self.badge_lbl.configure(text="✖ FALTA CARPETA BASE", fg=ERR_COLOR)
            self.btn_play.configure(state="disabled")
        elif patch_ok and use_patch:
            psfo = read_sfo(patch_path / "sce_sys" / "param.sfo")
            pver = psfo.get("APP_VER", "01.07")
            self.badge_lbl.configure(text=f"●  LISTO · PATCH v{pver}", fg=ACCENT)
            self.btn_play.configure(state="normal")
        else:
            sfo = read_sfo(game_path / "sce_sys" / "param.sfo")
            ver = sfo.get("APP_VER", "01.00")
            self.badge_lbl.configure(text=f"●  LISTO · BASE v{ver}", fg=GREEN_OK)
            self.btn_play.configure(state="normal")

    def on_save_clicked(self):
        self.save_settings()
        self.lbl_status_bar.configure(text="✔ Ajustes guardados en pes2017.ini", fg=GREEN_OK)

    def ensure_boot_image(self, game_dir: Path, patch_dir: Path | None) -> Path:
        """
        Garantiza que exista el boot-linked.bin correspondiente al eboot activo (base o patch).
        """
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

        python_exe = str(MSYS2_BIN / "python3.exe") if (MSYS2_BIN / "python3.exe").is_file() else sys.executable
        cmd_prep = [python_exe, str(ENGINE_DIR / "scripts" / "prepare.py"), str(game_dir), "--out", str(OUT_DIR)]
        cmd_link = [python_exe, str(ENGINE_DIR / "scripts" / "link_modules.py"), str(game_dir), "--out", str(OUT_DIR)]
        if patch_dir and (patch_dir / "eboot.bin").is_file():
            cmd_prep += ["--patch-dir", str(patch_dir)]
            cmd_link += ["--patch-dir", str(patch_dir)]

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        subprocess.run(cmd_prep, check=True, cwd=str(ENGINE_DIR), creationflags=creation_flags)
        subprocess.run(cmd_link, check=True, cwd=str(ENGINE_DIR), creationflags=creation_flags)

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
            messagebox.showerror("Error", "No se encontró eboot.bin en la carpeta del juego base.")
            return

        patch_dir = Path(cfg["patch_dir"]) if (cfg["use_patch"] and cfg["patch_dir"]) else None
        if patch_dir and not (patch_dir / "eboot.bin").is_file():
            patch_dir = None

        self.btn_play.configure(state="disabled", text="Iniciando...")
        self.lbl_status_bar.configure(
            text="Preparando módulos de Pro Evolution Soccer 2017...",
            fg=ACCENT,
        )
        self.root.update_idletasks()

        def worker():
            try:
                boot_bin = self.ensure_boot_image(game_dir, patch_dir)
                content_bin = OUT_DIR / "content.bin"
                if not content_bin.is_file():
                    python_exe = str(MSYS2_BIN / "python3.exe") if (MSYS2_BIN / "python3.exe").is_file() else sys.executable
                    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    subprocess.run(
                        [python_exe, str(ENGINE_DIR / "scripts" / "content_profile.py"), str(game_dir), "--out", str(OUT_DIR)],
                        check=True,
                        cwd=str(ENGINE_DIR),
                        creationflags=creation_flags,
                    )

                env = os.environ.copy()
                if MSYS2_BIN.is_dir():
                    env["PATH"] = f"{MSYS2_BIN};{MSYS2_USR};{env.get('PATH', '')}"
                env["SPARTAN_CONFIG"] = str(INI_FILE)
                env["SPARTAN_PARTIAL_HEIGHT_VIEWS"] = "0"
                env["SPARTAN_DEFERRED_READBACK"] = "1"
                env["SPARTAN_STALE_READBACK"] = "1"
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
                    game_exe = OUT_DIR / "PES2017.exe"

                user_dir = Path(cfg["user_dir"])
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
                self.root.after(0, lambda: self.on_launch_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def on_launch_success(self):
        self.btn_play.configure(state="normal", text="▶   JUGAR PES 2017")
        self.lbl_status_bar.configure(text="✔ ¡Pro Evolution Soccer 2017 en ejecución!", fg=GREEN_OK)
        if self.var_close_on_launch.get():
            self.root.destroy()

    def on_launch_error(self, err_msg: str):
        self.btn_play.configure(state="normal", text="▶   JUGAR PES 2017")
        self.lbl_status_bar.configure(text=f"✖ Error al iniciar: {err_msg}", fg=ERR_COLOR)
        messagebox.showerror("Error al lanzar PES 2017", err_msg)


def main():
    root = tk.Tk()
    PES2017Launcher(root)
    root.mainloop()


if __name__ == "__main__":
    main()

"""PES 2017 interface switching, persistence and stable game settings.

Run with: python -m unittest discover -s tests -p test_pes2017_language.py
The widget tests require Tk and a desktop; no game files are needed.
"""
import ast
import json
from pathlib import Path
from string import Formatter
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import launcher_pes2017 as launcher
from pes2017_lang import ENGLISH, UI_LANGUAGES, translate


class TranslationTests(unittest.TestCase):
    def test_catalog_covers_every_marked_string_and_choice(self):
        tree = ast.parse((ROOT / "launcher_pes2017.py").read_text(encoding="utf-8"))
        marked = {node.args[0].value for node in ast.walk(tree)
                  if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "tr"
                  and node.args and isinstance(node.args[0], ast.Constant)}
        self.assertEqual(marked - ENGLISH.keys(), set())
        for pairs in (launcher.DISPLAY_MODES, launcher.UPSCALERS, launcher.FPS_LIMITS,
                      launcher.ANISO_OPTIONS, launcher.AUDIO_CHANNELS, launcher.LANGUAGES):
            for _key, label in pairs:
                self.assertIn(label, ENGLISH)

    def test_translation_format_fields_are_preserved(self):
        def fields(text):
            return sorted((name, spec, conversion) for _, name, spec, conversion
                          in Formatter().parse(text) if name is not None)
        for spanish, english in ENGLISH.items():
            with self.subTest(text=spanish):
                self.assertTrue(english)
                self.assertEqual(fields(spanish), fields(english))
                self.assertEqual(translate(spanish, "es"), spanish)
                self.assertEqual(translate(spanish, "en"), english)

    def test_unknown_languages_and_untranslated_technical_labels(self):
        self.assertEqual(translate("Vulkan 1.3", "en"), "Vulkan 1.3")
        self.assertEqual(translate("Menú", "unknown"), "Menú")

    def test_windows_release_includes_translation_module(self):
        package = (ROOT / "empaquetar_release.bat").read_text(encoding="utf-8")
        self.assertIn('copy /y "pes2017_lang.py" "%STAGE_DIR%\\"', package)


class LauncherLanguageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for name, value in {
            "SETTINGS_FILE": self.directory / "settings.json",
            "INI_FILE": self.directory / "pes2017.ini",
            "OUT_DIR": self.directory / "out",
            "auto_detect_folders": lambda: ("", ""),
        }.items():
            mock = patch.object(launcher, name, value)
            mock.start()
            self.addCleanup(mock.stop)
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Tk desktop unavailable: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = launcher.PES2017Launcher(self.root)
        self.root.update_idletasks()

    def switch_language(self, language):
        self.app.set_combo_by_key(self.app.cb_ui_lang, UI_LANGUAGES, language)
        self.app.cb_ui_lang.event_generate("<<ComboboxSelected>>")
        self.root.update()

    def test_old_and_invalid_settings_keep_spanish_default(self):
        for saved in ({"language": "1"}, {"ui_language": "fr"}, {"ui_language": None}, []):
            with self.subTest(saved=saved):
                launcher.SETTINGS_FILE.write_text(json.dumps(saved), encoding="utf-8")
                self.assertEqual(self.app.load_settings()["ui_language"], "es")
        launcher.SETTINGS_FILE.write_text("broken json", encoding="utf-8")
        self.assertEqual(self.app.load_settings()["ui_language"], "es")

    def test_switch_preserves_every_pending_setting_and_active_page(self):
        app = self.app
        choices = [("cb_display_mode", launcher.DISPLAY_MODES, "fullscreen"),
                   ("cb_resolution", launcher.RESOLUTIONS, "4K"),
                   ("cb_upscaler", launcher.UPSCALERS, "taa"),
                   ("cb_fps", launcher.FPS_LIMITS, "144"),
                   ("cb_aniso", launcher.ANISO_OPTIONS, "16"),
                   ("cb_audio", launcher.AUDIO_CHANNELS, "7.1"),
                   ("cb_lang", launcher.LANGUAGES, "16")]
        for attribute, pairs, key in choices:
            app.set_combo_by_key(getattr(app, attribute), pairs, key)
        for variable, value in [("var_game_dir", str(self.directory / "game")),
                                ("var_patch_dir", str(self.directory / "patch")),
                                ("var_user_dir", str(self.directory / "saves")),
                                ("var_volume", 135), ("var_vsync", False),
                                ("var_show_fps", True), ("var_use_patch", True),
                                ("var_close_on_launch", True)]:
            getattr(app, variable).set(value)
        expected = app.save_settings()
        app.switch_page("aud")
        for language in ("en", "es", "en"):
            self.switch_language(language)
            expected["ui_language"] = language
            self.assertEqual(app.ui_language, language)
            self.assertEqual(app.active_page, "aud")
            self.assertEqual(app.save_settings(), expected)
            self.assertEqual(app.load_settings(), expected)
            for attribute, pairs, key in choices:
                combo = getattr(app, attribute)
                self.assertEqual(app.get_combo_key(combo, pairs, ""), key)
                label = next(label for value, label in pairs if value == key)
                self.assertEqual(combo.get(), translate(label, language))
        ini = launcher.INI_FILE.read_text(encoding="utf-8")
        self.assertIn("upscaler=taa", ini)
        self.assertIn("audio_channels=7.1", ini)
        self.assertNotIn("ui_language", ini)

    def test_saved_english_is_used_on_fresh_start(self):
        self.switch_language("en")
        self.app.main_wrap.destroy()
        self.app = launcher.PES2017Launcher(self.root)
        self.assertEqual(self.app.ui_language, "en")
        self.assertEqual(self.app.cb_ui_lang.get(), "English")
        self.assertEqual(self.app.play_label, "▶   PLAY PES 2017")
        self.assertEqual(self.app.hero_badge_text, "BASE GAME MISSING")

    def test_english_widgets_and_canvas_contain_no_spanish_catalog_text(self):
        self.switch_language("en")
        def check(widget):
            if "text" in widget.keys():
                self.assertNotIn(str(widget.cget("text")), ENGLISH)
            if isinstance(widget, tk.Canvas):
                for item in widget.find_all():
                    if widget.type(item) == "text":
                        self.assertNotIn(widget.itemcget(item, "text"), ENGLISH)
            for child in widget.winfo_children():
                check(child)
        check(self.app.main_wrap)

    def test_dynamic_detection_and_dialogs_use_english(self):
        self.switch_language("en")
        game = self.directory / "game"
        (game / "sce_module").mkdir(parents=True)
        (game / "eboot.bin").touch()
        (game / "sce_module" / "libc.prx").touch()
        patch_dir = self.directory / "patch"
        patch_dir.mkdir()
        (patch_dir / "eboot.bin").touch()
        self.app.var_game_dir.set(str(game))
        self.app.var_patch_dir.set(str(patch_dir))
        self.app.var_use_patch.set(True)
        self.app.refresh_detection()
        self.assertIn("Base game ready", self.app.lbl_base_status.cget("text"))
        self.assertIn("Patch ACTIVE", self.app.lbl_patch_status.cget("text"))
        self.assertEqual(self.app.hero_badge_text, "v01.07 READY")
        self.app.var_use_patch.set(False)
        self.app.refresh_detection()
        self.assertIn("disabled", self.app.lbl_patch_status.cget("text"))
        self.app.var_game_dir.set("")
        with patch.object(launcher.messagebox, "showerror") as dialog:
            self.app.on_play_clicked()
        dialog.assert_called_once_with("Error", "eboot.bin was not found in the base game folder.")

    def test_switch_is_blocked_while_launching_and_reenabled_after_error(self):
        self.app.launch_in_progress = True
        self.switch_language("en")
        self.assertEqual(self.app.ui_language, "es")
        self.assertEqual(self.app.cb_ui_lang.get(), "Español")
        with patch.object(launcher.messagebox, "showerror"):
            self.app.on_launch_error("test")
        self.assertFalse(self.app.launch_in_progress)
        self.assertEqual(str(self.app.cb_ui_lang.cget("state")), "readonly")
        self.switch_language("en")
        self.assertEqual(self.app.ui_language, "en")


if __name__ == "__main__":
    unittest.main()

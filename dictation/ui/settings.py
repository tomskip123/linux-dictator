"""Settings window using Libadwaita."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from ..config import get_config, save_config
from ..transcriber import cuda_available, reload_model


class SettingsWindow(Adw.PreferencesWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Dictation Settings")
        self.set_default_size(500, 400)

        config = get_config()

        # Transcription page
        transcription_page = Adw.PreferencesPage()
        transcription_page.set_title("Transcription")
        transcription_page.set_icon_name("audio-input-microphone-symbolic")

        # Device group
        device_group = Adw.PreferencesGroup()
        device_group.set_title("Processing")
        device_group.set_description("Choose CPU or GPU for transcription")

        self.device_row = Adw.ComboRow()
        self.device_row.set_title("Device")
        self.device_row.set_subtitle("CUDA provides faster transcription" if cuda_available() else "CUDA not available")

        device_model = Gtk.StringList.new(["CPU", "CUDA"])
        self.device_row.set_model(device_model)
        self.device_row.set_selected(0 if config.device == "cpu" else 1)
        self.device_row.set_sensitive(cuda_available())
        self.device_row.connect("notify::selected", self._on_device_changed)
        device_group.add(self.device_row)

        # Model group
        model_group = Adw.PreferencesGroup()
        model_group.set_title("Model")
        model_group.set_description("Larger models are more accurate but slower")

        self.model_row = Adw.ComboRow()
        self.model_row.set_title("Model Size")

        models = ["tiny", "base", "small", "medium", "large-v3"]
        model_model = Gtk.StringList.new(models)
        self.model_row.set_model(model_model)
        self.model_row.set_selected(models.index(config.model))
        self.model_row.connect("notify::selected", self._on_model_changed)
        model_group.add(self.model_row)

        # Language
        self.language_row = Adw.EntryRow()
        self.language_row.set_title("Language")
        self.language_row.set_text(config.language)
        self.language_row.connect("changed", self._on_language_changed)
        model_group.add(self.language_row)

        transcription_page.add(device_group)
        transcription_page.add(model_group)

        # Hotkey page
        hotkey_page = Adw.PreferencesPage()
        hotkey_page.set_title("Hotkey")
        hotkey_page.set_icon_name("preferences-desktop-keyboard-symbolic")

        hotkey_group = Adw.PreferencesGroup()
        hotkey_group.set_title("Activation")

        self.mode_row = Adw.ComboRow()
        self.mode_row.set_title("Mode")
        self.mode_row.set_subtitle("How the hotkey activates dictation")
        mode_model = Gtk.StringList.new(["Hold to talk", "Toggle"])
        self.mode_row.set_model(mode_model)
        self.mode_row.set_selected(0 if config.mode == "hold" else 1)
        self.mode_row.connect("notify::selected", self._on_mode_changed)
        hotkey_group.add(self.mode_row)

        hotkey_display = Adw.ActionRow()
        hotkey_display.set_title("Current Hotkey")
        hotkey_display.set_subtitle(" + ".join(config.hotkey))
        hotkey_group.add(hotkey_display)

        hotkey_page.add(hotkey_group)

        self.add(transcription_page)
        self.add(hotkey_page)

    def _on_device_changed(self, row, _) -> None:
        config = get_config()
        config.device = "cpu" if row.get_selected() == 0 else "cuda"
        save_config()
        reload_model()

    def _on_model_changed(self, row, _) -> None:
        config = get_config()
        models = ["tiny", "base", "small", "medium", "large-v3"]
        config.model = models[row.get_selected()]
        save_config()
        reload_model()

    def _on_language_changed(self, row) -> None:
        config = get_config()
        config.language = row.get_text() or "auto"
        save_config()

    def _on_mode_changed(self, row, _) -> None:
        config = get_config()
        config.mode = "hold" if row.get_selected() == 0 else "toggle"
        save_config()

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import mainthread
import threading

import settings_store as store
import voiceprint_engine as voiceprint
from llm_client import ClaudeMandyClient
from voice_engine import VoiceEngine

ENROLLMENT_SAMPLES_NEEDED = 3


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        outer = BoxLayout(orientation="vertical", padding=16, spacing=10)

        back_btn = Button(text="< Back", size_hint=(1, None), height=44, font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        outer.add_widget(back_btn)

        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None, padding=(0, 4))
        content.bind(minimum_height=content.setter("height"))

        def add_label(text, font_size="13sp"):
            lbl = Label(text=text, font_size=font_size, size_hint_y=None, height=30)
            content.add_widget(lbl)

        content.add_widget(Label(text="Settings", font_size="24sp",
                                  size_hint_y=None, height=40))

        add_label("Your name (Mandy will address you by this)")
        self.name_input = TextInput(text=store.get("user_name"), size_hint_y=None,
                                     height=44, multiline=False)
        content.add_widget(self.name_input)

        add_label("Wake phrase (in addition to \"Hi Mandy\" / \"Hey Mandy\", which always work)")
        self.wake_input = TextInput(text=store.get("wake_phrase"), size_hint_y=None,
                                     height=44, multiline=False)
        content.add_widget(self.wake_input)

        add_label("Voice personality")
        self.voice_spinner = Spinner(
            text=store.get("voice_personality"),
            values=["Warm & friendly", "Professional & clear",
                    "Soft & empathetic", "Strong & confident"],
            size_hint_y=None, height=44,
        )
        content.add_widget(self.voice_spinner)

        add_label(
            "Insurer app package name (e.g. com.acko.android) -- lets the "
            "Documents screen open it directly. Find it in your insurer app's "
            "Play Store URL.",
            font_size="12sp",
        )
        self.insurer_input = TextInput(text=store.get("insurer_app_package"),
                                        size_hint_y=None, height=44, multiline=False)
        content.add_widget(self.insurer_input)

        # ---- Voice recognition / enrollment ----
        content.add_widget(Label(
            text="Voice Recognition",
            font_size="18sp", size_hint_y=None, height=36))
        add_label(
            "Train Mandy on a few samples of your voice so she only acts on "
            "commands that sound like you. This is a lightweight on-device "
            "check (pitch/energy/rhythm), not bank-grade security -- it "
            "filters out clearly different voices, not a perfect impression.",
            font_size="12sp",
        )

        self.enroll_status_label = Label(
            text=self._enrollment_status_text(),
            font_size="13sp", size_hint_y=None, height=30,
        )
        content.add_widget(self.enroll_status_label)

        enroll_row = BoxLayout(size_hint_y=None, height=50, spacing=8)
        self.enroll_btn = Button(text="Train Mandy on my voice",
                                  background_color=(0.2, 0.55, 0.85, 1))
        self.enroll_btn.bind(on_press=self._start_enrollment)
        clear_btn = Button(text="Clear voiceprint",
                            background_color=(0.5, 0.2, 0.2, 1))
        clear_btn.bind(on_press=self._clear_voiceprint)
        enroll_row.add_widget(self.enroll_btn)
        enroll_row.add_widget(clear_btn)
        content.add_widget(enroll_row)

        # ---- AI backend ----
        add_label(
            "Conversational AI API key (optional - enables real open-ended "
            "conversation instead of built-in responses)",
            font_size="12sp",
        )
        self.api_key_input = TextInput(text=store.get("api_key"), size_hint_y=None,
                                        height=44, multiline=False, password=True)
        content.add_widget(self.api_key_input)

        save_btn = Button(text="Save Settings", font_size="18sp", size_hint_y=None,
                           height=50, background_color=(0.2, 0.6, 0.3, 1))
        save_btn.bind(on_press=self._save)
        content.add_widget(save_btn)

        self.status_label = Label(text="", font_size="13sp", size_hint_y=None, height=30)
        content.add_widget(self.status_label)

        scroll.add_widget(content)
        outer.add_widget(scroll)
        self.add_widget(outer)

        self._enroll_engine = None
        self._enroll_samples = []

    def _enrollment_status_text(self):
        return ("Voiceprint: trained" if voiceprint.has_enrolled_profile()
                else "Voiceprint: not trained yet")

    # ---------------- Enrollment flow ----------------

    def _start_enrollment(self, *_):
        self._enroll_samples = []
        self.enroll_btn.disabled = True
        self._enroll_engine = VoiceEngine(
            on_result=self._on_enroll_sample,
            on_error=self._on_enroll_error,
        )
        self._prompt_next_sample()

    def _prompt_next_sample(self):
        sample_num = len(self._enroll_samples) + 1
        self.enroll_status_label.text = (
            f"Say a natural sentence out loud ({sample_num}/{ENROLLMENT_SAMPLES_NEEDED})..."
        )
        threading.Thread(target=self._enroll_engine.listen_once, daemon=True).start()

    @mainthread
    def _on_enroll_sample(self, text, raw_audio):
        features = voiceprint.extract_features(raw_audio)
        if features is None:
            self.enroll_status_label.text = "Couldn't analyze that -- try again, a bit louder."
            threading.Thread(target=self._enroll_engine.listen_once, daemon=True).start()
            return

        self._enroll_samples.append(features)

        if len(self._enroll_samples) >= ENROLLMENT_SAMPLES_NEEDED:
            success = voiceprint.enroll(self._enroll_samples)
            self.enroll_btn.disabled = False
            self.enroll_status_label.text = (
                self._enrollment_status_text() if success
                else "Enrollment failed -- please try again."
            )
        else:
            self._prompt_next_sample()

    @mainthread
    def _on_enroll_error(self, message):
        self.enroll_status_label.text = f"Didn't catch that ({message}). Try again."
        threading.Thread(target=self._enroll_engine.listen_once, daemon=True).start()

    def _clear_voiceprint(self, *_):
        voiceprint.clear_profile()
        self.enroll_status_label.text = self._enrollment_status_text()

    # ---------------- General settings save ----------------

    def _save(self, *_):
        store.set("user_name", self.name_input.text.strip() or "there")
        store.set("wake_phrase", self.wake_input.text.strip())
        store.set("voice_personality", self.voice_spinner.text)
        store.set("api_key", self.api_key_input.text.strip())
        store.set("insurer_app_package", self.insurer_input.text.strip())

        home_screen = self.manager.get_screen("home")
        api_key = self.api_key_input.text.strip()
        home_screen.conversation.user_name = self.name_input.text.strip() or "there"
        if api_key:
            home_screen.conversation.llm_client = ClaudeMandyClient(api_key)
        else:
            home_screen.conversation.llm_client = None

        self.status_label.text = "Saved."

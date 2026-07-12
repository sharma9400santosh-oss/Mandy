"""
Dashboard screen: multifunction speedometer (real GPS speed), RPM gauge
(real, needs OBD-II adapter), toll plaza alerts, and speed-limit warnings.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import mainthread, Clock

from widgets import Gauge
from gps_speed import SpeedTracker
from obd_reader import OBDReader
from toll_engine import TollEngine
from speed_limit_tracker import SpeedLimitTracker


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.speed_tracker = SpeedTracker(
            on_speed_update=self._update_speed,
            on_location_update=self._on_location_update,
        )
        self.obd_reader = OBDReader(
            on_rpm_update=self._update_rpm, on_status_change=self._update_obd_status
        )
        self.toll_engine = TollEngine(on_toll_approaching=self._on_toll_approaching)
        self.speed_limit_tracker = SpeedLimitTracker(
            on_limit_update=self._on_limit_update,
            on_over_limit=self._on_over_limit,
        )
        self._started = False
        self._last_speed = 0.0

        root = BoxLayout(orientation="vertical", padding=16, spacing=10)

        back_btn = Button(text="< Back", size_hint=(1, 0.08), font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back_btn)

        gauges_row = BoxLayout(size_hint=(1, 0.55), spacing=16)
        self.speed_gauge = Gauge(max_value=200, unit="km/h", accent=(0.2, 0.8, 0.5, 1))
        self.rpm_gauge = Gauge(max_value=8000, unit="RPM", accent=(0.9, 0.5, 0.2, 1))
        gauges_row.add_widget(self.speed_gauge)
        gauges_row.add_widget(self.rpm_gauge)
        root.add_widget(gauges_row)

        self.obd_status_label = Label(
            text="RPM: connect an OBD-II Bluetooth adapter for real data",
            font_size="12sp", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.08),
        )
        root.add_widget(self.obd_status_label)

        self.speed_limit_label = Label(
            text="Speed limit: --",
            font_size="15sp", color=(0.8, 0.8, 0.8, 1), size_hint=(1, 0.1),
        )
        root.add_widget(self.speed_limit_label)

        self.toll_banner = Label(
            text="No toll nearby",
            font_size="14sp", color=(0.6, 0.6, 0.6, 1), size_hint=(1, 0.1),
        )
        root.add_widget(self.toll_banner)

        self.add_widget(root)

    def on_enter(self, *_):
        if not self._started:
            self.speed_tracker.start()
            self.obd_reader.connect()
            self._started = True

    @mainthread
    def _update_speed(self, speed_kmh):
        self._last_speed = speed_kmh
        self.speed_gauge.set_value(speed_kmh)

    @mainthread
    def _update_rpm(self, rpm):
        self.rpm_gauge.set_value(rpm)

    @mainthread
    def _update_obd_status(self, status_text):
        self.obd_status_label.text = f"OBD: {status_text}"

    def _on_location_update(self, lat, lon, speed_kmh):
        self.toll_engine.update_location(lat, lon)
        self.speed_limit_tracker.update(lat, lon, speed_kmh)

    @mainthread
    def _on_toll_approaching(self, name, price, vehicle_class):
        if price is not None:
            self.toll_banner.text = f"Toll ahead: {name} -- approx Rs {price} ({vehicle_class})"
        else:
            self.toll_banner.text = f"Toll ahead: {name} -- price not set in database"
        self.toll_banner.color = (0.95, 0.75, 0.25, 1)
        Clock.schedule_once(lambda dt: self._reset_toll_banner(), 15)

    def _reset_toll_banner(self):
        self.toll_banner.text = "No toll nearby"
        self.toll_banner.color = (0.6, 0.6, 0.6, 1)

    @mainthread
    def _on_limit_update(self, limit_kmh):
        if limit_kmh:
            self.speed_limit_label.text = f"Speed limit: {limit_kmh} km/h"
            self.speed_limit_label.color = (0.8, 0.8, 0.8, 1)
        else:
            self.speed_limit_label.text = "Speed limit: not tagged for this road"
            self.speed_limit_label.color = (0.6, 0.6, 0.6, 1)

    @mainthread
    def _on_over_limit(self, current_kmh, limit_kmh):
        self.speed_limit_label.text = (
            f"Over limit! {current_kmh:.0f} km/h in a {limit_kmh} km/h zone"
        )
        self.speed_limit_label.color = (0.95, 0.3, 0.3, 1)

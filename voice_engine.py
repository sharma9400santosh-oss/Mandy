"""
OBD-II reader: real RPM (and other engine data) via a Bluetooth ELM327
adapter plugged into your car's OBD-II port.

REQUIRES HARDWARE: a ~$10-15 Bluetooth ELM327 dongle. Without one
plugged in, this cannot show real RPM -- there is no way around that;
regular car Bluetooth (the audio/hands-free kind) does not expose
engine data, only the OBD-II port does.

Protocol summary: ELM327 acts as a classic Bluetooth SPP (serial) device.
We send AT commands to initialize it, then send OBD PID requests like
"010C" (engine RPM) and parse the hex response.
"""

from kivy.utils import platform
from kivy.clock import Clock

RPM_PID = "010C"
SPEED_PID = "010D"  # (backup/cross-check vs GPS speed)


class OBDReader:
    def __init__(self, on_rpm_update, on_status_change):
        self.on_rpm_update = on_rpm_update
        self.on_status_change = on_status_change
        self._socket = None
        self._connected = False

    def connect(self, device_name_hint="OBD"):
        if platform != "android":
            self.on_status_change("OBD only available on Android device")
            self._simulate()
            return

        try:
            from jnius import autoclass
            import uuid as uuid_lib

            BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
            UUID = autoclass("java.util.UUID")

            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter is None or not adapter.isEnabled():
                self.on_status_change("Bluetooth not available/enabled")
                return

            paired = adapter.getBondedDevices().toArray()
            target = None
            for device in paired:
                name = (device.getName() or "").lower()
                if "obd" in name or "elm" in name:
                    target = device
                    break

            if target is None:
                self.on_status_change(
                    "No paired OBD adapter found. Pair your ELM327 dongle first."
                )
                return

            spp_uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
            self._socket = target.createRfcommSocketToServiceRecord(spp_uuid)
            self._socket.connect()
            self._connected = True
            self.on_status_change(f"connected to {target.getName()}")

            self._send_at("ATZ")   # reset
            self._send_at("ATE0")  # echo off
            self._send_at("ATSP0")  # auto protocol

            Clock.schedule_interval(self._poll_rpm, 0.5)

        except Exception as exc:  # noqa: BLE001
            self.on_status_change(f"OBD connection failed: {exc}")

    def _send_at(self, command):
        if not self._socket:
            return None
        try:
            out = self._socket.getOutputStream()
            out.write((command + "\r").encode())
            out.flush()
        except Exception as exc:  # noqa: BLE001
            print(f"OBD command failed: {exc}")

    def _poll_rpm(self, dt):
        if not self._connected:
            return False
        try:
            out = self._socket.getOutputStream()
            out.write((RPM_PID + "\r").encode())
            out.flush()

            inp = self._socket.getInputStream()
            buffer = bytearray()
            while True:
                b = inp.read()
                if b in (-1, 0x3E):  # '>' prompt marks end of response
                    break
                buffer.append(b)

            response = bytes(buffer).decode(errors="ignore")
            rpm = self._parse_rpm(response)
            if rpm is not None:
                self.on_rpm_update(rpm)
        except Exception as exc:  # noqa: BLE001
            print(f"OBD poll failed: {exc}")
        return True

    @staticmethod
    def _parse_rpm(response: str):
        # Expected reply looks like: "41 0C 1A F8" -> RPM = ((A*256)+B)/4
        hex_bytes = [b for b in response.replace("\r", " ").split(" ") if b]
        try:
            idx = hex_bytes.index("0C")
            a = int(hex_bytes[idx + 1], 16)
            b = int(hex_bytes[idx + 2], 16)
            return int(((a * 256) + b) / 4)
        except (ValueError, IndexError):
            return None

    def _simulate(self):
        """Desktop dev fallback so the gauge UI can be built/tested
        without a car or OBD adapter."""
        import random

        self._sim_rpm = 800

        def tick(dt):
            self._sim_rpm = max(700, min(6000, self._sim_rpm + random.uniform(-150, 180)))
            self.on_rpm_update(int(self._sim_rpm))

        Clock.schedule_interval(tick, 0.5)

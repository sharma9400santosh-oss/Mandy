# Mandy

A voice-controlled car AI assistant, built in Python with Kivy. Mandy has
a face, listens to you, talks back with emotion-adjusted tone, and can
navigate, call people, play music, and show live vehicle gauges.

## Features

| Feature | Status | Notes |
|---|---|---|
| Mandy's face + animated glow | Working | Uses your uploaded avatar image, glow color/pulse reflects her state |
| Voice input | Working | Native Android speech recognition, no API key |
| Wake word ("Hi Mandy" / "Hey Mandy") | Working | Toggle in Home screen; always-listening, uses more battery than tap-to-speak |
| Voice recognition (voiceprint) | Working, approximate | Only acts on commands that sound like your enrolled voice -- see limitation below |
| Talk-back voice output | Working | Android TTS, pitch/rate shift based on detected emotion |
| Navigation | Working | Hands off to Google Maps for real turn-by-turn |
| Phone calls | Working | Calls by contact name (looked up from your phone) or number |
| Spotify / YouTube / Radio | Working | Opens the real apps / streams |
| Speedometer | Working | Real GPS speed, works in any car |
| RPM gauge | Needs hardware | Real data, but only with a Bluetooth OBD-II adapter |
| Speed limit tracker | Working, needs internet | Looks up posted limits via OpenStreetMap, flags when you're over |
| Toll plaza alerts | Working, example data | Geofenced alerts + price; bundled database is a placeholder, see below |
| File explorer | Working | Browse and open files on your phone |
| Vehicle documents tracker | Working, manual entry | Insurance/PUC/Registration/DL expiry tracking -- see limitation below |
| RajmargYatra / mParivahan / insurer app launchers | Working | Opens the real apps; can't read their data |
| Settings (name, wake phrase, voice style, AI key, insurer app) | Working | Persisted on-device |
| Open-ended conversation with real reasoning | Optional | Off by default; add an API key in Settings |
| Route options with live ETA comparisons | Not built | Would need Google Directions API (paid at scale) -- next phase candidate |

## Honest limitations (read before you expect more than this delivers)

- **Emotional voice**: Android's TTS engine has no real "sound sad" or
  "sound excited" control. What this app does is shift pitch and speaking
  rate based on detected emotion, which reads as *more expressive* than
  flat, but it is not actorly emotional speech. For that you'd eventually
  want a cloud TTS with emotion styles (ElevenLabs, Azure Neural voices) —
  there's a marked swap-in point in `tts_engine.py`.
- **RPM**: there is no way to get real engine RPM without a physical
  Bluetooth OBD-II adapter (~$10-15 ELM327 dongle) plugged into your
  car's OBD-II port. Regular car Bluetooth (the audio/hands-free kind)
  does not expose this data. Without the dongle, the RPM gauge has
  nothing to show.
- **Radio**: phones generally don't expose the FM radio chip without
  carrier-specific support, so this streams internet radio instead of
  broadcast FM. Swap in your own station URLs in `media_manager.py`.
- **Spotify/YouTube control**: these hand off to the real apps rather
  than reimplementing playback — the reliable way to do this without
  needing OAuth app registrations with Spotify/Google. Deeper in-app
  control (skip track without leaving Mandy) is a further phase.
- **Open-ended conversation**: without an API key in Settings, Mandy
  responds using a small set of built-in, honest responses — she will
  tell you she's not able to reason about something rather than fake it.
  Add a Claude API key in Settings and she'll use it for real.
- **Dashboard display (showing up on your car's built-in screen)**: not
  built yet — this currently runs on your phone's screen only. That
  needs Android Auto integration, a separate project phase.
- **Voiceprint ("recognize my voice")**: this compares pitch and speech
  rhythm between your enrolled voice and each command -- not a trained
  neural speaker-recognition model. It will reliably reject clearly
  different voices, but it is not bank-grade security and could in
  theory be fooled by a good impression. Enroll your voice in
  Settings → "Train Mandy on my voice."
- **Vehicle documents (Insurance/PUC/Registration/DL)**: entirely
  self-reported. There is no public API for a third-party app to check
  Vahan/Sarathi/mParivahan records, so this only tracks the dates you
  type in -- it cannot confirm your actual government records are
  correct or current.
- **RajmargYatra / mParivahan / insurer app**: these buttons only
  *launch* the real apps (or their Play Store page if not installed).
  None of them offer a public API, so Mandy can't pull data out of them
  or verify anything they show.
- **Toll alerts**: `assets/toll_database.json` ships with two clearly
  labeled EXAMPLE entries (fake prices, arbitrary coordinates) — not
  real, current toll data. Replace them with real toll plazas along
  your routes (name, lat/lon, radius, price per vehicle class) from
  NHAI's official FASTag toll list for this to be trustworthy. The
  detection engine itself (geofencing + cooldown) is fully real and
  tested.
- **Speed limit tracker**: uses OpenStreetMap's crowd-sourced `maxspeed`
  tags via the free Overpass API. Coverage is incomplete, especially
  off major highways — no warning shown doesn't mean you're within a
  legal limit, it may just mean the road isn't tagged. Needs internet.

## Project structure

```
Mandy/
├── main.py                    # App entry point, screen manager
├── screens/
│   ├── home_screen.py          # Mandy's face + voice interaction
│   ├── dashboard_screen.py     # Speedometer, RPM, toll alerts, speed limit
│   ├── media_screen.py         # Spotify / YouTube / Radio
│   ├── calls_screen.py         # Phone calling
│   ├── navigate_screen.py      # Manual destination entry
│   ├── documents_screen.py     # Vehicle number + document expiry tracker
│   ├── file_explorer_screen.py # Browse device storage
│   └── settings_screen.py      # Name, wake phrase, voice, AI key, insurer app
├── mandy_avatar.py             # Animated face widget
├── voice_engine.py             # Speech-to-text + raw audio capture
├── voiceprint_engine.py        # Lightweight speaker verification
├── wake_word_engine.py         # "Hi Mandy" / "Hey Mandy" always-listening
├── tts_engine.py                # Text-to-speech with emotion shift
├── conversation_engine.py       # Intent parsing + emotion detection
├── llm_client.py                 # Optional real AI backend (Claude API)
├── navigation.py                # Destination parsing + Maps launch
├── call_manager.py              # Phone calls + contact lookup
├── media_manager.py             # Spotify/YouTube/Radio launching
├── gps_speed.py                  # Real GPS speed + location tracking
├── obd_reader.py                 # Real RPM via OBD-II Bluetooth adapter
├── toll_engine.py                 # Toll plaza geofencing + price lookup
├── speed_limit_tracker.py         # Posted speed limit via OpenStreetMap
├── vehicle_documents.py            # Insurance/PUC/Registration/DL tracking
├── external_apps.py                # RajmargYatra/mParivahan/insurer launcher
├── bluetooth_manager.py          # General Bluetooth pairing/connection
├── widgets.py                    # Reusable circular gauge widget
├── settings_store.py             # Persistent on-device settings
├── buildozer.spec                # Android packaging config
├── requirements-desktop.txt      # For testing on your computer first
└── assets/
    ├── mandy_face.png            # Her face
    ├── icon.png                  # App icon
    └── toll_database.json        # EXAMPLE toll data -- replace with real data
```

## Step 1 — Test on your computer first (recommended)

```bash
pip install -r requirements-desktop.txt
python main.py
```

On desktop: GPS speed and RPM are simulated with fake fluctuating values
so you can see the gauges move without a phone or OBD adapter. Voice
uses your computer's mic; navigation opens in your browser; calls/Spotify/
YouTube just print what they *would* do, since there's no Android to
hand off to.

## Step 2 — Build the real Android APK

Must be done on Linux or WSL2 (Buildozer doesn't support Windows/macOS
directly).

```bash
# One-time setup
sudo apt update
sudo apt install -y python3-pip build-essential git python3 python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev

pip3 install --break-system-packages buildozer cython

cd Mandy
buildozer -v android debug
```

First build downloads the Android SDK/NDK automatically (30-60 min).
APK will be at:

```
bin/mandy-0.1-arm64-v8a-debug.apk
```

Install with `adb install bin/*.apk` (phone plugged in) or copy the file
to your phone and allow "install from unknown sources."

## Step 3 — First run on your phone

1. Grant microphone, Bluetooth, location, phone, and contacts permissions
   when prompted.
2. Go to Settings in the app: set your name, pick a wake phrase (not yet
   wired to always-listening — see Next phases), choose a voice
   personality label, and optionally add an AI API key for real
   conversation.
3. Pair your car's Bluetooth as usual, and if you have one, pair your
   OBD-II Bluetooth adapter too.
4. Mount your phone, open Mandy, tap "Talk to Mandy," and try:
   - *"Navigate to [destination]"*
   - *"Call [contact name]"*
   - *"Play [song] on Spotify"*
   - *"Open YouTube"*
   - *"Open radio"*
   - *"I'm exhausted today"* (she'll respond with a calmer, supportive tone)

## Next phases (recommended order)

1. **Always-listening wake word** ("Mandy, I need you") instead of
   tap-to-speak — needs an offline wake-word engine (e.g. Porcupine)
   running as a background service.
2. **Cloud emotional TTS** (ElevenLabs/Azure) for genuinely expressive
   speech instead of pitch/rate approximation.
3. **Android Auto integration** so Mandy shows up on your car's own
   screen, not just your phone.
4. **Deeper Spotify control** via the Spotify Web API (needs your own
   app registration with Spotify) for in-app playback control.

Tell me which one you want next and I'll build it in.

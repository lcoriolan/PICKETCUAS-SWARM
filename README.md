# PICKET ACOUSTINT — Acoustic Detection Plugin for ATAK

PICKET ACOUSTINT turns an Android phone running ATAK into an acoustic sensing node.
It captures audio on-device, runs all signal processing on the phone (no cloud), and
gives the operator a live acoustic bearing cue and a 7-class sound classification
(background, drone, aircraft, vehicle, voice, gunfire, explosion) directly on the
ATAK map. When paired with a PICKET Fusion server it also ships event clips and
telemetry over mutual-TLS WebSocket for multi-node correlation.

Glossary: **ATAK** = Android Team Awareness Kit (the DoD-released situational
awareness app). **DF** = direction finding (estimating which way a sound came from).
**C-UAS** = counter-unmanned-aircraft systems. **EUD** = end user device (the phone).

## What it does

- **On-device classification**: a compact on-device model classifies what the phone
  hears into 7 classes and shows an advisory "edge vote" with per-class confidence.
- **On-device direction finding**: on phones that expose two direct microphone
  channels, the plugin produces a live acoustic bearing cue, rendered as a bearing
  fan in the ACOUSTINT BUBBLE panel (six selectable cue styles).
- **Honest by design**: when there is no fresh bearing the cue says
  "NO FRESH BEARING" instead of holding a stale one; front/back ambiguous bearings
  render the rear lobe dimmed; an uncalibrated array widens the displayed cone.
- **Onset detection**: impulsive sounds are precisely time-stamped to support
  multi-node correlation on the server side.
- **Fusion uplink (optional)**: mono PCM clips + JSON telemetry over `wss://` using
  ATAK's own enrolled mTLS credentials; no separate certificate store.
- **Measurement-grade capture**: the plugin disables the phone's voice-call audio
  processing (gain control, noise suppression, echo cancellation) so the signal
  chain stays faithful to what the microphones actually heard.

## Supported ATAK versions

| Release asset | ATAK host |
|---|---|
| `...-ATAK551-TPC-SIGNED.apk` | ATAK-CIV 5.5.1.x |
| ATAK-CIV 5.6.0 build | coming; will be added to the v1.0.0 release |

The APK is signed by the TAK Product Center **third-party signing service**; ATAK
displays the third-party-signed indicator for such plugins.

## Install

1. Download the APK for your ATAK version from the [Releases page](https://github.com/lcoriolan/PICKETCUAS-SWARM/releases).
2. Transfer it to the EUD (any normal file transfer) and install it; approve
   Android's install prompt. No ADB required.
3. Start ATAK; approve the plugin when ATAK lists it. Open the **PICKET** tool.
4. Grant the microphone permission and press **START MIC**. Android's microphone
   foreground indicator must stay visible while capture runs.
5. (Optional, for fusion) Replace the example endpoint with your `wss://` Fusion
   address; it persists across restarts.

## Known limitations (read before relying on it)

- **Two-microphone bearing is a cue, not a fire-control solution.** A 2-mic
  baseline has inherent front/back ambiguity; the UI shows it honestly rather than
  hiding it.
- **Bearing quality depends on the phone.** Phones that expose only one direct mic
  channel get classification and onset detection but no local bearing.
- **The edge vote is advisory.** Classification confidence is displayed so an
  operator can weigh it; it is not an autonomous alarm, and any
  protection-bubble breach decision requires the server-side gate, not the phone.
- **A reboot requires the operator to press START MIC again** (deliberate: capture
  never self-starts on boot).
- Full multi-node capability (correlation, localization) requires a PICKET Fusion
  server; standalone phones get the local cue and classification only.

## Legal / usage

ATAK-CIV is a U.S. Government product released open source and classified EAR99.
Use of this plugin must comply with your organization's authority to operate and
all applicable laws on audio capture in your jurisdiction. This plugin performs
passive acoustic sensing only; it commands no effectors.

License: not yet finalized; the released APK is free to download and use, all other rights reserved for now.

## Contact

Bug reports and device-compatibility reports (which phones give you a bearing) via GitHub Issues.

# PICKET SWARM: Distributed Acoustic Detection Plugin for ATAK

PICKET SWARM turns an Android phone running ATAK into an acoustic sensing node, and
turns a handful of those phones into one distributed microphone array.
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
  fan in the PICKET SWARM bubble panel (six selectable cue styles).
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
- **Live spectrogram (SPECTRO)**: a real-time waterfall so you can see a source's
  tonal signature, with SUPER LISTEN controls to tune and zoom a frequency band.
- **DUAL view**: a full-screen, side-by-side spectrogram and DF bubble, the primary
  "watch it work" operating screen.
- **Boresight calibration (CALIBRATE)**: face a known source, hold about five seconds,
  and the plugin learns a persisted bearing offset that corrects the local array.
- **Pairs with PICKET SNOOPY**: while streaming, SWARM tells the RF plugin to ease its
  radios ("gentle mode") so the acoustic clock stays in sync, and hands SNOOPY its
  acoustic drone detections so they can be cross-checked against Remote ID.

## Distributed acoustic array (what SWARM is for)

A single phone gives you classification and a bearing. The point of PICKET SWARM is
what happens with **several** phones: each one is a node in a distributed acoustic
array. Every node contributes its own time-stamped onsets and bearing to a shared
PICKET server, which cross-fixes those independent per-phone bearings into a single
located contact on the ATAK map. More phones spread over more ground means a wider
synthetic aperture and a better fix. It is a synthetic-aperture microphone array built
from the phones an operator already carries, instead of one fixed sensor mast.

- **Free (this repo)**: a report-level array. Independent per-phone bearings are
  crossed (triangulated) on the open reference server to localize the source.
- **Production PICKET**: a coherent, sensor-level array. Devices are combined into one
  array for materially better localization accuracy and reliability.

## Supported ATAK versions

| Release asset | ATAK host |
|---|---|
| `PICKETCUAS-SWARM-2.0.0-ATAK5.5.1.apk` | ATAK-CIV 5.5.1.x |
| `PICKETCUAS-SWARM-2.0.0-ATAK5.8.apk` | ATAK-CIV 5.8.x |

Same plugin, same version: install the APK that matches your ATAK host (a plugin's
API level must match the ATAK it runs on).

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

## Free version vs. production

This is the **free version**, and it is genuinely useful on its own: on-device
classification, a live acoustic bearing, and, with the open reference server, multi-device
cross-fixing on a map. It's free for noncommercial use, and it's meant to be used. The
production PICKET stack is a large step up in sensitivity, accuracy, scale, and
robustness. Side by side:

| Capability | Free (this repo) | Production PICKET |
|---|---|---|
| **Use / license** | Noncommercial: evaluation, research, personal (PolyForm Noncommercial) | Commercial & operational deployment (licensed) |
| **On-device detection + classification** | Yes: 7-class acoustic classifier on the phone | Yes: tuned, expanded class set, continuously improved |
| **Single-device bearing** | Yes: two-mic acoustic bearing | Yes: multi-mic, calibrated, higher accuracy |
| **Multi-device fusion** | Report-level: crosses independent per-phone bearings | Coherent, sensor-level: devices combined into one array |
| **Localization** | Bearing cross-fix (triangulation) on the reference server | Certified localization, materially better accuracy and reliability |
| **Sensing modalities** | Acoustic | Acoustic + passive RF, multi-modal |
| **Sensors supported** | COTS Android phones | COTS phones + purpose-built PICKET nodes and long-range sensors |
| **Scale** | Demo-grade: a handful of phones on one host, single process | Horizontal scale: large, self-healing meshes |
| **Server** | Bare-bones open reference server (in this repo) | Full PICKET Fusion engine (not in this repo) |
| **Persistence / evidence** | None (in-memory, ephemeral) | Persistent, evidence-grade logging and replay |
| **Field hardening** | None (evaluation only) | Hardened for degraded, denied, and contested environments |
| **ATAK / CoT** | Yes: fused contacts to the map | Yes, extended integration |
| **Support** | Community / GitHub issues | Commercial support, integration, and SLAs |

The free version proves the interface and lets you see it work. The production version is
what you deploy. See [`COMMERCIAL.md`](./COMMERCIAL.md) or open a "Commercial license
inquiry" issue.

## Legal / usage

ATAK-CIV is a U.S. Government product released open source and classified EAR99.
Use of this plugin must comply with your organization's authority to operate and
all applicable laws on audio capture in your jurisdiction. This plugin performs
passive acoustic sensing only; it commands no effectors.

License: not yet finalized; the released APK is free to download and use, all other rights reserved for now.

## Contact

Bug reports and device-compatibility reports (which phones give you a bearing) via GitHub Issues.

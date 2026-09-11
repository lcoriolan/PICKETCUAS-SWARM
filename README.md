# PICKET SWARM: Distributed Acoustic Detection Plugin for ATAK

PICKET SWARM turns an Android phone running ATAK into an acoustic sensing node, and
turns a handful of those phones into one distributed microphone array.
It captures audio on-device, runs all signal processing on the phone (no cloud), and
gives the operator a live acoustic bearing cue and a 7-class sound classification
(background, drone, aircraft, vehicle, voice, gunfire, explosion) directly on the
ATAK map. When paired with a PICKET Fusion server it also ships event clips and
telemetry over mutual-TLS WebSocket for multi-node correlation.

More than a drone spotter, PICKET SWARM is the phone tier of a holistic **acoustic
battlefield situational-awareness** system. It hears and places the sounds of the fight,
drones overhead, gunfire, vehicles, and other movers, and turns them into tracks on the
map. Sound is passive: it needs no emitter, keeps working when GPS and comms are denied,
and gives an enemy nothing to detect or jam, so the acoustic picture holds when other
sensors go dark.

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

## CoHear: the differentiator (one big ear)

Report-level cross-fixing is table stakes. **PICKET's real strength is CoHear: coherent,
sample-level combining that turns many phones into one big ear.** Where the free array crosses
independent bearings, CoHear aligns the raw clips from every node to sub-sample accuracy with
GCC-PHAT and delay-and-sums them, so a source too faint for any single phone to call rises out
of the noise. The array gain grows with every node that contributes a clip, and the alignment
needs no shared microsecond hardware clock, which is what makes it work across ordinary,
software-clocked phones.

That coherent combining is what separates PICKET from a collection of independent sensors:
weak-signal detection, a single beamformed rendering of the source, and tighter localization,
all from commodity devices.

**What the simulations show** (CoHear benchmark suite, all cases PASS):

- **Array gain tracks the theoretical ideal.** Measured gain lands within ~0.1 dB of
  `10*log10(N)`: **+3.0 dB at 2 nodes, +6.0 dB at 4, +9.0 dB at 8, +10.8 dB at 12.**
- **Detection range scales with the square root of the node count.** About **2x range at 4
  nodes, 2.8x at 8, and 3.4x at 12** versus a single phone.
- **Sub-meter localization.** Steered-response-power localization placed a source to within
  **0.35 m** of truth.
- **Robust to software-clock sync error.** CoHear keeps roughly **9.5 dB of gain at 0.5 ms**
  of inter-node timing jitter and about **5 dB at 1.3 ms**, so it does not need a
  microsecond-accurate hardware clock. This is what makes it work on ordinary phones.

These are simulation-benchmark results; field tests corroborate the on-node combining case.

See [`cohear-demo/`](./cohear-demo/) for a runnable, self-contained demonstration on synthetic
data: a source 6 dB under the noise on every phone becomes clearly detectable once six of them
combine. The production CoHear engine (the gating, clip selection, coincidence-gain weighting,
and field tuning that make it robust at scale) is not in this repository.

**For a full CoHear demonstration on live hardware, reach out** by opening an issue on this
repository (a "CoHear demo request"). We are glad to show coherent combining running on real
nodes end to end.

## Listening range and coherent scale

CoHear's array gain (`10·log10(N)`) converts to detection range as about `√N` **in the
weak-signal regime**: roughly 4x more coherent phones doubles the range on a faint source.
From a single phone's ~80 m bare range against a quiet small drone:

| Coherent phones | Array gain | Range vs 1 | Reach on a quiet drone* |
|---|---|---|---|
| 1 | 0 dB | 1x | ~80 m |
| 4 | +6.0 dB | 2x | ~160 m |
| 12 | +10.8 dB | 3.5x | ~280 m |
| 24 | +13.8 dB | 4.9x | ~390 m |
| 48 | +16.8 dB | 6.9x | ~555 m |
| ~96 | +19.8 dB | 10x | ~785 m |

Past ~100 coherent phones the curve flattens (`√N` needs 4x the devices to double range
again), and only phones close enough to hear an event combine coherently for it, so beyond a
local cluster more phones add **coverage**, not **range**. That is the practical
diminishing-returns point for a single source.

### By drone class: single sensor vs CoHear (modeled)

A "drone" is not one sound: a two-stroke Shahed and a whisper-quiet electric FPV differ by
about 30 dB (roughly 30x in range), and they sit in different parts of the spectrum, heavy ICE
engines dominate the low end while small electric rotors scream up in the kHz. This is what CoHear
coherent combining reaches per class, one phone versus a swarm, from PICKET's threat model
(`SPL(r) = SPL@1m - 20*log10(r)`, coherent reach scales as `√N`):

| Class (example) | SPL@1m | Acoustic signature (modeled) | 1 sensor | With CoHear (~48 sensors)* |
|---|---|---|---|---|
| Naval USV (Magura V5) | ~98 dB | marine engine, ~50-300 Hz | ~3.8 km | ~26 km |
| One-way attack (Shahed-136) | ~98 dB | two-stroke buzz, ~80-300 Hz | ~2.5 km | ~17 km |
| MALE (Bayraktar TB2) | ~88 dB | prop + engine, ~100-500 Hz | ~795 m | ~5.5 km |
| Recon (Orlan-10) | ~84 dB | small ICE buzz, ~150-600 Hz | ~500 m | ~3.5 km |
| Loiter munition (Lancet-3) | ~78 dB | electric pusher, ~200 Hz-2 kHz | ~250 m | ~1.7 km |
| FPV quad | ~70 dB | multirotor whine, ~2-8 kHz (blade-rate comb) | ~100 m | ~690 m |
| Quiet / fiber-optic FPV | ~68 dB | high whine, ~2-8 kHz | ~80 m | ~555 m |

\* Each CoHear figure is the single-sensor range times `√48 ≈ 6.9` (array gain in the weak-signal
regime); scale to other counts by `√N` (about 10x at ~96 phones). **Low-frequency emissions (ICE,
marine engines) propagate far with little air absorption**, so the model extends them a long way,
the km-plus figures are optimistic ceilings, and for low-altitude sources terrain and line of sight
bound them further. The high-frequency FPV whine (~2-8 kHz) is air-absorption-limited, so treat its
figure as an upper bound too. Field metering is needed to pin the real numbers.

Frequency compounds the range story. Low-frequency engine noise (ICE, marine) barely attenuates
in air, which is why the loud ICE classes are heard for kilometers; the high-pitched kHz whine of a
small electric FPV is absorbed fast, so its short range is set by *both* its low level *and* its high
band, the double reason FPVs are the hard target. PICKET pulls the rotor/blade-rate tonals out of
that band (DEMON/LOFAR-style) even when wind masks the low end, and coherent combining then turns the
FPV's ~80-100 m single-phone range into hundreds of meters as the cluster grows. Loud, long-range
classes are already absorption-limited, so more ears tighten the **bearing and fix**, not the range.

### Other battlefield sounds (published-literature estimates, illustrative)

SWARM's classifier also flags gunfire, explosions, vehicles, aircraft, and voice. We have not
metered these ourselves, so the figures below are **published-literature typical ranges for a
single acoustic sensor, illustrative only** and are NOT from PICKET's model or measurements.
Impulsive sources (muzzle blast, detonations) do not follow the drone free-field model, and
real ranges swing widely with the weapon, terrain, wind, and atmosphere.

| Source | Character | Illustrative single-sensor range |
|---|---|---|
| Small-arms gunfire | very loud, impulsive | ~1-2 km |
| Heavy weapons / autocannon | very loud, impulsive | ~2-4 km |
| Artillery / mortar / explosions | extreme, impulsive | ~5-15+ km |
| Armored vehicle / engine | loud, continuous | ~0.3-1 km |
| Low helicopter / aircraft | loud, continuous | ~2-5 km |
| Human speech (conversational) | quiet | ~10-50 m |

### Inter-node spread matters

Coherent scale is not just node *count*, it is node *spacing*. PICKET seeds nodes at roughly
**70-120 m** apart (tighter on the danger avenues, looser across open ground), so any mover is
heard by at least three ears. A wider spread gives a bigger aperture and a sharper fix; too
wide and a given source is not co-heard by enough nodes to combine coherently. Because the
combine is timing-based, timing spread matters too: in simulation CoHear holds about **9.5 dB
of gain at 0.5 ms** of inter-node jitter and about **5 dB at 1.3 ms**, which is why it works on
ordinary software-clocked phones with no shared hardware clock.

### Beamforming

The combine is coherent (sub-sample GCC-PHAT alignment, not averaged reports), so CoHear steers
a beam toward the source. The same step that lifts a weak signal also sharpens its bearing, so
more ears mean longer reach **and** a tighter fix at the same time.

### Distributed noise cancellation

A coherent array does not just add signal, it subtracts noise. The source arrives coherently at
every node while each node's ambient does not, so combining cancels the uncorrelated part of the
noise. That is the array gain, and it is exactly why more ears help most when the environment is
loud: the noise-floor limit above is what a distributed array is built to push back on.

Beyond that inherent gain, when a single loud interferer dominates (a generator, a road, a
nearby engine), adaptive beamforming (MVDR / Capon) can steer a spatial null onto that direction
and reject it while holding the main beam on the target. Spatially separated ears are what make
this possible: a distributed array can null noise that no single microphone ever could. (The
inherent uncorrelated-noise gain is the validated part; directional null-steering is standard
adaptive-array processing that the beamforming path supports.)

\* Modeled projection, not hardware-measured, and **set by the ambient noise floor.** Detection
happens where the source level clears the local noise, so range scales inversely with that
floor: these figures assume a quiet ~30 dB floor, and **every +6 dB of ambient roughly halves
the range.** Wind alone adds ~10-20 dB, and a live battlefield is nowhere near quiet, so treat
these as best-case-quiet ceilings, not field guarantees. The array's job is partly to fight
this: coherent gain raises the effective floor margin, which is why more ears help most exactly
when it is noisy. Uses the `10·log10(N)` / `√N` array law (validated in simulation through 12
nodes) on a modeled ~80 m single-phone baseline (propulsion-class SPL estimate). Real range
depends on the source, the ambient noise floor, wind, and terrain.

## At scale: a distributed array on the phones you already have

Every capability above runs on ordinary phones. Each phone is a node: it self-positions from its
own GPS (so a deployment needs no survey), classifies and bearings on-device, and, when it is
pointed at a Fusion server, streams its detections and mono audio clips into the shared picture
(standalone, nothing leaves the phone). The architecture does not care whether there are three
phones or a thousand, more phones mean a wider aperture, more coherent gain, longer reach, and
denser coverage.

Taken to its limit, that is the interesting part: stand up enough phones running this tool,
hundreds across an area, and you have a distributed acoustic battlefield-awareness mesh built
entirely from commodity devices, with no dedicated sensors at all. A thousand phones is, in
principle, a thousand-node acoustic array.

Phones normally take their position from GPS, but they need not depend on it. The same acoustic
self-localization the dedicated PICKET nodes use, solving each node's position by multilaterating
a sound the array shares, could in principle run on the phones too, so a phone swarm could keep
placing itself even with GPS denied. The purpose-built PICKET system still pushes the idea
further with longer-range collectors and ruggedized drop-and-go hardware, but the core capability
is this tool, and it scales with the phones already in people's pockets.

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

## PICKET family

- [PICKET SNOOPY](https://github.com/lcoriolan/PICKETCUAS-SNOOPY): passive RF/ESM ATAK plugin (Wi-Fi/BLE survey + drone Remote ID).
- [SWARM-DEVICE-AGNOSTIC](https://github.com/lcoriolan/SWARM-DEVICE-AGNOSTIC): web-based acoustic reference; any browser is a sensor node, inter-device TDOA fusion.
- [SNOOPY RF fusion server](https://github.com/lcoriolan/PICKETCUAS-SNOOPY/tree/main/rf-fusion-server): web-based server that merges many devices' Wi-Fi/BLE reports into one picture (in the SNOOPY repo).

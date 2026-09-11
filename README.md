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

### Beamforming

The combine is coherent (sub-sample GCC-PHAT alignment, not averaged reports), so CoHear steers
a beam toward the source. The same step that lifts a weak signal also sharpens its bearing, so
more ears mean longer reach **and** a tighter fix at the same time.

### Coherent noise cancellation: filtering the ambient

A coherent array does not just add signal, it **filters the ambient**, and that is the direct answer
to the "a battlefield is loud" limit on detection range: it pushes the noise floor down instead of
just tolerating it. It works three ways.

- **Uncorrelated noise averages away.** The source arrives coherently at every node, but each node's
  ambient, wind, distant hum, general din, is different, so summing the aligned clips cancels the
  uncorrelated part and the noise falls as `√N` relative to the signal. That is the array gain, and
  it is why more ears help most exactly when it is loud.
- **Directional interferers get nulled.** When one loud source dominates (a generator, a road, an
  idling engine), adaptive beamforming (MVDR / Capon) steers a spatial null onto its direction and
  rejects it while holding the beam on the target, something no single microphone can do.
- **Reference-channel subtraction.** Nodes far from the target hear mostly the shared ambient, so
  they can act as noise references to subtract the correlated background from the nodes on the
  target (classic adaptive noise cancellation).

Together these raise the effective signal-to-noise ratio and let detection reach through clutter
that would swamp any single phone. The inherent `√N` uncorrelated-noise gain is the validated part;
the directional null-steering and reference subtraction are standard adaptive-array techniques the
beamforming path supports (see the extension points), not separately benchmarked here.

### Inter-node spread matters

Coherent scale is not just node *count*, it is node *spacing*. PICKET seeds nodes at roughly
**70-120 m** apart (tighter on the danger avenues, looser across open ground), so any mover is
heard by at least three ears. A wider spread gives a bigger aperture and a sharper fix; too
wide and a given source is not co-heard by enough nodes to combine coherently. Because the
combine is timing-based, timing spread matters too: in simulation CoHear holds about **9.5 dB
of gain at 0.5 ms** of inter-node jitter and about **5 dB at 1.3 ms**, which is why it works on
ordinary software-clocked phones with no shared hardware clock.

## Range and scale

CoHear's array gain (`10·log10(N)`) turns into detection range as about `√N` in the weak-signal
regime, the clean **spreading-only law, before air absorption**: roughly 4x more coherent phones
doubles the range on a faint source. From a single phone's ~80 m bare range against a quiet small
drone (the absorption-aware, per-class figures are in the next table):

| Coherent phones | Array gain | Range vs 1 | Reach, spreading only* |
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

\* Spreading-only `√N`: array gain versus distance with **no air absorption**, a clean upper-bound
law. Real reach is lower once frequency-dependent absorption is folded in (sharply for high-pitched
sources), see the by-drone-class table below. All figures also assume a quiet ambient floor, and
**every +6 dB of ambient roughly halves the range** (wind adds ~10-20 dB, and a battlefield is far
from quiet), so treat them as best-case-quiet ceilings, exactly what the coherent noise cancellation
above is built to push back on.

### By drone class: single sensor vs CoHear (modeled)

A "drone" is not one sound: a two-stroke Shahed and a whisper-quiet electric FPV differ by
about 30 dB (roughly 30x in range), and they sit in different parts of the spectrum, heavy ICE
engines dominate the low end while small electric rotors scream up in the kHz. This is what CoHear
coherent combining reaches per class, one phone versus a swarm, from PICKET's threat model
(`SPL(r) = SPL@1m - 20*log10(r)`):

| Class (example) | SPL@1m | Acoustic signature (modeled) | 1 sensor | With CoHear (~48 sensors)* |
|---|---|---|---|---|
| Naval USV (Magura V5) | ~98 dB | marine engine, ~50-300 Hz | ~3.8 km | ~14 km |
| One-way attack (Shahed-136) | ~98 dB | two-stroke buzz, ~80-300 Hz | ~2.5 km | ~11 km |
| MALE (Bayraktar TB2) | ~88 dB | prop + engine, ~100-500 Hz | ~795 m | ~4 km |
| Recon (Orlan-10) | ~84 dB | small ICE buzz, ~150-600 Hz | ~500 m | ~2.5 km |
| Loiter munition (Lancet-3) | ~78 dB | electric pusher, ~200 Hz-2 kHz | ~250 m | ~1.1 km |
| FPV quad | ~70 dB | multirotor whine, ~2-8 kHz (blade-rate comb) | ~100 m | ~320 m |
| Quiet / fiber-optic FPV | ~68 dB | high whine, ~2-8 kHz | ~80 m | ~280 m |

\* CoHear figures apply the ~48-node array gain (~17 dB) with **both** spherical spreading **and**
frequency-dependent air absorption (`α`), not a flat `√N` (which would be `6.9x` and ignores
absorption). **Low-frequency classes (ICE, marine, ~50-300 Hz) attenuate little (`α` well under
1 dB/km), so the gain reaches far**; the high-frequency FPV whine (~2-8 kHz) is absorbed fast
(tens of dB/km), so the same gain buys far less, which is why the FPV barely doubles while the loud
low-band classes stretch to kilometers. Modeled with representative `α` per band on literature/threat
anchors, not PICKET-metered; terrain and line of sight bound low-altitude sources further.

**A drone's low-frequency emissions travel much farther than its high-frequency sound.** Air absorbs
high frequencies quickly and low frequencies hardly at all, so a drone's deep engine and rotor tones
carry for kilometers while its high-pitched whine dies off fast over the same air. That is why the
loud, low-band classes (ICE engines, marine) are detected far and keep scaling as the swarm grows,
and why a small electric FPV is the hard target: it is quiet *and* high-pitched (~2-8 kHz), so its
short range is set by both its low level and its rapidly-absorbed band. PICKET pulls the
rotor/blade-rate tonals out of that band (DEMON/LOFAR-style) even when wind masks the low end, and
coherent combining then extends the reach as more ears join.

### Other battlefield sounds

SWARM's classifier also flags gunfire, explosions, vehicles, aircraft, and voice, and a swarm both
hears them a long way off **and** locates them. Single-sensor ranges are **published-literature
typical figures, illustrative only**, NOT PICKET-metered:

| Source | 1 sensor | Heard with CoHear (~48)* | Located to within** |
|---|---|---|---|
| Small-arms gunfire | ~1-2 km | ~4-6 km | ~10-25 m |
| Heavy weapons / autocannon | ~2-4 km | ~7-12 km | ~tens of m |
| Artillery / mortar / explosions | ~5-15+ km | ~20-40 km | ~50-100 m (firing point + impact) |
| Armored vehicle / engine | ~0.3-1 km | ~2-5 km | ~50-150 m (track) |
| Low helicopter / aircraft | ~2-5 km | ~8-15 km | bearing / track fix |
| Human speech (conversational) | ~10-50 m | ~70-300 m | ~a few m (if several hear it) |

\* Heard = the range where the ~48-node array gain (~17 dB) still clears the noise floor, computed
with **both** spherical spreading **and** frequency-dependent air absorption (`α`), not a flat `√N`.
Low-frequency loud sources (artillery ~50-150 Hz, `α` well under 1 dB/km) attenuate little and reach
far; higher-frequency content is absorbed fast, which caps the reach. Modeled with representative `α`
on literature single-sensor anchors, not PICKET-metered; terrain, weather, and the horizon vary.
\*\* Located = TDOA multilateration across the nodes that hear it; fix figures are published-literature
typical for gunshot and sound-ranging systems, illustrative, not PICKET-metered.

### Distributed counter-battery

A swarm does not just hear these far, it **locates** them. By timestamping the same event across nodes
and multilaterating the **muzzle blast and supersonic shockwave** (small arms, heavy weapons) or the
**point of origin and impact** (mortars, artillery, rockets), it fixes a hostile firing position to
within tens of meters, the same principle as classic acoustic sound-ranging and modern gunshot
locators, but built from commodity phones dispersed across the ground. That is a near-real-time
**counter-battery cue** on the ATAK map, firing position plus impact point, ready to hand to
counterfire. It is **passive** (nothing to detect or jam), **self-heals** as nodes drop, and
**densifies** by adding devices, no dedicated array or radar. Report-level timing and cross-fix are in
the open reference; the precision alignment and firing-solution logic that turn it into a metered
counter-battery fix are production (see the extension points), and real accuracy needs field validation.

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
cross-fixing on a map. It's open source (Apache-2.0), and it's meant to be used. The
production PICKET stack is a large step up in sensitivity, accuracy, scale, and
robustness. Side by side:

| Capability | Free (this repo) | Production PICKET |
|---|---|---|
| **Use / license** | Open source, Apache-2.0 (commercial use OK) | Commercial license for the production engine |
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
what you deploy. Open a "Commercial license inquiry" issue to talk deployment.

## Legal / usage

ATAK-CIV is a U.S. Government product released open source and classified EAR99.
Use of this plugin must comply with your organization's authority to operate and
all applicable laws on audio capture in your jurisdiction. This plugin performs
passive acoustic sensing only; it commands no effectors. This plugin is licensed under the
**Apache License 2.0** (see `LICENSE`), free and open for any use including commercial; the
production PICKET engine is a separate product and separately licensed.

## Contact

Bug reports and device-compatibility reports (which phones give you a bearing) via GitHub Issues.

## PICKET family

- [PICKET SNOOPY](https://github.com/lcoriolan/PICKETCUAS-SNOOPY): passive RF/ESM ATAK plugin (Wi-Fi/BLE survey + drone Remote ID).
- [SWARM-DEVICE-AGNOSTIC](https://github.com/lcoriolan/SWARM-DEVICE-AGNOSTIC): web-based acoustic reference; any browser is a sensor node, inter-device TDOA fusion.
- [SNOOPY RF fusion server](https://github.com/lcoriolan/PICKETCUAS-SNOOPY/tree/main/rf-fusion-server): web-based server that merges many devices' Wi-Fi/BLE reports into one picture (in the SNOOPY repo).

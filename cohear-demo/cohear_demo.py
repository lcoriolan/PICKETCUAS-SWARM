#!/usr/bin/env python3
# PROJECT:     PICKET SWARM - CoHear capability demo (neutered / reference)
# CREATED:     2026-09-10 16:23 MDT | 18:23 EDT | 22:23 Zulu
# DESCRIPTION: A self-contained, SYNTHETIC demonstration of CoHear, PICKET's coherent
#              multi-node acoustic combining ("many phones -> one big ear"). It generates
#              fake node clips of a faint source buried in independent noise, aligns them
#              with textbook GCC-PHAT, delay-and-sums them, and reports the array gain and
#              the recovered inter-node delays. Optionally it writes before/after WAV files
#              so you can HEAR a source emerge from the noise.
#
#              THIS IS A NEUTERED DEMO. It uses only textbook DSP (cross-correlation with a
#              phase transform, and plain delay-and-sum) on synthetic data. It deliberately
#              contains NONE of the production PICKET CoHear engine: no signal gating, no
#              clip selection, no coincidence-gain weighting, no acoustic classifier, no
#              protection-bubble covariance gating, no ranging, and no real signatures or
#              node data. Its only job is to make the coherent-combining CONCEPT tangible.
#
# USAGE:       python3 cohear_demo.py                 # 6 nodes, -6 dB per-node SNR
#              python3 cohear_demo.py --nodes 10 --snr-db -12 --wav
#              (requires: numpy;  WAV output uses the Python standard library only)

import argparse
import math
import wave
import struct

import numpy as np

# Speed of sound in air (m/s) at ~20 C. Turns node geometry into per-node arrival delays.
C_SOUND = 343.0
# Demo sample rate. 16 kHz covers the voice/drone band and keeps WAV files small.
FS = 16000


def synth_source(n_samples, fs):
    """Build a synthetic 'event' clip: a broadband chirp + a tonal line in the FIRST HALF only.

    Leaving the second half silent keeps the clip compact, so the small inter-node delays
    applied below (a few hundred samples) never wrap around the FFT buffer. Broadband content
    is what makes GCC-PHAT alignment sharp, like a real transient (a drone whine, a slam).
    Returned at unit RMS over the active portion so the requested SNR is exact.
    """
    t = np.arange(n_samples) / fs
    active = n_samples // 2                              # source occupies the first half
    f0, f1 = 300.0, 3000.0                               # 300 Hz -> 3 kHz linear chirp
    k = (f1 - f0) / (active / fs)
    sig = np.zeros(n_samples)
    ta = t[:active]
    sig[:active] = np.sin(2 * math.pi * (f0 * ta + 0.5 * k * ta * ta)) \
        + 0.3 * np.sin(2 * math.pi * 1000.0 * ta)        # + a 1 kHz tonal line
    return sig / (np.sqrt(np.mean(sig ** 2)) + 1e-12)    # unit RMS


def frac_delay(sig, delay_samples):
    """Delay a signal by a (possibly fractional) number of samples via an FFT phase shift.

    Models each node hearing the SAME source a little later because it sits farther away.
    Fractional delay matters: real inter-node delays are almost never whole samples, and
    recovering the sub-sample part is the whole point of CoHear.
    """
    n = len(sig)
    freqs = np.fft.rfftfreq(n)
    shift = np.exp(-2j * math.pi * freqs * delay_samples)
    return np.fft.irfft(np.fft.rfft(sig) * shift, n=n)


def gcc_phat(a, b, max_shift):
    """Estimate the delay (in samples) of `a` relative to `b` via GCC-PHAT.

    GCC-PHAT = cross-power spectrum divided by its own magnitude (the 'phase transform'),
    inverse-transformed to a sharp correlation peak. It aligns two clips and recovers a
    sub-sample delay WITHOUT a microsecond-accurate shared hardware clock, which is exactly
    what lets CoHear combine software-clocked phones. Textbook DSP, not proprietary.
    Returns the integer lag L that best aligns `a` to `b` (apply frac_delay(a, -L) to align).
    """
    n = len(a) + len(b)                                  # linear (zero-padded) cross-correlation
    A = np.fft.rfft(a, n=n)
    B = np.fft.rfft(b, n=n)
    R = A * np.conj(B)
    R /= np.abs(R) + 1e-12                                # phase transform
    cc = np.fft.irfft(R, n=n)
    # Positive lags live at the front of cc, negative lags wrap to the back. Fold both ends
    # into one window [-max_shift .. +max_shift] and take the strongest peak.
    window = np.concatenate((cc[:max_shift + 1], cc[-max_shift:]))
    idx = int(np.argmax(np.abs(window)))
    return idx if idx <= max_shift else idx - (2 * max_shift + 1)


def measured_snr_db(estimate, source_unit):
    """SNR of `estimate` against the known unit-RMS source, in dB (higher is better).

    Projects the estimate onto the source to split it into a signal component (alpha * source)
    and a residual (everything else, i.e. noise), then reports 10log10(signal_power/noise_power).
    The demo can do this because it owns the ground-truth source; in the field CoHear uses
    gated references, which the neutered demo omits.
    """
    alpha = float(np.mean(estimate * source_unit))       # source is unit RMS -> projection coeff
    resid = estimate - alpha * source_unit               # noise = estimate minus signal component
    return 10 * math.log10((alpha ** 2) / (np.mean(resid ** 2) + 1e-12))


def write_wav(path, sig):
    """Write a mono 16-bit WAV of a float signal, normalized to avoid clipping (stdlib only)."""
    x = sig / (np.max(np.abs(sig)) + 1e-12)
    pcm = (x * 32767.0).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FS)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser(description="PICKET CoHear neutered capability demo (synthetic).")
    ap.add_argument("--nodes", type=int, default=6, help="number of synthetic nodes (phones)")
    ap.add_argument("--snr-db", type=float, default=-6.0, help="per-node SNR in dB (source vs noise)")
    ap.add_argument("--seconds", type=float, default=1.0, help="clip length in seconds")
    ap.add_argument("--wav", action="store_true", help="also write before/after WAV files")
    args = ap.parse_args()

    rng = np.random.default_rng(0)                       # fixed seed -> reproducible printout
    n = int(args.seconds * FS)
    source = synth_source(n, FS)                         # unit-RMS reference we combine toward

    # Compact cluster: nodes on a 5 m circle, source ~60 m off to one side. This keeps the
    # inter-node delay spread to a few hundred samples (safe for the FFT shift) while still
    # giving every node a genuinely different fractional-sample arrival time.
    angles = np.linspace(0, 2 * math.pi, args.nodes, endpoint=False)
    node_xy = np.stack([5.0 * np.cos(angles), 5.0 * np.sin(angles)], axis=1)
    src_xy = np.array([60.0, 15.0])
    dists = np.linalg.norm(node_xy - src_xy, axis=1)
    true_delays = (dists - dists.min()) / C_SOUND * FS   # samples, relative to the nearest node
    max_shift = int(true_delays.max()) + 64              # search window for GCC-PHAT, with guard

    # Each node's clip: the delayed source at the requested SNR + its OWN independent noise.
    # Independent noise is the crux: it does not add coherently, so summing aligned clips lifts
    # the source out of the noise. That lift is the array gain.
    sig_scale = 10 ** (args.snr_db / 20.0)               # per-node signal amplitude vs unit noise
    clips = []
    for d in true_delays:
        s = sig_scale * frac_delay(source, d)
        noise = rng.standard_normal(n)
        noise /= np.sqrt(np.mean(noise ** 2))            # unit-RMS noise -> SNR is exactly snr_db
        clips.append(s + noise)

    # Single-node baseline: align node 0's own copy back to t=0 (fair reference point).
    single = frac_delay(clips[0], -true_delays[0])
    single_snr = measured_snr_db(single, source)

    # CoHear combine: align every clip to node 0 with GCC-PHAT, then delay-and-sum.
    aligned = [single]
    delay_err = []
    for i in range(1, args.nodes):
        est_lag = gcc_phat(clips[i], clips[0], max_shift)   # delay of node i relative to node 0
        true_rel = true_delays[i] - true_delays[0]          # ground truth, for the error report
        delay_err.append(abs(est_lag - true_rel))
        # Undo node i's measured delay AND node 0's own offset, so all land at t=0 like `single`.
        aligned.append(frac_delay(clips[i], -est_lag - true_delays[0]))
    combined = np.mean(aligned, axis=0)                  # coherent sum (mean preserves scale)
    combined_snr = measured_snr_db(combined, source)

    gain = combined_snr - single_snr
    ideal = 10 * math.log10(args.nodes)                  # ideal array gain for N coherent nodes

    print("PICKET CoHear - neutered capability demo (synthetic input)")
    print(f"  nodes:                 {args.nodes}")
    print(f"  per-node SNR:          {args.snr_db:+.1f} dB")
    print(f"  single-node SNR:       {single_snr:+.2f} dB")
    print(f"  CoHear combined SNR:   {combined_snr:+.2f} dB")
    print(f"  measured array gain:   {gain:+.2f} dB   (ideal {ideal:+.2f} dB for {args.nodes} nodes)")
    print(f"  mean alignment error:  {np.mean(delay_err):.2f} samples "
          f"({np.mean(delay_err) / FS * 1e6:.1f} us) via GCC-PHAT")
    if args.wav:
        write_wav("single_node.wav", single)
        write_wav("cohear_combined.wav", combined)
        print("  wrote single_node.wav and cohear_combined.wav - listen to the difference")
    print("\nThis demo shows the CONCEPT (coherent combining -> array gain) on synthetic data.")
    print("Production PICKET CoHear adds the gating, clip selection, coincidence-gain weighting,")
    print("and field tuning that make it robust on real, software-clocked fleets. Those are not")
    print("in this repository.")


if __name__ == "__main__":
    main()

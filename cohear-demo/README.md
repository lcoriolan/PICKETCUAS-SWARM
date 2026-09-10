# CoHear demo (neutered)

**CoHear is what makes PICKET SWARM more than a bag of phones: it turns many independent
nodes into one big ear.** Each phone hears the same source at a slightly different time.
CoHear aligns those clips to sub-sample accuracy and coherently combines them, so a faint
source that no single phone can call rises out of the noise. More nodes, more gain.

This folder is a small, self-contained demonstration of that idea. It is **neutered on
purpose**: textbook DSP on synthetic data, so anyone can run it and see the effect, while the
production engine stays private (see "What this is not" below).

## What it shows

`cohear_demo.py` builds N synthetic node clips of a faint source buried in independent noise,
aligns them with **GCC-PHAT** (generalized cross-correlation with a phase transform), and
**delay-and-sums** them. It reports the SNR of one node versus the CoHear combination, and the
alignment accuracy.

```
$ python3 cohear_demo.py
  nodes:                 6
  per-node SNR:          -6.0 dB
  single-node SNR:       -6.04 dB
  CoHear combined SNR:   +1.15 dB
  measured array gain:   +7.19 dB   (ideal +7.78 dB for 6 nodes)
  mean alignment error:  0.51 samples (32.0 us) via GCC-PHAT
```

A source that is 6 dB *under* the noise on every single phone becomes a positive-SNR,
clearly-detectable signal once six of them combine, and the clips are aligned to about half a
sample without any shared microsecond clock. That last point matters: it is why CoHear works
across ordinary, software-clocked phones.

## Run it

```bash
pip install numpy
python3 cohear_demo.py                      # 6 nodes, -6 dB per node
python3 cohear_demo.py --nodes 10 --snr-db -12
python3 cohear_demo.py --wav                # also writes single_node.wav + cohear_combined.wav
```

With `--wav` you can *hear* the difference: the single-node file is mostly hiss; the combined
file has an audible chirp.

## What this is not

This demo uses only standard, published DSP (GCC-PHAT and plain delay-and-sum) on synthetic
input. It deliberately contains **none** of the production PICKET CoHear engine:

- no signal gating or event detection to decide *which* clips to combine,
- no clip selection or coincidence-gain weighting,
- no acoustic classifier, protection-bubble covariance gating, or ranging,
- no real signatures, node data, or field tuning.

Those are what make CoHear robust on real fleets in the field, and they are not in this
repository. The demo proves the capability; the capability at scale is the product.

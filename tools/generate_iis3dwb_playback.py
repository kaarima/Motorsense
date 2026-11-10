#!/usr/bin/env python3
"""Generate ignored IIS3DWB-rate replay and RMS reference from CWRU MAT data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.signal import firwin, resample_poly

SOURCE_RATE_HZ = 12_000
SENSOR_RATE_NUMERATOR = 80_000
SENSOR_RATE_DENOMINATOR = 3
OUTPUT_RATE_HZ = 12_000
WINDOW_SAMPLES = 6_000
FIR_TAPS = 9


def stream_resample(samples: np.ndarray, coefficients: np.ndarray) -> np.ndarray:
    """Reference the MCU's short causal FIR and 9/20 phase accumulator."""
    history = np.zeros(FIR_TAPS, dtype=np.float64)
    phase = 0
    output: list[float] = []
    for sample in samples:
        history[1:] = history[:-1]
        history[0] = sample
        filtered = float(np.dot(coefficients, history))
        phase += 9
        if phase >= 20:
            phase -= 20
            output.append(filtered)
    return np.asarray(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mat_file", type=Path)
    parser.add_argument("--channel", default="X105_DE_time")
    parser.add_argument("--binary", type=Path, default=Path("build/cwru_iis3dwb.bin"))
    parser.add_argument("--reference", type=Path, default=Path("build/cwru_iis3dwb_rms.txt"))
    parser.add_argument("--metadata", type=Path, default=Path("build/cwru_iis3dwb.json"))
    args = parser.parse_args()

    source = np.asarray(loadmat(args.mat_file)[args.channel], dtype=np.float64).reshape(-1)
    sensor_stream = resample_poly(source, up=20, down=9)
    scale = 24_000.0 / max(float(np.max(np.abs(sensor_stream))), np.finfo(float).eps)
    x = np.clip(np.rint(sensor_stream * scale), -32768, 32767).astype("<i2")
    xyz = np.zeros((x.size, 3), dtype="<i2")
    xyz[:, 0] = x

    coefficients = firwin(FIR_TAPS, 0.45, window=("kaiser", 5.0))
    output = stream_resample(x.astype(np.float64), coefficients)
    if output.size < WINDOW_SAMPLES:
        raise ValueError(f"Need {WINDOW_SAMPLES} output samples; only generated {output.size}")
    rms = float(np.sqrt(np.mean(np.square(output[:WINDOW_SAMPLES]))))

    args.binary.parent.mkdir(parents=True, exist_ok=True)
    args.reference.write_text(f"{rms:.2f}\n", encoding="ascii")
    xyz.tofile(args.binary)
    args.metadata.write_text(
        json.dumps(
            {
                "channel": args.channel,
                "source_rate_hz": SOURCE_RATE_HZ,
                "sensor_rate_hz": SENSOR_RATE_NUMERATOR / SENSOR_RATE_DENOMINATOR,
                "resample_ratio": "20/9 to sensor, 9/20 on MCU",
                "sensor_samples": int(xyz.shape[0]),
                "window_samples": WINDOW_SAMPLES,
                "window_rms_counts": rms,
                "fir_coefficients": coefficients.tolist(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {xyz.shape[0]} sensor samples to {args.binary}")
    print(f"12 kHz Python reference RMS: {rms:.2f} counts ({WINDOW_SAMPLES} samples)")


if __name__ == "__main__":
    main()

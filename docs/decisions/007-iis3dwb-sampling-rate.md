# Decision 007: IIS3DWB sampling and CWRU replay

## Finding

The IIS3DWB accelerometer ODR is fixed at 26.667 kHz. Its 3 KB FIFO batches
accelerometer samples at 26,667 Hz; decimation controls apply to timestamps, not
acceleration data. FIFO words contain one tag byte followed by six bytes of
X/Y/Z data.

## Choice

Keep the 12 kHz firmware/DSP contract in Decision 004. Acquire the full 26.667
kHz FIFO stream and apply an anti-aliasing rational resampler on the MCU before
forming 6,000-sample, 0.5-second analysis windows. The nominal rational
conversion is 9/20 (26,666.7 Hz to 12,000 Hz); resampling must use the configured
sensor rate rather than assume the physical clock is exactly 26,666.7 Hz. Do
not drop every other sample or use timestamp FIFO decimation.

For CWRU replay, use the 12 kHz drive-end channel from `105.mat`, resample it to
the sensor ODR with polyphase filtering, and feed that stream through the
virtual FIFO. The playback file and generated intermediates remain untracked.
The Python reference computes expected post-resampling RMS from the same replay
segment and filter coefficients used by firmware.

## Renode model

Renode 1.15.3 has no IIS3DWB model. The current prototype implements
`WHO_AM_I=0x7B`, the control registers used by initialization, FIFO
watermark/overrun/count status, and sequential seven-byte FIFO words sourced
from the binary replay. It is currently a combined mock SPI register window,
not a sensor peripheral connected to Renode's SPI controller; see the Phase 2
plan for the remaining controller/DMA integration work.

## Sources

- [IIS3DWB datasheet DS12569, Rev. 8](https://www.st.com/resource/en/datasheet/iis3dwb.pdf): fixed 26.7 kHz ODR and 3 KB FIFO (page 2), SPI protocol (section 3.2), FIFO modes and seven-byte words (section 4.3), FIFO BDR configuration (section 9.4–9.5).
- [IIS3DWB application note AN5444](https://www.st.com/resource/en/application_note/an5444-iis3dwb-ultrawide-bandwidth-lownoise-3axis-digital-vibration-sensor-stmicroelectronics.pdf): FIFO batching and timestamp-decimation behavior (section 6.1).

#!/usr/bin/env python3
"""
wbfm_lime.py – Capture 5 s of WBFM from a LimeSDR-Mini 2.0, demodulate,
               and visualise the spectrum & audio waveform.
"""
import SoapySDR
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import decimate
import soundfile as sf   # pip install soundfile

# ---------- Parameters ----------------------------------------------------
fc   = 103.7e6       # centre-frequency (Hz) – change to your local station
fs   = 2.048e6      # Lime sample-rate (complex)
gain = 40           # LMS7002M RF gain (dB) – adjust for ~ -12 dBFS max
secs = 5            # capture length
audio_fs = 48000    # final audio sample-rate
iq_file  = "fm_iq.bin"
wav_file = "fm_audio.wav"
# --------------------------------------------------------------------------

# 1) Open Lime via Soapy
dev = SoapySDR.Device(dict(driver="lime"))
dev.setSampleRate(SoapySDR.SOAPY_SDR_RX, 0, fs)
dev.setFrequency (SoapySDR.SOAPY_SDR_RX, 0, fc)
dev.setGain      (SoapySDR.SOAPY_SDR_RX, 0, gain)

# 2) Prepare stream
rx = dev.setupStream(SoapySDR.SOAPY_SDR_RX, "CF32")
dev.activateStream(rx)

# 3) Capture IQ
N = int(fs * secs)
buf = np.empty(N, dtype=np.complex64)
sptr = 0
while sptr < N:
    sr = dev.readStream(rx, [buf[sptr:]], N - sptr)
    if sr.ret > 0:
        sptr += sr.ret
print(f"Captured {sptr} samples.")
dev.deactivateStream(rx); dev.closeStream(rx)

buf.tofile(iq_file)          # optional: raw data for GNURadio/etc.

# 4) Basic wide-FM demodulation
#    a) FM discriminator (phase diff)
dphi = np.angle(buf[1:] * np.conj(buf[:-1]))
#    b) De-emphasis & decimate to audio_fs
audio = decimate(dphi, int(fs / audio_fs), ftype='fir')
audio /= np.max(np.abs(audio)) * 1.1  # normalise –1…1
sf.write(wav_file, audio.astype(np.float32), audio_fs)
print(f"Wrote {wav_file}")

# 5) Visualisation
plt.figure(figsize=(12, 6))

# Spectrum (first 1 M samples)
plt.subplot(2, 1, 1)
spec = np.fft.fftshift(np.fft.fft(buf[:1_000_000]))
freq = np.fft.fftshift(np.fft.fftfreq(len(spec), d=1/fs))
plt.plot(freq/1e6, 20*np.log10(np.abs(spec)+1e-3))
plt.title("RF Spectrum (~1 s snapshot)")
plt.xlabel("Offset (MHz)"); plt.ylabel("Magnitude (dB)"); plt.grid(True)

# Audio waveform (first 2 s)
plt.subplot(2, 1, 2)
t = np.arange(len(audio)) / audio_fs
plt.plot(t, audio)
plt.title("Demodulated audio (first 2 s)")
plt.xlabel("Time (s)"); plt.ylabel("Amplitude"); plt.xlim(0, 2)

plt.tight_layout(); plt.show()

# How to Build a Real-Time FM Radio and Spectrum Analyzer in Python ft LimeSDR Mini V2

Ever wondered how you can turn your computer and a simple Software-Defined Radio (SDR) into a buttery-smooth, real-time FM receiver and spectrum analyzer? It might seem complex, but with modern Python libraries, it's more achievable than you think.

## First Steps: Simple FM Capture and Process

1. Waking Up the Radio 📡
First, the script needs to communicate with the SDR hardware. It uses the SoapySDR library, a universal hardware abstraction layer, to find and configure the LimeSDR. It sets three crucial parameters:

- Center Frequency (fc): This tells the SDR which radio station to listen to (e.g., 103.7 MHz).

- Sample Rate (fs): This defines how many data points (samples) of the radio waves are captured per second.

- Gain (gain): This is like a volume knob for the radio antenna, amplifying the faint incoming signals.

```python
# 1) Open Lime via Soapy
dev = SoapySDR.Device(dict(driver="lime"))
dev.setSampleRate(SoapySDR.SOAPY_SDR_RX, 0, fs)
dev.setFrequency (SoapySDR.SOAPY_SDR_RX, 0, fc)
dev.setGain      (SoapySDR.SOAPY_SDR_RX, 0, gain)
```

2. Capturing the Signal
Unlike a real-time radio that plays audio continuously, this script captures a fixed five-second chunk of data all at once. It calculates the total number of samples needed, creates an empty NumPy array to hold them, and starts reading from the SDR in a loop until the buffer is full.

This raw data, known as IQ data, is a stream of complex numbers that represents the raw radio waves. The script saves this data directly to a file, which is useful for analysis in other tools.

```python
# 3) Capture IQ
N = int(fs * secs)
buf = np.empty(N, dtype=np.complex64)
sptr = 0
while sptr < N:
    sr = dev.readStream(rx, [buf[sptr:]], N - sptr)
    if sr.ret > 0:
        sptr += sr.ret
```

3. The Magic of FM Demodulation ✨
Now we have the raw radio signal, but how do we get sound out of it? This is where the digital signal processing (DSP) begins. For wideband FM, the script uses a straightforward two-step process.

FM Discriminator: The audio information in an FM signal is encoded in its frequency changes. A simple way to extract this is to calculate the change in phase between each consecutive sample. This line of NumPy code does it beautifully by multiplying the signal by a one-sample-delayed version of itself and finding the angle.

Decimation: The signal's sample rate is over 2 MHz, which is way too high for audio. scipy.signal.decimate is used to drastically lower the sample rate to a standard 48 kHz. As a bonus, this function also applies a high-quality filter that removes unwanted noise and artifacts.

The resulting audio is then normalized and saved as a .wav file.

```python
# 4) Basic wide-FM demodulation
#    a) FM discriminator (phase diff)
dphi = np.angle(buf[1:] * np.conj(buf[:-1]))
#    b) De-emphasis & decimate to audio_fs
audio = decimate(dphi, int(fs / audio_fs), ftype='fir')
```

4. Visualizing the Results 📊
Finally, to confirm everything worked, the script uses Matplotlib to create two plots.

RF Spectrum: This shows the frequency content of the raw radio signal we captured. You can clearly see the powerful broadcast signal at the center, surrounded by the noise of the radio spectrum.

Audio Waveform: This is a plot of the final, demodulated audio signal, showing the classic shape of sound waves over time.

```python
# 5) Visualisation
plt.figure(figsize=(12, 6))

# Spectrum (first 1 M samples)
plt.subplot(2, 1, 1)
# ... code to plot spectrum ...
plt.title("RF Spectrum (~1 s snapshot)")

# Audio waveform (first 2 s)
plt.subplot(2, 1, 2)
# ... code to plot audio ...
plt.title("Demodulated audio (first 2 s)")

plt.tight_layout(); plt.show()
```

This simple script was a fantastic starting point, demonstrating the entire core workflow of an SDR application: capture, process, and visualize.

## Tackling the Big Boy

Having gotten this down and done I decided to do a real-time fm radio with a full spectrum analyzer.
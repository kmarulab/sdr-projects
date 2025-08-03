# main.py
"""
WBFM Receiver Main Application

This script initializes and runs the WBFM receiver by coordinating
the SDR, audio, and GUI components.
"""
from __future__ import annotations
import matplotlib.pyplot as plt
import config
from shared_state import AppState
from sdr import SDRManager
from audio import AudioManager
from gui import SpectrumGUI

def main():
    """Initializes and runs all application components."""
    app_state = AppState(center_freq_mhz=config.CENTER_MHZ, volume=config.VOL_INIT)

    sdr_manager = SDRManager(app_state)
    audio_manager = AudioManager(app_state)
    gui = SpectrumGUI(app_state)

    try:
        sdr_manager.start()
        audio_manager.start()
        
        while gui.is_active():
            gui.update_plots()
            plt.pause(0.05)

    except (KeyboardInterrupt, SystemExit):
        print("\nShutting down.")
    finally:
        app_state.stop_event.set()
        audio_manager.stop()
        gui.close()
        print("Done.")

if __name__ == "__main__":
    main()
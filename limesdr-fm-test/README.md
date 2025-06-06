# Vibe Coded LimeSDR Mini 2.0 - FM Complete Receiver Chain
## Prelims

I initially intended to do everything inside a virtual enviroment, but soapysdr wasn't cooperating with pip so I ended up installing it as a system wide package, then added the other packages inside my virtual environment.

```bash
sudo apt install python3-soapysdr libsoapysdr-dev      
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install numpy scipy matplotlib soundfile
```
## Running
Do this inside your virtual environment

```bash
python3 limesdr-fm.py
```
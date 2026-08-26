"""
Install dependencies:
mpremote fs cp -r lib_common :/lib
"""

from machine import Pin
from utils.neopixelmanager import NeoPixelManager, Pulse, Wave
import time

PIN_NUM = 22
NUM_PIXELS = 32

# Create the strip manager and start with everything off.
np = NeoPixelManager(PIN_NUM, NUM_PIXELS)
np.clear()
np.write()

np.add_subset(8)
np.add_subset(8)
np.add_subset(8)
np.add_subset(8)

# Trigger a pulse across all 16 pixels, breathing between red and off,
# once every 2 seconds.
np.set_pattern(
    Pulse(
        color1=(0, 0, 50),
        color2=(0, 5, 80),
        period_ms=2000,
    ),
    id=0,
)

np.set_pattern(
    Pulse(
        color1=(25, 0, 25),
        color2=(40, 3, 40),
        period_ms=2000,
    ),
    id=1,
)
np.set_pattern(
    Wave(
        color1=(0, 0, 30),
        color2=(0, 0, 50),
        period_ms=2000,
    ),
    id=2,
)

np.set_pattern(
    Wave(
        color1=(0, 30, 0),
        color2=(0, 100, 0),
        period_ms=2000,
        phase_deg=180,
    ),
    id=3,
)

print("Pulsing... press Ctrl+C to stop")

try:
    while True:
        np.poll()  # recompute pulse colours and push to the strip
        time.sleep_ms(20)
except KeyboardInterrupt:
    pass
finally:
    np.reset()
    np.write()
    print("Stopped and cleared strip")

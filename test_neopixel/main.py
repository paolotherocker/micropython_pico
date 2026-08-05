import time
from machine import Pin
from neopixel import NeoPixel

NUM_LEDS = 8  # match your ring's pixel count
PIN_NUM = 10

np_1 = NeoPixel(Pin(PIN_NUM), NUM_LEDS)

np_1.fill((255, 0, 0))  # set all pixels red
np_1.write()
time.sleep(0.5)

np_1.fill((0, 0, 0))
np_1[0] = (0, 255, 127)
np_1.write()

np_2 = NeoPixel(Pin(11), NUM_LEDS)

np_2.fill((255, 0, 0))  # set all pixels red
np_2.write()
time.sleep(0.5)

np_2.fill((0, 0, 0))
np_2[0] = (0, 255, 127)
np_2.write()

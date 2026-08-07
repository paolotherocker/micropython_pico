import utime as time
from lib_common.rotary import Rotary, RotaryEvent
from machine import Pin

dt_pin = Pin(2, Pin.IN, Pin.PULL_UP)
clk_pin = Pin(3, Pin.IN, Pin.PULL_UP)
rotary = Rotary(dt_pin=dt_pin, clk_pin=clk_pin)

while True:
    evt = rotary.consume()
    if evt == RotaryEvent.CW:
        print("CW")
    elif evt == RotaryEvent.CCW:
        print("CCW")
    time.sleep_ms(10)

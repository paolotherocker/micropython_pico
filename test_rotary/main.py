import utime as time
from utils.ky040 import KY040, RotaryEvent
from utils.button import Button, ButtonEvent
from machine import Pin

BUTTON_PIN = const(4)  # GPIO pin the button is connected to

button = Button(BUTTON_PIN, Pin.PULL_UP)
led = Pin(25, Pin.OUT)

rotary = KY040(dt_pin=3, clk_pin=2, debounce_ms=1)

while True:
    rotary_event = rotary.consume()
    if rotary_event == RotaryEvent.CW:
        print("CW")
    elif rotary_event == RotaryEvent.CCW:
        print("CCW")

    button_event = button.consume()
    if button_event == ButtonEvent.PRESSED:
        print("SW")

    time.sleep_ms(10)

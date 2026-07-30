from machine import Pin
import time

BUTTON_PIN = 15      # GPIO pin the button is connected to
DEBOUNCE_MS = 100

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(25, Pin.OUT)


last_state = button.value()  # 1 = released (pull-up), 0 = pressed
last_change_time = time.ticks_ms()

while True:
    current_state = button.value()
    now = time.ticks_ms()

    if current_state != last_state and time.ticks_diff(now, last_change_time) > DEBOUNCE_MS:
        last_change_time = now
        last_state = current_state

        if current_state == 0:  # Button pressed (active low)
            led.on()
        else:  # Button released
            led.off()
from machine import Pin
from micropython import const
import time

BUTTON_PIN = const(15)      # GPIO pin the button is connected to
DEBOUNCE_MS = const(100)
LONG_PRESS_MS = const(600)


class Button:

    OFF = const(0)
    SHORT_PRESS = const(1)
    LONG_PRESS = const(2)

    def __init__(self, pin_:int):
        self._button = Pin(pin_, Pin.IN, Pin.PULL_UP)
        self._button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._on_irq)
        self._last_edge = time.ticks_ms()
        self._previous_edge = self._last_edge
        self._state = self.OFF

    def _on_irq(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_edge) < DEBOUNCE_MS:
            return  # ignore bounce
        self._previous_edge = self._last_edge
        self._last_edge = now

    def consume(self)->int:
        now = time.ticks_ms()

        old_state = self._state

        # the button is pressed, check if was pressed long enough for long press
        if self._button.value() == 0:
            if time.ticks_diff(now, self._last_edge) > LONG_PRESS_MS:
                self._state = self.LONG_PRESS
            else:
                self._state = self.OFF
        # the button is not pressed, check that we aren't following a long press
        else:
            if time.ticks_diff(self._last_edge, self._previous_edge) < LONG_PRESS_MS:
                # reset the time so this can only happen once
                self._previous_edge = 0
                self._state = self.SHORT_PRESS
            else:
                self._state = self.OFF

        if old_state != self._state:
            return self._state
        else:
            return self.OFF
        
        
button = Button(BUTTON_PIN)
led = Pin(25, Pin.OUT)

button_state = 0
prev_state = button_state

while True:
    prev_state = button_state
    button_state = button.consume()

    if button_state != Button.OFF:
        print(button_state)
        
    time.sleep_ms(100)
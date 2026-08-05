"""
Dependencies:
mpremote mip install enum
"""

from machine import Pin
from micropython import const
import time


class ButtonEvent:
    NONE = const(0)
    SHORT_PRESS = const(1)
    LONG_PRESS = const(2)


class Button:

    def __init__(self, pin: int, debounce_ms: int = 30, long_press_ms: int = 600):
        self._button = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._on_irq)
        self._debounce_ms = debounce_ms
        self._long_press_ms = long_press_ms

        self._last_edge = time.ticks_ms()
        self._flag = False
        self._long_press = False

    def _on_irq(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_edge) < self._debounce_ms:
            return  # ignore bounce
        self._last_edge = now

        # If the previous event was a long press, don't set the flag to avoid triggering a short press
        if self._long_press == True:
            self._long_press = False
        else:
            self._flag = True

    def is_pressed(self) -> bool:
        return self._button.value() == 0

    def consume_event(self) -> ButtonEvent:
        now = time.ticks_ms()

        if self._flag == False:
            return ButtonEvent.NONE

        # the button is pressed, check if was pressed long enough for long press
        # continue without resetting the flag
        if self.is_pressed():
            if time.ticks_diff(now, self._last_edge) > self._long_press_ms:
                self._long_press = True
                self._flag = False
                return ButtonEvent.LONG_PRESS
        # the button is not pressed, check that we aren't following a long press
        else:
            self._flag = False
            return ButtonEvent.SHORT_PRESS

        return ButtonEvent.NONE

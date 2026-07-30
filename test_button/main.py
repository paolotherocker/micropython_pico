from machine import Pin
from micropython import const
import time

BUTTON_PIN = const(15)      # GPIO pin the button is connected to
DEBOUNCE_MS = const(30)
LONG_PRESS_MS = const(600)


class Button:

    OFF = const(0)
    SHORT_PRESS = const(1)
    LONG_PRESS = const(2)

    def __init__(self, pin_:int):
        self._button = Pin(pin_, Pin.IN, Pin.PULL_UP)
        self._button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._on_irq)
        self._last_edge = time.ticks_ms()
        self._flag = False
        self._long_press = False

    def _on_irq(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_edge) < DEBOUNCE_MS:
            return  # ignore bounce
        self._last_edge = now

        # If the previous event was a long press, don't set the flag to avoid triggering a short press
        if self._long_press == True:
            self._long_press = False
        else:
            self._flag = True

    def consume(self)->int:
        now = time.ticks_ms()
        is_pressed = self._button.value() == 0

        if self._flag == False:
            return self.OFF

        # the button is pressed, check if was pressed long enough for long press
        # continue without resetting the flag
        if is_pressed:
            if time.ticks_diff(now, self._last_edge) > LONG_PRESS_MS:
                self._long_press = True
                self._flag = False
                return self.LONG_PRESS
        # the button is not pressed, check that we aren't following a long press
        else:
            self._flag = False
            return self.SHORT_PRESS

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
        
    time.sleep_ms(10)
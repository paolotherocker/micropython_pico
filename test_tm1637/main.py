"""
mpremote mip install github:mcauser/micropython-tm1637
"""

import tm1637
from machine import Pin, Timer

k_led_pin = int(25)
k_btn_pin = int(6)


class Test_tm1637:
    def __init__(self) -> None:
        self.disp = tm1637.TM1637(clk=Pin(19), dio=Pin(18))
        self.led = Pin(k_led_pin, Pin.OUT)
        self.value = 0
        self.btn = Pin(k_btn_pin, Pin.IN, Pin.PULL_UP)
        self.button_timer = Timer()

        self.disp.brightness(3)
        self.btn.irq(handler=self.button_callback)

        self.led.off()
        self.disp.show(f"P{self.value:3}")

    def button_callback(self, pin: Pin):

        def button_timer_callback(timer: Timer):
            self.value += 1
            if self.value > 127:
                self.value = 0

            self.disp.show(f"P{self.value:3}")

            if self.btn.value() is 0:
                self.led.on()
            else:
                self.led.off()

        # Delay the action for a few milliseconds to reject some noise
        self.button_timer.init(
            mode=Timer.ONE_SHOT, period=20, callback=button_timer_callback
        )


tm = Test_tm1637()

while 1:
    pass

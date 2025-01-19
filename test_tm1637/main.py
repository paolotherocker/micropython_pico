import tm1637
from machine import Pin

k_led_pin = int(25)
k_btn_pin = int(16)


class Test_tm1637:
    def __init__(self) -> None:
        self.disp = tm1637.TM1637(clk=Pin(26), dio=Pin(27))
        self.led = Pin(k_led_pin, Pin.OUT)
        self.value = 0
        self.btn = Pin(k_btn_pin, Pin.IN, Pin.PULL_UP)

        self.disp.brightness(3)
        self.btn.irq(handler=self.button_callback)

        self.led.off()
        self.disp.show(f"P{self.value:3}")

    def button_callback(self, pin: Pin):
        self.value += 1
        if self.value > 127:
            self.value = 0

        self.disp.show(f"P{self.value:3}")

        if self.btn.value() is 0:
            self.led.on()
        else:
            self.led.off()


tm = Test_tm1637()

while 1:
    pass

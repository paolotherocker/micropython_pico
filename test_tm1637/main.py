import tm1637
from machine import Pin


class Test_tm1637:
    def __init__(self) -> None:
        self.disp = tm1637.TM1637(clk=Pin(26), dio=Pin(27))
        self.led = Pin(25, Pin.OUT)
        self.value = 0
        self.btn = Pin(16, Pin.IN, Pin.PULL_UP)

        self.disp.brightness(3)
        self.btn.irq(handler=self.button_callback)

        self.led.off()
        self.disp.show("P   ")

    def button_callback(self, pin: Pin):
        self.value += 1
        self.disp.show(f"P{self.value:3}")

        if self.btn.value() is 0:
            self.led.on()
        else:
            self.led.off()


tm = Test_tm1637()

while 1:
    pass

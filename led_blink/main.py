from machine import Pin, Timer

led = Pin(25, Pin.OUT)
timer = Timer()


def blink(timer: Timer):
    led.toggle()


timer.init(freq=2, mode=Timer.PERIODIC, callback=blink)

while True:
    pass

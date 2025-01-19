from machine import Pin, Timer, PWM

State: dict[str, int] = {"UP": 0, "DOWN": 1}

k_pwm_max = 65025


def pwm_duty(ratio: float) -> int:
    """Calculate PWM duty cycle from a ratio (0.0 to 1.0)"""
    return int(k_pwm_max * max(min(ratio, 1.0), 0.0))


class LedFader:
    def __init__(self) -> None:
        self.brightness = 0.0
        self.timer = Timer()
        self.led = PWM(Pin(25, Pin.OUT))
        self.state = State["UP"]

        self.led.freq(1000)
        self.timer.init(period=5, mode=Timer.PERIODIC, callback=self.update)

    def update(self, timer):
        if self.brightness >= 1:
            self.state = State["DOWN"]
        elif self.brightness <= 0:
            self.state = State["UP"]

        if self.state is State["UP"]:
            self.brightness += 0.01
        elif self.state is State["DOWN"]:
            self.brightness -= 0.01

        self.led.duty_u16(pwm_duty(self.brightness))


led_fader = LedFader()

while True:
    pass

import tm1637
from machine import Pin, Timer, PWM
from enum import Enum


def pwm_duty_pct(pct: float) -> float:
    return 65025 * pct * 0.01


patch_btn = [
    Pin(14, Pin.IN, Pin.PULL_DOWN),
    Pin(15, Pin.IN, Pin.PULL_DOWN),
    Pin(16, Pin.IN, Pin.PULL_DOWN),
]
btn_page_up = Pin(17, Pin.IN, Pin.PULL_DOWN)
btn_page_down = Pin(19, Pin.IN, Pin.PULL_DOWN)
btn_cfg = Pin(20, Pin.IN, Pin.PULL_DOWN)
patch_led = [PWM(Pin(24, Pin.OUT)), PWM(Pin(25, Pin.OUT)), PWM(Pin(26, Pin.OUT))]
disp = tm1637.TM1637(clk=Pin(31), dio=Pin(32))


class UpdateValue(Enum):
    DOWN = -1
    UP = 1


class State(Enum):
    IDLE = 0
    PAGE_CHANGE = 1
    PAGE_CHANGE_WAIT = 2
    SEND_PC_MESSAGE = 3
    PROGRAM_CHANGE_DISP = 4
    CONFIG = 5


class MidiProgramManager:
    def __init__(self) -> None:
        self.midi_program = 0
        self.midi_channel = 0
        self.page = 0
        self.patch = 0

    def set_patch(self, patch_number: int):
        self.patch = patch_number
        self._update_program()

    def set_page(self, page_number: int):
        self.page = page_number
        self._update_program()

    def update_page(self, value: UpdateValue):
        self.page += value.value
        self._update_program()

    def update_channel(self, value: UpdateValue):
        self.midi_channel += value.value

    def _update_program(self):
        self.midi_program = self.page * 3 + self.patch


class MidiProgramController:
    def __init__(self) -> None:
        self.pm = MidiProgramManager()

        self.state = State.IDLE

        self.send_timer = Timer()
        self.update_timer = Timer()

        for led in patch_led:
            led.freq(1000)

        for idx, btn in enumerate(patch_btn):
            btn.irq(trigger=Pin.IRQ_RISING, handler=lambda: self.patch_callback(idx))

        btn_page_up.irq(trigger=Pin.IRQ_RISING, handler=lambda: self.page_callback(UpdateValue.UP))
        btn_page_down.irq(
            trigger=Pin.IRQ_RISING, handler=lambda: self.page_callback(UpdateValue.DOWN)
        )
        btn_cfg.irq(trigger=Pin.IRQ_RISING, handler=setattr(self, "state", State.CONFIG))
        btn_cfg.irq(trigger=Pin.IRQ_FALLING, handler=setattr(self, "state", State.SEND_PC_MESSAGE))

        # Main update loop
        self.update_timer.init(mode=Timer.PERIODIC, freq=120, callback=self.update_callback)

    def patch_callback(self, value: int):
        # Don't do anything if we are in configuration mode
        self.pm.set_patch(value)
        self.state = State.SEND_PC_MESSAGE

    def page_callback(self, value: UpdateValue):
        if self.state is State.CONFIG:
            self.pm.update_channel(value)
        else:
            self.state = State.PAGE_CHANGE
            self.pm.update_page(value)

    def send_midi_pc(self):
        pass

    def update_callback(self):
        # Update LED states
        for led in patch_led:
            led.duty_u16(0)

        if self.state is State.PAGE_CHANGE:
            patch_led[self.pm.patch].duty_u16(pwm_duty_pct(50))
        else:
            patch_led[self.pm.patch].duty_u16(pwm_duty_pct(100))

        # Refresh display
        match self.state:
            case State.IDLE:
                disp.number(self.pm.page)

            case State.PAGE_CHANGE:
                disp.number(self.pm.page)

                # Go into wait mode and trigger a send state after a short period
                self.state = State.PAGE_CHANGE_WAIT
                self.send_timer.init(
                    mode=Timer.ONE_SHOT,
                    period=500,
                    callback=lambda: setattr(self, "state", State.SEND_PC_MESSAGE),
                )

            case State.PAGE_CHANGE_WAIT:
                disp.number(self.pm.page)

            case State.SEND_PC_MESSAGE:
                self.send_midi_pc()
                disp.show(f"P{self.pm.midi_program:3}")

                # Go into program display mode and trigger the idle state after a short period
                self.state = State.PROGRAM_CHANGE_DISP
                self.send_timer.init(
                    mode=Timer.ONE_SHOT,
                    period=250,
                    callback=lambda: setattr(self, "state", State.IDLE),
                )

            case State.PROGRAM_CHANGE_DISP:
                self.send_timer.deinit()
                disp.show(f"P{self.pm.midi_program:3}")

            case State.CONFIG:
                self.send_timer.deinit()
                disp.show(f"C{self.pm.midi_channel:3}")

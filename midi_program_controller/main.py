import tm1637
from machine import Pin, Timer, PWM, UART
from enum import Enum
import math

patch_btn = [
    Pin(14, Pin.IN, Pin.PULL_DOWN),
    Pin(15, Pin.IN, Pin.PULL_DOWN),
    Pin(16, Pin.IN, Pin.PULL_DOWN),
]
btn_page_up = Pin(17, Pin.IN, Pin.PULL_DOWN)
btn_page_down = Pin(19, Pin.IN, Pin.PULL_DOWN)
btn_cfg = Pin(20, Pin.IN, Pin.PULL_DOWN)
patch_led = [PWM(Pin(24, Pin.OUT)), PWM(Pin(25, Pin.OUT)), PWM(Pin(26, Pin.OUT))]
send_led = Pin(27, Pin.OUT)
disp = tm1637.TM1637(clk=Pin(31), dio=Pin(32))

k_midi_uart_id = 0
k_pages = math.ceil(127 / len(patch_btn))


def pwm_duty(pct: float) -> float:
    """Calculate PWM duty cycle from a percentage value"""
    return 65025 * max(min(pct, 100.0), 0.0) * 0.01


class State(Enum):
    IDLE = 0
    PAGE_CHANGE = 1
    PAGE_CHANGE_WAIT = 2
    SEND_PC_MESSAGE = 3
    PROGRAM_CHANGE_DISP = 4
    CONFIG = 5


class Midi:
    def __init__(self, UART_id: int) -> None:
        self.channel = int(0)
        self.uart = UART(UART_id)
        self.uart.init(baudrate=31250)

    def set_channel(self, channel: int):
        if channel < 0 or channel > 15:
            print(f"Channel {channel} request is out of bound")
            return
        self.channel = channel

    def write_program_change(self, program: int) -> None:
        self.uart.write(bytearray([0xC0 | self.channel, program]))


class MidiProgramManager:
    def __init__(self) -> None:
        self.program = int(0)
        self.page = int(0)
        self.patch = int(0)

    def set_patch(self, patch_number: int):
        self.patch = patch_number
        self._update_program()

    def set_page(self, page_number: int):
        if page_number < 0 or page_number > k_pages:
            print(f"Page {page_number} request is out of bound")
            return
        self.page = page_number
        self._update_program()

    def _update_program(self):
        self.program = max(min(self.page * 3 + self.patch, 127), 0)


class MidiProgramController:
    def __init__(self) -> None:
        self.midi = Midi(k_midi_uart_id)
        self.pm = MidiProgramManager()

        self.state = State.IDLE

        self.send_timer = Timer()
        self.update_timer = Timer()

        for led in patch_led:
            led.freq(1000)

    def init(self, frequency: int):
        """Link callbacks and start main update timer

        :param int frequency: frequency at which the state machine and display are updated
        """
        for idx, btn in enumerate(patch_btn):
            btn.irq(trigger=Pin.IRQ_RISING, handler=lambda p: self.patch_press_callback(idx))
            btn.irq(
                trigger=Pin.IRQ_FALLING,
                handler=self.patch_release_callback,
            )

        btn_page_up.irq(trigger=Pin.IRQ_RISING, handler=lambda p: self.page_update_callback(1))
        btn_page_down.irq(trigger=Pin.IRQ_RISING, handler=lambda p: self.page_update_callback(-1))
        btn_cfg.irq(trigger=Pin.IRQ_RISING, handler=lambda p: setattr(self, "state", State.CONFIG))
        btn_cfg.irq(
            trigger=Pin.IRQ_FALLING, handler=lambda p: setattr(self, "state", State.SEND_PC_MESSAGE)
        )

        # Main update loop
        self.update_timer.init(mode=Timer.PERIODIC, freq=frequency, callback=self.update_callback)

    def patch_press_callback(self, value: int):
        self.pm.set_patch(value)
        self.state = State.SEND_PC_MESSAGE

    def patch_release_callback(self, pin: Pin):
        if self.state is State.PROGRAM_CHANGE_DISP:
            self.state = State.IDLE

    def page_update_callback(self, delta: int):
        if self.state is State.CONFIG:
            self.midi.set_channel(self.midi.channel + delta)
        else:
            self.pm.set_page(self.pm.page + delta)
            self.state = State.PAGE_CHANGE

    def send_midi_pc(self):
        pass

    def update_callback(self, timer: Timer):
        led_brightness = 100.0

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
                    callback=lambda t: setattr(self, "state", State.SEND_PC_MESSAGE),
                )

            case State.PAGE_CHANGE_WAIT:
                led_brightness = 25.0
                disp.number(self.pm.page)

            case State.SEND_PC_MESSAGE:
                self.send_timer.deinit()
                self.midi.write_program_change(self.pm.program)

                # Blink the send LED once
                send_led.on()
                self.send_timer.init(
                    mode=Timer.ONE_SHOT, period=250, callback=lambda t: send_led.off()
                )

                # Go into program display mode and trigger the idle state after a short period
                self.state = State.PROGRAM_CHANGE_DISP

            case State.PROGRAM_CHANGE_DISP:
                disp.show(f"P{self.pm.program:3}")

            case State.CONFIG:
                self.send_timer.deinit()

                led_brightness = 25.0
                # Add one to the Midi channel being displayed, as this seems to be quite common
                disp.show(f"C{self.midi.channel + 1:3}")

        # Update LED states
        for led in patch_led:
            led.duty_u16(0)
        patch_led[self.pm.patch].duty_u16(pwm_duty(led_brightness))


midi_pc = MidiProgramController()
midi_pc.init(frequency=120)

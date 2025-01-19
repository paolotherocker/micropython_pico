import tm1637
from machine import Pin, Timer, PWM, UART
import math
import json
from typing import Any

# Pins
p_patch_btn = [14, 15, 16]
p_patch_led = [24, 25, 26]
p_page_up = 17
p_page_down = 19
p_cfg = 20
p_send_led = 27
# Other constants
k_midi_uart_id = 0
k_pages = math.ceil(127 / len(p_patch_btn))
k_file_name = "data.json"
k_pwm_max = 65025


def pwm_duty(ratio: float) -> float:
    """Calculate PWM duty cycle from a ratio (0.0 to 1.0)"""
    return k_pwm_max * max(min(ratio, 1.0), 0.0)


class State:
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
        # Try to read from file first
        data = dict[str, Any]()
        try:
            data = json.load(open(k_file_name))
        except:
            pass

        self.program = data.get("program", 0)
        self.page = data.get("page", 0)
        self.patch = data.get("patch", 0)

    def set_patch(self, patch_number: int):
        self.patch = patch_number
        self._update_program()

    def set_page(self, page_number: int):
        if page_number < 0 or page_number > k_pages:
            print(f"Page {page_number} request is out of bound")
            return
        self.page = page_number
        self._update_program()

    def save_to_file(self) -> None:
        data = dict[str, Any]()
        data["program"] = self.program
        data["page"] = self.page
        data["patch"] = self.patch
        file = open(k_file_name, "w")
        json.dump(data, file)

    def _update_program(self):
        self.program = max(min(self.page * 3 + self.patch, 127), 0)


class MidiProgramController:
    def __init__(self) -> None:
        # Hardware
        self.patch_btn = [Pin(x, Pin.IN, Pin.PULL_UP) for x in p_patch_btn]
        self.btn_page_up = Pin(p_page_up, Pin.IN, Pin.PULL_UP)
        self.btn_page_down = Pin(p_page_down, Pin.IN, Pin.PULL_UP)
        self.btn_cfg = Pin(p_cfg, Pin.IN, Pin.PULL_UP)
        self.patch_led = [PWM(Pin(p, Pin.OUT)) for p in p_patch_led]
        self.send_led = Pin(p_send_led, Pin.OUT)
        self.disp = tm1637.TM1637(clk=Pin(31), dio=Pin(32))
        self.midi = Midi(k_midi_uart_id)

        # Internal variables
        self.pm = MidiProgramManager()
        self.state = State.IDLE
        self.send_timer = Timer()
        self.update_timer = Timer()

        for led in self.patch_led:
            led.freq(1000)

    def init(self, frequency: int):
        """Link callbacks and start main update timer

        :param int frequency: frequency at which the state machine and display are updated
        """
        for idx, btn in enumerate(self.patch_btn):

            def patch_callback(p: Pin):
                if p.value() is 0:
                    self.pm.set_patch(idx)
                    self.state = State.SEND_PC_MESSAGE
                elif self.state is State.PROGRAM_CHANGE_DISP:
                    self.state = State.IDLE

            btn.irq(handler=patch_callback)

        self.btn_page_up.irq(trigger=Pin.IRQ_FALLING, handler=self.page_up_callback)
        self.btn_page_down.irq(trigger=Pin.IRQ_FALLING, handler=self.page_down_callback)
        self.btn_cfg.irq(handler=self.cfg_callback)

        # Main update loop
        self.update_timer.init(
            mode=Timer.PERIODIC, freq=frequency, callback=self.update_callback
        )

    def cfg_callback(self, p: Pin):
        if p.value() is 0:
            self.state = State.CONFIG
        else:
            self.state = State.SEND_PC_MESSAGE

    def page_up_callback(self, p: Pin):
        if self.state is State.CONFIG:
            self.midi.set_channel(self.midi.channel + 1)
        else:
            self.pm.set_page(self.pm.page + 1)
            self.state = State.PAGE_CHANGE

    def page_down_callback(self, p: Pin):
        if self.state is State.CONFIG:
            self.midi.set_channel(self.midi.channel - 1)
        else:
            self.pm.set_page(self.pm.page - 1)
            self.state = State.PAGE_CHANGE

    def set_patch_led(self, brightness: float):
        for led in self.patch_led:
            led.duty_u16(0)
        self.patch_led[self.pm.patch].duty_u16(pwm_duty(brightness))

    def update_callback(self, timer: Timer):
        led_brightness = 1.0

        # Refresh display
        if self.state is State.IDLE:
            self.disp.number(self.pm.page)

        elif self.state is State.PAGE_CHANGE:
            self.disp.number(self.pm.page)

            # Go into wait mode and trigger a send state after a short period
            self.state = State.PAGE_CHANGE_WAIT
            self.send_timer.init(
                mode=Timer.ONE_SHOT,
                period=500,
                callback=lambda t: setattr(self, "state", State.SEND_PC_MESSAGE),
            )

        elif self.state is State.PAGE_CHANGE_WAIT:
            led_brightness = 0.25
            self.disp.number(self.pm.page)

        elif self.state is State.SEND_PC_MESSAGE:
            self.send_timer.deinit()
            self.midi.write_program_change(self.pm.program)
            self.pm.save_to_file()

            # Blink the send LED once
            self.send_led.on()
            self.send_timer.init(
                mode=Timer.ONE_SHOT,
                period=250,
                callback=lambda t: self.send_led.off(),
            )

            # Go into program display mode and trigger the idle state after a short period
            self.state = State.PROGRAM_CHANGE_DISP

        elif self.state is State.PROGRAM_CHANGE_DISP:
            self.disp.show(f"P{self.pm.program:3}")

        elif self.state is State.CONFIG:
            self.send_timer.deinit()

            led_brightness = 0.25
            # Add one to the Midi channel being displayed, as this seems to be quite common
            self.disp.show(f"C{self.midi.channel + 1:3}")

        # Update LED states
        self.set_patch_led(led_brightness)


midi_pc = MidiProgramController()
midi_pc.init(frequency=120)

while 1:
    pass

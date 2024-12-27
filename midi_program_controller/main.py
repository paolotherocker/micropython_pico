import picozero
import tm1637
from machine import Pin, Timer
from enum import Enum


class DisplayState(Enum):
    PAGE = 0
    MIDI_PROGRAM = 1
    MIDI_CHANNEL = 2


class HardwareManager:
    def __init__(self) -> None:
        # Buttons
        self.b_0 = picozero.Button(14)
        self.b_1 = picozero.Button(15)
        self.b_2 = picozero.Button(16)
        self.b_page_down = picozero.Button(17)
        self.b_page_up = picozero.Button(19)
        self.b_cfg = picozero.Button(20)
        # LEDs
        self.led_0 = picozero.LED(24)
        self.led_1 = picozero.LED(25)
        self.led_2 = picozero.LED(26)
        # Display
        self.tm = tm1637.TM1637(clk=Pin(31), dio=Pin(32))

    def set_patch_led(self, id: int = -1):
        self.led_0.off()
        self.led_1.off()
        self.led_2.off()
        match id:
            case 0:
                self.led_0.on()
            case 1:
                self.led_1.on()
            case 2:
                self.led_2.on()

    def display_page(self, page: int):
        self.tm.number(page)

    def display_program(self, program: int):
        self.tm.show(f"P{program:3}")

    def display_channel(self, channel: int):
        self.tm.show(f"C{channel:3}")


class MidiProgramManager:
    def __init__(self) -> None:
        self.midi_program = 0
        self.midi_channel = 0
        self.page = 0
        self.patch = 0

    def set_patch(self, patch_number: int):
        self.patch = patch_number
        self.update_program()

    def set_page(self, page_number: int):
        self.page = page_number
        self.update_program()

    def update_page(self, delta: int):
        self.page += delta
        self.update_program()

    def update_channel(self, delta: int):
        self.midi_channel += delta

    def update_program(self):
        self.midi_program = self.page * 3 + self.patch


class MidiProgramController:
    def __init__(self):
        self.hw = HardwareManager()
        self.pm = MidiProgramManager()

        self.send_timer = Timer()
        # The display refreshes at a constant
        self.display_refresh_timer = Timer()
        self.display_refresh_timer.init(
            mode=Timer.PERIODIC, freq=60, callback=self.display_refresh_timer
        )

        self.display_state = DisplayState.PAGE
        self.midi_program = 0
        self.page = 0
        self.patch = 0

        self.hw.b_0.when_activated = lambda: self.patch_update(0)
        self.hw.b_1.when_activated = lambda: self.patch_update(1)
        self.hw.b_2.when_activated = lambda: self.patch_update(2)
        self.hw.b_page_down.when_activated = lambda: self.page_update(-1)
        self.hw.b_page_up.when_activated = lambda: self.page_update(1)
        self.hw.b_cfg.when_activated = self.cfg_on
        self.hw.b_cfg.when_deactivated = self.cfg_off

    def send_midi_program_change(self):
        # Show the midi program being sent for a brief period
        self.display_state = DisplayState.MIDI_PROGRAM
        self.send_timer.deinit()
        self.send_timer.init(mode=Timer.ONE_SHOT, period=100, callback=self.cfg_off)

        # Send the midi program change request

    def refresh_display(self):
        match self.display_state:
            case DisplayState.PAGE:
                self.hw.display_page(self.pm.page)
            case DisplayState.MIDI_PROGRAM:
                self.hw.display_program(self.pm.midi_program)
            case DisplayState.MIDI_CHANNEL:
                self.hw.display_channel(self.pm.midi_channel)

    def patch_update(self, patch_number: int):
        if self.hw.b_cfg.is_active:
            return
        self.pm.set_patch(patch_number)
        self.hw.set_patch_led(patch_number)
        self.send_midi_program_change()

    def page_update(self, delta: int):
        if self.hw.b_cfg.is_active:
            self.pm.update_channel(delta)
        else:
            self.display_state = DisplayState.PAGE
            self.pm.update_page(delta)
        # Delay the prgram change message a bit, in case you are searching through the pages
        self.send_timer.init(
            period=500, mode=Timer.ONE_SHOT, callback=self.send_midi_program_change
        )

    def cfg_on(self):
        self.display_state = DisplayState.MIDI_CHANNEL

    def cfg_off(self):
        self.display_state = DisplayState.PAGE


while True:
    pass

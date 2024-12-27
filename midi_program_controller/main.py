import picozero
from machine import Timer


class HardwareManager:
    def __init__(self) -> None:
        self.b_0 = picozero.Button(14)
        self.b_1 = picozero.Button(15)
        self.b_2 = picozero.Button(16)
        self.b_page_down = picozero.Button(17)
        self.b_page_up = picozero.Button(19)
        self.b_cfg = picozero.Button(20)
        self.led_0 = picozero.LED(24)
        self.led_1 = picozero.LED(25)
        self.led_2 = picozero.LED(26)

    def set_patch_led(self, id: int):
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

    def update_program(self):
        self.program = self.page * 3 + self.patch


class MidiProgramController:
    def __init__(self):
        self.hw = HardwareManager()
        self.pm = MidiProgramManager()

        self.send_timer = Timer()
        self.midi_program = 0
        self.page = 0
        self.patch = 0

        self.hw.b_0.when_activated = lambda: self.patch_update(0)
        self.hw.b_1.when_activated = lambda: self.patch_update(1)
        self.hw.b_2.when_activated = lambda: self.patch_update(2)
        self.hw.b_page_down.when_activated = lambda: self.page_update(-1)
        self.hw.b_page_up.when_activated = lambda: self.page_update(1)

    def patch_update(self, patch_number: int):
        self.pm.set_patch(patch_number)
        self.hw.set_patch_led(patch_number)
        self.send_midi_program_change()

    def page_update(self, delta: int):
        self.pm.update_page(delta)
        self.send_timer.init(
            period=500, mode=Timer.ONE_SHOT, callback=self.send_midi_program_change
        )

    def send_midi_program_change(self):
        self.send_timer.deinit()
        pass


while True:
    pass

from lib_common.button import Button, ButtonEvent
from lib_common.neopixelmanager import NeoPixelManager, Pulse, Solid
from lib_common.rotary import Rotary, RotaryEvent
from tm1637 import TM1637


class PatchManager:
    """Manages the control buttons, LEDs and the rotary encoder to generate MIDI messages"""

    _PATCH_MAP = [" ", "A", "B", "C", "D", "E", "F", "G", "H"]

    def __init__(
        self,
        controls: list[Button],
        np: NeoPixelManager,
        encoder: Rotary,
        display: TM1637,
    ):
        self.controls = controls
        self.num_c = len(controls)
        self.np = np
        self.encoder = encoder
        self.display = display

        self.c_active_1: list[tuple]
        self.c_active_2: list[tuple]
        self.c_passive: list[tuple]
        self.preset_up: int
        self.preset_down: int
        self.preset_num: int

        self.active: int = -1
        self.mode: list[int] = [0, 0, 0, 0]  # 0 for primary 1 for secondary

        self.preset: int = 1
        self.snap: int = 0

        self.display.brightness(3)
        self.display.show("")

    def update(self):
        event_id = -1
        event = ButtonEvent.NONE

        for ctrl in self.controls:
            event_id = event_id + 1
            event = ctrl.consume()
            if event != ButtonEvent.NONE:
                break

        if event == ButtonEvent.SHORT_PRESS:
            self.np.clear()

            if event_id == self.active:
                self.mode[event_id] = 1 - self.mode[event_id]
            self.active = event_id

            for i in range(self.num_c):
                mode = self.mode[i]  # primary or secondary
                if i == event_id:
                    self.np.set_pattern(
                        Pulse(
                            color1=self.c_active_1[mode],
                            color2=self.c_active_2[mode],
                            period_ms=2000,
                        ),
                        id=i,
                    )
                else:
                    self.np.set_pattern(Solid(color=self.c_passive[mode]), id=i)

            self.snap = event_id * 2 + self.mode[event_id] + 1

        elif event == ButtonEvent.LONG_PRESS:
            if event_id == self.preset_up:
                self.preset = self.preset + 1
            elif event_id == self.preset_down:
                self.preset = self.preset - 1

            # Wrap around 1 and the maximum
            if self.preset < 1:
                self.preset = self.preset_num
            elif self.preset > self.preset_num:
                self.preset = 1

        if event != ButtonEvent.NONE:
            buffer = " " + self._PATCH_MAP[self.preset] + " " + str(self.snap)
            self.display.show(buffer)

        self.np.update()
        self.np.write()

from lib_common.button import Button, ButtonEvent
from lib_common.neopixelmanager import NeoPixelManager
from lib_common.rotary import Rotary, RotaryEvent


class PatchManager:
    """_summary_"""

    c_active_1: list[tuple]
    c_active_2: list[tuple]
    c_passive: list[tuple]

    def __init__(self, controls: list[Button], np: NeoPixelManager, encoder: Rotary):
        self.controls = controls
        self.num_c = len(controls)
        self.np = np
        self.encoder = encoder

        self.active: int = -1
        self.mode: list[int] = [0, 0, 0, 0]  # 0 for primary 1 for secondary

        self.preset: int = 0
        self.snap: int = 0

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
                    self.np.add_pulse(
                        color1=self.c_active_1[mode],
                        color2=self.c_active_2[mode],
                        period_ms=2000,
                        id=i,
                    )
                else:
                    self.np.fill(color=self.c_passive[mode], id=i)

            self.snap = event_id * 2 + self.mode[event_id]
            print("snap: " + str(self.snap))

        self.np.update()
        self.np.write()

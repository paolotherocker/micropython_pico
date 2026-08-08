from lib_common.button import Button, ButtonEvent
from lib_common.neopixelmanager import NeoPixelManager
from lib_common.rotary import Rotary, RotaryEvent


class PatchManager:
    """_summary_"""

    def __init__(self, controls: list[Button], np: NeoPixelManager, encoder: Rotary):
        self.controls = controls
        self.num_c = len(controls)
        self.np = np
        self.encoder = encoder

        self.preset: int = 0
        self.active: int = 0
        self.mode: list[int] = [0, 0, 0, 0]  # 0 for primary 1 for secondary
        self.c_active_1: list[tuple] = [(0, 200, 32), (0, 32, 200)]
        self.c_active_2: list[tuple] = [(0, 200, 96), (0, 96, 200)]
        self.c_passive: list[tuple] = [(0, 100, 48), (0, 48, 100)]

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

            print()
            for i in range(self.num_c):
                mode = self.mode[i]  # primary or secondary
                if i == event_id:
                    self.np.add_pulse(
                        color1=self.c_active_1[mode],
                        color2=self.c_active_2[mode],
                        period_ms=1000,
                        id=i,
                    )
                else:
                    self.np.fill(color=self.c_passive[mode], id=i)

        self.np.update()
        self.np.write()

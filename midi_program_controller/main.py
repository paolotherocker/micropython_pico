import tm1637
from machine import Pin, Timer, PWM, UART
import math
import json

# Pins
p_patch_btn = [6, 7, 8]
p_patch_led = [18, 19, 20]
p_page_up = 10
p_page_down = 9
p_send_led = 21
p_disp_clk = 26
p_disp_dio = 27
# Other constants
k_midi_uart_id = 0
k_pages = math.ceil(127 / len(p_patch_btn))
k_file_name = "data.json"
k_pwm_max = 65025
k_midi_channel = 0


def pwm_duty(ratio: float) -> int:
    """Calculate PWM duty cycle from a ratio (0.0 to 1.0)"""
    return int(k_pwm_max * max(min(ratio, 1.0), 0.0))


class Midi:
    def __init__(self, UART_id: int) -> None:
        self.channel = k_midi_channel
        self.uart = UART(UART_id)
        self.uart.init(baudrate=31250)

    def set_channel(self, channel: int):
        if channel < 0 or channel > 15:
            print(f"Channel {channel} request is out of bound")
            return
        self.channel = channel

    def write_program_change(self, program: int) -> None:
        self.uart.write(bytearray([0xC0 | self.channel, program]))
        self.uart.flush()


class MidiProgramManager:
    def __init__(self) -> None:
        # Try to read from file first
        data = dict()
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
        data = dict()
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
        self.patch_led = [PWM(Pin(p, Pin.OUT)) for p in p_patch_led]
        self.send_led = Pin(p_send_led, Pin.OUT)
        self.disp = tm1637.TM1637(clk=Pin(p_disp_clk), dio=Pin(p_disp_dio))
        self.midi = Midi(k_midi_uart_id)

        # Internal variables
        self.pm = MidiProgramManager()
        self.send_timer = Timer()
        self.disp_timer = Timer()
        self.btn_timer = Timer()

        for led in self.patch_led:
            led.freq(1000)
            led.duty_u16(0)
        self.send_led.off()

        self.disp.brightness(3)
        self.disp.number(self.pm.page)

        # Link patch button callbacks
        self.patch_btn[0].irq(handler=lambda p: self.patch_callback(0))
        self.patch_btn[1].irq(handler=lambda p: self.patch_callback(1))
        self.patch_btn[2].irq(handler=lambda p: self.patch_callback(2))

        # Link page button callbacks
        self.btn_page_up.irq(
            trigger=Pin.IRQ_FALLING,
            handler=lambda p: self.btn_timer.init(
                mode=Timer.ONE_SHOT, period=25, callback=self.page_callback
            ),
        )
        self.btn_page_down.irq(
            trigger=Pin.IRQ_FALLING,
            handler=lambda p: self.btn_timer.init(
                mode=Timer.ONE_SHOT, period=25, callback=self.page_callback
            ),
        )

        self.set_patch(self.pm.patch)

    def set_patch(self, patch: int):
        self.pm.set_patch(patch)
        self.midi.write_program_change(self.pm.program)
        self.pm.save_to_file()

        # Blink the send LED once
        self.send_led.on()
        self.send_timer.init(
            mode=Timer.ONE_SHOT, period=50, callback=lambda t: self.send_led.off()
        )

        self.set_patch_led(0.8)

    def patch_callback(self, idx: int):
        if self.patch_btn[idx].value() is 0:
            self.btn_timer.init(
                mode=Timer.ONE_SHOT, period=25, callback=lambda t: self.set_patch(idx)
            )
        else:
            self.btn_timer.deinit()

    def page_callback(self, p: Pin):
        if self.btn_page_up.value() is 0:
            self.pm.set_page(self.pm.page + 1)
        elif self.btn_page_down.value() is 0:
            self.pm.set_page(self.pm.page - 1)
        else:
            return

        # Trigger a patch set after a delay
        self.send_timer.init(
            mode=Timer.ONE_SHOT,
            period=500,
            callback=lambda t: self.set_patch(self.pm.patch),
        )

        # Dim the LEDs a bit while the page is changing
        self.set_patch_led(0.2)
        self.disp.number(self.pm.page)

    def set_patch_led(self, brightness: float):
        for led in self.patch_led:
            led.duty_u16(0)
        self.patch_led[self.pm.patch].duty_u16(pwm_duty(brightness))


midi_pc = MidiProgramController()

while 1:
    pass

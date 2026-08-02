import time
import machine
import usb.device
from usb.device.midi import MIDIInterface

BUTTON_PIN = 15
CHANNEL = 0
CONTROLLER = 33
CC_VALUE_ON = 127
CC_VALUE_OFF = 0
DEBOUNCE_MS = 20

button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

midi = MIDIInterface()
usb.device.get().init(midi, builtin_driver=True, product_str="MicroPython CC Button")

print("Waiting for USB host to configure MIDI interface...")
while not midi.is_open():
    time.sleep_ms(100)

print("MIDI device ready. Press the button to send CC messages.")

last_state = button.value()  # 1 = released (pull-up), 0 = pressed
last_change_time = time.ticks_ms()

cc_value = 1

while midi.is_open():
    current_state = button.value()
    now = time.ticks_ms()

    if current_state != last_state and time.ticks_diff(now, last_change_time) > DEBOUNCE_MS:
        last_change_time = now
        last_state = current_state

        if current_state == 1:
            midi.control_change(CHANNEL, CONTROLLER, cc_value)
            print(f"CC {CONTROLLER} -> {cc_value}")
            if cc_value < 8:
                cc_value = cc_value + 1
            else:
                cc_value = 1


    time.sleep_ms(5)
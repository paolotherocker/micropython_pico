import time
import machine
import usb.device
from usb.device.midi import MIDIInterface

# --- Configuration ---
BUTTON_PIN = 15      # GPIO pin the button is connected to
CHANNEL = 0           # MIDI channel (0-15)
CONTROLLER = 64       # CC number (e.g. 64 = sustain pedal)
CC_VALUE_ON = 127     # Value sent when button is pressed
CC_VALUE_OFF = 0      # Value sent when button is released
DEBOUNCE_MS = 200

button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

midi = MIDIInterface(num_cables=1)
usb.device.get().init(midi, builtin_driver=True)

print("Waiting for USB host to configure MIDI interface...")
while not midi.is_open():
    time.sleep_ms(100)

print("MIDI device ready. Press the button to send CC messages.")

last_state = button.value()  # 1 = released (pull-up), 0 = pressed
last_change_time = time.ticks_ms()

while midi.is_open():
    current_state = button.value()
    now = time.ticks_ms()

    if current_state != last_state and time.ticks_diff(now, last_change_time) > DEBOUNCE_MS:
        last_change_time = now
        last_state = current_state

        if current_state == 0:  # Button pressed (active low)
            midi.control_change(CHANNEL, CONTROLLER, CC_VALUE_ON)
            print(f"CC {CONTROLLER} -> {CC_VALUE_ON}")
        else:  # Button released
            midi.control_change(CHANNEL, CONTROLLER, CC_VALUE_OFF)
            print(f"CC {CONTROLLER} -> {CC_VALUE_OFF}")

    time.sleep_ms(5)
"""
Install dependencies:
mpremote mip install ssd1306
"""

from machine import Pin, I2C
import ssd1306

# Initialize I2C0 on GP8 and GP9 with a 400kHz frequency
i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)

# Initialize the SSD1306 display (Width, Height, I2C object)
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# Clear the display buffer (0 = black)
display.fill(0)

# Write text: string, x, y, color
display.text("Hello, Pico!", 0, 0, 1)
display.text("System Nominal", 0, 16, 1)

# Push the buffer to the screen
display.show()

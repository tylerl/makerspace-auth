# OpenLCD driver.
# This is an abstration around the SparkFun OpenLCD interface.
# https://github.com/sparkfun/OpenLCD
# This protocol is used my multiple products, including
# * Serial Enabled 16x2 LCD: https://www.sparkfun.com/products/9395
# * 16x2 SerLCD: https://www.sparkfun.com/products/14073
# * Serial Enabled LCD Backpack: https://www.sparkfun.com/products/retired/258
# * Serial LCD Kit: https://www.sparkfun.com/tutorials/289
#
# This just dumps everything you send over serial onto the LCD, except for
# that 0xFE makes the next byte be interepreted as a command. We only care
# really need two of them:
#
# * 0xfe,0x01 - Clear screen
# * 0xfe,0x80,0xBB - Move cursor position "BB"
#     0x00 - 0x0F - Line 1
#     0x10 - 0x1F - Line 2
#     0x20 - 0x2F - Line 1 (again)
#       ... and so on

# https://github.com/jimblom/Serial-LCD-Kit/wiki/Serial-Enabled-LCD-Kit-Datasheet
#
#

from . import display

class OpenLCD(display.BaseDriver):
  def __init__(self, serial):
    self._serial = serial

  def clear(self):
    raise NotImplementedError()

  def move(self, line, col):
    raise NotImplementedError()

  def write(self, msg):
    raise NotImplementedError()
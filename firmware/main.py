import board
import busio
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC, Key
from kmk.scanners import DiodeOrientation
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.rgb import RGB, AnimationModes
from kmk.extensions.media_keys import MediaKeys
from kmk.extensions.display import Display, TextEntry
from kmk.extensions.display.ssd1306 import SSD1306

class RGBToggle(Key):
    def __init__(self, modifier, key, rgb):
        self.modifier = modifier
        self.key = key
        self.rgb = rgb
        self.enabled = True

    def on_press(self, keyboard, coord_int=None):
        if self.modifier in keyboard.keys_pressed:
            self.enabled = not self.enabled
            if self.enabled:
                self.rgb.val_limit = 255
            else:
                self.rgb.val_limit = 0
            return keyboard
        self.key.on_press(keyboard, coord_int)

    def on_release(self, keyboard, coord_int=None):
        self.key.on_release(keyboard, coord_int)
        return keyboard

class DualKey(Key):
    def __init__(self, key, modifier, key2):
        self.modifier = modifier
        self.key = key
        self.key2 = key2

    def on_press(self, keyboard, coord_int=None):
        if self.modifier in keyboard.keys_pressed:
            self.key2.on_press(keyboard, coord_int)
        else:
            self.key.on_press(keyboard, coord_int)
        return keyboard

    def on_release(self, keyboard, coord_int=None):
        self.key.on_release(keyboard, coord_int)
        self.key2.on_release(keyboard, coord_int)
        return keyboard

class ArrowDualKey(DualKey):
    def __init__(self, key, key2):
        super().__init__(key, None, key2)

    def on_press(self, keyboard, coord_int=None):
        arrows = {KC.LEFT, KC.RIGHT, KC.UP, KC.DOWN}
        if keyboard.keys_pressed.intersection(arrows):
            self.key2.on_press(keyboard, coord_int)
        else:
            self.key.on_press(keyboard, coord_int)
        return keyboard

keyboard = KMKKeyboard()
keyboard.extensions.append(MediaKeys())

rgb = RGB(
    pixel_pin=board.D9,
    num_pixels=8,
    val_limit=100,
    breathe_center=1.5,
    animation_mode=AnimationModes.BREATHING_RAINBOW,
    animation_speed=2,
)
keyboard.extensions.append(rgb)

i2c = busio.I2C(scl=board.D5, sda=board.D4)
oled = SSD1306(i2c, board.D4, board.D5)
display = Display(
    display=oled,
    entries=[TextEntry("Celeste Hackpad", x_anchor="M", y_anchor="M", x=64, y=12)],
    height=32,
    flip=True
)
keyboard.extensions.append(display)

encoder = EncoderHandler()
encoder.pins = [[board.D3, board.D6, None, False, 2]]
encoder.map = [
    [[KC.VOLD, KC.VOLU]]
]
keyboard.modules.append(encoder)

keyboard.col_pins = [board.A0, board.A1, board.A2]
keyboard.row_pins = [board.D7, board.D8, board.D10]
keyboard.diode_orientation = DiodeOrientation.COL2ROW
keyboard.keymap = [
    [
        KC.RIGHT, DualKey(KC.DOWN, KC.ESC, KC.F), DualKey(RGBToggle(KC.ESC, KC.UP, rgb), KC.C, KC.D),
        KC.LEFT, KC.C, KC.X,
        KC.Z, ArrowDualKey(KC.ESC, KC.S), KC.AUDIO_MUTE
    ],
]

if __name__ == '__main__':
    keyboard.go()

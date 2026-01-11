import board
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from kmk.extensions.rgb import RGB, AnimationModes
from kmk.extensions.media_keys import MediaKeys

keyboard = KMKKeyboard()
keyboard.extensions.append(MediaKeys())

keyboard.col_pins = (board.A0, board.A1, board.A2)
keyboard.row_pins = (board.D7, board.D8, board.D10)
keyboard.diode_orientation = DiodeOrientation.COL2ROW
keyboard.keymap = [
    [KC.RIGHT, KC.DOWN, KC.UP, KC.LEFT, KC.C, KC.X, KC.Z, KC.ENTER, KC.AUDIO_MUTE],
]

rgb = RGB(
    pixel_pin=board.D9,
    num_pixels=8,
    val_limit=100,
    breathe_center=1.5,
    animation_mode=AnimationModes.BREATHING_RAINBOW,
    animation_speed=2,
)
keyboard.extensions.append(rgb)

if __name__ == '__main__':
    keyboard.go()

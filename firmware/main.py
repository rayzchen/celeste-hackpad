import board

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeyMatrix
from kmk.keys import KC

keyboard = KMKKeyboard()

# macros = Macros()
# keyboard.modules.append(macros)

keyboard.matrix = KeyMatrix(
    [board.D0, board.D1, board.D2],
    [board.D7, board.D8, board.D10],
    columns_to_anodes=True
)

keyboard.keymap = [
    [
        KC.RIGHT, KC.DOWN, KC.UP, KC.LEFT,
        KC.C, KC.X, KC.Z, KC.ESC
    ]
]

# Start kmk!
if __name__ == '__main__':
    keyboard.go()
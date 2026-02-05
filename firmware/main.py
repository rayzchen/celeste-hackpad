import board
import busio
import random
import displayio
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC, Key
from kmk.scanners import DiodeOrientation
from kmk.kmktime import PeriodicTimer
from kmk.modules import Module
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.rgb import RGB, AnimationModes
from kmk.extensions.media_keys import MediaKeys
from kmk.extensions.display.ssd1306 import SSD1306

class RGBToggle(Key):
    def __init__(self, modifier, key, rgb):
        self.modifier = modifier
        self.key = key
        self.rgb = rgb
        self.enabled = True

    def check_modifier(self, keyboard):
        if isinstance(self.modifier, list):
            for key in self.modifier:
                if key not in keyboard.keys_pressed:
                    return False
            return True
        return self.modifier in keyboard.keys_pressed

    def on_press(self, keyboard, coord_int=None):
        if self.check_modifier(keyboard):
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

    def check_modifier(self, keyboard):
        if isinstance(self.modifier, list):
            for key in self.modifier:
                if key not in keyboard.keys_pressed:
                    return False
            return True
        return self.modifier in keyboard.keys_pressed

    def on_press(self, keyboard, coord_int=None):
        if self.check_modifier(keyboard):
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

class AltTabDualKey(DualKey):
    def __init__(self, key, modifier):
        super().__init__(key, modifier, KC.TAB)
        self.alt_held = False
        self.release_backup = None

    def on_press(self, keyboard, coord_int=None):
        if self.check_modifier(keyboard) and not self.alt_held:
            KC.LALT.on_press(keyboard, coord_int)
            self.alt_held = True
            self.release_backup = self.modifier.on_release
            self.modifier.on_release = self.release_wrapper
        super().on_press(keyboard, coord_int)

    def release_wrapper(self, keyboard, coord_int=None):
        KC.LALT.on_release(keyboard, coord_int)
        self.alt_held = False
        self.modifier.on_release = self.release_backup
        self.modifier.on_release(keyboard, coord_int)

class DisplayDualKey(DualKey):
    def __init__(self, key, modifier):
        super().__init__(key, modifier, KC.UP)

    def on_press(self, keyboard, coord_int=None):
        if self.check_modifier(keyboard):
            mod = None
            for module in screen_modules:
                if module in keyboard.modules:
                    mod = module
                    break
            i = (screen_modules.index(mod) + 1) % 3
            keyboard.modules.remove(mod)
            keyboard.modules.append(screen_modules[i])
            screen_modules[i].during_bootup(keyboard)
        super().on_press(keyboard, coord_int)

class KeyTracker(Module):
    def __init__(self):
        tilemap = displayio.Bitmap(48, 16, 2)
        for i in range(14):
            tilemap[17 + i, 1] = 1
            tilemap[17 + i, 14] = 1
            tilemap[33 + i, 1] = 1
            tilemap[33 + i, 14] = 1
        for i in range(12):
            tilemap[17, 2 + i] = 1
            tilemap[30, 2 + i] = 1
            tilemap[33, 2 + i] = 1
            tilemap[46, 2 + i] = 1
        for i in range(10):
            for j in range(10):
                tilemap[35 + i, 3 + j] = 1
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = 0xFFFFFF

        self.tilegrid = displayio.TileGrid(
            tilemap,
            pixel_shader=palette,
            width=7,
            height=2,
            tile_width=16,
            tile_height=16,
            default_tile=0,
            x=8,
            y=0
        )
        self.display = oled.display
        self.group = displayio.Group()
        self.group.append(self.tilegrid)

        self.keymap = [
            KC.S, KC.D, KC.F, None, None, KC.UP, KC.ESC,
            KC.Z, KC.X, KC.C, None, KC.LEFT, KC.DOWN, KC.RIGHT
        ]
        self.pressed = [False] * len(self.keymap)
        self.updated = True
        for i in range(len(self.keymap)):
            if self.keymap[i] is not None:
                self.tilegrid[i] = 1

    def during_bootup(self, keyboard):
        self.display.root_group = self.group
    def before_matrix_scan(self, keyboard):
        pass
    def after_matrix_scan(self, keyboard):
        for i in range(len(self.keymap)):
            if self.keymap[i] is not None:
                if not self.pressed[i] and self.keymap[i] in keyboard.keys_pressed:
                    self.tilegrid[i] = 2
                    self.pressed[i] = True
                if self.pressed[i] and self.keymap[i] not in keyboard.keys_pressed:
                    self.tilegrid[i] = 1
                    self.pressed[i] = False
        if self.updated:
            self.display.refresh()
    def before_hid_send(self, keyboard):
        pass
    def after_hid_send(self, keyboard):
        pass

class GameOfLife(Module):
    def __init__(self):
        self.bitmap = displayio.Bitmap(128, 32, 2)
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = 0xFFFFFF
        self.tilegrid = displayio.TileGrid(
            self.bitmap,
            pixel_shader=palette
        )
        self.display = oled.display
        self.group = displayio.Group()
        self.group.append(self.tilegrid)

        import random
        self.board1 = [0] * 32 * 16
        self.board2 = [0] * 32 * 16
        for i in range(32 * 16):
            if random.randint(1, 4) == 1:
                self.board1[i] = 1

    def during_bootup(self, keyboard):
        self.display.root_group = self.group
    def before_matrix_scan(self, keyboard):
        pass
    def after_matrix_scan(self, keyboard):
        for i in range(32 * 16):
            y, x = divmod(i, 32)
            for offset in [0, 1, 128, 129]:
                self.bitmap[y * 256 + x * 2 + 32 + offset] = self.board1[i]
        self.display.refresh()
        self.board1, self.board2 = self.board2, self.board1

        for i in range(64 * 16):
            neighbours = 0
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    x = (i % 32 + dx) % 32
                    y = (i // 32 + dy) % 16
                    neighbours += self.board2[y * 32 + x]
            if neighbours == 3:
                self.board1[i] = 1
            if neighbours == 4:
                self.board1[i] = self.board2[i]
            if neighbours < 3 or neighbours > 4:
                self.board1[i] = 0

    def before_hid_send(self, keyboard):
        pass
    def after_hid_send(self, keyboard):
        pass

class Snake(Module):
    def __init__(self):
        self.bitmap = displayio.Bitmap(128, 32, 2)
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = 0xFFFFFF
        self.tilegrid = displayio.TileGrid(
            self.bitmap,
            pixel_shader=palette
        )
        self.display = oled.display
        self.group = displayio.Group()
        self.group.append(self.tilegrid)

        self.history = [(0, 0)]
        self.direction = (1, 0)
        self.dmap = {
            KC.UP: (0, -1),
            KC.DOWN: (0, 1),
            KC.LEFT: (-1, 0),
            KC.RIGHT: (1, 0)
        }
        self.pressed = {key: False for key in self.dmap}
        self.pressed[KC.ESC] = False
        self.input_buffer = []
        self.apple = (15, 7)
        self.grow = False
        self.dead = False
        self.pause = False
        self.timer = PeriodicTimer(50)
        self.frame_cooldown = 0
        self.death_cooldown = 0
        self.respawn_cooldown = 0
        self.pause_cooldown = 0

    def set_block(self, x, y, value):
        for offset in [0, 1, 128, 129]:
            self.bitmap[(y + 1) * 2 * 128 + (x + 1) * 2 + offset] = value

    def during_bootup(self, keyboard):
        self.display.root_group = self.group
        for i in range(128):
            self.bitmap[i, 0] = 1
            self.bitmap[i, 31] = 1
        for i in range(30):
            self.bitmap[0, i + 1] = 1
            self.bitmap[127, i + 1] = 1
    def before_matrix_scan(self, keyboard):
        pass
    def after_matrix_scan(self, keyboard):
        for key in self.pressed:
            if key in keyboard.keys_pressed:
                if not self.pressed[key]:
                    self.pressed[key] = True
                    self.input_buffer.append(key)
            else:
                self.pressed[key] = False
                if key in self.input_buffer:
                    self.input_buffer.remove(key)

        if not self.timer.tick():
            return

        if self.dead:
            if self.death_cooldown:
                self.death_cooldown -= 1
                return

            if self.history:
                self.set_block(self.apple[0], self.apple[1], 0)
                tail = self.history.pop(0)
                self.set_block(tail[0], tail[1], 0)
                self.display.refresh()
                return

            self.respawn_cooldown = 20
            self.dead = False
            self.history = [(0, 0)]
            self.direction = (1, 0)
            self.apple = (15, 7)
            self.grow = False
            return

        if self.respawn_cooldown:
            self.respawn_cooldown -= 1
            return

        if self.frame_cooldown:
            self.frame_cooldown -= 1
            return
        self.frame_cooldown = 1

        if KC.ESC in self.input_buffer:
            self.pause = not self.pause
            self.input_buffer.remove(KC.ESC)

        if self.pause:
            self.pause_cooldown += 1
            if self.pause_cooldown == 5:
                self.set_block(self.apple[0], self.apple[1], 0)
            elif self.pause_cooldown == 10:
                self.pause_cooldown = 0
                self.set_block(self.apple[0], self.apple[1], 1)
            self.display.refresh()
            return

        while self.input_buffer:
            entered = self.dmap[self.input_buffer.pop(0)]
            if entered[0] != -self.direction[0] or entered[1] != -self.direction[1]:
                self.direction = entered
                break

        x = self.history[-1][0] + self.direction[0]
        y = self.history[-1][1] + self.direction[1]
        head = (x, y)
        if x == -1 or x == 62 or y == -1 or y == 14 or head in self.history:
            self.dead = True
            self.death_cooldown = 20
            return
        self.history.append(head)

        tail = None
        if self.grow:
            self.grow = False
        else:
            tail = self.history.pop(0)

        if head == self.apple:
            self.grow = True
            while self.apple in self.history:
                self.apple = (random.randint(0, 61), random.randint(0, 13))

        if tail is not None:
            self.set_block(tail[0], tail[1], 0)
        self.set_block(head[0], head[1], 1)
        self.set_block(self.apple[0], self.apple[1], 1)
        self.display.refresh()

    def before_hid_send(self, keyboard):
        pass
    def after_hid_send(self, keyboard):
        pass

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
oled.during_bootup(128, 32, 180).auto_refresh = False
screen_modules = [KeyTracker(), GameOfLife(), Snake()]
keyboard.modules.append(screen_modules[0])

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
        KC.RIGHT,
        DualKey(DualKey(KC.DOWN, KC.ESC, KC.F), [KC.C, KC.UP], KC.D),
        DisplayDualKey(RGBToggle(KC.ESC, KC.UP, rgb), [KC.LEFT, KC.RIGHT]),
        AltTabDualKey(KC.LEFT, KC.ESC), KC.C, KC.X,
        KC.Z, DualKey(ArrowDualKey(KC.ESC, KC.S), KC.Z, KC.TAB),
        KC.AUDIO_MUTE
    ],
]

if __name__ == '__main__':
    keyboard.go()

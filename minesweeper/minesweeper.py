import pyxel
import time

NUM_BOMBS = 99
WIDTH = 30
HEIGHT = 16
TILE = 8
BOMB_MAP = [[0] * WIDTH for _ in range(HEIGHT)] # bomb allocation map
FIELD = [[9] * WIDTH for _ in range(HEIGHT)] # state of each field cell
# 0 open with no bombs around.
# 1 2 3 4 5 6 7 8 open with number of bombs around.
# 9 closed, 10 flag, 11 bomb, 12 explosion

STATE = {
    'isGameOver': False,
    'isFirst': True,
    'time': 0,
    'bombs': NUM_BOMBS,
}

def getBomb(x, y):
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        return 0
    else:
        return BOMB_MAP[y][x]

def getNumFlags(x, y):
    ret = 0
    for j in [-1, 0, 1]:
        for i in [-1, 0, 1]:
            new_x, new_y = x + i, y + j
            if new_x < 0 or new_x >= WIDTH or new_y < 0 or new_y >= HEIGHT:
                continue
            if FIELD[new_y][new_x] == 10:
                ret += 1
    return ret

def wfs(x, y):
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        return
    if FIELD[y][x] != 9:
        return
    b = 0
    for j in [-1, 0, 1]:
        for i in [-1, 0, 1]:
            b += getBomb(x+i, y+j)
    FIELD[y][x] = b
    if b ==  0:
        for j in [-1, 0, 1]:
            for i in [-1, 0, 1]:
                wfs(x+i, y+j)

def open(x, y):
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        return
    if FIELD[y][x] == 9:
        if BOMB_MAP[y][x] == 1:
            openBombs()
            FIELD[y][x] = 12
            STATE['isGameOver'] = True
        else:
            wfs(x, y)

def checkClear():
    target = WIDTH * HEIGHT - NUM_BOMBS
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if FIELD[y][x] < 9:
                target -= 1
    if target <= 0:
        STATE['isGameOver'] = True
        STATE['bombs'] = 0
        openBombs()

def openBombs():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if BOMB_MAP[y][x] == 1 and FIELD[y][x] != 10:
                FIELD[y][x] = 11

class App:

    def __init__(self):
        pyxel.init((WIDTH + 2) * TILE, (HEIGHT + 2) * TILE, title="Minesweeper")
        pyxel.load("minesweeper.pyxres")
        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if  pyxel.btnp(pyxel.KEY_R): # Retry the game.
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    BOMB_MAP[y][x] = 0
                    FIELD[y][x] = 9
            STATE['isGameOver'] = False
            STATE['isFirst'] = True
            STATE['time'] = 0
            STATE['bombs'] = NUM_BOMBS
        if STATE['isGameOver']:
            return
        if pyxel.frame_count % 30 == 0 and not STATE['isFirst']:
            STATE['time'] += 1
        x, y = pyxel.mouse_x // TILE - 1, pyxel.mouse_y // TILE - 1
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return
        if pyxel.btnp(pyxel.MOUSE_BUTTON_MIDDLE) or pyxel.btnp(pyxel.KEY_DOWN): # middle click
            num = FIELD[y][x]
            if num <= 8 and num >= 1 and getNumFlags(x, y) == num:
                for j in [-1, 0, 1]:
                    for i in [-1, 0, 1]:
                        open(x+i, y+j)
                checkClear()
        elif pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT) or pyxel.btnp(pyxel.KEY_RIGHT): # right click
            if FIELD[y][x] == 9:
                FIELD[y][x] = 10
                STATE['bombs'] -= 1
            elif FIELD[y][x] == 10:
                FIELD[y][x] = 9
                STATE['bombs'] += 1
        elif pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) or pyxel.btnp(pyxel.KEY_LEFT): # left click
            if STATE['isFirst']:
                i = 0
                pos = y * WIDTH + x
                pyxel.rseed(int(time.time()))
                for r in sorted([((pyxel.rndf(0, 1), i)) for i in range(WIDTH * HEIGHT)]):
                    if r[1] == pos:
                        continue
                    if i == NUM_BOMBS:
                        break
                    BOMB_MAP[r[1] // WIDTH][r[1] % WIDTH] = 1
                    i += 1
                STATE['isFirst'] = False
            open(x, y)
            checkClear()

    def draw(self):
        pyxel.cls(1)
        time, bombs = STATE['time'], STATE['bombs']
        pyxel.text(3 * TILE, 2,  f"{bombs:3}", 6)
        pyxel.text((WIDTH - 4) * TILE, 2, f"{time:3}", 6)

        for y in range(HEIGHT):
            for x in range(WIDTH):
                pyxel.blt((x+1) * TILE, (y+1) * TILE, 0, FIELD[y][x] * TILE, 0, TILE, TILE)

App()

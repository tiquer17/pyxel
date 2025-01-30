import pyxel
import copy

# from https://qiita.com/igarashisan_t/items/6e5fc39dd5bafd195000
import platform
# from js はEmscripten環境以外では例外発生するのでcatchして環境を判定する
try:
    from js import navigator
    is_web_launcher = True
except ImportError:
    is_web_launcher = False

class DeviceChecker:
    def __init__(self):
        if is_web_launcher:
            # Web launcherから起動している場合、js関数でOS判定する
            self.user_agent = navigator.userAgent.lower()
            self.os_pc = not ("android" in self.user_agent or "iphone" in self.user_agent or "ipad" in self.user_agent)
        else:
            # ローカルから起動している場合、platformから判定する
            self.os_name = platform.system()
            self.os_pc =  self.os_name == "Windows" or self.os_name == "Darwin" or self.os_name == "Linux"

    def is_pc(self):
        return self.os_pc

    def is_web_launcher(self):
        return is_web_launcher

T = 16
SPD = 4
FPS = 60
BASELINE = T * 5

DECK = []
HOME = []
FREE = []
MOVE = []
UNDO = []

STATE = {
    'isGameOver': False,
    'isNewGame': True,
    'time': 0,
    'id': 0,
    'newId': '',
    'idSelection': False,
    'help': False,
}

# gameover clear right click

# copied from https://rosettacode.org/wiki/Deal_cards_for_FreeCell#Python
def randomGenerator(seed=1):
    max_int32 = (1 << 31) - 1
    seed = seed & max_int32

    while True:
        seed = (seed * 214013 + 2531011) & max_int32
        yield seed >> 16

def deal(seed):
    nc = 52
    cards = list(range(nc - 1, -1, -1))
    rnd = randomGenerator(seed)
    for i, r in zip(range(nc), rnd):
        j = (nc - 1) - r % (nc - i)
        cards[i], cards[j] = cards[j], cards[i]
    return cards

class Card:

    def __init__(self, num, suit, x=0, y=0, fm=None, to=None, cnt=0):
        self.num = num 
        self.suit = suit # 0: spade, 1: heart, 2: club, 3: diamond
        self.x = x
        self.y = y
        self.fm = fm
        self.to = to
        self.cnt = cnt

    def draw(self):
        if self.num == -1:
            return
        col = 1 if self.suit % 2 == 0 else 2
        pyxel.blt(self.x, self.y , 0, self.num * T, col * T, T, T, 15)
        pyxel.blt((self.x + T), self.y , 0, self.suit * T, 0, T, T, 15)
        pyxel.blt(self.x, (self.y + T), 0, 4 * T, 0, 2 * T, T, 15)
        pyxel.blt(self.x, (self.y + 2 * T) , 0, self.suit * T, 0, - T, - T ,15)
        pyxel.blt((self.x + T) , (self.y + 2 * T), 0, self.num * T, col * T, - T, - T, 15)


def type_text(x, y, s, col=0):
    for i, c in enumerate(s):
        ascii = ord(c) - 32
        pyxel.blt(x + i * 8, y, 1, (ascii % 16) * 8, (ascii //16 + col * 4)* 16, 8, 16, 0)

class App:
    def __init__(self):
        pyxel.init(T * 16, T * 24, title="Freecell", display_scale= 32 // T , quit_key=pyxel.KEY_Q, fps=FPS)
        self.is_pc = DeviceChecker().is_pc()
        if self.is_pc:
            pyxel.mouse(True)
        pyxel.load("freecell.pyxres" if T == 8 else "freecell16.pyxres")
        self.restart()
        self.do_draw()
        pyxel.run(self.update, self.draw)
        self.changed = False

    def restart(self, id=0):
        if id == 0:
            id = pyxel.rndi(1, 32000)
        STATE['id'] = id
        STATE['isGameOver'] = False
        STATE['isGameClear'] = False
        STATE['isNewGame'] = True
        cards = deal(STATE['id'])
        DECK.clear()
        DECK.extend([[], [], [], [], [], [], [], []])
        for i, c in enumerate(cards):
            DECK[i % 8].append(Card(c // 4, [2, 3, 1, 0][c % 4]))
        FREE.clear()
        FREE.extend([None, None, None, None])
        HOME.clear()
        HOME.extend([Card(-1, -1), Card(-1, -1), Card(-1, -1), Card(-1, -1)])
        UNDO.clear()

    def set_id(self):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x, y = pyxel.mouse_x, pyxel.mouse_y
            if len(STATE['newId']) < 5:
                for i in range(10):
                    if T * (6 + i % 4) <= x and x < T * (7 + i % 4) and T * (8 + i // 4) <= y and y < T * (9 + i // 4):
                        STATE['newId'] += str(i)
                        self.changed = True
            if T * 8 <= x and x < T * 10 and T * 10 <= y and y < T * 11:
                STATE['newId'] = STATE['newId'][:-1]
                self.changed = True

            if T * 6 <= x and x < T * 8 and T * 12 <= y and y < T * 13:
                if STATE['newId'] and int(STATE['newId']) != STATE['id']:
                    STATE['time'] = 0
                    self.restart(int(STATE['newId']))
                STATE['newId'] = ''
                STATE['idSelection'] = False
                self.changed = True
                return

            if T * 8 <= x and x < T * 10 and T * 12 <= y and y < T * 13:
                STATE['newId'] = ''
                STATE['idSelection'] = False
                self.changed = True

    def undo(self):
        STATE['isGameOver'] = False
        if self.has_undo():
            global DECK, FREE, HOME
            DECK = UNDO[0]
            FREE = UNDO[1]
            HOME = UNDO[2]
            UNDO.clear()

    def has_undo(self):
        return len(UNDO) > 0

    def is_game_over(self):
        if all([_ is not None for _ in FREE]):
            if all(DECK):
                tails = [d[-1] for d in DECK]
                for c in FREE + tails:
                    for t in tails:
                        if (c.suit + t.suit) % 2 == 1 and t.num - c.num == 1:
                            return False
                    if c.num - HOME[c.suit].num == 1:
                        return False
                return True
        return False

    def move(self, c, fm, to, undo=True):
        if undo:
            global UNDO
            UNDO = [copy.deepcopy(DECK), copy.deepcopy(FREE), copy.deepcopy(HOME)]
        c.fm, c.to, c.cnt = fm, to, 0
        MOVE.append(c)

    def do_move(self):
        global MOVE
        self.changed = True
        for m in MOVE:
            if m.cnt == SPD:
                if m.to[1] >= 0:
                    DECK[m.to[0]].append(m)
                elif m.to[0] < 4:
                    FREE[m.to[0]] = m
                else:
                    HOME[m.to[0] -4] = m
                m.fm = None
                m.to = None
            else:
                m.x = (m.fm[0] * (SPD - m.cnt) + m.to[0] * m.cnt) * T / SPD * 2
                m.y = (m.fm[1] * (SPD - m.cnt) + m.to[1] * m.cnt) * T / SPD + BASELINE
                m.cnt += 1
        MOVE = [m for m in MOVE if m.fm]


    def move_to_another_cascade(self, x, y, num_super_move):
        l = [FREE[x]] if y == -4 else DECK[x][y:]
        c1 = l[0]
        if len(l) <= num_super_move:
            r = range(8) if y == -4 else range(x + 1, x + 8)
            for i in r:
                if len(DECK[i % 8]) > 0:
                    c2 = DECK[i % 8][-1]
                    if c2.num - c1.num == 1 and (c2.suit + c1.suit) % 2 == 1:
                        for j, d in enumerate(l):
                            self.move(d, (x, y + j), (i % 8, len(DECK[i % 8]) + j))
                        if y == -4:
                            FREE[x] = None
                        else:
                            DECK[x] = DECK[x][:y]
                        return True
        return False

    def move_to_empty_cascade(self, x, y, num_super_move):
        l = [FREE[x]] if y == -4 else DECK[x][y:]
        if len(l) <= num_super_move // 2:
            for i in range(8) if y == -4 else range(x + 1, x + 8):
                if len(DECK[i % 8]) == 0:
                    for j, d in enumerate(l):
                        self.move(d, (x, y + j), (i % 8, len(DECK[i % 8]) + j))
                    if y == -4:
                        FREE[x] = None
                    else:
                        DECK[x] = DECK[x][:y]
                    return True
        return False

    def move_to_free_cell(self, x, y):
        for i, f in enumerate(FREE):
            if f is None:
                self.move(DECK[x][-1], (x, y), (i, -4))
                DECK[x].pop()
                return True
        return False

    def move_to_home_cell(self, x, y):
        c = FREE[x] if y == -4 else DECK[x][-1]
        if HOME[c.suit].num == c.num - 1:
            self.move(c, (x, y), (c.suit + 4, -4))
            if y == -4:
                FREE[x] = None
            else:
                DECK[x].pop()
            return True
        return False

    def help(self):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x, y = pyxel.mouse_x, pyxel.mouse_y
            if T * 7 <= x and x < T * 9 and T * 11 <= y and y < T * 12:
                STATE['help'] = False
                self.changed = True

    def update(self):
        self.changed = False
        global MOVE

        if pyxel.frame_count % FPS == 0 and not STATE['idSelection'] and not STATE['help'] and not STATE['isGameOver'] and not STATE['isGameClear']:
            if STATE['time'] < 5999:
                STATE['time'] += 1
                self.changed = True

        if MOVE:
            self.do_move()
            return

        if not STATE['isNewGame']:
            if self.auto_move_to_home():
                return

        if STATE['idSelection']:
            self.set_id()
            return

        if STATE['help']:
            self.help()
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x, y = pyxel.mouse_x, pyxel.mouse_y
            if 0 <= y and y < T and 0 <= x and x < T * 3: # id
                STATE['idSelection'] = True
                STATE['newId'] = str(STATE['id'])
                self.changed = True
                return
            if 0 <= y and y < T and T * 3 <= x and x < T * 6: # new
                STATE['time'] = 0
                self.restart()
                self.changed = True
                return
            if 0 <= y and y < T and T * 6 <= x and x < T * 9: # retry
                if STATE['isGameClear']:
                    STATE['time'] = 0
                self.restart(STATE['id'])
                self.changed = True
                return
            if 0 <= y and y < T and T * 9 <= x and x < T * 12: # undo
                self.undo()
                self.changed = True
                return
            if 0 <= y and y < T and T * 12 <= x and x < T * 13: # help
                STATE['help'] = True                
                self.changed = True
                return

        if STATE['isGameClear'] or STATE['isGameOver']:
            return

        if all([c.num == 12 for c in HOME]):
            STATE['isGameClear'] = True
            UNDO.clear()
            self.changed = True
            return

        if self.is_game_over():
            STATE['isGameOver'] = True
            self.changed = True
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x, y = self.get_position(pyxel.mouse_x, pyxel.mouse_y)
            # moving deck cards
            if y >= 0 and x >= 0 and x < 8:
                STATE['isNewGame'] = False

                # if bottom move
                if len(DECK[x]) == y + 1:
                    if self.move_to_another_cascade(x, y, 1):
                        return
                    if self.move_to_free_cell(x, y):
                        return
                    if self.move_to_empty_cascade(x, y, 2):
                        return
                    if self.move_to_home_cell(x, y):
                        return
                else:
                    # check if super move is possible.
                    tmp = DECK[x][y]
                    for i, c in enumerate(DECK[x][y:]):
                        if i > 0:
                            if tmp.num - c.num != 1 or (tmp.suit + c.suit) % 2 == 0:
                                return
                        tmp = c
                    num_free_cells = len([_ for _ in FREE if _ is None])
                    num_empty_decks = len([_ for _ in DECK if len(_) == 0])
                    num_super_move = (2 ** num_empty_decks) * (num_free_cells + 1)
                    if self.move_to_another_cascade(x, y, num_super_move):
                        return
                    if self.move_to_empty_cascade(x, y, num_super_move):
                        return

            # moving free cell cards
            if y == -4 and x >= 0 and x < 4:
                if FREE[x] is not None:
                    if self.move_to_another_cascade(x, y, 1):
                        return
                    if self.move_to_empty_cascade(x, y, 2):
                        return
                    if self.move_to_home_cell(x, y):
                        return

            # moving to home cell card
            if y == -4 and x >= 0 and x >= 4 and x < 8:
                for i, c in enumerate(FREE):
                    if c is not None:
                        if c.num - HOME[x - 4].num == 1 and c.suit == x - 4:
                            self.move(c, (i, -4), (x, -4))
                            FREE[i] = None
                            return
                for i, d in enumerate(DECK):
                    if len(d) > 0:
                        c = d[-1]
                        if c.num - HOME[x - 4].num == 1 and c.suit == x - 4:
                            self.move(c, (i, len(d)), (x, -4))
                            d.pop()
                            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            STATE['isNewGame'] = False

            x, y = self.get_position(pyxel.mouse_x, pyxel.mouse_y)
            if y >= 0 and x >= 0 and x < 8:
                # moving to home cell
                if self.move_to_home_cell(x, y):
                    return
                # # moving to free cell
                # if self.move_to_free_cell(x, y):
                #     return

            # moving free cell cards
            if y == -4 and x >= 0 and x < 4:
                # moving to home cell
                if self.move_to_home_cell(x, y):
                    return

    def get_position(self, x, y):
        dx, dy = -1, -1
        if x >= 0 and x < T * 16:
            dx = x // (T * 2)
        if y < T * 4 and y >= T:
            dy = -4
        if y >= BASELINE:
            dy = (y - BASELINE) // T

        if dx >= 0 and dy >= 0:
            l = len(DECK[dx])
            if dy >= l + 2:
                dy = -1
            elif dy >= l:
                dy = l - 1
        return dx, dy

    def auto_move_to_home(self):
        cur = [h.num for h in HOME]
        for i, d in enumerate(DECK):
            if len(d) > 0:
                c = d[-1]
                if c.num - cur[c.suit] == 1 and (c.num == 1 or c.num <= min(cur[((c.suit + 1) % 2)::2]) + 1):
                    self.move(c, (i, len(d)), (c.suit + 4, -4), False)
                    d.pop()
                    return True
        for i, c in enumerate(FREE):
            if c is not None:
                if c.num - cur[c.suit] == 1 and (c.num == 1 or c.num <= min(cur[((c.suit + 1) % 2)::2]) + 1):
                    self.move(c, (i, -4), (c.suit + 4, -4), False)
                    FREE[i] = None
                    return True
        return False

    def draw(self):
        # if self.changed or self.is_pc:
        if self.changed:
            self.do_draw()

    def do_draw(self):
        pyxel.bltm(0, 0, 0, 0, 0, T * 16, T * 24)

        mm, ss = STATE['time'] // 60 , STATE['time'] % 60
        if T == 8:
            pyxel.text(2, 2, f"{STATE['id']:05}", 15 if STATE['help'] or STATE['idSelection'] else 7)
            pyxel.text(30, 2, f"NEW", 7)
            pyxel.text(50, 2, f"RETRY", 7)
            pyxel.text(76, 2, f"UNDO", 7 if self.has_undo() else 11)
            pyxel.text(98, 2, f"?", 7)
            pyxel.text(102, 2, f"{mm:3}:{ss:02}", 7)
        else:
            type_text(4, 0, f"{STATE['id']:05}", 3 if STATE['help'] or STATE['idSelection'] else 0)
            type_text(3 * T + 12, 0, f"NEW")
            type_text(6 * T + 4, 0, f"RETRY")
            type_text(9 * T + 8, 0, f"UNDO", 0 if self.has_undo() else 1)
            type_text(12 * T + 4, 0, f"?")
            type_text(T * 12 + 12, 0, f"{mm:3}:{ss:02}")


        for i, d in enumerate(DECK):
            for j, c in enumerate(d):
                c.x = i * 2 * T
                c.y = j * T + BASELINE
                c.draw()

        for i, c in enumerate(HOME):
            c.x = i * 2 * T + T * 8
            c.y = T
            c.draw()

        for i, c in enumerate(FREE):
            if c is not None:
                c.x = i * 2 * T
                c.y = T
                c.draw()

        if T == 8:
            for i in [0, 16, 32, 48]:
                pyxel.line(65 + i, 8, 78 + i , 8, 6)
                pyxel.line(65 + i, 31, 78 + i , 31, 6)
                pyxel.line(64 + i, 9, 64 + i , 30, 6)
                pyxel.line(79 + i, 9, 79 + i , 30, 6)
        else:
            pyxel.bltm(T * 8, T, 0, T * 8, T, T * 8, T * 3, 3)

        for c in MOVE:
            c.draw()

        if STATE['isGameOver']:
            pyxel.bltm(T * 5, T * 6, 0, T * 5, T * 6, T * 6, T * 3)
            if T == 8:
                pyxel.text(T * 6, T * 7 + 2, f"YOU LOSE", 7)
            else:
                type_text(T * 6, T * 7, f"YOU LOSE")

        if STATE['idSelection']:
            pyxel.bltm(T * 4, T * 4, 0, T * 24, 0, T * 8, T * 10)
            if T == 8:
                pyxel.text(T * 5, T * 5, f"ENTER", 7)
                pyxel.text(T * 5, T * 5, f"      GAME ID", 15)
                pyxel.text(T * 7 + 2, T * 6 + 2, f"{STATE['newId']:>5}", 7)
                pyxel.text(T * 6 + 2, T * 8 + 2, f"0 1 2 3", 7)
                pyxel.text(T * 6 + 2, T * 9 + 2, f"4 5 6 7", 7)
                pyxel.text(T * 6 + 2, T * 10 + 2, f"8 9 DEL", 7)
                pyxel.text(T * 6 + 4, T * 12 + 2, f"OK  BK", 7)
            else:
                type_text(T * 5, T * 5, f"ENTER")
                type_text(T * 5, T * 5, f"      GAME ID", 3)
                type_text(T * 7 + 4, T * 6, f"{STATE['newId']:>5}")
                type_text(T * 6 + 4, T * 8, f"0 1 2 3")
                type_text(T * 6 + 4, T * 9, f"4 5 6 7")
                type_text(T * 6 + 4, T * 10, f"8 9 DEL")
                type_text(T * 6 + 8, T * 12, f"OK  BK")

        if STATE['help']:
            pyxel.bltm(0, T * 5, 0, T * 24, T * 16, T * 16, T * 8)
            if T == 8:
                pyxel.text(0, T * 6, "  TAP SEQUENCE: MOVE AT ONCE", 7)
                pyxel.text(0, T * 8, " TAP          : MOVE NEXT CARD", 7)
                pyxel.text(0, T * 8, "     HOME CELL", 6)
                pyxel.text(0, T * 10, "   TAP        : SELECT GAME", 7)
                pyxel.text(0, T * 10, "       GAME ID", 15)
                pyxel.text(T * 7 + 4, T * 11 + 2, f"OK", 7)
            else:
                type_text(0, T * 6, "  TAP SEQUENCE: MOVE AT ONCE")
                type_text(0, T * 8, " TAP          : MOVE NEXT CARD")
                type_text(0, T * 8, "     HOME CELL", 2)
                type_text(0, T * 10, "   TAP        : SELECT GAME")
                type_text(0, T * 10, "       GAME ID", 3)
                type_text(T * 7 + 8, T * 11, f"OK")

App()

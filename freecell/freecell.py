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

T = 8
SPD = 4
FPS = 60

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
    'isMoving': False,
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

class App:
    def __init__(self):
        pyxel.init(128, 200, title="Freecell", display_scale=4, quit_key=pyxel.KEY_Q, fps=FPS)
        if DeviceChecker().is_pc():
            pyxel.mouse(True)
        pyxel.load("freecell.pyxres")
        self.restart()
        pyxel.run(self.update, self.draw)

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
                if 48 <= x and x < 56 and 64 <= y and y < 72:
                    STATE['newId'] += '0'
                if 56 <= x and x < 64 and 64 <= y and y < 72:
                    STATE['newId'] += '1'
                if 64 <= x and x < 72 and 64 <= y and y < 72:
                    STATE['newId'] += '2'
                if 72 <= x and x < 80 and 64 <= y and y < 72:
                    STATE['newId'] += '3'
                if 48 <= x and x < 56 and 72 <= y and y < 80:
                    STATE['newId'] += '4'
                if 56 <= x and x < 64 and 72 <= y and y < 80:
                    STATE['newId'] += '5'
                if 64 <= x and x < 72 and 72 <= y and y < 80:
                    STATE['newId'] += '6'
                if 72 <= x and x < 80 and 72 <= y and y < 80:
                    STATE['newId'] += '7'
                if 48 <= x and x < 56 and 80 <= y and y < 88:
                    STATE['newId'] += '8'
                if 56 <= x and x < 64 and 80 <= y and y < 88:
                    STATE['newId'] += '9'
            if 64 <= x and x < 80 and 80 <= y and y < 88:
                STATE['newId'] = STATE['newId'][:-1]

            if 48 <= x and x < 64 and 96 <= y and y < 104:
                if STATE['newId']:
                    STATE['time'] = 0
                    self.restart(int(STATE['newId']))
                STATE['newId'] = ''
                STATE['idSelection'] = False

            if 64 <= x and x < 80 and 94 <= y and y < 104:
                STATE['newId'] = ''
                STATE['idSelection'] = False

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
                m.y = (m.fm[1] * (SPD - m.cnt) + m.to[1] * m.cnt) * T / SPD + 40
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
            if 56 <= x and x < 72 and 88 <= y and y < 96:
                STATE['help'] = False

    def update(self):
        global MOVE
        if STATE['idSelection']:
            self.set_id()
            return

        if STATE['help']:
            self.help()
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x, y = pyxel.mouse_x, pyxel.mouse_y
            if 0 <= y and y < 8 and 0 <= x and x < 24: # id
                STATE['idSelection'] = True
                STATE['newId'] = str(STATE['id'])
                return
            if 0 <= y and y < 8 and 24 <= x and x < 48: # new
                STATE['time'] = 0
                self.restart()
                return
            if 0 <= y and y < 8 and 48 <= x and x < 72: # retry
                if STATE['isGameClear']:
                    STATE['time'] = 0
                self.restart(STATE['id'])
                return
            if 0 <= y and y < 8 and 72 <= x and x < 96: # undo
                self.undo()
                return
            if 0 <= y and y < 8 and 96 <= x and x < 104: # help
                STATE['help'] = True                
                return

        if STATE['isGameClear']:
            return

        if STATE['isGameOver']:
            return

        if pyxel.frame_count % FPS == 0:
            if STATE['time'] < 5999:
                STATE['time'] += 1

        if MOVE:
            self.do_move()
            return

        if not STATE['isNewGame']:
            if self.auto_move_to_home():
                return

        if all([_.num == 12 for _ in HOME]):
            STATE['isGameClear'] = True
            UNDO.clear()
            return

        if self.is_game_over():
            STATE['isGameOver'] = True
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
        if x >= 0 and x < 128:
            dx = x // 16
        if y < 32 and y >= 8:
            dy = -4
        if y >= 40:
            dy = (y - 40) // T

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
        pyxel.bltm(0, 0, 0, 0, 0, 256, 256)

        mm, ss = STATE['time'] // 60 , STATE['time'] % 60
        pyxel.text(2, 2, f"{STATE['id']:05}", 7)
        pyxel.text(30, 2, f"NEW", 7)
        pyxel.text(50, 2, f"RETRY", 7)
        pyxel.text(76, 2, f"UNDO", 7 if self.has_undo() else 11)
        pyxel.text(98, 2, f"?", 7)
        pyxel.text(102, 2, f"{mm:3}:{ss:02}", 7)

        for i, d in enumerate(DECK):
            for j, c in enumerate(d):
                c.x = i * 2 * T
                c.y = j * T + 40
                c.draw()

        for i, c in enumerate(HOME):
            c.x = i * 2 * T + 64
            c.y = 8
            c.draw()

        for i, c in enumerate(FREE):
            if c is not None:
                c.x = i * 2 * T
                c.y = 8
                c.draw()

        for c in MOVE:
            c.draw()

        if STATE['isGameOver']:
            pyxel.bltm(40, 48, 0, 40, 48, 48, 24)
            pyxel.text(48, 58, f"YOU LOSE", 7)

        if STATE['idSelection']:
            pyxel.bltm(32, 32, 0, 192, 0, 64, 80)
            pyxel.text(40, 40, f"ENTER GAME ID", 7)
            pyxel.text(58, 50, f"{STATE['newId']:>5}", 7)
            pyxel.text(50, 66, f"0 1 2 3", 7)
            pyxel.text(50, 74, f"4 5 6 7", 7)
            pyxel.text(50, 82, f"8 9 DEL", 7)
            pyxel.text(52, 98, f"OK  BK", 7)

        if STATE['help']:
            pyxel.bltm(0, 40, 0, 192, 128, 128, 64)
            pyxel.text(0, 48, "  Tap sequence: Move at once", 7)
            pyxel.text(0, 64, " Tap home cell: Move next card", 7)
            pyxel.text(0, 80, "   Tap game ID: Select game", 7)
            pyxel.text(60, 90, f"OK", 7)

App()

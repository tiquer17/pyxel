import pyxel
import copy

T = 8

DECK = []
HOME = []
FREE = []

STATE = {
    'isGameOver': False,
    'isNewGame': True,
    'time': 0,
    'id': 0,
    'newId': '',
    'idSelection': False,
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

    def __init__(self, num, suit, x=0, y=0):
        self.num = num 
        self.suit = suit # 0: spade, 1: heart, 2: club, 3: diamond
        self.x = x
        self.y = y

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
        pyxel.init(128, 200, title="Freecell", display_scale=4, quit_key=pyxel.KEY_Q)
        pyxel.mouse(True)
        pyxel.load("freecell.pyxres")
        self.restart()
        pyxel.run(self.update, self.draw)

    def restart(self, id=0):
        if id == 0:
            id = pyxel.rndi(1, 32000)
        STATE['id'] = id
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

    def update(self):
        if STATE['idSelection']:
            self.set_id()
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x, y = pyxel.mouse_x, pyxel.mouse_y
            if 0 <= y and y < 8 and 0 <= x and x < 24: # id
                STATE['idSelection'] = True
            if 0 <= y and y < 8 and 32 <= x and x < 56: # new
                STATE['time'] = 0
                self.restart()
            if 0 <= y and y < 8 and 64 <= x and x < 88: # retry
                if STATE['isGameClear']:
                    STATE['time'] = 0
                self.restart(STATE['id'])

        if STATE['isGameClear']:
            return

        if pyxel.frame_count % 30 == 0:
            STATE['time'] += 1

        if all([_.num == 12 for _ in HOME]):
            STATE['isGameClear'] = True

        if not STATE['isNewGame']:
            if self.auto_move_to_home():
                return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            dx, dy, fy = self.get_position(pyxel.mouse_x, pyxel.mouse_y)
            # moving deck cards
            if dy >= 0 and dx >= 0:
                STATE['isNewGame'] = False
                c1 = DECK[dx][dy]

                # check if super move is possible.
                tmp = c1
                for c in DECK[dx][(dy+1):]:
                    if tmp.num - c.num != 1 or tmp.suit == c.suit:
                        return
                    tmp = c

                num_free_cells = len([_ for _ in FREE if _ is None])
                num_empty_decks = len([_ for _ in DECK if len(_) == 0])
                num_super_move = (2 ** num_empty_decks) * (num_free_cells + 1)

                # moving to another cascade
                if len(DECK[dx][dy:]) <= num_super_move:
                    for i in range(dx + 1, dx + 8):
                        if len(DECK[i % 8]) > 0:
                            c2 = DECK[i % 8][-1]
                            if c2.num - c1.num == 1 and (c2.suit + c1.suit) % 2 == 1:
                                DECK[i % 8].extend(DECK[dx][dy:])
                                tmp = DECK[dx][:dy]
                                DECK[dx] = tmp
                                return
                # moving to empty cascade
                if len(DECK[dx][dy:]) <= num_super_move // 2:
                    for i in range(dx + 1, dx + 8):
                        if len(DECK[i % 8]) == 0:
                            DECK[i % 8].extend(DECK[dx][dy:])
                            tmp = DECK[dx][:dy]
                            DECK[dx] = tmp
                            return

                # if bottom move
                if len(DECK[dx]) == dy + 1:
                    # moving to free cell
                    if dy == len(DECK[dx]) - 1:
                        for i, f in enumerate(FREE):
                            if f is None:
                                FREE[i] = DECK[dx].pop()
                                return

                # moving to home cell
                if HOME[c1.suit].num == c1.num - 1:
                    HOME[c1.suit] = DECK[dx].pop()
                    return

            # moving free cell cards
            if fy >= 0 and dx >= 0 and dx <= 3:
                c1 = FREE[dx]

                if c1 is not None:
                    # moving to a cascade
                    for i in range(8):
                        if len(DECK[i % 8]) > 0:
                            c2 = DECK[i % 8][-1]
                            if c2.num - c1.num == 1 and (c2.suit + c1.suit) % 2 == 1:
                                DECK[i % 8].append(c1)
                                FREE[dx] = None
                                return
                    # moving to an empty cascade
                    for i in range(8):
                        if len(DECK[i % 8]) == 0:
                            DECK[i % 8].append(c1)
                            FREE[dx] = None
                            return

                    # moving to home cell
                    if HOME[c1.suit].num == c1.num - 1:
                        HOME[c1.suit] = c1
                        FREE[dx] = None
                        return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            STATE['isNewGame'] = False

            dx, dy, fy = self.get_position(pyxel.mouse_x, pyxel.mouse_y)
            if dy >= 0 and dx >= 0:
                c1 = DECK[dx][dy]
                if len(DECK[dx]) == dy + 1:
                    # moving to home cell
                    if HOME[c1.suit].num == c1.num - 1:
                        HOME[c1.suit] = DECK[dx].pop()
                        return

                    # moving to free cell
                    if dy == len(DECK[dx]) - 1:
                        for i, f in enumerate(FREE):
                            if f is None:
                                FREE[i] = DECK[dx].pop()
                                return

            # moving free cell cards
            if fy >= 0 and dx >= 0 and dx <= 3:
                c1 = FREE[dx]
                # moving to home cell
                if c1 is not None:
                    if HOME[c1.suit].num == c1.num - 1:
                        HOME[c1.suit] = c1
                        FREE[dx] = None
                        return


    def get_position(self, x, y):
        dx, dy, fy = -1, -1, -1
        if x >= 0 and x < 128:
            dx = x // 16
        if y < 32 and y >= 8:
            fy = 1
        if y >= 40:
            dy = (y - 40) // T

        if dx >= 0 and dy >= 0:
            l = len(DECK[dx])
            if dy >= l + 2:
                dy = -1
            elif dy >= l:
                dy = l - 1
        return dx, dy, fy

    def auto_move_to_home(self):
        cur = [h.num for h in HOME]
        for d in DECK:
            if len(d) > 0:
                c = d[-1]
                if c.num - cur[c.suit] == 1 and (c.num == 1 or c.num <= min(cur[((c.suit + 1) % 2)::2]) + 1):
                    HOME[c.suit] = d.pop()
                    return True
        for i, c in enumerate(FREE):
            if c is not None:
                if c.num - cur[c.suit] == 1 and (c.num == 1 or c.num <= min(cur[((c.suit + 1) % 2)::2]) + 1):
                    HOME[c.suit] = c
                    FREE[i] = None
                    return True
        return False

    def draw(self):
        pyxel.bltm(0, 0, 0, 0, 0, 256, 256)

        mm, ss, id = STATE['time'] // 60 , STATE['time'] % 60, STATE['id']
        pyxel.text(2, 2, f"{id:05}", 7)
        pyxel.text(38, 2, f"NEW", 7)
        pyxel.text(66, 2, f"RETRY", 7)
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

        if STATE['idSelection']:
            pyxel.bltm(32, 32, 0, 192, 0, 64, 80)
            newId = STATE['newId']

            pyxel.text(40, 40, f"ENTER DECK ID", 7)
            pyxel.text(58, 50, f"{newId:>5}", 7)
            pyxel.text(50, 66, f"0 1 2 3", 7)
            pyxel.text(50, 74, f"4 5 6 7", 7)
            pyxel.text(50, 82, f"8 9 DEL", 7)
            pyxel.text(52, 98, f"OK  BK", 7)



App()

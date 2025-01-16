import pyxel
import copy

T = 8

DECK = []
HOME = []
FREE = []

SUIT = [2, 3, 1, 0]
STATE = {
    'isGameOver': False,
    'time': 0,
    'id': 0,
}


# gameover clear right click

# from https://rosettacode.org/wiki/Deal_cards_for_FreeCell#Python
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
        pyxel.init(200, 200, title="Freecell", display_scale=4, quit_key=pyxel.KEY_Q)
        pyxel.mouse(True)
        pyxel.load("freecell.pyxres")
        self.restart()
        pyxel.run(self.update, self.draw)

    def restart(self, id=0):
        if id == 0:
            id = pyxel.rndi(1, 32000)
        STATE['id'] = id
        cards = deal(STATE['id'])
        DECK.clear()
        DECK.extend([[], [], [], [], [], [], [], []])
        for i, c in enumerate(cards):
            DECK[i % 8].append(Card(c // 4, SUIT[c % 4]))
        FREE.clear()
        FREE.extend([None, None, None, None])
        HOME.clear()
        HOME.extend([Card(-1, -1), Card(-1, -1), Card(-1, -1), Card(-1, -1)])
        STATE['time'] = 0

    def update(self):
        if  pyxel.btnp(pyxel.KEY_R):
            self.restart(STATE['id'])
        if  pyxel.btnp(pyxel.KEY_N):
            self.restart()

        if pyxel.frame_count % 30 == 0:
            STATE['time'] += 1

        self.auto_move_to_home()

        x, y = pyxel.mouse_x , pyxel.mouse_y

        dx, dy, fy = -1, -1, -1
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) or pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            if x % 24 > 8:
                dx = x // 24
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

            print(dx, dy, fy)
            # moving deck cards
            if dy >= 0 and dx >= 0:
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

                print(num_super_move)

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

                # bottom move
                if len(DECK[dx]) == dy + 1:

                    # moving to home cell
                    if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
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
                if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
                    if HOME[c1.suit].num == c1.num - 1:
                        HOME[c1.suit] = c1
                        FREE[dx] = None
                        return

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

    def auto_move_to_home(self):
        cur = [h.num for h in HOME]
        for d in DECK:
            if len(d) > 0:
                c = d[-1]
                if c.num - cur[c.suit] == 1 and (c.num == 1 or c.num <= min(cur[(c.suit % 2 + 1)::2]) + 1):
                    HOME[c.suit] = d.pop()
                    return
        for i, c in enumerate(FREE):
            if c is not None:
                if c.num - cur[c.suit] == 1 and (c.num == 1 or c.num <= min(cur[(c.suit % 2 + 1)::2]) + 1):
                    HOME[c.suit] = c
                    FREE[i] = None
                    return


    def draw(self):
        pyxel.bltm(0, 0, 0, 0, 0, 256, 256)

        time, id = STATE['time'], STATE['id']
        pyxel.text(8, 2,  f"#{id:05}", 11)
        pyxel.text(180, 2, f"{time:3}", 11)

        for i, d in enumerate(DECK):
            for j, c in enumerate(d):
                c.x = i * 3 * T + 8
                c.y = j * T + 40
                c.draw()

        for i, c in enumerate(HOME):
                c.x = i * 3 * T + 104
                c.y = 8
                c.draw()

        for i, c in enumerate(FREE):
                if c is not None:
                    c.x = i * 3 * T + 8
                    c.y = 8
                    c.draw()

App()

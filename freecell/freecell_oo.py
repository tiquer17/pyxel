from __future__ import annotations
import pyxel

# from https://qiita.com/igarashisan_t/items/6e5fc39dd5bafd195000
import platform
# from js はEmscripten環境以外では例外発生するのでcatchして環境を判定する
try:
    from js import navigator # type: ignore
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
FPS = 60

class Game:

    def __init__(self):
        pyxel.init(T * 16, T * 24, title="Freecell", display_scale= 32 // T , quit_key=pyxel.KEY_Q, fps=FPS)
        self.is_pc = DeviceChecker().is_pc()
        if self.is_pc:
            pyxel.mouse(True)
        pyxel.load("freecell_oo.pyxres")
        self.board = Board(self.is_pc)
        pyxel.run(self.update, self.draw)

    def update(self):
        self.board.update()

    def draw(self):
        self.board.draw()

class Board:
    STATE_NEW = 0
    STATE_PLAYING = 1
    STATE_GAMEOVER = 2
    STATE_GAMECLEAR = 3

    def __init__(self, is_pc: bool):
        self.is_pc = is_pc
        self.time = Time(self)
        self.move = Move(self)
        self.game_id_dialog = GameIdDialog(self)
        self.help_dialog = HelpDialog(self)
        self.btn_game_id = Button(0, 0, 3 * T)
        self.btn_new = Button(3 * T, 0, 3 * T, label="NEW")
        self.btn_retry = Button(6 * T, 0, 3 * T, label="RETRY")
        self.btn_undo = Button(9 * T, 0, 3 * T, label="UNDO", is_active=self.move.has_undo)
        self.btn_help = Button(12 * T, 0, T, label="?")
        self.reset()

    def reset(self, game_id: int = 0, retry: bool = False):
        self.changed : bool = True
        self.time_changed: bool = False
        self.freecells : list[Free] = [Free(i) for i in range(4)]
        self.homecells : list[Home] = [Home(i) for i in range(4)]
        self.decks : list[Deck] = [Deck(i) for i in range(8)]
        if game_id == 0:
            self.game_id : int = pyxel.rndi(1, 9999)
        else:
            self.game_id : int  = game_id
        cards = deal(self.game_id)
        for i, c in enumerate(cards):
            self.decks[i % 8].cards.append(Card(c // 4 + 1, [2, 3, 1, 0][c % 4]))
        self.btn_game_id.label= f"{self.game_id:05}"
        self.move.reset()
        if not retry or self.state == Board.STATE_GAMECLEAR:
            self.time.reset()
        self.state: int = Board.STATE_NEW

    def update(self):

        if pyxel.frame_count % FPS == 0 and self.state in (Board.STATE_NEW, Board.STATE_PLAYING) and not self.game_id_dialog.is_shown and not self.help_dialog.is_shown:
            self.time.update()

        if self.move.is_moving():
            self.move.update()
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x, y = pyxel.mouse_x, pyxel.mouse_y
            if self.game_id_dialog.is_shown:
                for b in self.game_id_dialog.buttons:
                    if b.contains(x, y):
                        b.click()
                        return
                return

            if self.help_dialog.is_shown:
                if self.help_dialog.button.contains(x, y):
                    self.help_dialog.hide()
                return

        if self.state == Board.STATE_PLAYING and self.autoplay():
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x, y = pyxel.mouse_x, pyxel.mouse_y

            if self.btn_game_id.contains(x, y):
                self.game_id_dialog.show(self.game_id)
                return

            if self.btn_new.contains(x, y):
                self.state = Board.STATE_NEW
                self.reset()
                return
            if self.btn_retry.contains(x, y):
                self.reset(self.game_id, retry=True)
                return
            if self.btn_undo.contains(x, y):
                if self.move.has_undo():
                    self.move.undo()
                return
            if self.btn_help.contains(x, y):
                self.help_dialog.show()
                return

            num_free_cells = len([_ for _ in self.freecells if _.is_empty()])
            num_empty_decks = len([_ for _ in self.decks if _.is_empty()])
            num_super_move = (2 ** num_empty_decks) * (num_free_cells + 1)

            for fm in self.decks:
                if fm.contains(x, y):
                    cards = fm.get_sequence((y - 5 * T) // T)
                    if cards:
                        # move to deck
                        for i in range (fm.id + 1, fm.id + 8):
                            to = self.decks[i % 8]
                            if not to.is_empty() and to.can_take(cards, num_super_move):
                                self.move.set(cards, fm, to)
                                return
                        # move to freecell
                        if len(cards) == 1:
                            for f in self.freecells:
                                if f.is_empty():
                                    self.move.set(cards, fm, f)
                                    return
                        # move to empty deck
                        for i in range (fm.id + 1, fm.id + 8):
                            to = self.decks[i % 8]
                            if to.is_empty() and to.can_take(cards, num_super_move // 2):
                                self.move.set(cards, fm, to)
                                return
                        # move to homecell
                        if len(cards) == 1:
                            for to in self.homecells:
                                if to.can_take(cards[0]):
                                    self.move.set(cards, fm, to)
                                    return

            for fm in self.freecells:
                if fm.contains(x, y):
                    if not fm.is_empty():
                        for to in self.decks:
                            if not to.is_empty() and to.can_take([fm.card]):
                                self.move.set([fm.card], fm, to)
                                return
                        for to in self.decks:
                            if to.is_empty() and to.can_take([fm.card]):
                                self.move.set([fm.card], fm, to)
                                return
                        for to in self.homecells:
                            if to.can_take(fm.card):
                                self.move.set([fm.card], fm, to)
                                return

            for to in self.homecells:
                if to.contains(x, y):
                    for fm in self.freecells:
                        if not fm.is_empty() and to.can_take(fm.card):
                            self.move.set([fm.card], fm, to)
                            return
                    for fm in self.decks:
                        if not fm.is_empty() and to.can_take(fm.cards[-1]):
                            self.move.set(fm.cards[-1:], fm, to)
                            return

    def is_game_clear(self) -> bool:
        return all([h.card.num == 13 for h in self.homecells])        

    def is_game_over(self) -> bool:
        if any([f.is_empty() for f in self.freecells]):
            return False
        if any([d.is_empty() for d in self.decks]):
            return False
        for c in [d.cards[-1] for d in self.decks] + [f.card for f in self.freecells]:
                for d in self.decks:
                    if d.can_take([c]):
                        return False
                for h in self.homecells:
                    if h.can_take(c):
                        return False
        return True
        
    def autoplay(self):
        """
        Microsoft safe auto play

        only plays an available card to its homecell automatically when all of the lower-ranked cards of the opposite color are already on the homecells
        (except that a two is played if the corresponding ace is on its homecell); aces are always played when available.
        """
        def can_autoplay(c: Card):
            return self.homecells[c.suit].can_take(c) and (c.num == 2 or c.num <= min([self.homecells[i].card.num for i in range((c.suit + 1) % 2,4,2)]) + 1)

        for fm in self.decks:
            if not fm.is_empty():
                c = fm.cards[-1]
                if can_autoplay(c):
                    self.move.set([c], fm, self.homecells[c.suit], False)
                    return True
        for fm in self.freecells:
            if not fm.is_empty():
                c = fm.card
                if can_autoplay(c):
                    self.move.set([c], fm, self.homecells[c.suit], False)
                    return True
        return False

    def draw(self):
        if self.time_changed or self.is_pc:
            self.time_changed = False
            self.time.draw()
        if self.changed or self.is_pc:
            self.changed = False
            pyxel.rect(0, T, T * 16, T * 23, 3)
            self.btn_game_id.draw()
            self.btn_new.draw()
            self.btn_retry.draw()
            self.btn_undo.draw()
            self.btn_help.draw()
            for c in self.freecells:
                c.draw()
            for c in self.homecells:
                c.draw()
            for d in self.decks:
                d.draw()
            self.move.draw()
            if self.state == Board.STATE_GAMEOVER:
                pyxel.rect(T * 5, T * 6, T * 6, T * 3, 3)
                type_text(T * 6, T * 7, f"YOU LOSE")
            if self.state == Board.STATE_GAMECLEAR:
                time = self.time.get_time().strip()
                type_text(T * 6, T * 7, f"YOU WIN!", shading=True)
                type_text(T * 2 + 8, T * 9, f"CLEARED #{self.game_id:05} IN {time}", shading=True)
            self.game_id_dialog.draw()
            self.help_dialog.draw()


class Card:
    def __init__(self, num: int, suit: int, x: int = 0, y: int = 0):
        self.num = num # start with one
        self.suit = suit # 0: spade, 1: heart, 2: club, 3: diamond
        self.x = x
        self.y = y

    def can_take(self, card: Card) -> bool:
        return self.num - card.num == 1 and (self.suit + card.suit) % 2 == 1

    def draw(self):
        if self.suit % 2 == 1:
            pyxel.pal(0, 8)
        pyxel.blt(self.x, self.y , 0, self.num * T, 0, T, T, 15)
        pyxel.blt(self.x + T, self.y , 0, self.suit * T, T, T, T, 15)
        pyxel.blt(self.x, self.y + T, 0, 4 * T, T, 2 * T, T, 15)
        pyxel.blt(self.x, self.y + 2 * T, 0, self.suit * T, T, - T, - T ,15)
        pyxel.blt(self.x + T, self.y + 2 * T, 0, self.num * T, 0, - T, - T, 15)
        pyxel.pal()

class Deck:
    def __init__(self, id: int):
        self.id = id
        self.x, self.y, self.w, self.h = 2 * id * T, 5 * T, 2 * T, 19 * T
        self.cards : list[Card] = []

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    def get_sequence(self, i: int) -> list[Card]:
        if self.is_empty():
            return []
        n_cards = len(self.cards)
        if n_cards + 2 <= i:
            return []
        if n_cards <= i:
            i = n_cards - 1
        cards = self.cards[i:]
        tmp = cards[0]
        for c in cards[1:]:
            if not tmp.can_take(c):
                return []
            tmp = c
        return cards

    def is_empty(self) -> bool:
        return not self.cards

    def can_take(self, cards: list[Card], num_super_move: int = 1) -> bool:
        if len(cards) > num_super_move:
            return False
        return self.is_empty() or self.cards[-1].can_take(cards[0]) 

    def take(self, card: Card):
        self.cards.append(card)

    def draw(self):
        for i, c in enumerate(self.cards):
            c.x = self.x
            c.y = self.y + i * T
            c.draw()

class Home:
    def __init__(self, id: int):
        self.id = id
        self.x, self.y, self.w, self.h = (id + 4) * 2 * T, T, 2 * T, 3 * T
        self.card : Card = Card(0, id)

    def contains(self, x, y):
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    def can_take(self, card):
        return card.suit == self.id and card.num - self.card.num == 1

    def take(self, card: Card):
        card.x, card.y = self.x, self.y
        self.card = card

    def draw(self):
        if self.card.num == 0:
            pyxel.pal(11, 6)
            pyxel.blt(self.x, self.y, 0, 0, 2 * T, self.w, self.h)
            pyxel.pal()
        else:
            self.card.x, self.card.y = self.x, self.y
            self.card.draw()

class Free:
    def __init__(self, id: int):
        self.id = id
        self.x, self.y, self.w, self.h = id * 2 * T, T, 2 * T, 3 * T
        self.card: Card | None = None

    def contains(self, x, y):
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    def is_empty(self):
        return self.card is None
    
    def take(self, card: Card):
        self.card = card

    def draw(self):
        if self.card is None:
            pyxel.blt(self.x, self.y, 0, 0, 2 * T, self.w, self.h)
        else:
            self.card.x, self.card.y = self.x, self.y
            self.card.draw()

class Move:
    SPEED = 4
    def __init__(self, board: Board):
        self.cards = []
        self.board = board
        self.snapshot = None

    def set(self, cards: list[Card], fm: Deck | Free, to: Deck | Free | Home, can_undo: bool = True):
        self.board.changed = True
        if self.board.state == Board.STATE_NEW:
            self.board.state = Board.STATE_PLAYING
        if can_undo:
            self.snapshot = ([h.card for h in self.board.homecells], [f.card for f in self.board.freecells], [d.cards[:] for d in self.board.decks])
        self.cards = cards
        self.fm_x, self.fm_y = cards[0].x, cards[0].y
        if isinstance(to, Deck):
            self.to_y = to.y + len(to.cards) * T
        else:
            self.to_y = to.y
        if isinstance(fm, Deck):
            del fm.cards[-len(cards):]
        else:
            fm.card = None
        self.fm = fm
        self.to = to
        self.cnt = Move.SPEED

    def is_moving(self) -> bool:
        return bool(self.cards)
    
    def has_undo(self) -> bool:
        return self.snapshot is not None
    
    def reset(self):
        self.snapshot = None

    def undo(self):
        self.board.changed = True
        for i, c in enumerate(self.snapshot[0]):
            self.board.homecells[i].card = c
        for i, c in enumerate(self.snapshot[1]):
            self.board.freecells[i].card = c
        for i, cards in enumerate(self.snapshot[2]):
            self.board.decks[i].cards = cards[:]
        self.snapshot = None
        self.board.state = Board.STATE_PLAYING

    def update(self):
        self.board.changed = True
        if self.cnt == 0:
            for c in self.cards:
                self.to.take(c)
            self.cards.clear()
            if self.board.is_game_over():
                self.board.state = Board.STATE_GAMEOVER
            if self.board.is_game_clear():
                self.board.state = Board.STATE_GAMECLEAR
                self.snapshot = None
        else:
            for i, c in enumerate(self.cards):
                c.x = (self.fm_x * self.cnt + self.to.x * (Move.SPEED - self.cnt)) / Move.SPEED
                c.y = (self.fm_y * self.cnt + self.to_y * (Move.SPEED - self.cnt)) / Move.SPEED + i * T
            self.cnt -= 1

    def draw(self):
        for c in self.cards:
            c.draw()

class Time:
    def __init__(self, board: Board):
        self.x, self.y, self.w, self.h = 13 * T, 0, T * 3, T
        self.board = board
        self.reset()

    def reset(self):
        self.board.time_changed = True
        self.time: int = 0

    def update(self):
        if self.time < 5999:
            self.board.time_changed = True
            self.time += 1

    def get_time(self):
        mm, ss = self.time // 60 , self.time % 60
        return f"{mm:2}:{ss:02}"

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, 3)
        type_text(self.x + 4, self.y, self.get_time())

class Button:
    def __init__(self, x: int, y: int, w: int, on_click=lambda: None, label: str = "", is_active=lambda: True):
        self.x, self.y, self.w, self.h = x, y, w, T
        self.on_click = on_click
        self.label = label
        self.is_active: bool = is_active

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h
    
    def click(self):
        if self.is_active():
            self.on_click()

    def draw(self):
        pyxel.blt(self.x, self.y, 0, 0, 5 * T, T // 2, T)
        for i in range(self.w // T - 1):
            pyxel.blt(self.x + i * T + T // 2, self.y, 0, T // 2, 5 * T, T, T)
        pyxel.blt(self.x + self.w - T // 2, self.y, 0, T + T // 2, 5 * T, T //2, T)
        type_text(self.x + self.w // 2 - len(self.label) * T // 4, self.y, self.label, 7 if self.is_active() else 11)

class GameIdDialog:
    def __init__(self, board: Board):
        self.x, self.y, self.w, self.h = T * 4, T * 4, T * 8, T * 11
        self.board = board
        self.buttons: list[Button] = []
        self.is_shown: bool = False

        for c in "0123456789":
            i = int(c)
            self.buttons.append(Button(T * (6 + i % 4), T * (8 + i // 4), T, on_click=lambda c=c: self.edit(c), label=c))
        self.buttons.append(Button(T * 8, T * 10, T * 2, on_click=lambda: self.edit("DEL"), label="DEL"))

        for i, c in enumerate(["-", "+"]):
            self.buttons.append(Button(T * (6 + 2 * i), T * 11, T * 2, on_click=lambda c=c: self.edit(c), label=c))
        for i, c in enumerate(["OK", "CSL"]):
            self.buttons.append(Button(T * (6 + 2 * i), T * 13, T * 2, on_click=lambda c=c: self.edit(c), label=c))

    def show(self, game_id: int):
        self.board.changed = True
        self.game_id = str(game_id)
        self.is_shown = True

    def hide(self):
        self.is_shown = False

    def edit(self, c: str):
        self.board.changed = True
        if c in "0123456789":
            if len(self.game_id) < 5:
                self.game_id += c
        elif c == "+":
            if self.game_id == "":
                self.game_id = "1"
            elif int(self.game_id) < 99999:
                self.game_id = str(int(self.game_id) + 1)
        elif c == "-":
            if self.game_id != "" and int(self.game_id) > 1:
                self.game_id = str(int(self.game_id) - 1)
        elif c == "DEL":
            self.game_id = self.game_id[:-1]
        elif c == "OK":
            if self.game_id and self.board.game_id != int(self.game_id):
                self.board.reset(int(self.game_id))
            self.hide()
        elif c == "CSL":
            self.hide()

    def draw(self):
        if self.is_shown:
            pyxel.rect(self.x, self.y, self.w, self.h, 5)
            type_text(T * 5, T * 5, "ENTER GAME ID")
            pyxel.rect(T * 6, T * 6, T * 4, T, 3)
            type_text(T * 7 + 4, T * 6, f"{self.game_id:>5}")
            for b in self.buttons:
                b.draw()

class HelpDialog:
    def __init__(self, board: Board):
        self.x, self.y, self.w, self.h = 0, T * 5, T * 16, T * 10
        self.board = board
        self.button = Button(T * 7, T * 13, T * 2, on_click=self.hide, label="OK")
        self.is_shown = False

    def show(self):
        self.board.changed = True
        self.is_shown = True

    def hide(self):
        self.board.changed = True
        self.is_shown = False

    def draw(self):
        if self.is_shown:
            pyxel.rect(self.x, self.y, self.w, self.h, 5)
            type_text(T * 4, T * 6, "TAPPING FREECELL")
            type_text(T, T * 8, " TAP SEQUENCE: MOVE STACK")
            type_text(T, T * 10, "TAP HOME CELL: DRAW NEXT CARD")
            type_text(T, T * 12, "  TAP GAME ID: SELECT GAME")
            self.button.draw()

############
# Utilities
############

def type_text(x: int, y: int, s: str, col=7, shading=False):
    for i, c in enumerate(s):
        ascii = ord(c) - 32
        if shading:
            pyxel.pal(7, 0)
            pyxel.blt(x + i * 8 + 1, y + 1, 1, (ascii % 16) * 8, (ascii //16)* 16, 8, 16, 0)
        pyxel.pal(7, col)
        pyxel.blt(x + i * 8, y, 1, (ascii % 16) * 8, (ascii //16)* 16, 8, 16, 0)
        pyxel.pal()

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

Game()


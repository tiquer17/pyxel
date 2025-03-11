import pyxel
import random

T = 8
class Maze:

    def __init__(self):
        self.floor = [[9] * 30 for _ in range(30)]
        self.generate_maze()

    def generate_maze(self):
        self.n_rooms = random.choice([7, 8])
        self.grid_size = grid_size = 4 if random.random() < 0.75 else 3
        directions = [1, grid_size, -1, -grid_size]
        room_ids = random.sample(range(grid_size**2), self.n_rooms)

        self.grids = []
        self.rooms = []
        for i in range(grid_size**2):
            if i in room_ids:
                r = Room(i, grid_size)
                self.grids.append(r)
                self.rooms.append(r)
            else:
                self.grids.append(Point(i, grid_size))

        visited = set()
        visited.add(room_ids[0])
        paths = set()
        i = room_ids[0]
        d = directions[random.randint(0,3)]
        while len(visited) < self.n_rooms:
            d = directions[random.randint(0,3)]
            if 0 <= i + d < grid_size**2 and (not abs(d) == 1 or (i * 2 + d) % (grid_size*2) != grid_size*2 - 1):
                paths.add(Path(i, i+d, self.grids))
                if i + d in room_ids:
                    visited.add(i+d)
                i += d

        # make rooms
        for r in self.rooms:
            for y in range(r.y, r.y + r.h):
                for x in range(r.x, r.x + r.w):
                    self.floor[y][x] = 0

        # make paths
        for p in paths:
            p.junction()
            if p.grid_b - p.grid_a == 1:
                mx = (p.ax + p.bx) // 2
                for x in range(p.ax, p.bx + 1):
                    if x <= mx:
                        self.floor[p.ay][x] = 0
                    if x >= mx:
                        self.floor[p.by][x] = 0
                for y in range(min(p.ay, p.by), max(p.ay, p.by)):
                    self.floor[y][mx] = 0 
            else:
                my = (p.ay + p.by) // 2
                for y in range(p.ay, p.by + 1):
                    if y <= my:
                        self.floor[y][p.ax] = 0
                    if y >= my:
                        self.floor[y][p.bx] = 0
                for x in range(min(p.ax, p.bx), max(p.ax, p.bx)):
                    self.floor[my][x] = 0

    def get_room(self, x, y):
        for r in self.rooms:
            if r.x <= x < r.x + r.w and r.y <= y < r.y + r.h:
                return r
        return None

    def draw(self):
        for y, _ in enumerate(self.floor):
            for x, f in enumerate(_):
                if f == 0:
                    pyxel.blt(x*8, y*8,0,0,0,8,8)
                else:
                    pyxel.blt(x*8, y*8,0,16,0,8,8)

    
class Path:

    def __init__(self, grid_a, grid_b, grids):

        self.grid_a = min(grid_a, grid_b)
        self.grid_b = max(grid_a, grid_b)
        self.grids = grids

    def junction(self):
        d = self.grid_b - self.grid_a
        a = self.grids[self.grid_a]
        b = self.grids[self.grid_b]
        if isinstance(a, Room):
            if d == 1:
                self.ax = a.x+a.w
                self.ay = a.y+random.randint(1, a.h-2)
            else:
                self.ax = a.x+random.randint(1, a.w-2)
                self.ay = a.y+a.h
        else:
            self.ax = a.x
            self.ay = a.y
        if isinstance(b, Room):
            if d == 1:
                self.bx = b.x
                if self.bx - self.ax == 2:
                    self.by = self.ay = random.randint(max(a.y, b.y) + 1, min(a.y + a.h, b.y + b.h)-2)
                else:
                    self.by = b.y+random.randint(1, b.h-2)
            else:
                self.by = b.y
                if self.by - self.ay == 2:
                    self.bx = self.ax = random.randint(max(a.x, b.x) + 1, min(a.x + a.w, b.x + b.w)-2)
                else:
                    self.bx = b.x+random.randint(1, b.w-2)
        else:
            self.bx = b.x
            self.by = b.y
        if isinstance(a, Room):
            if d == 1:
                a.junctions.append([self.ax - 1, self.ay, [1, 0]])
            else:
                a.junctions.append([self.ax, self.ay - 1, [0, 1]])
        if isinstance(b, Room):
            b.junctions.append([self.bx, self.by, [-1, 0] if d == 1 else [0, -1]])

    def __eq__(self, other):
        return self.grid_a == other.grid_a and self.grid_b == other.grid_b
    
    def __lt__(self, other):
        return self.grid_a < other.grid_a and self.grid_b < other.grid_b
    
    def __repr__(self):
        return f"Path({self.grid_a}, {self.grid_b})"
    
    def __hash__(self):
        return hash((self.grid_a, self.grid_b))
    

class Room:
    def __init__(self, i, grid_size):
        self.junctions = []
        room_size = (4, 5) if grid_size == 4 else (6, 8)
        room_offset = 2 if grid_size == 4 else 1
        self.w = random.randint(*room_size)
        self.h = random.randint(*room_size)
        self.x = (i % grid_size) * (30//grid_size) + room_offset
        self.y = (i // grid_size) * (30//grid_size) + room_offset
        if self.w != room_size[1]:
            self.x += random.randint(0, self.w - room_size[0])
        if self.h != room_size[1]:
            self.y += random.randint(0, self.h - room_size[0])
        self.i = i

class Point:
    def __init__(self, i, grid_size):
        pos = (3, 5) if grid_size == 4 else (4, 6)
        self.x = (i % grid_size) * (30//grid_size) + random.randint(*pos) 
        self.y = (i // grid_size) * (30//grid_size) + random.randint(*pos)
        self.i = i


class Character:
    def __init__(self, char_id, game):
        self.game = game
        r = self.game.maze.rooms[random.randint(0, self.game.maze.n_rooms-1)]
        self.x = (r.x + random.randint(0, r.w -1)) * T
        self.y = (r.y + random.randint(0, r.h -1)) * T
        self.char_id = char_id
        self.flip = 0        
        self.count = 0
        self.d = [0, 1]
        self.target = None

    def update(self):
        if pyxel.frame_count % 30 == 0:
            self.flip ^= 1
        if self.move():
            return
        r = self.game.maze.get_room(self.x//T, self.y//T)

        if r is None: # in a path
            self.target = None
            if self.game.maze.floor[self.y//T+self.d[1]][self.x//T+self.d[0]] == 9:
                lr = random.sample([-1, 1], k=2)
                if self.game.maze.floor[self.y//T-self.d[0]*lr[0]][self.x//T+self.d[1]*lr[0]] == 0:
                    self.d = [self.d[1]*lr[0], -self.d[0]*lr[0]]
                elif self.game.maze.floor[self.y//T-self.d[0]*lr[1]][self.x//T+self.d[1]*lr[1]] == 0:
                    self.d = [self.d[1]*lr[1], -self.d[0]*lr[1]]
                else:
                    self.d = [-self.d[0], -self.d[1]]

        else: # in a room
            if self.target is None:
                if len(r.junctions) == 1: # dead end
                    self.target = r.junctions[0]
                else:
                    self.target = random.choice([j for j in r.junctions if [self.x//T, self.y//T] != j[:2]])
                self.d = self.target[2]                

            dx, dy = self.target[0] - self.x//T, self.target[1] - self.y//T
            self.d = [self.get_direction(dx), self.get_direction(dy)]
            if self.d == [0, 0]:
                self.d = self.target[2]

        if self.game.moving:
            self.count = 8

    def get_direction(self, d): # return 1 if positive, -1 if negative
        return (d > 0) - (d < 0)

    def move(self):
        if self.count > 0:
            self.x += self.d[0]
            self.y += self.d[1]
            self.count -= 1
        return self.count > 0

    def draw(self):
        pyxel.blt(self.x, self.y,0, self.flip*T, self.char_id*T, T, T, 10)

class Player(Character):
        
    def update(self):
        if pyxel.frame_count % 30 == 0:
            self.flip ^= 1

        if self.move():
            return
        self.game.moving = False
        self.d = [0, 0]
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            self.d[0] = 1
        if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP):
            self.d[1] = -1
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            self.d[0] = -1
        if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN):
            self.d[1] = 1

        if self.d != [0, 0]:
            if self.d[0] != 0:
                if self.game.maze.floor[self.y//T][self.x//T+self.d[0]] == 9:
                    return
            if self.d[1] != 0:
                if self.game.maze.floor[self.y//T+self.d[1]][self.x//T] == 9:
                    return
            if self.game.maze.floor[self.y//T+self.d[1]][self.x//T+self.d[0]] == 0:
                self.count = 8
                self.game.moving = True

class Game:

    def __init__(self):
        pyxel.init(240, 240, title="Roguelike", fps=60, display_scale=3, quit_key=pyxel.KEY_Q)
        # pyxel.init(96, 80, title="Roguelike")
        pyxel.load("roguelike.pyxres")
        self.maze = Maze()
        self.moving = True
        self.chars = [Player(4, self), Character(5, self), Character(5, self), Character(6, self)]
        pyxel.run(self.update, self.draw)

    def update(self):
        for c in self.chars:
            c.update()


    def draw(self):
        
        self.maze.draw()
        for c in self.chars:
            c.draw()

Game()
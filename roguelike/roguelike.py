import pyxel
import random

SIZE = 30

class Maze:

    def __init__(self):
        self.floor = [[9] * SIZE for _ in range(SIZE)]
        self.parts = self.generate_maze()


    def generate_maze(self):
        n_rooms = random.choice([7, 8])
        grid = 4 if random.random() < 0.75 else 3
        self.grid = grid
        directions = [1, grid, -1, -grid]
        room_ids = random.sample(range(grid**2), n_rooms)

        parts = []
        for i in range(grid**2):
            if i in room_ids:
                parts.append(Room(i, grid))
            else:
                parts.append(Point(i, grid))


        visited = set()
        visited.add(room_ids[0])
        paths = set()
        i = room_ids[0]
        d = directions[random.randint(0,3)]
        # j = 0
        # while not (len(visited) == n_rooms and j > 20):
        while len(visited) < n_rooms:
            # if i not in room_ids and (0 <= i + d < 16 and (i * 2 + d) % 8 != 7):
            #     pass
            # else:
            d = directions[random.randint(0,3)]
            if 0 <= i + d < grid**2 and (i * 2 + d) % (grid*2) != grid*2 - 1:
                paths.add(Path(i, i+d, parts, grid))
                if i + d in room_ids:
                    visited.add(i+d)
                i += d
                # j += 1
        # print(j)
        # print(sorted(paths))
        # print(len(paths))
        # print(visited)

        for i in room_ids:
            r =parts[i]
            for y in range(r.y, r.y + r.h):
                for x in range(r.x, r.x + r.w):
                    self.floor[y][x] = 0

        for p in paths:
            if abs(p.grid_b - p.grid_a) == 1:
                mx = (p.fx + p.tx) // 2
                for x in range(p.fx, p.tx + 1):
                    if x <= mx:
                        self.floor[p.fy][x] = 0
                    if x >= mx:
                        self.floor[p.ty][x] = 0
                if p.ty > p.fy:
                    for y in range(p.fy, p.ty + 1):
                        self.floor[y][mx] = 0
                elif p.fy > p.ty:
                    for y in range(p.ty, p.fy + 1):
                        self.floor[y][mx] = 0
            else:
                my = (p.fy + p.ty) // 2
                for y in range(p.fy, p.ty + 1):
                    if y <= my:
                        self.floor[y][p.fx] = 0
                    if y >= my:
                        self.floor[y][p.tx] = 0
                if p.tx > p.fx:
                    for x in range(p.fx, p.tx):
                        self.floor[my][x] = 0
                if p.fx > p.tx:
                    for x in range(p.tx, p.fx):
                        self.floor[my][x] = 0

        return parts
    
class Path:
    def __init__(self, grid_a, grid_b, parts, grid):

        self.grid_a = min(grid_a, grid_b)
        self.grid_b = max(grid_a, grid_b)
        self.parts = parts

        d = self.grid_b - self.grid_a
        a = self.parts[self.grid_a]
        b = self.parts[self.grid_b]
        if isinstance(a, Room):
            if d == 1:
                self.fx = a.x+a.w
                self.fy = a.y+random.randint(1, a.h-2)
            else:
                self.fx = a.x+random.randint(1, a.w-2)
                self.fy = a.y+a.h
        else:
            self.fx = a.x
            self.fy = a.y
        if isinstance(b, Room):
            if d == 1:
                self.tx = b.x
                if self.tx - self.fx == 2:
                    self.ty = self.fy = random.randint(max(a.y, b.y), min(a.y + a.h, b.y + b.h)-1)
                else:
                    self.ty = b.y+random.randint(1, b.h-2)
            else:
                self.ty = b.y
                if self.ty - self.fy == 2:
                    self.tx = self.fx = random.randint(max(a.x, b.x), min(a.x + a.w, b.x + b.w)-1)
                else:
                    self.tx = b.x+random.randint(1, b.w-2)
        else:
            self.tx = b.x
            self.ty = b.y

    def __eq__(self, other):
        return self.grid_a == other.grid_a and self.grid_b == other.grid_b
    
    def __lt__(self, other):
        return self.grid_a < other.grid_a and self.grid_b < other.grid_b
    
    def __repr__(self):
        return f"Path({self.grid_a}, {self.grid_b}, {self.fx}, {self.fy}, {self.tx}, {self.ty})"
    
    def __hash__(self):
        return hash((self.grid_a, self.grid_b))

class Room:
    def __init__(self, i, grid):
        room_size = (4, 5) if grid == 4 else (6, 8)
        room_offset = 2 if grid == 4 else 1
        self.w = random.randint(*room_size)
        self.h = random.randint(*room_size)
        self.x = (i % grid) * (30//grid) + room_offset
        self.y = (i // grid) * (30//grid) + room_offset
        if self.w != room_size[1]:
            self.x += random.randint(0, self.w - room_size[0])
        if self.h != room_size[1]:
            self.y += random.randint(0, self.h - room_size[0])
        self.i = i
    
    def draw(self):
        for y in range(self.y, self.y + self.h):
            for x in range(self.x, self.x + self.w):
                pyxel.blt(x*8, y*8,0,0,0,8,8)

class Point:
    def __init__(self, i, grid):
        pos = (3, 5) if grid == 4 else (4, 6)
        self.x = (i % grid) * (30//grid) + random.randint(*pos) 
        self.y = (i // grid) * (30//grid) + random.randint(*pos)
        self.i = i

class Main:

    def __init__(self):
        pyxel.init(240, 240, title="Roguelike")
        pyxel.load("roguelike.pyxres")
        self.maze = Maze()

        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.maze = Maze()

    def draw(self):
        # pyxel.cls(0)
        for y in range(SIZE):
            for x in range(SIZE):
                pyxel.blt(x*8, y*8,0,16,0,8,8)                
        
        for y, _ in enumerate(self.maze.floor):
            for x, f in enumerate(_):
                if f == 0:
                    pyxel.blt(x*8, y*8,0,0,0,8,8)
                else:
                    pyxel.blt(x*8, y*8,0,16,0,8,8)

Main()
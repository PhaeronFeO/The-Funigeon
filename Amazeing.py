import pygame
import pygame.freetype
import pygame.mixer
from pygame.locals import *
from random import choice, randint

WIDTH = 1200
HEIGHT = 600
FrameRate = 60
clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode([WIDTH, HEIGHT])
largeFont = pygame.freetype.SysFont('Ariel', 20)
background = pygame.Surface(screen.get_size())
background.fill((0, 0, 0))
maze_tile = 25
PSpeed = 4


class Player(pygame.sprite.Sprite):
    def __init__(self, cords: tuple, dim):
        super(Player, self).__init__()
        self.Speed = PSpeed
        self.surf = pygame.Surface((dim, dim))
        self.surf.fill((255, 0, 0))
        self.rect = self.surf.get_rect()
        self.rect.bottomright = cords
        self.offset = int(dim / 2)
        self.Intense = 100
        lights.add(self)

    def update(self):
        pressed_keys = pygame.key.get_pressed()
        px, py = 0, 0
        if pressed_keys[K_UP]:
            py += -1 * self.Speed
        if pressed_keys[K_DOWN]:
            py += self.Speed
        if pressed_keys[K_LEFT]:
            px += -1 * self.Speed
        if pressed_keys[K_RIGHT]:
            px += self.Speed
        self.rect.move_ip(px, py)

        if self.rect.colliderect(bot.rect):
            print("FAILIURE")
            exit()  # DEFEAT

        if self.rect.colliderect(exit_tile.rect):
            print("VICTORY")
            exit()  # VICTORY

        collision_list = pygame.sprite.spritecollide(self, obstacles, False)
        for collided_object in collision_list:
            if px < 0 and (self.rect.left - collided_object.rect.right >= px):
                self.rect.left = collided_object.rect.right
            elif px > 0 and (self.rect.right - collided_object.rect.left <= px):
                self.rect.right = collided_object.rect.left
            if py > 0 and (self.rect.bottom - collided_object.rect.top <= py):
                self.rect.bottom = collided_object.rect.top
            elif py < 0 and (self.rect.top - collided_object.rect.bottom >= py):
                self.rect.top = collided_object.rect.bottom

        # Keep player on the screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT

    def centre_cord(self):
        return [self.rect.right - self.offset, self.rect.bottom - self.offset]


class Bot(pygame.sprite.Sprite):
    def __init__(self, cords: tuple):
        super(Bot, self).__init__()
        # self.surf = pygame.Surface((maze_tile, maze_tile))
        self.surf = pygame.image.load("Art/SHE_SCREAM.JPG").convert()
        self.rect = self.surf.get_rect()
        self.rect.topleft = cords
        self.offset = int(maze_tile / 2)
        self.Delay = int(FrameRate / int((FrameRate * PSpeed) / (maze_tile * 0.9)))
        print(self.Delay)
        self.Count = -2 * FrameRate
        self.Route = []
        self.Speed = maze_tile / self.Delay
        print(self.Speed)
        all_sprites.add(self)
        # lights.add(self)
        pygame.mixer.init()
        pygame.mixer.music.load("Music/CompressedJohn.mp3")
        pygame.mixer.music.set_volume(0)
        pygame.mixer.music.play()

    def centre_cord(self):
        return [self.rect.right - self.offset, self.rect.bottom - self.offset]

    def update(self):
        if len(self.Route) == 0:
            self.Count = FrameRate
        if self.Count == FrameRate:  # Update Route
            self.Count = 0
            route = explore2(maze_cord(self.centre_cord()), maze_cord(player.centre_cord()))[1]
            route_len = len(route)
            self.Route = []
            segsize = maze_tile * 3
            for maze_point in range(route_len):
                self.Route.append((route[maze_point][0] * segsize + maze_tile * (4 % 3),
                                   route[maze_point][1] * segsize + maze_tile * int(4 / 3)))
                if maze_point != 0:
                    self.Route[-2] = (self.Route[-1][0] * (2/3) + self.Route[-4][0] * (1/3), self.Route[-1][1] * (2/3) + self.Route[-4][1] * (1/3))
                    self.Route[-3] = (self.Route[-1][0] * (1/3) + self.Route[-4][0] * (2/3), self.Route[-1][1] * (1/3) + self.Route[-4][1] * (2/3))
                if maze_point != route_len - 1:
                    self.Route.append([])
                    self.Route.append([])
        else:
            self.Count += 1
        if self.Count % self.Delay == 0:  # Move towards player
            self.rect.topleft = self.Route[0]
            self.Route.pop(0)  # Remove the instruction it just used
            pygame.mixer.music.set_volume(50 / ((abs(player.rect.left - self.rect.left) + abs(player.rect.top - self.rect.top)) + 1))
        else: # This section is what causes the shakiness and stopping
            if self.rect.left > self.Route[0][0]:
                self.rect.left -= self.Speed
            elif self.rect.left < self.Route[0][0]:
                self.rect.left += self.Speed
            if self.rect.top > self.Route[0][1]:
                self.rect.top -= self.Speed
            elif self.rect.top < self.Route[0][1]:
                self.rect.top += self.Speed


class Wall(pygame.sprite.Sprite):
    def __init__(self, cords: tuple, dim):
        super(Wall, self).__init__()
        self.surf = pygame.Surface((dim, dim))
        self.surf.fill((0, 0, 0))
        pattern = pygame.Rect(dim / 10, dim / 10, dim - (dim / 10), dim - (dim / 10))
        pygame.draw.rect(self.surf, (50, 50, 50), pattern)
        self.rect = self.surf.get_rect()
        self.rect.topleft = cords
        all_sprites.add(self)
        obstacles.add(self)


class Floor(pygame.sprite.Sprite):
    def __init__(self, cords: tuple, dim, color, intense=0):
        super(Floor, self).__init__()
        self.surf = pygame.Surface((dim, dim))
        self.surf.fill(color)
        self.rect = self.surf.get_rect()
        self.rect.topleft = cords
        self.offset = int(dim / 2)
        self.Intense = intense
        all_sprites.add(self)

    def centre_cord(self):
        return self.rect.right - self.offset, self.rect.bottom - self.offset


def create_segment(start_cord: tuple, empty_spaces: list, dim):
    for sp in range(9):
        if sp in empty_spaces:
            Floor((start_cord[0] + dim * (sp % 3), start_cord[1] + dim * int(sp / 3)), dim, (128, 128, 128))
        else:
            Wall((start_cord[0] + dim * (sp % 3), start_cord[1] + dim * int(sp / 3)), dim)


def segment(width, height, x, y, maze_list, segsize, direction):
    maze_list[x][y] = [8 - direction, 4]
    bonus_list = []
    for bonus in range(1, 9, 2):
        if not bonus == 8 - direction:
            if bonus == 1 and y == 0:
                pass
            elif bonus == 7 and y == int((height - segsize) / segsize):
                pass
            elif bonus == 3 and x == 0:
                pass
            elif bonus == 5 and x == int((width - segsize) / segsize):
                pass
            else:
                if bonus != direction:  # Increases likelihood of twists instead of straights
                    for b in range(3):
                        bonus_list.append(bonus)
                bonus_list.append(bonus)
    direction = choice(bonus_list)
    maze_list[x][y].append(direction)
    return maze_list, direction


def generate_maze(width, height, dim):
    maze_list = []
    segsize = 3 * dim
    for x in range(0, int(width / segsize)):
        maze_list.append([])
        for y in range(0, int(height / segsize)):
            maze_list[x].append(0)
    maze_list[0][y] = [4, 1]  # Entrance
    direction = 1
    maze_count = 0
    maze_area = (x + 1) * (y + 1) - 1
    x = 0
    while maze_count != maze_area:
        if direction == 1:
            y -= 1
        elif direction == 7:
            y += 1
        elif direction == 3:
            x -= 1
        elif direction == 5:
            x += 1
        if maze_list[x][y] == 0:
            maze_count += 1
            maze_list, direction = segment(width, height, x, y, maze_list, segsize, direction)
            # print("Created", 8 - direction, 4, maze_list[x][y][-1])
        else:  # Is already an entry
            if randint(1, 4) == 2:
                if not 8 - direction in maze_list[x][y]:
                    # print("Added", 8 - direction)
                    maze_list[x][y].append(8 - direction)
            found = False
            for x in range(0, int(width / segsize)):
                for y in range(0, int(height / segsize)):
                    if maze_list[x][y] == 0:
                        if x != 0:
                            if type(maze_list[x - 1][y]) is list:
                                direction = 5
                                maze_list[x - 1][y].append(direction)
                                found = True
                                break
                        if x != int((width - segsize) / segsize):
                            if type(maze_list[x + 1][y]) is list:
                                direction = 3
                                maze_list[x + 1][y].append(direction)
                                found = True
                                break
                        if y != 0:
                            if type(maze_list[x][y - 1]) is list:
                                direction = 7
                                maze_list[x][y - 1].append(direction)
                                found = True
                                break
                        if y != int((height - segsize) / segsize):
                            if type(maze_list[x][y + 1]) is list:
                                direction = 1
                                maze_list[x][y + 1].append(direction)
                                found = True
                                break
                if found:
                    maze_list, direction = segment(width, height, x, y, maze_list, segsize, direction)
                    maze_count += 1
                    break

    for x in range(0, int(width / segsize)):
        for y in range(0, int(height / segsize)):
            r_list = []
            for d in range(len(maze_list[x][y])):
                if d != 4:
                    mn = convert_maze(maze_list[x][y][d])
                    if not 8 - maze_list[x][y][d] in maze_list[x + mn[0]][y + mn[1]]:
                        r_list.append(maze_list[x][y][d])
            for d in r_list:
                for mn in range(len(maze_list[x][y])):
                    if maze_list[x][y][mn] == d:
                        maze_list[x][y].pop(mn)
                        break
            create_segment((x * segsize, y * segsize), maze_list[x][y], dim)
    return maze_list


def convert_maze(maze_num):
    if maze_num == 1:
        return [0, -1]
    if maze_num == 3:
        return [-1, 0]
    if maze_num == 5:
        return [1, 0]
    if maze_num == 7:
        return [0, 1]
    return [0, 0]


def convert_direction(direction):
    if direction == [0, -1]:
        return 1
    if direction == [-1, 0]:
        return 3
    if direction == [1, 0]:
        return 5
    if direction == [0, 1]:
        return 7


def maze_cord(point):
    return [int(point[0] / (maze_tile * 3)), int(point[1] / (maze_tile * 3))]


def explore2(current_point: tuple, end_point: tuple):
    direction = [0, 0]
    junctions = []
    route = []
    shortest = [99999, []]
    while True:
        cancel = False
        if len(route) > shortest[0] or current_point in route:
            cancel = True
        if current_point == end_point:
            if shortest[0] > len(route):
                shortest = [len(route), route]
            cancel = True
        route.append(current_point)
        if not cancel:
            if len(maze[current_point[0]][current_point[1]]) > 3 or (
                    direction == [0, 0] and len(maze[current_point[0]][current_point[1]]) == 3):  # Junction
                j_list = []
                for d in maze[current_point[0]][current_point[1]]:
                    if d != 4 and direction != convert_maze(8 - d):
                        j_list.append(convert_maze(d))
                direction = j_list[0]
                junctions.append([current_point, j_list[1:], direction])
            else:  # Not a junction
                dead_end = True
                for d in maze[current_point[0]][current_point[1]]:
                    if d != 4 and direction != convert_maze(8 - d):
                        direction = convert_maze(d)
                        dead_end = False
                        break
                if dead_end:
                    cancel = True
        if cancel:  # Move back
            done = True
            for j in range(len(junctions) - 1, -1, -1):
                if len(junctions[j][1]) > 0:
                    done = False
                    break
            if done:
                return shortest
            else:
                direction = junctions[j][1][0]
                current_point = [junctions[j][0][0] + direction[0], junctions[j][0][1] + direction[1]]
                junctions[j][1].pop(0)
                junctions = junctions[:(j + 1)]
                for r in range(len(route) - 1, -1, -1):
                    if junctions[j][0] == route[r]:
                        break
                route = route[:(r + 1)]
                continue
        else:  # Move on
            current_point = [current_point[0] + direction[0], current_point[1] + direction[1]]


# noinspection PyUnresolvedReferences
def exit_gen():
    p_start = maze_cord([2 * maze_tile - (maze_tile / 2) / 2, HEIGHT - maze_tile - (maze_tile / 2) / 2])
    furthest = [0, None]
    for column_num in range(len(maze)):
        for section_num in range(len(maze[column_num])):
            if len(maze[column_num][section_num]) == 2:
                dist_to_end = explore2(p_start, [column_num, section_num])
                if furthest[0] < dist_to_end[0]:
                    furthest = [dist_to_end[0], dist_to_end[1][-1]]
    print(furthest)
    exit_t = Floor((furthest[1][0] * (maze_tile * 3) + maze_tile, furthest[1][1] * (maze_tile * 3) + maze_tile),
                   maze_tile, (255, 255, 0), intense=10)
    lights.add(exit_t)
    b = Bot((furthest[1][0] * (maze_tile * 3) + maze_tile, furthest[1][1] * (maze_tile * 3) + maze_tile))
    return exit_t, b


all_sprites = pygame.sprite.Group()
obstacles = pygame.sprite.Group()
lights = pygame.sprite.Group()

maze = generate_maze(WIDTH, HEIGHT, maze_tile)

exit_tile, bot = exit_gen()

player = Player((2 * maze_tile - (maze_tile / 2) / 2, HEIGHT - maze_tile - (maze_tile / 2) / 2), maze_tile / 4)

fog_of_war = pygame.Surface((WIDTH, HEIGHT))

running = True
while running:  # Run until the user asks to quit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Did the user click the window close button?
            running = False
    screen.blit(background, (0, 0))

    for s in all_sprites:
        screen.blit(s.surf, s.rect)

    player.update()
    bot.update()
    screen.blit(player.surf, player.rect)

    fog_of_war.fill((0, 0, 0))
    for light_source in lights:
        pygame.draw.circle(fog_of_war, (60, 60, 60), light_source.centre_cord(), light_source.Intense, 0)
    fog_of_war.set_colorkey((60, 60, 60))
    screen.blit(fog_of_war, (0, 0))

    clock.tick(FrameRate)
    pygame.display.flip()  # Flip the display

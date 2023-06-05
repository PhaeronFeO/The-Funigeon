import pygame
import pygame.freetype
import pygame.mixer
from pygame.locals import *
from random import choice, randint
from time import time


class MazePlayer(pygame.sprite.Sprite):
    def __init__(self, cords: tuple, dim, player_speed):
        super(MazePlayer, self).__init__()
        self.Speed = player_speed
        self.surf = pygame.Surface((dim, dim))
        self.surf.fill((255, 0, 0))
        self.rect = self.surf.get_rect()
        self.rect.bottomright = cords
        self.Intense = 100

    def update(self, bot, exit_tile, obstacles):
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
            return 1
        if self.rect.colliderect(exit_tile.rect):
            print("VICTORY")
            return 2
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
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
        return 0


class NextBot(pygame.sprite.Sprite):
    def __init__(self, cords: tuple):
        super(NextBot, self).__init__()
        # self.surf = pygame.Surface((maze_tile, maze_tile))
        self.surf = pygame.image.load("Art/Greben_Bot.JPG").convert()
        self.rect = self.surf.get_rect()
        self.rect.topleft = cords
        self.Delay = int(FrameRate / int((FrameRate * PSpeed) / (maze_tile * 0.9)))
        self.Count = -2 * FrameRate
        self.Route = []
        self.Speed = maze_tile / self.Delay
        # lights.add(self)
        pygame.mixer.init()
        pygame.mixer.music.load("Music/CompressedJohn.mp3")
        pygame.mixer.music.set_volume(0)
        pygame.mixer.music.play(-1)

    def update(self, maze, player):
        if len(self.Route) == 0:
            self.Count = FrameRate
        if self.Count == FrameRate:  # Update Route
            self.Count = 0
            route = explore3(maze, maze_cord(self.rect.center), maze_cord(player.rect.center))[1]
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
        else:  # This section is what causes the shakiness and stopping
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


class Floor(pygame.sprite.Sprite):
    def __init__(self, cords: tuple, dim, color, intense=0):
        super(Floor, self).__init__()
        self.surf = pygame.Surface((dim, dim))
        self.surf.fill(color)
        self.rect = self.surf.get_rect()
        self.rect.topleft = cords
        self.Intense = intense


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


def choose_direction(j_list, current_point, end_point):
    not_found = True
    diff = [current_point[0] - end_point[0], current_point[1] - end_point[1]]
    if abs(diff[1]) > abs(diff[0]):
        pref = 1
    else:
        pref = 0
    for d in range(len(j_list)):
        if j_list[d][pref] == 0:
            pass
        elif diff[pref] / j_list[d][pref] < 0:  # Is the direction leading closer
            not_found = False
            break
        if j_list[d][pref - 1] == 0:
            pass
        elif diff[pref - 1] / j_list[d][pref - 1] < 0:  # Is the direction leading closer
            not_found = False
            break
    if not_found:
        direction = j_list.pop(0)
    else:
        direction = j_list.pop(d)
    return direction, [current_point, j_list, direction]


def explore3(maze: list, current_point: tuple, end_point: tuple):
    direction = [0, 0]
    junctions = []
    route = []
    shortest = [99999, []]
    c = 0
    while True:
        cancel = False
        if len(route) > shortest[0] or current_point in route:
            cancel = True
        if current_point == end_point:
            if shortest[0] > len(route):
                c += 1
                if c == 3:
                    route.append(current_point)
                    return [len(route), route]
                else:
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
                direction, j = choose_direction(j_list, current_point, end_point)
                junctions.append(j)
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
                direction, junct = choose_direction(junctions[j][1], [junctions[j][0][0], junctions[j][0][1]], end_point)
                junctions[j][1] = junct[1]
                current_point = [junctions[j][0][0] + direction[0], junctions[j][0][1] + direction[1]]
                junctions = junctions[:(j + 1)]
                for r in range(len(route) - 1, -1, -1):
                    if junctions[j][0] == route[r]:
                        break
                route = route[:(r + 1)]
                continue
        else:  # Move on
            current_point = [current_point[0] + direction[0], current_point[1] + direction[1]]


class MazeGame:
    def __init__(self, W, H):
        self.all_sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.lights = pygame.sprite.Group()

        # Generate the maze
        maze_list = []
        segsize = 3 * maze_tile
        for x in range(0, int(W / segsize)):
            maze_list.append([])
            for y in range(0, int(H / segsize)):
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
                maze_list, direction = segment(W, H, x, y, maze_list, segsize, direction)
                # print("Created", 8 - direction, 4, maze_list[x][y][-1])
            else:  # Is already an entry
                if randint(1, 4) == 2:
                    if not 8 - direction in maze_list[x][y]:
                        # print("Added", 8 - direction)
                        maze_list[x][y].append(8 - direction)
                found = False
                for x in range(0, int(W / segsize)):
                    for y in range(0, int(H / segsize)):
                        if maze_list[x][y] == 0:
                            if x != 0:
                                if type(maze_list[x - 1][y]) is list:
                                    direction = 5
                                    maze_list[x - 1][y].append(direction)
                                    found = True
                                    break
                            if x != int((W - segsize) / segsize):
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
                            if y != int((H - segsize) / segsize):
                                if type(maze_list[x][y + 1]) is list:
                                    direction = 1
                                    maze_list[x][y + 1].append(direction)
                                    found = True
                                    break
                    if found:
                        maze_list, direction = segment(W, H, x, y, maze_list, segsize, direction)
                        maze_count += 1
                        break

        for x in range(0, int(W / segsize)):
            for y in range(0, int(H / segsize)):
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
                start_cord = (x * segsize, y * segsize)
                for sp in range(9):
                    if sp in maze_list[x][y]:
                        newsp = Floor((start_cord[0] + maze_tile * (sp % 3), start_cord[1] + maze_tile * int(sp / 3)), maze_tile, (128, 128, 128))
                        self.all_sprites.add(newsp)
                    else:
                        newsp = Wall((start_cord[0] + maze_tile * (sp % 3), start_cord[1] + maze_tile * int(sp / 3)), maze_tile)
                        self.all_sprites.add(newsp)
                        self.obstacles.add(newsp)
        self.maze = maze_list

        # Generate Exit and Bot
        p_start = maze_cord([2 * maze_tile - (maze_tile / 2) / 2, HEIGHT - maze_tile - (maze_tile / 2) / 2])
        furthest = [0, None]
        for column_num in range(len(self.maze)):
            for section_num in range(len(self.maze[column_num])):
                if len(self.maze[column_num][section_num]) == 2:
                    dist_to_end = explore3(self.maze, p_start, [column_num, section_num])
                    if furthest[0] < dist_to_end[0]:
                        furthest = [dist_to_end[0], [column_num, section_num]]
        print("Furthest:", furthest)
        self.exit_t = Floor((furthest[1][0] * (maze_tile * 3) + maze_tile, furthest[1][1] * (maze_tile * 3) + maze_tile),
                            maze_tile, (255, 255, 0), intense=10)
        self.all_sprites.add(self.exit_t)
        self.lights.add(self.exit_t)
        self.bot = NextBot((furthest[1][0] * (maze_tile * 3) + maze_tile, furthest[1][1] * (maze_tile * 3) + maze_tile))
        self.all_sprites.add(self.bot)

        self.player = MazePlayer((2 * maze_tile - (maze_tile / 2) / 2, H - maze_tile - (maze_tile / 2) / 2), maze_tile / 4, PSpeed)
        self.lights.add(self.player)
        self.fog_of_war = pygame.Surface((W, H))

        self.score = 0
        self.movement = False

    def game_loop(self):
        game = True
        dead = False
        start_time = time()
        while game:  # Run until the user asks to quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Did the user click the window close button?
                    pygame.mixer.quit()
                    return False
                if dead or (not self.movement):
                    if event.type == KEYDOWN:
                        if pygame.key.get_pressed()[K_RETURN]:
                            game = False

            if not self.movement:
                if time() - start_time > 3:
                    self.movement = True

            screen.blit(background, (0, 0))

            for s in self.all_sprites:
                screen.blit(s.surf, s.rect)
            if (not dead) and self.movement:
                result = self.player.update(self.bot, self.exit_t, self.obstacles)
                if result == 1:
                    dead = True
                    self.score = 0
                    text, text_rect = largeFont.render("YOU DIED", (128, 0, 0))
                    text_rect.center = (WIDTH / 2, HEIGHT / 2)
                    bottom_text, bottom_rect = smallFont.render('THE SCATMAN CLAIMS ANOTHER SOUL', (128, 0, 0))
                    bottom_rect.center = (WIDTH / 2, HEIGHT / 2 + 70)
                    continue
                elif result == 2:
                    dead = True
                    self.score += 25
                    text, text_rect = largeFont.render("YOU ESCAPED", (128, 0, 0))
                    text_rect.center = (WIDTH / 2, HEIGHT / 2)
                    bottom_text, bottom_rect = smallFont.render('SCORE IS NOW: ' + str(self.score), (128, 0, 0))
                    bottom_rect.center = (WIDTH / 2, HEIGHT / 2 + 70)
                    continue
                self.fog_of_war.fill((0, 0, 0))

            screen.blit(self.player.surf, self.player.rect)

            if dead:
                screen.blit(text, text_rect)
                screen.blit(bottom_text, bottom_rect)
            elif self.movement:
                self.bot.update(self.maze, self.player)
                for light_source in self.lights:
                    pygame.draw.circle(self.fog_of_war, (60, 60, 60), light_source.rect.center, light_source.Intense, 0)
                self.fog_of_war.set_colorkey((60, 60, 60))
                screen.blit(self.fog_of_war, (0, 0))

            clock.tick(FrameRate)
            pygame.display.flip()  # Flip the display
        return True


class JumpPlayer(pygame.sprite.Sprite):
    def __init__(self, cords, dim, player_speed, jump, g, obstacles):
        super(JumpPlayer, self).__init__()
        self.Friction = 0.5 / player_speed
        self.Speed = player_speed / 10
        self.Jump = jump
        self.G = g
        self.Velocity = [0, 0]
        self.surf = pygame.Surface((dim, dim))
        self.dim = dim
        self.surf.fill((255, 0, 0))
        self.rect = self.surf.get_rect()
        self.rect.bottomright = cords
        self.cords = cords
        self.obstacle_group = obstacles
        self.Air = False
        self.Airs = 0
        self.AirDelay = int(FrameRate / 3)

    def collisions(self, start_point, end_point, collision_list):
        start_point = [start_point[0], start_point[1]]
        end_point = [end_point[0], end_point[1]]
        offset = [0, 0]
        if end_point[1] - start_point[1] < 0:
            offset[1] -= self.dim
            start_point[1] += offset[1]
            end_point[1] += offset[1]
        if end_point[0] - start_point[0] < 0:
            offset[0] -= self.dim
            start_point[0] += offset[0]
            end_point[0] += offset[0]
        m = end_point[1] - start_point[1] / end_point[0] - start_point[0]
        c = start_point[1] - m * start_point[0]
        for collided in collision_list:
            collision_pnt = [collided.rect.left, collided.rect.top]
            if end_point[1] - start_point[1] < 0:
                collision_pnt[1] = collided.rect.bottom
            if end_point[0] - start_point[0] < 0:
                collision_pnt[0] = collided.rect.right
            if min(start_point[0], end_point[0]) <= round((collision_pnt[1] - c) / m) <= max(start_point[0], end_point[0]):
                cp = ((collision_pnt[1] - c) / m, collision_pnt[1])
                if abs(end_point[0] - start_point[0]) + abs(end_point[1] - start_point[1]) \
                        >= abs(cp[0] - start_point[0]) + abs(cp[1] - start_point[1]):
                    end_point = cp
                    self.Velocity[1] = collided.velocity[1]
                    self.Air = True
                    self.Airs = 0
            if min(start_point[1], end_point[1]) <= round((collision_pnt[0] * m) + c) <= max(start_point[1], end_point[1]):
                cp = (collision_pnt[0], (collision_pnt[0] * m) + c)
                if abs(end_point[0] - start_point[0]) >= abs(cp[0] - start_point[0]) and abs(
                        end_point[1] - start_point[1]) >= abs(cp[1] - start_point[1]):
                    end_point = cp
                    self.Velocity[0] = collided.velocity[0]
        self.set_cords([end_point[0] - offset[0], end_point[1] - offset[1]])

    def set_cords(self, new_cords):
        self.cords = [new_cords[0], new_cords[1]]
        self.rect.right = self.cords[0]
        self.rect.bottom = self.cords[1]

    def stood_on(self, obstacles):
        self.rect.move_ip(0, 1)
        collision_list = pygame.sprite.spritecollide(self, obstacles, False)
        self.rect.move_ip(0, -1)
        for coll_obj in collision_list:
            if coll_obj.Crumble:
                coll_obj.crumble_check(obstacles)

    def update(self, downforce, damage_group, obstacles):
        pressed_keys = pygame.key.get_pressed()
        self.rect.move_ip(0, 1)
        collision_list = pygame.sprite.spritecollide(self, obstacles, False)
        self.rect.move_ip(0, -1)
        for coll_obj in collision_list:
            if coll_obj.Crumble:
                coll_obj.crumble_check(obstacles)
        if len(collision_list) > 0 and self.Velocity[1] == 0:  # Is touching ground
            if pressed_keys[K_LEFT]:
                self.Velocity[0] += -1 * self.Speed
            if pressed_keys[K_RIGHT]:
                self.Velocity[0] += self.Speed
            self.Velocity[0] += self.Friction * -1 * self.Velocity[0]
            if pressed_keys[K_SPACE] and self.Air:
                self.Air = False
                self.Velocity[1] = -1 * self.Jump
                self.Airs = 2
                self.AirDelay = int(FrameRate / 3)
        else:
            if pressed_keys[K_SPACE] and self.Airs > 0 >= self.AirDelay:
                self.Airs -= 1
                self.Velocity[1] = -1 * int(self.Jump / 2)
                self.AirDelay = int(FrameRate / 3)
            else:
                self.Velocity[1] += self.G + downforce
                if self.AirDelay > 0 and self.Airs > 0:
                    self.AirDelay -= 1
        px, py = self.Velocity[0], self.Velocity[1]
        start_cord = self.rect.bottomright
        self.cords = [self.cords[0] + px, self.cords[1] + py]
        self.set_cords(self.cords)
        collision_list = pygame.sprite.spritecollide(self, damage_group, False)
        if len(collision_list) > 0:
            print("FAILIURE")
            return 1
        # if self.rect.colliderect(exit_tile.rect):
            # print("VICTORY")
            # return 2
        collision_list = pygame.sprite.spritecollide(self, obstacles, False)
        if collision_list:
            self.collisions(start_cord, self.rect.bottomright, collision_list)
        if self.rect.left < 0:
            self.rect.left = 0
            self.Velocity[0] = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.Velocity[0] = 0
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.Velocity[1] = 0
        return 0


class JumpWall(pygame.sprite.Sprite):
    def __init__(self, cords, dims, col):
        super(JumpWall, self).__init__()
        self.surf = pygame.Surface((dims[0], dims[1]))
        self.surf.fill(col)
        self.rect = self.surf.get_rect()
        self.rect.bottomright = cords
        self.velocity = [0, 0]
        self.Crumble = False

    def update(self, obstacles):
        pass


class CrumbleWall(JumpWall):
    def __init__(self, cords, dims, col):
        super(CrumbleWall, self).__init__(cords, dims, col)
        self.surf.fill((128, 0, 0))
        self.Crumble = True
        self.CrumbleTime = FrameRate * 4

    def crumble_check(self, obstacles):
        if self.CrumbleTime <= 0:
            print("DIES OF DEATH")
            pass  # Remove from obstacles
        else:
            self.CrumbleTime -= 4

    def update(self, obstacles):
        if self.CrumbleTime <= 0:
            obstacles.remove(self)
            self.surf.fill((48, 0, 0))
        if self.CrumbleTime < FrameRate * 4:
            self.CrumbleTime += 1
        elif self.CrumbleTime >= FrameRate * 4:
            obstacles.add(self)
            self.surf.fill((128, 0, 0))
            self.CrumbleTime = FrameRate * 4


class JumpGame:
    def __init__(self, W, H, jump_height):
        self.all_sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.liquids = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.create_wall([W, H], [W, 50])
        self.create_wall([W/2, H - (jump_height - 5) - 15], [100, 15], crumble=True)
        self.create_wall([W / 4, H - (jump_height - 5) - 15], [100, 15])
        self.create_wall([3 * W / 4, H - 2 * (jump_height - 5) - 15], [100, 15])
        jump_speed = 4 * jump_height / FrameRate
        self.Gravity = 2 * jump_speed / FrameRate
        self.Jump = jump_height - 5
        self.player = JumpPlayer([int(W / 2), H - 200], 20, 5, jump_speed, self.Gravity, self.obstacles)

    def create_wall(self, cords, dims, crumble=False):
        if crumble:
            wall = CrumbleWall(cords, dims, (128, 128, 128))
        else:
            wall = JumpWall(cords, dims, (128, 128, 128))
        self.all_sprites.add(wall)
        self.obstacles.add(wall)
        self.walls.add(wall)

    def game_loop(self):
        game = True
        dead = False
        while game:  # Run until the user asks to quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Did the user click the window close button?
                    return False

            screen.blit(background, (0, 0))
            for s in self.all_sprites:
                screen.blit(s.surf, s.rect)

            for obstacle in self.walls:
                obstacle.update(self.obstacles)

            self.player.update(0, self.liquids, self.obstacles)
            screen.blit(self.player.surf, self.player.rect)

            clock.tick(FrameRate)
            pygame.display.flip()  # Flip the display


class Emu:
    def __init__(self, text_list: tuple, grayed=(150, 150, 150), highlight=(250, 250, 250)):
        self.Grayed = grayed
        self.Highlight = highlight
        self.all_sprites = pygame.sprite.Group()
        text, rect = largeFont.render(text_list[0], (255, 255, 255))
        rect.topleft = (20, 20)
        self.texts = [[text, rect, (255, 255, 255), text_list[0]]]
        for t in range(1, len(text_list)):
            text_list[t] = "   " + text_list[t]
            text, rect = smallFont.render(text_list[t], self.Grayed)
            if t == len(text_list) - 1:
                rect.topleft = (20, HEIGHT - 50)
            else:
                rect.topleft = (20, 60 + (30 * t))
            self.texts.append([text, rect, self.Grayed, text_list[t]])

    def change_text(self, text):
        if text[2] == self.Grayed:
            text[0], rect = smallFont.render(text[3], self.Highlight)
            text[2] = self.Highlight
        else:
            text[0], rect = smallFont.render(text[3], self.Grayed)
            text[2] = self.Grayed
        return text

    def game_loop(self):
        game = True
        while game:  # Run until the user asks to quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Did the user click the window close button?
                    return False

            screen.blit(background, (0, 0))
            mouse_pos = pygame.mouse.get_pos()
            r_click = pygame.mouse.get_pressed(num_buttons=3)[0]
            for t in range(len(self.texts)):
                if self.texts[t][1].collidepoint(mouse_pos):
                    if r_click and t != 0:
                        return t
                    else:
                        if self.texts[t][2] == self.Grayed:
                            self.change_text(self.texts[t])
                else:
                    if self.texts[t][2] == self.Highlight:
                        self.change_text(self.texts[t])
                screen.blit(self.texts[t][0], self.texts[t][1])

            for s in self.all_sprites:
                screen.blit(s.surf, s.rect)

            clock.tick(FrameRate)
            pygame.display.flip()  # Flip the display


WIDTH = 1200
HEIGHT = 600
FrameRate = 60
clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode([WIDTH, HEIGHT])
largeFont = pygame.freetype.SysFont('Ariel', 64)
smallFont = pygame.freetype.SysFont('Ariel', 24)
background = pygame.Surface(screen.get_size())
background.fill((0, 0, 0))
maze_tile = 25
PSpeed = 4

if __name__ == "__main__":
    while True:
        gaming = True
        main_game = Emu(["THE FUNIGEON",
                         "1. THE SCATMAN'S A_MAZE_ING WORLD",
                         "2. JUMP COOMER JUMP",
                         "3. BLUNDRTALE: RETURN OF THE RIZZ",
                         "Credits"])
        next_game = main_game.game_loop()
        if next_game is False:
            break
        if next_game == 1:
            while gaming:
                main_game = MazeGame(WIDTH, HEIGHT)
                gaming = main_game.game_loop()
        elif next_game == 2:
            while gaming:
                main_game = JumpGame(WIDTH, HEIGHT, 150)
                gaming = main_game.game_loop()

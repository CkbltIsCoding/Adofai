import pygame
import time
from math import pi, sin as _sin, cos as _cos, floor
from pygame.math import Vector2 as Vec2
from pygame.locals import *

from data import data as _data


def deg2rad(deg):
    return deg * pi / 180


# def rad2deg(rad):
#     return rad * 180 / pi


def sin(deg):
    deg %= 360
    if deg == 0 or deg == 180:
        return 0.0
    if deg == 90:
        return 1.0
    if deg == 270:
        return -1.0
    return _sin(deg2rad(deg))


def cos(deg):
    deg %= 360
    if deg == 90 or deg == 270:
        return 0.0
    if deg == 0:
        return 1.0
    if deg == 180:
        return -1.0
    return _cos(deg2rad(deg))


def move_step(direction):  # 向 direction° 方向移动一个单位
    return Vec2(sin(direction), cos(direction))


CLOCKWISE = True
COUNTERCLOCKWISE = False

STATE_PLAYING = 1


class App:
    def __init__(self):
        pygame.init()

        self.size = self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("A dance of fire and ice")
        self.running = True
        self.fullscreen = False

        self.state = STATE_PLAYING
        self.pre_state = 0

        self.data = _data
        self.delay = _data["delay"]
        self.title = _data['title']
        self.tiles = []
        self.process_data()

        self.keys = [K_a, K_s, K_d, K_f, K_SPACE, K_j, K_k, K_l, K_SEMICOLON]

        self.timer_begin = self.timer = 0
        self.beat = 0
        self.player_beat = 0
        self.pre_beat = 0

        # 摄像机
        self.camera_pos = Vec2()
        self.camera_sight = 20.0
        self.camera_angle = 90

        # 行星
        self.planet1_pos = Vec2()
        self.planet2_pos = Vec2()
        self.planet_size = 0.5
        self.planet_angle = 90.0
        self.planet_static = 1

        # （玩家）现在/前一帧砖块
        self.player_now_tile = 0
        self.player_pre_tile = 0
        self.now_tile = 0
        self.pre_tile = 0

        # 玩家打的延迟
        self.timing = 0
        self.timing_delay = -30
        self.timing_list = []
        self.timing_sprites = []

        self.autoplay = False
        self.waiting_for_key = True

        # 打的完美 稍慢 稍快 太慢 太快 错过 空敲
        self.p = self.lp = self.ep = self.l = self.e = self.tl = self.te = 0
        # 判定 (单位：毫秒)
        self.P = 25
        self.LEP = 45
        self.LE = 60

        self.clock = pygame.time.Clock()
        self.FPS = 120
        self.delta = 1

        self.keydown_event_count = 0

        self.font_debug = pygame.font.SysFont("Consolas", 24)
        self.font_title = pygame.font.SysFont("Papyrus", 36)
        self.font_acc = pygame.font.SysFont("Consolas", 12)

        text_title_shadow = self.font_title.render(self.title, True, "#00000099")
        self.text_title = pygame.Surface(Vec2(text_title_shadow.get_size()) + Vec2(1, 1), SRCALPHA)
        self.text_title.blit(text_title_shadow, (1, 1))
        text_title = self.font_title.render(self.title, True, "#ffffff")
        self.text_title.blit(text_title, (0, 0))

        pygame.mixer.init()

        self.sound_ready = pygame.mixer.Sound("ready.wav")
        self.channel_ready = pygame.mixer.Channel(0)

        self.sound_beat = pygame.mixer.Sound("beat.wav")
        self.channel_beat = pygame.mixer.Channel(1)

        self.music_path = "Ludicin - Fallen Symphony.mp3"

        if self.music_path != "":
            pygame.mixer_music.load(self.music_path)

    def process_data(self):  # 处理谱面
        self.tiles = [{} for _ in range(len(self.data["content"]))]
        tile_pos = Vec2()
        tile_dir = 90
        tile_rot = CLOCKWISE
        tile_ms = 0
        for index in range(len(self.data["content"])):
            tile = self.data["content"][index]
            self.tiles[index]["ang"] = tile["ang"]
            if tile["bpm"] != -1:
                self.tiles[index]["bpm"] = tile["bpm"]
            else:
                self.tiles[index]["bpm"] = self.tiles[index - 1]["bpm"]
            if tile["rot"]:
                tile_rot = not tile_rot
            self.tiles[index]["rot"] = tile_rot
            self.tiles[index]["pos"] = tile_pos.copy()
            self.tiles[index]["dir"] = tile_dir

            if tile_rot:
                tile_dir += tile["ang"] - 180
            else:
                tile_dir -= tile["ang"] - 180
            tile_dir %= 360
            tile_pos += move_step(tile_dir)
            tile_pos += Vec2(tile["x"], tile["y"])

            tile_ms += self.tiles[index]["ang"] / 180 / (self.tiles[index]["bpm"] / 60) * 1000
            self.tiles[index]["ms"] = tile_ms

            self.tiles[index]["color"] = tile["color"]

            self.tiles[index]["super_pos"] = []
            for j in range(index):
                if (
                        -0.001 <= self.tiles[index]["pos"].x - self.tiles[j]["pos"].x <= 0.001 and
                        -0.001 <= self.tiles[index]["pos"].y - self.tiles[j]["pos"].y <= 0.001 and
                        self.tiles[index]["dir"] == self.tiles[j]["dir"] and
                        self.tiles[index]["ang"] == self.tiles[j]["ang"] and
                        self.tiles[index]["rot"] == self.tiles[j]["rot"]):
                    self.tiles[index]["super_pos"].append(j)

    def execute(self):
        while self.running:
            self.keydown_event_count = 0
            for event in pygame.event.get():
                self.event(event)
            self.loop()
            self.render()
            self.clock.tick(self.FPS)
        self.cleanup()

    def event(self, event):
        if event.type == QUIT:  # 退出程序
            self.running = False

        if event.type == KEYDOWN:
            if event.dict["key"] == K_ESCAPE:  # 退出程序
                self.running = False
            if event.dict["key"] == K_F11:  # 全屏开关
                self.fullscreen = not self.fullscreen
                if self.fullscreen:
                    self.size = self.width, self.height = pygame.display.list_modes()[0]
                    self.screen = pygame.display.set_mode(self.size, FULLSCREEN | HWSURFACE)
                else:
                    self.size = self.width, self.height = 800, 600
                    self.screen = pygame.display.set_mode(self.size)
            if self.waiting_for_key and event.dict["key"] == K_BACKSLASH:  # Autoplay 开关
                self.autoplay = not self.autoplay
            if event.dict["key"] in self.keys:  # 打的键
                self.keydown_event_count += 1

    def loop(self):
        global STATE_PLAYING

        self.delta = self.clock.get_time() * self.FPS / 1000

        if self.state == STATE_PLAYING:
            if not self.waiting_for_key:
                self.timer = round(time.time() * 1000 - self.timer_begin - max(3 / self.tiles[0]["bpm"] * 60 * 1000,
                                                                               self.delay))
            if self.autoplay:
                self.timing = self.timer - self.tiles[self.now_tile]["ms"]  # + self.timing_delay
            else:
                self.timing = self.timer - self.tiles[self.player_now_tile]["ms"] + self.timing_delay

            self.calc_beat()
            if floor(self.pre_beat) != floor(self.beat) and -3 <= floor(self.beat) <= 0:  # 准备的声音
                self.channel_ready.play(self.sound_ready)
            if self.pre_tile != self.now_tile:
                if self.autoplay:
                    self.timing_list.append([self.timing, 0])
                self.channel_beat.play(self.sound_beat)  # 打的声音

            for i in range(self.keydown_event_count):
                self.keydown_event()
                if self.autoplay:
                    self.timing = self.timer - self.tiles[self.now_tile]["ms"] + self.timing_delay
                else:
                    self.timing = self.timer - self.tiles[self.player_now_tile]["ms"] + self.timing_delay
                self.calc_beat()

            if not self.autoplay and self.player_now_tile < len(self.tiles) - 1:  # 错过判定
                while self.timing > self.LE:
                    self.player_now_tile += 1
                    self.tl += 1
                    self.timing_list.append([self.LE + 5, 0])
                    if self.planet_static == 1:
                        self.timing_sprites.append(['TL!!', self.planet2_pos, 0])
                    else:
                        self.timing_sprites.append(['TL!!', self.planet1_pos, 0])

                    self.calc_beat()
                    self.timing = self.timer - self.tiles[self.player_now_tile]["ms"] + self.timing_delay

            self.calc_planets()
            self.camera()

            index = 0
            while index < len(self.timing_list):
                self.timing_list[index][1] += self.delta
                if self.timing_list[index][1] >= 5 * self.FPS:
                    del self.timing_list[index]
                    continue
                index += 1

            index = 0
            while index < len(self.timing_sprites):
                self.timing_sprites[index][2] += self.delta
                if self.timing_sprites[index][2] >= 5 * self.FPS:
                    del self.timing_sprites[index]
                    continue
                index += 1

            self.pre_beat = self.beat
            self.pre_tile = self.now_tile
            self.player_pre_tile = self.player_now_tile
            self.pre_state = self.state

    def keydown_event(self):
        if self.waiting_for_key:
            if self.music_path != "":
                pygame.mixer_music.play()
            self.timer_begin = time.time() * 1000
            self.waiting_for_key = False
        elif not self.autoplay and self.player_now_tile < len(self.tiles) - 1:
            self.keydown_event_count += 1
            self.timing_list.append([self.timing, 0])
            self.timing = self.timer - self.tiles[self.player_now_tile]["ms"] + self.timing_delay  #
            self.player_now_tile += 1
            if abs(self.timing) <= self.P:
                self.p += 1
            elif abs(self.timing) <= self.LEP:
                if self.timing > 0:
                    self.lp += 1
                    self.timing_sprites.append(['LP!', self.tiles[self.player_now_tile]['pos'], 0])
                else:
                    self.ep += 1
                    self.timing_sprites.append(['EP!', self.tiles[self.player_now_tile]['pos'], 0])
            elif abs(self.timing) <= self.LE:
                if self.timing > 0:
                    self.l += 1
                    self.timing_sprites.append(['Late!', self.tiles[self.player_now_tile]['pos'], 0])
                else:
                    self.e += 1
                    self.timing_sprites.append(['Early!', self.tiles[self.player_now_tile]['pos'], 0])
            elif self.timing < 0:
                self.player_now_tile -= 1
                self.timing_list.pop()
                if self.beat >= 0:
                    self.timing_list.append([-self.LE - 5, 0])
                    self.te += 1
                    if self.planet_static == 1:
                        self.timing_sprites.append(['TE!!', self.planet2_pos, 0])
                    else:
                        self.timing_sprites.append(['TE!!', self.planet1_pos, 0])

    def calc_beat(self):
        bpm = self.tiles[0]["bpm"]
        if self.timer / (60 / bpm) < 1000:
            self.beat = self.timer / (60 / bpm) / 1000
            self.now_tile = 0
        else:
            self.beat = 0
            ms = 0
            flag = True
            for index in range(len(self.tiles)):
                tile = self.tiles[index]
                if ms > self.timer:
                    flag = False
                    self.now_tile = max(0, index - 1)
                    break
                bpm = tile["bpm"]
                ms += tile["ang"] / 180 / (bpm / 60) * 1000
                self.beat += tile["ang"] / 180
            if flag:
                self.now_tile = len(self.tiles) - 1
            self.beat += (self.timer - ms) / (60 / bpm) / 1000

    def calc_planets(self):
        self.planet_angle = 90
        self.player_beat = 0
        for index in range(self.now_tile if self.autoplay else self.player_now_tile):
            tile = self.tiles[index]
            self.player_beat += tile["ang"] / 180
            if tile["rot"] == CLOCKWISE:
                self.planet_angle += tile["ang"] - 180
            else:
                self.planet_angle -= tile["ang"] - 180
        if self.tiles[self.now_tile if self.autoplay else self.player_now_tile]["rot"] == CLOCKWISE:
            self.planet_angle += (self.beat - self.player_beat) * 180
        else:
            self.planet_angle -= (self.beat - self.player_beat) * 180
        self.planet_angle += 180
        self.planet1_pos = self.tiles[self.now_tile if self.autoplay else self.player_now_tile]["pos"]
        self.planet2_pos = self.planet1_pos + move_step(self.planet_angle)
        self.planet_static = 1
        if (self.now_tile if self.autoplay else self.player_now_tile) % 2 == 1:
            self.planet_static = 2
            self.planet1_pos, self.planet2_pos = self.planet2_pos, self.planet1_pos

    def camera(self):
        self.camera_sight += (self.now_tile - self.pre_tile) * 0.5

        # 视野
        camera_sight = 50
        if self.beat < 1:
            camera_sight = 20
        if 113 <= self.beat < 121:
            camera_sight = 100
        self.camera_sight += (camera_sight - self.camera_sight) / 100 * self.delta
        if floor(self.beat) == 65 and floor(self.pre_beat) != 65:
            self.camera_sight += 50

        # 角度
        camera_angle = 90
        if self.beat >= 1:
            camera_angle = 80

        if self.beat >= 121:
            camera_angle = 90
        self.camera_angle += (camera_angle - self.camera_angle) / 100 * self.delta
        if floor(self.beat) == 65 and floor(self.pre_beat) != 65:
            self.camera_angle += 100

        # 位置
        for i in range(round(20 * self.delta)):
            self.camera_pos += (self.tiles[self.now_tile if self.autoplay else self.player_now_tile]["pos"]
                                - self.camera_pos) / 1000 * self.delta

    def render(self):
        self.screen.fill("#333333")

        self.render_tiles()

        # 绘制行星
        pygame.draw.circle(self.screen, "#ff3333", self.convert_pos(self.planet1_pos), self.planet_size * self.camera_sight / 2)
        if not self.waiting_for_key:
            pygame.draw.circle(self.screen, "#3366ff", self.convert_pos(self.planet2_pos), self.planet_size * self.camera_sight / 2)

        # 绘制准度
        for sprite in self.timing_sprites:
            color = "#ff0000"
            if sprite[0] == 'Late!' or sprite[0] == 'Early!':
                color = '#ffcc00'
            if sprite[0] == 'LP!' or sprite[0] == 'EP!':
                color = '#ffff00'
            text = self.font_acc.render(sprite[0], True, color)
            text.set_alpha(self.FPS * 5 - sprite[2])
            text = pygame.transform.scale_by(text, min(1, sprite[2] / 10))
            self.screen.blit(text, text.get_rect(center=self.convert_pos(sprite[1])))

        # 绘制准度条
        pygame.draw.rect(self.screen, "#ff0000", (self.width // 2 - self.LE*2 - 20, self.height - 40, self.LE*4 + 40, 30))
        pygame.draw.rect(self.screen, "#ffcc00", (self.width // 2 - self.LE*2, self.height - 40, self.LE*4, 30))
        pygame.draw.rect(self.screen, "#ffff00", (self.width // 2 - self.LEP*2, self.height - 40, self.LEP*4, 30))
        pygame.draw.rect(self.screen, "#00ff00", (self.width // 2 - self.P*2, self.height - 40, self.P*4, 30))
        line = pygame.surface.Surface((3, 20))
        line.fill("#000000")
        for timing in self.timing_list:
            line.set_alpha(max(0, min(255, 127 - timing[1] / 2)))
            self.screen.blit(line, line.get_rect(centerx=self.width // 2 + timing[0]*2, y=self.height - 40))
        text_cnt = self.font_debug.render(f"{self.te} {self.e} {self.ep} "
                                          f"{self.p} {self.lp} {self.l} {self.tl}", True, "#ffffff")
        self.screen.blit(text_cnt, text_cnt.get_rect(centerx=self.width // 2, bottom=self.height - 40))

        # 绘制一些文字
        self.screen.blit(self.text_title, self.text_title.get_rect(centerx=self.width // 2, y=50))

        text_debug = self.font_debug.render("FPS: " + str(round(self.clock.get_fps(), 2)), False, "#ffffff")
        self.screen.blit(text_debug, (0, 0))

        if self.autoplay:
            text_autoplay = self.font_debug.render("Autoplay", False, "#ffffff")
            self.screen.blit(text_autoplay, (0, 30))

        pygame.display.flip()

    def render_tiles(self):
        square = pygame.Surface(((self.planet_size * self.camera_sight,
                                  self.planet_size * self.camera_sight)), SRCALPHA)
        rect = pygame.Surface(((self.planet_size * self.camera_sight * 2,
                                self.planet_size * self.camera_sight)), SRCALPHA)
        square_border = pygame.Surface(((self.planet_size * self.camera_sight + (10 * self.camera_sight / 100),
                                         self.planet_size * self.camera_sight + (10 * self.camera_sight / 100))), SRCALPHA)
        square_border.fill("#000000")
        for index in range(len(self.tiles) - 1, (self.now_tile if self.autoplay else self.player_now_tile) - 1, -1):
            if not self.render_tile_check(index):
                continue
            tile = self.tiles[index]

            ang = tile["ang"]
            if tile["rot"] == COUNTERCLOCKWISE:
                ang *= -1

            if tile["ang"] != 180:
                pygame.draw.circle(self.screen,
                                   "#000000",
                                   self.convert_pos(tile["pos"]),
                                   self.planet_size * self.camera_sight / 2 + (5 * self.camera_sight / 100))
            new_square_border = pygame.transform.rotate(square_border, -tile["dir"] - ang + (self.camera_angle - 90))
            self.screen.blit(new_square_border,
                             new_square_border.get_rect(
                                 center=self.convert_pos(tile["pos"] - self.planet_size / 2 * move_step(tile["dir"] + ang))
                             ))
            new_square_border = pygame.transform.rotate(square_border, -tile["dir"] + (self.camera_angle - 90))
            self.screen.blit(new_square_border,
                             new_square_border.get_rect(
                                 center=self.convert_pos(tile["pos"] - self.planet_size / 2 * move_step(tile["dir"]))
                             ))

            # pt1 = tile["pos"] + self.planet_size / 2 * move_step(tile["dir"] + ang + 90)
            # pt2 = tile["pos"] + self.planet_size / 2 * -move_step(tile["dir"] + ang + 90)
            # pt3 = pt2 + self.planet_size * move_step(tile["dir"] + ang - 180)
            # pt4 = pt1 + self.planet_size * -move_step(tile["dir"] + ang)
            # pt5 = tile["pos"] + self.planet_size / 2 * move_step(tile["dir"] + 90)
            # pt6 = tile["pos"] + self.planet_size / 2 * -move_step(tile["dir"] + 90)
            # pt7 = pt6 + self.planet_size * move_step(tile["dir"] - 180)
            # pt8 = pt5 + self.planet_size * -move_step(tile["dir"])
            # pygame.draw.lines(self.screen, "#000000", False, (self.convert_pos(pt1),
            #                                                   self.convert_pos(pt4),
            #                                                   self.convert_pos(pt3),
            #                                                   self.convert_pos(pt2)),
            #                   round(5 * self.camera_sight / 100 * 2))
            # pygame.draw.lines(self.screen, "#000000", False, (self.convert_pos(pt5),
            #                                                   self.convert_pos(pt8),
            #                                                   self.convert_pos(pt7),
            #                                                   self.convert_pos(pt6)),
            #                   round(5 * self.camera_sight / 100 * 2))
            # pygame.draw.polygon(self.screen,
            #                     tile["color"],
            #                     (self.convert_pos(pt1),
            #                      self.convert_pos(pt2),
            #                      self.convert_pos(pt3),
            #                      self.convert_pos(pt4)))
            # pygame.draw.polygon(self.screen,
            #                     tile["color"],
            #                     (self.convert_pos(pt5),
            #                      self.convert_pos(pt6),
            #                      self.convert_pos(pt7),
            #                      self.convert_pos(pt8)))
            if tile["ang"] != 180:
                pygame.draw.circle(self.screen,
                                   tile["color"],
                                   self.convert_pos(tile["pos"]),
                                   self.planet_size * self.camera_sight / 2)
                square.fill(tile["color"])
                new_square = pygame.transform.rotate(square, -tile["dir"] - ang + (self.camera_angle - 90))
                self.screen.blit(new_square,
                                 new_square.get_rect(
                                     center=self.convert_pos(tile["pos"] - self.planet_size / 2 * move_step(tile["dir"] + ang))
                                 ))
                new_square = pygame.transform.rotate(square, -tile["dir"] + (self.camera_angle - 90))
                self.screen.blit(new_square,
                                 new_square.get_rect(
                                     center=self.convert_pos(tile["pos"] - self.planet_size / 2 * move_step(tile["dir"]))
                                 ))
            else:
                rect.fill(tile["color"])
                new_rect = pygame.transform.rotate(rect, -tile["dir"] + 90 + (self.camera_angle - 90))
                self.screen.blit(new_rect,
                                 new_rect.get_rect(
                                     center=self.convert_pos(tile["pos"]))
                                 )

            if index != 0 and self.tiles[index - 1]["rot"] != tile["rot"]:
                pygame.draw.circle(self.screen,
                                   "#ff00ff",
                                   self.convert_pos(tile["pos"]),
                                   self.planet_size * self.camera_sight / 2 / 2,
                                   round(5 * self.camera_sight / 100))
            if index != 0 and self.tiles[index - 1]["bpm"] != tile["bpm"]:
                pygame.draw.circle(self.screen,
                                   "#ff0000" if tile["bpm"] > self.tiles[index - 1]["bpm"] else "#0000ff",
                                   self.convert_pos(tile["pos"]),
                                   self.planet_size * self.camera_sight / 2 / 2)

    def render_tile_check(self, index):
        if index < (self.now_tile if self.autoplay else self.player_now_tile):
            return False

        tile = self.tiles[index]
        if not (-self.planet_size * self.camera_sight <=
                self.convert_pos(tile["pos"]).x <=
                self.width + self.planet_size * self.camera_sight
                and -self.planet_size * self.camera_sight <=
                self.convert_pos(tile["pos"]).y <=
                self.height + self.planet_size * self.camera_sight):
            return False

        for i in tile["super_pos"]:
            if not i < (self.now_tile if self.autoplay else self.player_now_tile):
                return False

        return True

    def convert_pos(self, pos: Vec2):
        pos = pos.copy()
        pos -= self.camera_pos
        pos = pos.x * move_step(90 - (self.camera_angle - 90)) + pos.y * move_step(0 - (self.camera_angle - 90))
        pos.x = pos.x * self.camera_sight + self.width // 2
        pos.y = pos.y * -self.camera_sight + self.height // 2
        return pos

    def cleanup(self):
        pygame.quit()


if __name__ == '__main__':
    theApp = App()
    theApp.execute()

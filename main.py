"""
author: CkbltIsCoding
"""

import json
import os.path
import sys
import traceback
from math import pi, sin as _sin, cos as _cos, floor, cbrt

import pygame
from pygame.locals import *
from pygame.math import Vector2 as Vec2

import music


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
    return Vec2(cos(direction), sin(direction))


def move_step2(direction):  # 向 direction° 方向移动一个单位
    return Vec2(-cos(direction), -sin(direction))


CLOCKWISE = True
COUNTERCLOCKWISE = False

STATE_PLAYING = 1


class App:
    def __init__(self, _path_to_beatmap: str, _pitch: int = 100) -> None:
        self.music_path = ""
        self.offset = 0
        self.pitch = _pitch
        self.title = ""

        # self.path = ".\\2024"
        self.path = _path_to_beatmap
        self.tiles = []
        pygame.display.set_caption("A dance of fire and ice (Pygame version) (Loading...)")
        self.process_data()
        pygame.display.set_caption("A dance of fire and ice (Pygame version)")

        pygame.init()

        self.size = self.width, self.height = 1200, 800
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("A dance of fire and ice (Pygame)")
        self.running = True  # 是否运行
        self.fullscreen = False  # 全屏

        self.state = STATE_PLAYING  # 游戏状态
        self.pre_state = 0  # 上一帧的游戏状态

        self.keys = [K_a, K_s, K_d, K_f, K_SPACE, K_j, K_k, K_l, K_SEMICOLON]  # 键
        self.keys = [K_a, K_s, K_d, K_f, K_v, K_SPACE, K_n, K_j, K_k, K_l, K_SEMICOLON]  # 键
        # self.keys = [K_TAB, K_1, K_2, K_e, K_o, K_MINUS, K_EQUALS, K_RIGHTBRACKET,
        #              K_LSHIFT, K_CAPSLOCK, K_SPACE, K_c, K_COMMA, K_RETURN, K_RSHIFT]
        self.key_pressed = [False for _ in range(len(self.keys))]
        self.keyrain = [[False for _ in range(120)] for _ in range(len(self.keys))]

        self.timer = 0
        self.beat = 0
        self.player_beat = 0
        self.pre_beat = 0

        # 摄像机
        self.camera_pos = Vec2()
        self.camera_sight = 50
        self.camera_angle = 0

        # 行星
        self.planet1_pos = Vec2()
        self.planet2_pos = Vec2()
        self.planet_size = 0.5
        self.planet_angle = 0.0
        self.planet_static = 1

        # （玩家）现在/前一帧砖块
        self.player_now_tile = 0
        self.player_pre_tile = 0
        self.now_tile = 0
        self.pre_tile = 0

        # 玩家打的延迟
        self.timing = 0
        self.timing_offset = -40
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
        self.font_title = pygame.font.SysFont("Dengxian", 36, True, True)
        self.font_acc = pygame.font.SysFont("Consolas", 18, True)

        text_title_shadow = self.font_title.render(self.title, True, "#00000099")
        self.text_title = pygame.Surface(
            Vec2(text_title_shadow.get_size()) + Vec2(2, 2), SRCALPHA
        )
        self.text_title.blit(text_title_shadow, (2, 2))
        text_title = self.font_title.render(self.title, True, "#ffffff")
        self.text_title.blit(text_title, (0, 0))

        self.text_autoplay = self.font_debug.render("Autoplay", True, "#ffffff")

        self.text_tl = self.font_acc.render("TL!!", True, "#ff0000")
        self.text_l = self.font_acc.render("Late!", True, "#ffcc00")
        self.text_lp = self.font_acc.render("LP!", True, "#ffff00")
        # self.text_p = self.font_acc.render('P!', True, '#00ff00')
        self.text_ep = self.font_acc.render("EP!", True, "#ffff00")
        self.text_e = self.font_acc.render("Early!", True, "#ffcc00")
        self.text_te = self.font_acc.render("TE!!", True, "#ff0000")

        pygame.mixer.init()

        self.sound_ready = pygame.mixer.Sound("ready.wav")
        self.channel_ready = pygame.mixer.Channel(0)

        self.sound_beat = pygame.mixer.Sound("beat.wav")
        self.channel_beat = pygame.mixer.Channel(1)

        if self.music_path != "":
            pygame.mixer_music.load(self.music_path)
            # pygame.mixer_music.set_volume(0.5)

    def process_data(self) -> None:
        with open(
                os.path.join(self.path, "main.adofai"), "r", encoding="utf-8-sig"
        ) as f:
            beatmap = json.load(f, strict=False)
        if "songFilename" in beatmap["settings"].keys():
            self.music_path = os.path.join(
                self.path, beatmap["settings"]["songFilename"]
            )
            if self.pitch != 100:
                out_file = "out.wav"
                music.change_speed(self.music_path, out_file, self.pitch / 100)
                self.music_path = out_file
        self.title = beatmap['settings']['artist'] + ' - ' + beatmap['settings']['song']
        self.offset = beatmap["settings"]["offset"] * 100 / self.pitch + 50 * (
                100 / self.pitch - 1
        )
        self.tiles = []
        for index in range(len(beatmap["angleData"])):
            angle = beatmap["angleData"][index]
            if angle == 999:
                self.tiles[index - 1]["midspin"] = True
            self.tiles.append(
                {
                    "angle": angle,
                    "bpm": 0,
                    "twirl": False,
                    "orbit": CLOCKWISE,
                    "midspin": False,
                    "pause": 0,
                    "pos": Vec2(),
                    "ms": 0,
                    "beat": 0,
                    "color": "#debb7b",
                    "border_color": "#443310",
                }
            )

        self.tiles[0]["bpm"] = beatmap["settings"]["bpm"] * self.pitch / 100

        for action in beatmap["actions"]:
            try:
                tile = self.tiles[action["floor"]]
                match action["eventType"]:
                    case "SetSpeed":
                        if action["speedType"] == "Bpm":
                            tile["bpm"] = action["beatsPerMinute"] * self.pitch / 100
                        elif action["speedType"] == "Multiplier":
                            tile["bpm"] = -action["bpmMultiplier"]
                    case "Twirl":
                        tile["twirl"] = True
                    case "Pause":
                        tile["pause"] = action["duration"]
            except IndexError:
                pass

        self.tiles = list(filter(lambda t: t["angle"] != 999, self.tiles))

        for index in range(len(self.tiles)):
            tile = self.tiles[index]
            if tile["bpm"] == 0:
                tile["bpm"] = self.tiles[index - 1]["bpm"]
            elif tile["bpm"] < 0:
                tile["bpm"] = self.tiles[index - 1]["bpm"] * -tile["bpm"]

            if index == 0:
                tile["orbit"] = not tile["twirl"]
            elif tile["twirl"]:
                tile["orbit"] = not self.tiles[index - 1]["orbit"]
            else:
                tile["orbit"] = self.tiles[index - 1]["orbit"]

            i = index - 1
            while self.tiles[i]["midspin"]:
                i -= 1
            j = i - 1
            while self.tiles[j]["midspin"]:
                j -= 1

            if index == 0:
                tile["pos"] = Vec2()
            elif self.tiles[index]["midspin"]:
                tile["pos"] = self.tiles[index - 1]["pos"]
            else:
                tile["pos"] = self.tiles[i]["pos"] + 1 * move_step(
                    self.tiles[i]["angle"]
                )

            hairclip = (
                    abs(
                        self.tiles[index - 2]["angle"] % 360
                        - self.tiles[index - 1]["angle"] % 360
                    )
                    == 180
            )
            if index <= 1:
                tile["beat"] = 0
                tile["ms"] = 0
            elif hairclip:
                tile["beat"] = 2 + self.tiles[index - 1]["pause"]
                tile["ms"] = (
                        self.tiles[index - 1]["ms"]
                        + tile["beat"] / (self.tiles[index - 1]["bpm"] / 60) * 1000
                )
                tile["beat"] += self.tiles[index - 1]["beat"]
            else:
                if tile["midspin"]:
                    angle = 180 - tile["angle"] + self.tiles[i]["angle"]
                else:
                    angle = self.tiles[j]["angle"] - 180 - self.tiles[i]["angle"]
                if self.tiles[i]["orbit"] == COUNTERCLOCKWISE:
                    angle *= -1
                angle %= 360
                tile["beat"] = angle / 180 + self.tiles[i]["pause"]
                tile["ms"] = (
                        self.tiles[i]["ms"]
                        + tile["beat"] / (self.tiles[i]["bpm"] / 60) * 1000
                )
                tile["beat"] += self.tiles[i]["beat"]

    def execute(self) -> None:
        while self.running:
            self.keydown_event_count = 0
            for event in pygame.event.get():
                self.event(event)
            self.loop()
            self.render()
            self.clock.tick(self.FPS)
        self.cleanup()

    def event(self, event: pygame.event.Event) -> None:
        if event.type == QUIT:  # 退出程序
            self.running = False

        if event.type == KEYDOWN:
            if event.dict["key"] == K_ESCAPE:  # 退出程序
                self.running = False
            if event.dict["key"] == K_F11:  # 全屏开关
                self.fullscreen = not self.fullscreen
                if self.fullscreen:
                    self.size = self.width, self.height = pygame.display.list_modes()[0]
                    self.screen = pygame.display.set_mode(
                        self.size, FULLSCREEN | HWSURFACE
                    )
                else:
                    self.size = self.width, self.height = 1200, 800
                    self.screen = pygame.display.set_mode(self.size)
            if event.dict["key"] == K_BACKSLASH:  # Autoplay 开关
                self.autoplay = not self.autoplay
            if event.dict["key"] in self.keys:  # 打的键
                self.keydown_event_count += 1
                self.key_pressed[self.keys.index(event.dict["key"])] = True

        if event.type == KEYUP:
            if event.dict["key"] in self.keys:
                self.key_pressed[self.keys.index(event.dict["key"])] = False

    def loop(self) -> None:
        global STATE_PLAYING

        self.delta = self.clock.get_time()

        if self.state == STATE_PLAYING:
            if pygame.mixer_music.get_busy() or self.timer == 0:
                self.timer = round(
                    pygame.mixer_music.get_pos()
                    - max(3 / self.tiles[0]["bpm"] * 60 * 1000, self.offset)
                )
            if self.autoplay:
                self.player_now_tile = self.now_tile
                if self.now_tile + 1 < len(self.tiles):
                    self.timing = self.timer - self.tiles[self.now_tile + 1]["ms"]
            else:
                if self.player_now_tile + 1 < len(self.tiles):
                    self.timing = (
                            self.timer
                            - self.tiles[self.player_now_tile + 1]["ms"]
                            + self.timing_offset
                    )

            self.calc_beat()
            if (
                    floor(self.pre_beat) != floor(self.beat)
                    and -4 <= floor(self.beat) <= -1
            ):  # 准备的声音
                self.channel_ready.play(self.sound_ready)
            if self.pre_tile != self.now_tile:
                if self.autoplay:
                    self.timing_list.append([self.timing, 0])
                    self.judge()
                self.channel_beat.play(self.sound_beat)  # 打的声音

            if not self.autoplay:  # 错过判定
                while (
                        self.timing > self.LE and self.player_now_tile < len(self.tiles) - 1
                ):
                    self.player_now_tile += 1
                    self.tl += 1
                    self.timing_list.append([self.LE + 5, 0])
                    if self.planet_static == 1:
                        self.timing_sprites.append(["TL!!", self.planet2_pos, 0])
                    else:
                        self.timing_sprites.append(["TL!!", self.planet1_pos, 0])

                    self.calc_beat()
                    if self.player_now_tile + 1 < len(self.tiles):
                        self.timing = (
                                self.timer
                                - self.tiles[self.player_now_tile + 1]["ms"]
                                + self.timing_offset
                        )
            for i in range(self.keydown_event_count):
                self.keydown_event()
                if self.autoplay:
                    if self.now_tile + 1 < len(self.tiles):
                        self.timing = (
                                self.timer
                                - self.tiles[self.now_tile + 1]["ms"]
                                + self.timing_offset
                        )
                else:
                    if self.player_now_tile + 1 < len(self.tiles):
                        self.timing = (
                                self.timer
                                - self.tiles[self.player_now_tile + 1]["ms"]
                                + self.timing_offset
                        )
                self.calc_beat()

            self.calc_planets()
            self.camera()

            index = 0
            while index < len(self.timing_list):
                self.timing_list[index][1] += self.delta
                if self.timing_list[index][1] >= 5000 or len(self.timing_list) > 500:
                    del self.timing_list[index]
                    continue
                index += 1

            index = 0
            while index < len(self.timing_sprites):
                self.timing_sprites[index][2] += self.delta
                if self.timing_sprites[index][2] >= 5000 or len(self.timing_sprites) > 500:
                    del self.timing_sprites[index]
                    continue
                index += 1

            for i in range(len(self.keyrain)):
                self.keyrain[i].pop()
                self.keyrain[i].insert(0, self.key_pressed[i])

            self.pre_beat = self.beat
            self.pre_tile = self.now_tile
            self.player_pre_tile = self.player_now_tile
            self.pre_state = self.state

    def keydown_event(self) -> None:
        if self.waiting_for_key:
            if self.music_path != "":
                pygame.mixer_music.play()
            self.waiting_for_key = False
        elif not self.autoplay and self.player_now_tile < len(self.tiles) - 1:
            self.timing_list.append([self.timing, 0])
            self.timing = (
                    self.timer
                    - self.tiles[self.player_now_tile + 1]["ms"]
                    + self.timing_offset
            )  #
            self.player_now_tile += 1
            self.judge()

    def judge(self) -> None:
        if abs(self.timing) <= self.P:
            self.p += 1
        elif abs(self.timing) <= self.LEP:
            if self.timing > 0:
                self.lp += 1
                self.timing_sprites.append(
                    ["LP!", self.tiles[self.player_now_tile]["pos"], 0]
                )
            else:
                self.ep += 1
                self.timing_sprites.append(
                    ["EP!", self.tiles[self.player_now_tile]["pos"], 0]
                )
        elif abs(self.timing) <= self.LE:
            if self.timing > 0:
                self.l += 1
                self.timing_sprites.append(
                    ["Late!", self.tiles[self.player_now_tile]["pos"], 0]
                )
            else:
                self.e += 1
                self.timing_sprites.append(
                    ["Early!", self.tiles[self.player_now_tile]["pos"], 0]
                )
        elif self.timing < 0:
            self.player_now_tile -= 1
            self.timing_list.pop()
            if self.beat >= 0:
                self.timing_list.append([-self.LE - 5, 0])
                self.te += 1
                if self.planet_static == 1:
                    self.timing_sprites.append(["TE!!", self.planet2_pos, 0])
                else:
                    self.timing_sprites.append(["TE!!", self.planet1_pos, 0])

    def calc_beat(self) -> None:
        self.now_tile = 0
        if self.timer < 0:
            self.beat = self.timer / (60 / self.tiles[0]["bpm"]) / 1000
        else:
            self.beat = 0
            # midspin = 0
            # for index in range(len(self.tiles)):
            #     midspin = 0
            #
            #     tile = self.tiles[index]
            #     hairclip = abs(self.tiles[index - 2]['angle'] % 360 - self.tiles[index - 1]['angle'] % 360) == 180
            #
            #     i = index - 1
            #     while self.tiles[i]['midspin']:
            #         i -= 1
            #     j = i - 1
            #     while self.tiles[j]['midspin']:
            #         j -= 1
            #
            #     if self.timer >= tile['ms']:
            #         self.now_tile += 1
            #     else:
            #         break
            #
            #     if self.tiles[index]['midspin']:
            #         angle = 180 - self.tiles[index]['angle'] + self.tiles[i]['angle']
            #         if self.tiles[i]['orbit']:
            #             midspin = angle % 360 / 180
            #         else:
            #             midspin = -angle % 360 / 180
            #         if self.timer < self.tiles[index + 1]['ms']:
            #             break
            #         continue
            #     else:
            #         angle = abs(self.tiles[j]['angle'] - 180 - self.tiles[i]['angle'])
            #     if index >= 2:
            #         if hairclip:
            #             self.beat += 2
            #         elif self.tiles[i]['orbit']:
            #             self.beat += angle % 360 / 180
            #         else:
            #             self.beat += angle % 360 / 180
            #         self.beat += self.tiles[i]['pause']
            # self.beat += midspin

            for index in range(len(self.tiles)):
                tile = self.tiles[index]
                if self.timer >= tile["ms"]:
                    self.now_tile += 1
                else:
                    break

            if self.now_tile != 0:
                self.now_tile -= 1

            self.beat = self.tiles[self.now_tile]["beat"]
            self.beat += (
                    (self.timer - self.tiles[self.now_tile]["ms"])
                    / (60 / self.tiles[self.now_tile]["bpm"])
                    / 1000
            )

    def calc_planets(self) -> None:
        self.planet_angle = 0
        self.player_beat = 0
        self.planet_static = 2
        now_tile = self.now_tile if self.autoplay else self.player_now_tile
        self.player_beat = self.tiles[now_tile]["beat"]
        for index in range(now_tile + 1):
            if not self.tiles[index]["midspin"]:
                if self.planet_static == 1:
                    self.planet_static = 2
                else:
                    self.planet_static = 1
        if now_tile == 0:
            self.planet_angle = 0
        else:
            if self.tiles[now_tile]["midspin"]:
                self.planet_angle = self.tiles[now_tile]["angle"]
            else:
                i = now_tile - 1
                while self.tiles[i]["midspin"]:
                    i -= 1
                self.planet_angle = self.tiles[i]["angle"] - 180
        if self.tiles[now_tile]["orbit"] == CLOCKWISE:
            self.planet_angle -= (self.beat - self.player_beat) * 180
        else:
            self.planet_angle += (self.beat - self.player_beat) * 180
        if not self.autoplay:
            angle = (
                            self.timing_offset
                            / (60 / self.tiles[self.player_now_tile]["bpm"])
                            / 1000
                    ) * 180
            if self.tiles[self.player_now_tile]["orbit"] == CLOCKWISE:
                self.planet_angle -= angle
            else:
                self.planet_angle += angle
        self.planet_angle += 180
        self.planet1_pos = self.tiles[now_tile]["pos"]
        self.planet2_pos = self.planet1_pos + move_step2(self.planet_angle)
        if self.planet_static == 2:
            self.planet1_pos, self.planet2_pos = self.planet2_pos, self.planet1_pos

    def camera(self) -> None:
        # 视野
        camera_sight = max(10.0, min(200.0, 500 / cbrt(self.tiles[self.now_tile]["bpm"])))
        self.camera_sight += (camera_sight - self.camera_sight) / 1000 * self.delta
        # self.camera_sight += (self.now_tile - self.pre_tile) * 0.1

        # 位置
        self.camera_pos += (
                                   self.tiles[self.now_tile if self.autoplay else self.player_now_tile]["pos"]
                                   - self.camera_pos
                           ) / (
                                   (self.tiles[self.now_tile]["bpm"] + 10000)
                                   / self.tiles[self.now_tile]["bpm"]
                           )

    def render(self) -> None:
        self.screen.fill("#10131A")

        self.render_tiles()

        # 绘制行星
        pygame.draw.circle(
            self.screen,
            "#ff3333",
            self.convert_pos(self.planet1_pos),
            self.planet_size * self.camera_sight / 2,
        )
        if not self.waiting_for_key:
            pygame.draw.circle(
                self.screen,
                "#3366ff",
                self.convert_pos(self.planet2_pos),
                self.planet_size * self.camera_sight / 2,
            )

        # 绘制准度提示
        text_acc_dict = {
            "TL!!": self.text_tl,
            "Late!": self.text_l,
            "LP!": self.text_lp,
            "TE!!": self.text_te,
            "Early!": self.text_e,
            "EP!": self.text_ep,
        }
        for sprite in self.timing_sprites:
            pos = self.convert_pos(sprite[1])
            if not (
                    -100 <= pos.x <= self.width + 100 and -100 <= pos.y <= self.height + 100
            ):
                continue
            alpha = 255 - sprite[2] * 255 / 5000
            if alpha <= 0:
                continue
            text = text_acc_dict[sprite[0]].copy()
            text.set_alpha(alpha)
            if sprite[2] / 150 < 1:
                text = pygame.transform.scale_by(text, sprite[2] / 150)
            self.screen.blit(text, text.get_rect(center=pos))

        # 绘制准度条
        pygame.draw.rect(
            self.screen,
            "#ff0000",
            (
                self.width // 2 - self.LE * 2 - 20,
                self.height - 40,
                self.LE * 4 + 40,
                30,
            ),
        )
        pygame.draw.rect(
            self.screen,
            "#ffcc00",
            (self.width // 2 - self.LE * 2, self.height - 40, self.LE * 4, 30),
        )
        pygame.draw.rect(
            self.screen,
            "#ffff00",
            (self.width // 2 - self.LEP * 2, self.height - 40, self.LEP * 4, 30),
        )
        pygame.draw.rect(
            self.screen,
            "#00ff00",
            (self.width // 2 - self.P * 2, self.height - 40, self.P * 4, 30),
        )
        line = pygame.surface.Surface((3, 20))
        line.fill("#000000")
        for timing in self.timing_list:
            alpha = 255 - timing[1] * 255 / 5000
            if alpha <= 0:
                continue
            line.set_alpha(alpha)
            self.screen.blit(
                line,
                line.get_rect(
                    centerx=self.width // 2 + timing[0] * 2, y=self.height - 40
                ),
            )
        text_cnt = self.font_debug.render(
            f"{self.te} {self.e} {self.ep} " f"{self.p} {self.lp} {self.l} {self.tl}",
            True,
            "#ffffff",
        )
        self.screen.blit(
            text_cnt,
            text_cnt.get_rect(centerx=self.width // 2, bottom=self.height - 40),
        )

        self.render_keyrain()

        # 绘制一些文字
        self.screen.blit(
            self.text_title, self.text_title.get_rect(centerx=self.width // 2, y=50)
        )

        text_debug = self.font_debug.render(
            f"FPS: {round(self.clock.get_fps(), 2)}",
            True,
            "#ffffff",
        )
        self.screen.blit(text_debug, (10, 10))
        text_debug = self.font_debug.render(
            f"TileBPM: {round(self.tiles[self.now_tile]['bpm'], 3)}",
            True,
            "#ffffff",
        )
        self.screen.blit(text_debug, text_debug.get_rect(top=10, right=self.width - 10))
        real_bpm = self.tiles[self.now_tile]['bpm']
        if self.now_tile == len(self.tiles) - 1:
            real_bpm /= self.tiles[self.now_tile]['beat'] - self.tiles[self.now_tile - 1]['beat']
        elif self.now_tile != 0:
            real_bpm /= self.tiles[self.now_tile + 1]['beat'] - self.tiles[self.now_tile]['beat']
        text_debug = self.font_debug.render(
            f"RealBPM: {round(real_bpm, 3)}",
            True,
            "#ffffff",
        )
        self.screen.blit(text_debug, text_debug.get_rect(top=40, right=self.width - 10))

        if self.autoplay:
            self.screen.blit(self.text_autoplay, (10, 40))

        pygame.display.flip()

    def render_tiles(self) -> None:
        length = self.planet_size * self.camera_sight
        border_length = length / 20
        half_sqr = pygame.Surface((length / 2, length), SRCALPHA)
        half_sqr_border = pygame.Surface(
            (length / 2 + border_length * 2, length + border_length * 2), SRCALPHA
        )
        square = pygame.Surface((length, length), SRCALPHA)
        square_border = pygame.Surface(
            (length + border_length * 2, length + border_length * 2), SRCALPHA
        )
        rect = pygame.Surface((length * 2, length), SRCALPHA)
        rect_border = pygame.Surface(
            (length * 2 + border_length * 2, length + border_length * 2), SRCALPHA
        )
        tri = pygame.Surface((length / 2, length), SRCALPHA)
        tri_border = pygame.Surface(
            (length / 2 + border_length * 2, length + border_length * 2), SRCALPHA
        )
        # surf_tile_dict = {}  # 记忆
        for index in range(
                min(
                    len(self.tiles) - 1,
                    (self.now_tile if self.autoplay else self.player_now_tile) + 256,
                ),
                -1,
                -1,
        ):  # 倒序
            if not self.render_tile_check(index):
                continue

            tile = self.tiles[index]
            hairclip = (
                    abs(tile["angle"] % 360 - self.tiles[index - 1]["angle"] % 360) == 180
            )

            if index < (
                    self.now_tile if self.autoplay else self.player_now_tile
            ):  # 消失动画
                alpha = 255 - (
                        self.timer - (self.tiles[index]["ms"] if index != 0 else 0) - 200
                )
                if alpha <= 0:
                    break
            else:  # 出现动画
                if index == 0:
                    alpha = 255
                else:
                    alpha = 255 - (self.tiles[index]["ms"] - self.timer - 1000)
                    if alpha <= 0:
                        continue

            surf_tile = pygame.Surface(
                ((length + border_length * 2) * 2, (length + border_length * 2) * 2),
                SRCALPHA,
            )

            if index == 0:
                i = 0
            else:
                i = index - 1
                while self.tiles[i]["midspin"]:
                    i -= 1

            if self.tiles[index]["angle"] != self.tiles[index - 1]["angle"]:
                if tile["midspin"]:
                    half_sqr_border.fill(tile["border_color"])
                    new_half_sqr_border = pygame.transform.rotate(
                        half_sqr_border, tile["angle"]
                    )
                    surf_tile.blit(
                        new_half_sqr_border,
                        new_half_sqr_border.get_rect(
                            center=(
                                       length + border_length * 2,
                                       length + border_length * 2,
                                   )
                                   - length / 4 * move_step2(180 - tile["angle"])
                        ),
                    )
                    pygame.draw.polygon(
                        tri_border,
                        tile["border_color"],
                        (
                            (0, 0),
                            (0, length + border_length * 2),
                            (length / 2 + border_length, length / 2 + border_length),
                        ),
                    )
                    new_tri_border = pygame.transform.rotate(tri_border, tile["angle"])
                    surf_tile.blit(
                        new_tri_border,
                        new_tri_border.get_rect(
                            center=(
                                       length + border_length * 2,
                                       length + border_length * 2,
                                   )
                                   + (length / 4 + border_length * 2)
                                   * move_step2(180 - tile["angle"])
                        ),
                    )
                else:
                    pygame.draw.circle(
                        surf_tile,
                        tile["border_color"],
                        (length + border_length * 2, length + border_length * 2),
                        (length + border_length * 2) / 2,
                    )
                    if hairclip:
                        half_sqr_border.fill(tile["border_color"])
                        new_half_sqr_border = pygame.transform.rotate(
                            half_sqr_border, tile["angle"]
                        )
                        surf_tile.blit(
                            new_half_sqr_border,
                            new_half_sqr_border.get_rect(
                                center=(
                                           length + border_length * 2,
                                           length + border_length * 2,
                                       )
                                       + length / 4 * move_step(-tile["angle"])
                            ),
                        )
                    else:
                        square_border.fill(tile["border_color"])
                        new_square_border = pygame.transform.rotate(
                            square_border, tile["angle"]
                        )
                        surf_tile.blit(
                            new_square_border,
                            new_square_border.get_rect(
                                center=(
                                           length + border_length * 2,
                                           length + border_length * 2,
                                       )
                                       + length / 2 * move_step(-tile["angle"])
                            ),
                        )
                        new_square_border = pygame.transform.rotate(
                            square_border, self.tiles[i]["angle"]
                        )
                        surf_tile.blit(
                            new_square_border,
                            new_square_border.get_rect(
                                center=(
                                           length + border_length * 2,
                                           length + border_length * 2,
                                       )
                                       - length / 2 * move_step(-self.tiles[i]["angle"])
                            ),
                        )

                if tile["midspin"]:
                    # pygame.draw.circle(surf_tile,
                    #                    tile['color'],
                    #                    (length + border_length * 2, length + border_length * 2),
                    #                    length / 2)
                    half_sqr.fill(tile["color"])
                    new_half_sqr = pygame.transform.rotate(half_sqr, tile["angle"])
                    surf_tile.blit(
                        new_half_sqr,
                        new_half_sqr.get_rect(
                            center=(
                                       length + border_length * 2,
                                       length + border_length * 2,
                                   )
                                   - length / 4 * move_step2(180 - tile["angle"])
                        ),
                    )
                    pygame.draw.polygon(
                        tri,
                        tile["color"],
                        ((0, 0), (0, length), (length / 2, length / 2)),
                    )
                    new_tri = pygame.transform.rotate(tri, tile["angle"])
                    surf_tile.blit(
                        new_tri,
                        new_tri.get_rect(
                            center=(
                                       length + border_length * 2,
                                       length + border_length * 2,
                                   )
                                   + length / 4 * move_step2(180 - tile["angle"])
                        ),
                    )
                else:
                    pygame.draw.circle(
                        surf_tile,
                        tile["color"],
                        (length + border_length * 2, length + border_length * 2),
                        length / 2,
                    )
                    if hairclip:
                        half_sqr.fill(tile["color"])
                        new_half_sqr = pygame.transform.rotate(
                            half_sqr, self.tiles[i]["angle"]
                        )
                        surf_tile.blit(
                            new_half_sqr,
                            new_half_sqr.get_rect(
                                center=(
                                           length + border_length * 2,
                                           length + border_length * 2,
                                       )
                                       - length / 4 * move_step(-self.tiles[i]["angle"])
                            ),
                        )
                    else:
                        square.fill(tile["color"])
                        new_square = pygame.transform.rotate(square, tile["angle"])
                        surf_tile.blit(
                            new_square,
                            new_square.get_rect(
                                center=(
                                           length + border_length * 2,
                                           length + border_length * 2,
                                       )
                                       + length / 2 * move_step(-(tile["angle"]))
                            ),
                        )
                        new_square = pygame.transform.rotate(
                            square, self.tiles[i]["angle"]
                        )
                        surf_tile.blit(
                            new_square,
                            new_square.get_rect(
                                center=(
                                           length + border_length * 2,
                                           length + border_length * 2,
                                       )
                                       - length / 2 * move_step(-self.tiles[i]["angle"])
                            ),
                        )
            else:
                rect_border.fill(tile["border_color"])
                new_rect_border = pygame.transform.rotate(rect_border, tile["angle"])
                surf_tile.blit(
                    new_rect_border,
                    new_rect_border.get_rect(
                        center=(length + border_length * 2, length + border_length * 2)
                    ),
                )
                rect.fill(tile["color"])
                new_rect = pygame.transform.rotate(rect, tile["angle"])
                surf_tile.blit(
                    new_rect,
                    new_rect.get_rect(
                        center=(length + border_length * 2, length + border_length * 2)
                    ),
                )

            if not tile["midspin"]:
                msi = index + 1
                while msi < len(self.tiles) and self.tiles[msi]["midspin"]:
                    msi += 1
                for k in range(msi - 1, index, -1):
                    if k == index + 1:
                        pygame.draw.circle(
                            surf_tile,
                            tile["border_color"],
                            (length + border_length * 2, length + border_length * 2),
                            (length + border_length * 2) / 2,
                        )
                    new_square_border = pygame.transform.rotate(
                        square_border, self.tiles[k]["angle"]
                    )
                    surf_tile.blit(
                        new_square_border,
                        new_square_border.get_rect(
                            center=(
                                       length + border_length * 2,
                                       length + border_length * 2,
                                   )
                                   - length / 2 * move_step2(-self.tiles[k]["angle"])
                        ),
                    )
                    new_square = pygame.transform.rotate(square, self.tiles[k]["angle"])
                    surf_tile.blit(
                        new_square,
                        new_square.get_rect(
                            center=(
                                       length + border_length * 2,
                                       length + border_length * 2,
                                   )
                                   - length / 2 * move_step2(-self.tiles[k]["angle"])
                        ),
                    )
                if msi != index + 1:
                    new_square = pygame.transform.rotate(square, self.tiles[i]["angle"])
                    surf_tile.blit(
                        new_square,
                        new_square.get_rect(
                            center=(
                                       length + border_length * 2,
                                       length + border_length * 2,
                                   )
                                   + length / 2 * move_step2(self.tiles[i]["angle"])
                        ),
                    )
                    pygame.draw.circle(
                        surf_tile,
                        tile["color"],
                        (length + border_length * 2, length + border_length * 2),
                        length / 2,
                    )

            new_surf_tile = surf_tile.copy()

            # 加/减速
            if index != 0 and self.tiles[index - 1]["bpm"] != tile["bpm"]:
                pygame.draw.circle(
                    new_surf_tile,
                    "#ff0000"
                    if tile["bpm"] > self.tiles[index - 1]["bpm"]
                    else "#0000ff",
                    (length + border_length * 2, length + border_length * 2),
                    length / 2 * 0.6,
                )
            # 旋转
            if index != 0 and self.tiles[index - 1]["orbit"] != tile["orbit"]:
                pygame.draw.circle(
                    new_surf_tile,
                    "#ff00ff",
                    (length + border_length * 2, length + border_length * 2),
                    length / 2 * 0.6,
                    round(border_length),
                )

            if alpha < 255:
                new_surf_tile.set_alpha(alpha)
            # 旋转
            new_surf_tile = pygame.transform.rotate(
                new_surf_tile, -(-self.camera_angle)
            )
            if tile["midspin"]:
                self.screen.blit(
                    new_surf_tile,
                    new_surf_tile.get_rect(
                        center=self.convert_pos(tile["pos"])
                               - length * 2 * move_step2(-tile["angle"])
                    ),
                )
            else:
                self.screen.blit(
                    new_surf_tile,
                    new_surf_tile.get_rect(center=self.convert_pos(tile["pos"])),
                )

    def render_tile_check(self, index: int) -> bool:
        # if index < (self.now_tile if self.autoplay else self.player_now_tile):
        #     return False

        tile = self.tiles[index]
        if not (
                -self.planet_size * self.camera_sight
                <= self.convert_pos(tile["pos"]).x
                <= self.width + self.planet_size * self.camera_sight
                and -self.planet_size * self.camera_sight
                <= self.convert_pos(tile["pos"]).y
                <= self.height + self.planet_size * self.camera_sight
        ):
            return False

        # for i in tile['super_pos']:
        #     if not i < (self.now_tile if self.autoplay else self.player_now_tile):
        #         return False

        return True

    def render_keyrain(self):
        rect = pygame.Surface((40, 3), SRCALPHA)
        small_rect = pygame.Surface((30, 3), SRCALPHA)
        pos = [(1, 0), (1, 1), (1, 2), (1, 3), (0, 2), (0, 3.5), (0, 5), (1, 4), (1, 5), (1, 6), (1, 7)]
        name = list("ASDFV_NJKL;")
        for i in range(len(self.keys)):
            pygame.draw.rect(
                self.screen,
                "#ffffff",
                (10 + pos[i][1] * 42, self.height - 10 - 40 - pos[i][0] * 42, 40, 40),
                0 if self.key_pressed[i] else 2
            )
            text = self.font_debug.render(name[i], True, "#000000" if self.key_pressed[i] else "#ffffff")
            self.screen.blit(text, text.get_rect(center=((10 + pos[i][1] * 42 + 20,
                                                          self.height - 10 - 40 - pos[i][0] * 42 + 20))))
        for i in range(len(self.keys)):
            for j in range(120):
                if self.keyrain[i][j] and pos[i][0]:
                    rect.fill((255, 255, 255, max(0, min(255, 1000 - j * 10))))
                    self.screen.blit(rect, (10 + pos[i][1] * 42, self.height - 15 - 82 - j * 3))
        for i in range(len(self.keys)):
            for j in range(120):
                if self.keyrain[i][j] and not pos[i][0]:
                    small_rect.fill((255, 0, 255, max(0, min(255, 1000 - j * 10))))
                    self.screen.blit(small_rect, (15 + pos[i][1] * 42, self.height - 15 - 82 - j * 3))

    def convert_pos(self, pos: Vec2) -> Vec2:
        pos = pos.copy()
        pos -= self.camera_pos
        # pos = pos.x * move_step(90 - (self.camera_angle - 90)) + pos.y * move_step(0 - (self.camera_angle - 90))
        pos.x = pos.x * self.camera_sight + self.width // 2
        pos.y = pos.y * -self.camera_sight + self.height // 2
        return pos

    def cleanup(self) -> None:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    path_to_beatmap = "2024"
    pitch = 100
    try:
        print("Adofai (Pygame ver.)")
        print("支持按 A S D F 空格(Space) J K L ; 键")
        print('开关自动播放按 "\\" 键 (Autoplay)')
        path_to_beatmap = input("输入谱面的路径 (Enter the path to the beatmap) : ")
        pitch = input("输入音高，默认100 (Enter the pitch) : ")
        if pitch == "":
            pitch = 100
        else:
            pitch = int(pitch)
        print("加载中，请稍安勿躁。")
        theApp = App(path_to_beatmap, pitch)
        print("加载完成！你现在应该会看到一个Pygame窗口。")
        theApp.execute()
    except SystemExit:
        pass
    except FileNotFoundError:
        traceback.print_exc()
        pygame.quit()
        print(f"出错了！我没有找到 {path_to_beatmap}\\main.adofai 或者谱面的音乐。这个错误可能是因为谱面的路径不对。")
        input("按下回车键继续…… (Press the enter key to continue)")
    except KeyboardInterrupt:
        pygame.quit()
        print("游戏被你 Ctrl+C 搞没辣！")
        input("按下回车键继续…… (Press the enter key to continue)")
    except:
        traceback.print_exc()
        pygame.quit()
        print("出错了！我不知道怎么错的，但就是出错了！具体出错情况如上。")
        input("按下回车键继续…… (Press the enter key to continue)")

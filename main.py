"""
author: CkbltIsCoding
"""

import bisect
import json
import os.path
import sys
import time
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

        # self.path = ".\\2024\\main.adofai"
        self.path = _path_to_beatmap
        self.tiles = []
        self.bg_color = "#10131a"
        pygame.display.set_caption(
            "A dance of fire and ice (Pygame version) (Loading...)"
        )
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

        self.keys = [K_q, K_w, K_e, K_r, K_v, K_SPACE, K_n, K_u, K_i, K_o, K_p]  # 键
        self.key_pressed = [False for _ in range(len(self.keys))]
        self.keyrain = [[False for _ in range(120)] for _ in range(len(self.keys))]
        self.autoplay_keyrain = None
        self.process_autoplay_keyrain()

        self.start_timer = 0
        self.timer = -max(8 / self.tiles[0]["bpm"] * 60 * 1000, self.offset)
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

        self.text_tl = self.font_acc.render(
            "TL!!",
            True,
            "#ff0000",
        )
        self.text_l = self.font_acc.render(
            "Late!",
            True,
            "#ffcc00",
        )
        self.text_lp = self.font_acc.render(
            "LP!",
            True,
            "#ffff00",
        )
        self.text_p = self.font_acc.render(
            "P!",
            True,
            "#00ff00",
        )
        self.text_ep = self.font_acc.render(
            "EP!",
            True,
            "#ffff00",
        )
        self.text_e = self.font_acc.render(
            "Early!",
            True,
            "#ffcc00",
        )
        self.text_te = self.font_acc.render(
            "TE!!",
            True,
            "#ff0000",
        )

        pygame.mixer.init()

        self.sound_ready = pygame.mixer.Sound("ready.wav")
        self.channel_ready = pygame.mixer.Channel(0)

        self.sound_beat = pygame.mixer.Sound("beat.wav")
        self.channel_beat = pygame.mixer.Channel(1)

        if self.music_path != "":
            pygame.mixer_music.load(self.music_path)
            pygame.mixer_music.set_volume(0.3)

    def init(self):
        self.p = self.lp = self.ep = self.l = self.e = self.tl = self.te = 0
        self.keydown_event_count = 0
        self.timing = 0
        self.timing_offset = -40
        self.timing_list = []
        self.timing_sprites = []
        self.autoplay = False
        self.waiting_for_key = True
        self.keys = [K_q, K_w, K_e, K_r, K_v, K_SPACE, K_n, K_u, K_i, K_o, K_p]  # 键
        self.key_pressed = [False for _ in range(len(self.keys))]
        self.keyrain = [[False for _ in range(120)] for _ in range(len(self.keys))]
        self.start_timer = 0
        self.timer = -max(8 / self.tiles[0]["bpm"] * 60 * 1000, self.offset)
        self.beat = 0
        self.player_beat = 0
        self.pre_beat = 0
        self.camera_pos = Vec2()
        self.camera_sight = 50
        self.camera_angle = 0
        self.planet1_pos = Vec2()
        self.planet2_pos = Vec2()
        self.planet_size = 0.5
        self.planet_angle = 0.0
        self.planet_static = 1
        self.player_now_tile = 0
        self.player_pre_tile = 0
        self.now_tile = 0
        self.pre_tile = 0

    def process_data(self) -> None:
        with open(
            self.path, "r", encoding="utf-8-sig"
        ) as f:
            beatmap = json.load(f, strict=False)
        if (
            "songFilename" in beatmap["settings"].keys()
            and beatmap["settings"]["songFilename"] != ""
        ):
            self.music_path = os.path.join(
                os.path.dirname(self.path), beatmap["settings"]["songFilename"]
            )
            if self.pitch != 100:
                out_file = "out.wav"
                music.change_speed(self.music_path, out_file, self.pitch / 100)
                self.music_path = out_file
        self.title = beatmap["settings"]["artist"] + " - " + beatmap["settings"]["song"]
        self.offset = beatmap["settings"]["offset"] * 100 / self.pitch + 50 * (
            100 / self.pitch - 1
        )

        self.bg_color = "#" + beatmap["settings"]["backgroundColor"]
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
                    "color": "#" + beatmap["settings"]["trackColor"]
                    if "trackColor" in beatmap["settings"].keys()
                    else "#debb7b",
                    "border_color": "#" + beatmap["settings"]["secondaryTrackColor"]
                    if "secondaryTrackColor" in beatmap["settings"].keys()
                    else "#443310",
                    # "color": "#debb7b",
                    # "border_color": "#443310",
                }
            )

        self.tiles[0]["bpm"] = beatmap["settings"]["bpm"] * self.pitch / 100

        for action in beatmap["actions"]:
            try:
                tile = self.tiles[action["floor"]]
                if tile["midspin"] or tile["angle"] == 999:
                    tile = self.tiles[action["floor"] - 1]
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
                    case "RecolorTrack":
                        if action["startTile"][1] == "Start":
                            a = action["startTile"][0]
                        else:
                            a = action["startTile"][0] + action["floor"]
                        if action["endTile"][1] == "Start":
                            b = action["endTile"][0]
                        else:
                            b = action["endTile"][0] + action["floor"]
                        for i in range(a, b + 1):
                            self.tiles[i]["color"] = "#" + action["trackColor"]
                            self.tiles[i]["border_color"] = (
                                "#" + action["secondaryTrackColor"]
                            )
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

    def process_autoplay_keyrain(self):
        self.autoplay_keyrain = [[False for _ in range(round(self.tiles[-1]["ms"]) + 1000)].copy() for _ in self.keys]
        min_ms = 125
        max_ms = 250
        bpm_change = [0]
        for index in range(len(self.tiles[2:])):
            bpm1 = self.tiles[index]["bpm"]
            bpm2 = self.tiles[index - 1]["bpm"]
            if bpm1 != bpm2:
                if ((bpm1 / bpm2) % 1 == 0 and int(bpm1 / bpm2) & int(bpm1 / bpm2 - 1) == 0 or
                    (bpm2 / bpm1) % 1 == 0 and int(bpm2 / bpm1) & int(bpm2 / bpm1 - 1) == 0):
                    continue
                bpm_change.append(index)
        # right = True
        # count = 0
        # for index in range(1, len(self.tiles)):
        #     tile = self.tiles[index]
        #     bpm_change_index = bpm_change[bisect.bisect_right(bpm_change, index) - 1]
        #     ms = 1000 / (tile["bpm"] / 60)
        #     while ms > max_ms:
        #         ms /= 2
        #     while ms <= min_ms:
        #         ms *= 2
        #     if tile["ms"] - self.tiles[index - 1]["ms"] >= ms / 2.1:
        #         count = 0
        #     if (tile["ms"] - self.tiles[bpm_change_index]["ms"]) % ms < ms / 2:
        #         if not right:
        #             right = True
        #             count = 0
        #         for i in range(round(tile["ms"]), round(tile["ms"]) + 30):
        #             if count < 4:
        #                 self.autoplay_keyrain[7 + count][i] = True
        #             elif count < 6:
        #                 self.autoplay_keyrain[4 + count][i] = True
        #     else:
        #         if right:
        #             right = False
        #             count = 0
        #         for i in range(round(tile["ms"]), round(tile["ms"]) + 30):
        #             if count < 4:
        #                 self.autoplay_keyrain[3 - count][i] = True
        #             elif count < 6:
        #                 self.autoplay_keyrain[4 - count][i] = True
        #
        #     count += 1

        right = True
        count = 0
        p_index = 0
        yk = False
        for i in range(round(self.tiles[-1]["ms"]) + 1000):
            if i < self.tiles[-1]["ms"]:
                index = bisect.bisect_right(self.tiles, i, key=lambda x: x["ms"]) - 1
            else:
                index = len(self.tiles) - 1
            bpm_change_index = bpm_change[bisect.bisect_right(bpm_change, index) - 1]
            tile = self.tiles[index]
            ms = 1000 / (tile["bpm"] / 60)
            while ms > max_ms:
                ms /= 2
            while ms <= min_ms:
                ms *= 2
            if index < len(self.tiles) - 1 - 6 and self.tiles[index + 6]["ms"] - tile["ms"] < ms / 2:
                yk = True
            if yk:
                ms /= 2
            if (i - self.tiles[bpm_change_index]["ms"]) % ms < ms / 2:
                if not right:
                    right = True
                    count = 0
                    if yk and not (index < len(self.tiles) - 1 - 6 and self.tiles[index + 6]["ms"] - tile["ms"] < ms / 2):
                        ms *= 2
                        if (i - self.tiles[bpm_change_index]["ms"]) % ms >= ms / 2:
                            ms /= 2
                        else:
                            yk = False
                if p_index != index:
                    for j in range(i, i + int(ms / 3)):
                        if count < 4:
                            self.autoplay_keyrain[7 + count][j] = True
                        elif count < 6:
                            self.autoplay_keyrain[5 + count - 4][j] = True
                    count += 1
            else:
                if right:
                    right = False
                    count = 0
                if p_index != index:
                    for j in range(i, i + int(ms / 3)):
                        if count < 4:
                            self.autoplay_keyrain[3 - count][j] = True
                        elif count < 6:
                            self.autoplay_keyrain[5 - (count - 4)][j] = True
                    count += 1
            p_index = index

        self.autoplay_keyrain = tuple(self.autoplay_keyrain)

    def execute(self) -> None:
        self.init()
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
            elif event.dict["key"] == K_F11:  # 全屏开关
                self.fullscreen = not self.fullscreen
                if self.fullscreen:
                    self.size = self.width, self.height = pygame.display.list_modes()[0]
                    self.screen = pygame.display.set_mode(
                        self.size, FULLSCREEN | HWSURFACE
                    )
                else:
                    self.size = self.width, self.height = 1200, 800
                    self.screen = pygame.display.set_mode(self.size)
            elif event.dict["key"] == K_BACKSLASH:  # Autoplay 开关
                self.autoplay = not self.autoplay
            elif event.dict["key"] in self.keys:  # 打的键
                self.keydown_event_count += 1
                self.key_pressed[self.keys.index(event.dict["key"])] = True
            elif event.dict["key"] == K_BACKQUOTE:  # == GRAVE  #  重开
                pygame.mixer_music.stop()
                self.init()

        if event.type == KEYUP:
            if event.dict["key"] in self.keys:
                self.key_pressed[self.keys.index(event.dict["key"])] = False

    def loop(self) -> None:
        global STATE_PLAYING

        self.delta = self.clock.get_time()

        if self.state == STATE_PLAYING:
            # Timer & music
            if self.music_path == "":
                if not self.waiting_for_key:
                    self.timer = round(
                        (time.time() - self.start_timer) * 1000
                        - max(8 / self.tiles[0]["bpm"] * 60 * 1000, self.offset)
                    )
            else:
                if not self.waiting_for_key:
                    if pygame.mixer_music.get_busy():
                        self.timer = round(pygame.mixer_music.get_pos() - self.offset)
                    else:
                        self.timer = round(
                            (time.time() - self.start_timer) * 1000
                            - max(8 / self.tiles[0]["bpm"] * 60 * 1000, self.offset)
                        )

                if not pygame.mixer_music.get_busy() and -self.offset < self.timer <= 0:
                    pygame.mixer_music.play()

            # Timing
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
                if (
                    self.timing_sprites[index][2] >= 5000
                    or len(self.timing_sprites) > 500
                ):
                    del self.timing_sprites[index]
                    continue
                index += 1

            for i in range(len(self.keyrain)):
                self.keyrain[i].pop()
                if self.autoplay:
                    if 0 <= self.timer < len(self.autoplay_keyrain[0]):
                        self.keyrain[i].insert(0, self.autoplay_keyrain[i][self.timer])
                    else:
                        self.keyrain[i].insert(0, False)
                else:
                    self.keyrain[i].insert(0, self.key_pressed[i])

            self.pre_beat = self.beat
            self.pre_tile = self.now_tile
            self.player_pre_tile = self.player_now_tile
            self.pre_state = self.state

    def keydown_event(self) -> None:
        if self.waiting_for_key:
            self.start_timer = time.time()
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
        pos = self.tiles[self.now_tile if self.autoplay else self.player_now_tile][
            "pos"
        ] + (0, 0.5)
        if abs(self.timing) <= self.P:
            self.p += 1
            self.timing_sprites.append(["P!", pos, 0])
        elif abs(self.timing) <= self.LEP:
            if self.timing > 0:
                self.lp += 1
                self.timing_sprites.append(["LP!", pos, 0])
            else:
                self.ep += 1
                self.timing_sprites.append(["EP!", pos, 0])
        elif abs(self.timing) <= self.LE:
            if self.timing > 0:
                self.l += 1
                self.timing_sprites.append(["Late!", pos, 0])
            else:
                self.e += 1
                self.timing_sprites.append(["Early!", pos, 0])
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
        keys_pressed = pygame.key.get_pressed()
        # 视野
        # if keys_pressed[K_LEFTBRACKET]:
        #     self.camera_sight *= 1.001 ** self.delta
        # if keys_pressed[K_RIGHTBRACKET]:
        #     self.camera_sight /= 1.001 ** self.delta
        camera_sight = max(
            10.0, min(200.0, 500 / cbrt(self.tiles[self.now_tile]["bpm"]))
        )
        self.camera_sight += (camera_sight - self.camera_sight) / 1000 * self.delta

        if self.camera_sight < 0:
            self.camera_sight = 0

        # self.camera_sight += (self.now_tile - self.pre_tile) * 0.1

        # 位置
        # if keys_pressed[K_UP] or keys_pressed[K_DOWN] or keys_pressed[K_RIGHT] or keys_pressed[K_LEFT]:
        #     speed = 0.01
        #     if keys_pressed[K_RSHIFT]:
        #         speed = 0.1
        #     if keys_pressed[K_UP]:
        #         self.camera_pos.y += speed * self.delta
        #     if keys_pressed[K_DOWN]:
        #         self.camera_pos.y -= speed * self.delta
        #     if keys_pressed[K_RIGHT]:
        #         self.camera_pos.x += speed * self.delta
        #     if keys_pressed[K_LEFT]:
        #         self.camera_pos.x -= speed * self.delta
        # elif keys_pressed[K_RETURN]:
        #     self.camera_pos = self.tiles[self.now_tile if self.autoplay else self.player_now_tile]["pos"].copy()
        self.camera_pos += (
            self.tiles[self.now_tile if self.autoplay else self.player_now_tile]["pos"]
            - self.camera_pos
        ) / (
            (self.tiles[self.now_tile]["bpm"] + 10000)
            / self.tiles[self.now_tile]["bpm"]
        )

    def render(self) -> None:
        # self.screen.fill("#10131A")
        self.screen.fill(self.bg_color)

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
            "P!": self.text_p,
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
            if sprite[2] / 50 < 1:
                text = pygame.transform.scale_by(text, sprite[2] / 50)
            text = pygame.transform.scale_by(text, self.camera_sight / 100 * 2)
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
        self.render_text()
        self.render_keyrain()

        pygame.display.flip()

    def render_text(self) -> None:
        self.screen.blit(
            self.text_title, self.text_title.get_rect(centerx=self.width // 2, y=50)
        )

        text_debug = self.font_debug.render(
            f"FPS: {self.clock.get_fps():.3f}, {self.clock.get_time()}",
            True,
            "#ffffff",
        )
        self.screen.blit(text_debug, (10, 10))
        if self.autoplay:
            self.screen.blit(self.text_autoplay, (10, 40))
        real_bpm = self.tiles[self.now_tile]["bpm"]
        if self.now_tile == len(self.tiles) - 1:
            real_bpm /= (
                self.tiles[self.now_tile]["beat"]
                - self.tiles[self.now_tile - 1]["beat"]
            )
        elif self.now_tile != 0:
            real_bpm /= (
                self.tiles[self.now_tile + 1]["beat"]
                - self.tiles[self.now_tile]["beat"]
            )
        if self.player_now_tile != 0:
            x_acc = (
                (
                    self.p
                    + (self.lp + self.ep) * 0.75
                    + (self.l + self.e) * 0.4
                    + (self.tl + self.te) * 0.2
                )
                / (self.p + self.lp + self.ep + self.l + self.e + self.tl + self.te)
            ) * 100
        else:
            x_acc = 100
        texts = [
            f"TileBPM: {self.tiles[self.now_tile]['bpm']:.3f}",
            f"RealBPM: {real_bpm:.3f}",
            f"KPS: {real_bpm / 60:.3f}",
            f"XAcc: {x_acc:.3f}%",
        ]
        for i in range(len(texts)):
            text = self.font_debug.render(
                texts[i],
                True,
                "#ffffff",
            )
            self.screen.blit(
                text, text.get_rect(top=10 + 30 * i, right=self.width - 10)
            )

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
        stop = min(
                len(self.tiles) - 1,
                (self.now_tile if self.autoplay else self.player_now_tile) + 256,
            )
        # stop = len(self.tiles) - 1
        for index in range(stop, -1, -1):  # 倒序
            if not self.render_tile_check(index):
                continue

            tile = self.tiles[index]
            hairclip = (
                abs(tile["angle"] % 360 - self.tiles[index - 1]["angle"] % 360) == 180
            )

            alpha = 255
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
                    half_sqr_border.fill(tile["border_color"][:7])
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
                        tile["border_color"][:7],
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
                        tile["border_color"][:7],
                        (length + border_length * 2, length + border_length * 2),
                        (length + border_length * 2) / 2,
                    )
                    if hairclip:
                        half_sqr_border.fill(tile["border_color"][:7])
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
                        square_border.fill(tile["border_color"][:7])
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
                    half_sqr.fill(tile["color"][:7])
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
                        tile["color"][:7],
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
                        tile["color"][:7],
                        (length + border_length * 2, length + border_length * 2),
                        length / 2,
                    )
                    if hairclip:
                        half_sqr.fill(tile["color"][:7])
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
                        square.fill(tile["color"][:7])
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
                rect_border.fill(tile["border_color"][:7])
                new_rect_border = pygame.transform.rotate(rect_border, tile["angle"])
                surf_tile.blit(
                    new_rect_border,
                    new_rect_border.get_rect(
                        center=(length + border_length * 2, length + border_length * 2)
                    ),
                )
                rect.fill(tile["color"][:7])
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
                            tile["border_color"][:7],
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
                        tile["color"][:7],
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
        pos = [
            (1, 0),
            (1, 1),
            (1, 2),
            (1, 3),
            (0, 2),
            (0, 3.5),
            (0, 5),
            (1, 4),
            (1, 5),
            (1, 6),
            (1, 7),
        ]
        # name = list("ASDFV_NJKL;")
        name = list("QWERV_NUIOP")
        if self.autoplay:
            if 0 <= self.timer < len(self.autoplay_keyrain[0]):
                key_pressed = []
                for index in range(len(self.keys)):
                    key_pressed.append(self.autoplay_keyrain[index][self.timer])
            else:
                key_pressed = self.key_pressed
        else:
            key_pressed = self.key_pressed
        for i in range(len(self.keys)):
            pygame.draw.rect(
                self.screen,
                "#ffffff",
                (10 + pos[i][1] * 42, self.height - 10 - 40 - pos[i][0] * 42, 40, 40),
                0 if key_pressed[i] else 2,
            )
            text = self.font_debug.render(
                name[i], True, "#000000" if key_pressed[i] else "#ffffff"
            )
            self.screen.blit(
                text,
                text.get_rect(
                    center=(
                        (
                            10 + pos[i][1] * 42 + 20,
                            self.height - 10 - 40 - pos[i][0] * 42 + 20,
                        )
                    )
                ),
            )
        for i in range(len(self.keys)):
            for j in range(120):
                if self.keyrain[i][j] and pos[i][0]:
                    rect.fill((255, 255, 255, max(0, min(255, 1000 - j * 10))))
                    self.screen.blit(
                        rect, (10 + pos[i][1] * 42, self.height - 15 - 82 - j * 3)
                    )
        for i in range(len(self.keys)):
            for j in range(120):
                if self.keyrain[i][j] and not pos[i][0]:
                    small_rect.fill((255, 0, 255, max(0, min(255, 1000 - j * 10))))
                    self.screen.blit(
                        small_rect, (15 + pos[i][1] * 42, self.height - 15 - 82 - j * 3)
                    )

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
    path_to_beatmap = "2023/main.adofai"
    pitch = 100
    try:
        print("Adofai (Pygame ver.)")
        print("支持按 A S D F V 空格(Space) N J K L ; 键")
        print('开关自动播放按 "\\" 键 (Autoplay)')
        path_to_beatmap = input("输入谱面的路径 (Enter the path to the beatmap) : ")
        pitch = input("输入音高，默认100 (Enter the pitch) : ")
        if pitch == "":
            pitch = 100
        else:
            pitch = int(pitch)
    except ValueError:
        # traceback.print_exc()
        print("出错了！输入的音高不是整数。")
        input("按下回车键继续…… (Press the enter key to continue)")
        exit(1)

    try:
        print("加载中……")
        theApp = App(path_to_beatmap, pitch)
        print("加载完成！你现在应该会看到一个Pygame窗口。")
        theApp.execute()
    except (SystemExit, KeyboardInterrupt):
        pass
    except FileNotFoundError as e:
        traceback.print_exc()
        pygame.quit()
        print(
            f"出错了！我没有找到{e.filename}。这个错误可能是因为谱面的路径不对。"
        )
        input("按下回车键继续…… (Press the enter key to continue)")
    except:
        traceback.print_exc()
        pygame.quit()
        print("出错了！我不知道怎么错的，但就是出错了！具体出错情况如上。")
        input("按下回车键继续…… (Press the enter key to continue)")

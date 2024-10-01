"""
author: CkbltIsCoding
"""

import bisect
import json
import math
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
STATE_CHARTING = 2


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

        self.state = STATE_CHARTING  # 游戏状态
        self.pre_state = 0  # 上一帧的游戏状态

        self.keys = [K_q, K_w, K_e, K_r, K_v, K_SPACE, K_n, K_u, K_i, K_o, K_p]  # 键
        # self.keys = [K_LSHIFT, K_CAPSLOCK, K_TAB, K_1, K_2, K_e, K_c, K_SPACE,
        #              K_RALT, K_PERIOD, K_p, K_EQUALS, K_BACKSPACE, K_BACKSLASH, K_RETURN, K_RSHIFT]  # 键
        self.key_pressed = [False for _ in range(len(self.keys))]
        self.keyrain = [[False for _ in range(120)] for _ in range(len(self.keys))]
        self.autoplay_keyrain = None
        # self.process_autoplay_keyrain()

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

        self.active_tile = -1

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

        self.dragging = False

        pygame.mixer.init()

        self.sound_ready = pygame.mixer.Sound("ready.wav")
        self.channel_ready = pygame.mixer.Channel(0)

        self.sound_beat = pygame.mixer.Sound("beat.wav")
        self.channel_beat = pygame.mixer.Channel(1)

        if self.music_path != "":
            pygame.mixer_music.load(self.music_path)
            pygame.mixer_music.set_volume(0.3)

        self.music_played = False

        self.init()

    def init(self):
        self.p = self.lp = self.ep = self.l = self.e = self.tl = self.te = 0
        self.keydown_event_count = 0
        self.timing = 0
        self.timing_offset = -40
        self.timing_list = []
        self.timing_sprites = []
        self.waiting_for_key = True
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
        self.music_played = False

    def process_data(self) -> None:
        with open(
            self.path, "r", encoding="utf-8-sig"
        ) as f:
            beatmap = json.load(f, strict=False)
        self.title = beatmap["settings"]["artist"] + (" - " if beatmap["settings"]["artist"] and beatmap["settings"]["song"] else "") + beatmap["settings"]["song"]
        self.offset = beatmap["settings"]["offset"] * 100 / self.pitch + 50 * (
            100 / self.pitch - 1
        )

        self.bg_color = "#" + beatmap["settings"]["backgroundColor"]
        self.tiles = [                {
                    "angle": 0,
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
                }]
        path_data_dict = {'R': 0, 'p': 15, 'J': 30, 'E': 45, 'T': 60, 'o': 75, 'U': 90, 'q': 105, 'G': 120, 'Q':135, 'H':150, 'W':165, 'L': 180, 'x':195, 'N':210, 'Z':225, 'F':240, 'V':255, 'D':270, 'Y':285, 'B':300, 'C':315, 'M':330, 'A':345, '5':555, '6':666, '7':777, '8':888, '!':999}
        for index in range(len(beatmap["angleData"] if "angleData" in beatmap else beatmap["pathData"])):
            if "angleData" in beatmap:
                angle = beatmap["angleData"][index]
            elif "pathData" in beatmap:
                angle = path_data_dict[beatmap["pathData"][index]]

            if angle == 999:
                self.tiles[index]["midspin"] = True
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
                if tile["angle"] == 999:
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
            last_tile = self.tiles[index - 1]

            if tile["bpm"] == 0:
                tile["bpm"] = last_tile["bpm"]
            elif tile["bpm"] < 0:
                tile["bpm"] = last_tile["bpm"] * -tile["bpm"]

            if index == 0:
                tile["orbit"] = not tile["twirl"]
            elif tile["twirl"]:
                tile["orbit"] = not last_tile["orbit"]
            else:
                tile["orbit"] = last_tile["orbit"]

            if index == 0:
                tile["pos"] = Vec2()
            elif tile["midspin"]:
                tile["pos"] = last_tile["pos"]
            else:
                tile["pos"] = last_tile["pos"] + move_step(
                    tile["angle"]
                )

            if index == 0:
                tile["beat"] = 0
                tile["ms"] = 0
            else:
                if last_tile["midspin"]:
                    angle = last_tile["angle"] - tile["angle"]
                else:
                    angle = last_tile["angle"] - 180 - tile["angle"]
                if last_tile["orbit"] == COUNTERCLOCKWISE:
                    angle *= -1
                angle %= 360
                if angle == 0:
                    angle = 360
                if index == 1:
                    angle -= 180
                tile["beat"] = angle / 180 + last_tile["pause"]
                tile["ms"] = (
                        last_tile["ms"]
                        + tile["beat"] / (last_tile["bpm"] / 60) * 1000
                )
                tile["beat"] += last_tile["beat"]

        if (
                "songFilename" in beatmap["settings"].keys()
                and beatmap["settings"]["songFilename"] != ""
        ):
            self.music_path = os.path.join(
                os.path.dirname(self.path), beatmap["settings"]["songFilename"]
            )
            if self.pitch != 100:
                out_file = str(self.pitch) + os.path.split(self.music_path)[1]
                out_file = os.path.join(os.path.split(self.music_path)[0], out_file)
                music.change_speed(self.music_path, out_file, self.pitch / 100)
                self.music_path = out_file
            out_file = "(new) " + os.path.split(self.music_path)[1]
            out_file = os.path.join(os.path.split(self.music_path)[0], out_file)
            if not os.path.exists(out_file):
                music.add_sound(self.music_path, out_file, self.offset, [tile["ms"] for tile in self.tiles])
            self.music_path = out_file

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
        rev = False
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
            # ms = 1000 / (2023 / 60)
            while ms > max_ms:
                ms /= 2
            while ms <= min_ms:
                ms *= 2
            if (i - self.tiles[bpm_change_index]["ms"]) % ms < ms / 2:
                if (i - 1 - self.tiles[bpm_change_index]["ms"]) % ms >= ms / 2:
                    yk = index < len(self.tiles) - 1 - 16 and self.tiles[index + 16]["ms"] - tile["ms"] < ms
            if yk:
                ms /= 2
            if (i - self.tiles[bpm_change_index]["ms"]) % ms < ms / 2 and not rev or\
                (i - self.tiles[bpm_change_index]["ms"]) % ms >= ms / 2 and rev:
                if not right:
                    right = True
                    count = 0
                if p_index != index:
                    for j in range(i, i + min(100, int(ms / 2.1))):
                        # if count < 4:
                        #     self.autoplay_keyrain[7 + count][j] = True
                        # elif count < 6:
                        #     self.autoplay_keyrain[5 + count - 4][j] = True
                        if count < 4:
                            self.autoplay_keyrain[10 + count][j] = True
                        elif count < 6:
                            self.autoplay_keyrain[8 + count - 4][j] = True
                        elif count < 8:
                            self.autoplay_keyrain[14 + count - 6][j] = True
                        else:
                            rev = not rev
                            right = False
                            count = -1
                        # else:
                        #     raise Exception()
                    count += 1
            else:
                if right:
                    right = False
                    count = 0
                if p_index != index:
                    for j in range(i, i + min(100, int(ms / 2.1))):
                        # if count < 4:
                        #     self.autoplay_keyrain[3 - count][j] = True
                        # elif count < 6:
                        #     self.autoplay_keyrain[5 - (count - 4)][j] = True
                        if count < 4:
                            self.autoplay_keyrain[5 - count][j] = True
                        elif count < 6:
                            self.autoplay_keyrain[7 - count + 4][j] = True
                        elif count < 8:
                            self.autoplay_keyrain[1 - count + 6][j] = True
                        else:
                            rev = not rev
                            right = True
                            count = -1
                        # else:
                        #     print(index)
                        #     raise Exception()
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
            elif event.dict["key"] == K_F12:  # Autoplay 开关
                self.autoplay = not self.autoplay

            if self.state == STATE_PLAYING:
                if event.dict["key"] in self.keys:  # 打的键
                    self.keydown_event_count += 1
                    self.key_pressed[self.keys.index(event.dict["key"])] = True
                elif event.dict["key"] == K_ESCAPE:  #  重开
                    pygame.mixer_music.stop()
                    # self.init()
                    self.timing_list.clear()
                    self.timing_sprites.clear()
                    self.state = STATE_CHARTING
            elif self.state == STATE_CHARTING:
                if event.dict["key"] == K_ESCAPE:  # 退出程序
                    self.running = False
                elif event.dict["key"] == K_SPACE:
                    self.state = STATE_PLAYING
                    self.init()
                    if self.active_tile == -1:
                        pass
                    else:
                        self.camera_pos = self.tiles[self.active_tile]["pos"].copy()
                        self.pre_tile = self.active_tile - 1
                        self.now_tile = self.active_tile
                        self.player_pre_tile = self.active_tile - 1
                        self.player_now_tile = self.active_tile
                        self.start_timer = time.time() - self.tiles[self.active_tile]["ms"] / 1000 + self.offset / 1000
                elif event.dict["key"] == K_RIGHT:
                    if self.active_tile != -1 and self.active_tile + 1 < len(self.tiles):
                        self.active_tile += 1
                elif event.dict["key"] == K_LEFT:
                    if self.active_tile != -1:
                        self.active_tile -= 1

        if event.type == KEYUP:
            if event.dict["key"] in self.keys:
                self.key_pressed[self.keys.index(event.dict["key"])] = False

        if event.type == MOUSEBUTTONDOWN:
            if self.state == STATE_CHARTING:
                if event.dict["button"] == 1:
                    pos = self.convert_pos2(Vec2(pygame.mouse.get_pos()))
                    for index in range(len(self.tiles)):
                        if pos.distance_squared_to(self.tiles[index]["pos"]) <= 0.5:
                            self.active_tile = index
                            break
                    else:
                        self.active_tile = -1
                        self.dragging = True
                        pygame.mouse.get_rel()
                elif event.dict["button"] == 4:
                    self.camera_sight *= 1.1
                elif event.dict["button"] == 5:
                    self.camera_sight /= 1.1


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
                        if self.active_tile <= 0:
                            self.timer = round(pygame.mixer_music.get_pos() - self.offset)
                        else:
                            self.timer = round(pygame.mixer_music.get_pos()
                                               + self.tiles[self.active_tile]["ms"])
                    elif self.active_tile <= 0:
                        self.timer = round(
                            (time.time() - self.start_timer) * 1000
                            - max(8 / self.tiles[0]["bpm"] * 60 * 1000, self.offset)
                        )
                    else:
                        self.timer = round((time.time() - self.start_timer) * 1000)

                    if not pygame.mixer_music.get_busy() and not self.music_played:
                        if self.active_tile > 0:
                            pygame.mixer_music.play()
                            self.music_played = True
                            pygame.mixer_music.set_pos(self.offset / 1000 + self.tiles[self.active_tile]["ms"] / 1000)
                        elif -self.offset < self.timer <= 0:
                            pygame.mixer_music.play()
                            self.music_played = True

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
                # self.channel_beat.play(self.sound_beat)  # 打的声音

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
                if self.autoplay and self.autoplay_keyrain:
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
        elif self.state == STATE_CHARTING:
            self.camera()
            if pygame.mouse.get_pressed()[0] and self.dragging:
                rel = pygame.mouse.get_rel()
                self.camera_pos -= self.convert_pos2(Vec2(rel), False, False)
            else:
                self.dragging = False

    def keydown_event(self) -> None:
        if self.waiting_for_key:
            if self.active_tile <= 0:
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
            self.planet_angle = 180
        else:
            self.planet_angle = self.tiles[now_tile]["angle"]
        if self.tiles[now_tile]["midspin"]:
            self.planet_angle += 180
        if self.tiles[now_tile]["orbit"] == CLOCKWISE:
            self.planet_angle -= (self.beat - self.player_beat) * 180
        else:
            self.planet_angle += (self.beat - self.player_beat) * 180
        if not self.autoplay:
            angle = (
                self.timing_offset
                / (60 / self.tiles[now_tile]["bpm"])
                / 1000
            ) * 180
            if self.tiles[now_tile]["orbit"] == CLOCKWISE:
                self.planet_angle -= angle
            else:
                self.planet_angle += angle
        self.planet1_pos = self.tiles[now_tile]["pos"]
        self.planet2_pos = self.planet1_pos + move_step2(self.planet_angle)
        if self.planet_static == 2:
            self.planet1_pos, self.planet2_pos = self.planet2_pos, self.planet1_pos

    def camera(self) -> None:
        keys_pressed = pygame.key.get_pressed()

        if self.camera_sight < 0:
            self.camera_sight = 0

        # self.camera_sight += (self.now_tile - self.pre_tile) * 0.1



        if self.state == STATE_CHARTING:
            # 视野
            # if keys_pressed[K_LEFTBRACKET]:
            #     self.camera_sight *= 1.001 ** self.delta
            # if keys_pressed[K_RIGHTBRACKET]:
            #     self.camera_sight /= 1.001 ** self.delta
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
            if keys_pressed[K_RETURN]:
                self.camera_pos = self.tiles[self.now_tile if self.autoplay else self.player_now_tile]["pos"].copy()
        else:
            # 视野
            camera_sight = max(
                10.0, min(200.0, 500 / cbrt(self.tiles[self.now_tile]["bpm"]))
            )
            self.camera_sight += (camera_sight - self.camera_sight) / 1000 * self.delta
            # 位置
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

        if self.state == STATE_CHARTING:
            if self.active_tile != -1:
                tile = self.tiles[self.active_tile]
                text_list = [str(tile["angle"]) + "°"]
                if tile["midspin"]:
                    text_list.append("midspin")
                if tile["twirl"]:
                    text_list.append("twirl")
                if self.active_tile - 1 >= 0 and tile["bpm"] != self.tiles[self.active_tile - 1]["bpm"]:
                    text_list.append(str(tile["bpm"]) + "BPM")
                text = self.font_acc.render(" ".join(text_list), True, "#ffffff", "#000000")
                self.screen.blit(text, self.convert_pos(self.tiles[self.active_tile]["pos"]))

        elif self.state == STATE_PLAYING:
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
        if self.state == STATE_PLAYING:
            self.render_keyrain()

        pygame.display.flip()

    def render_text(self) -> None:
        self.screen.blit(
            self.text_title, self.text_title.get_rect(centerx=self.width // 2, y=50)
        )

        text_debug = self.font_debug.render(
            f"FPS: {self.clock.get_fps():.3f}/{self.FPS}",
            True,
            "#ffffff",
        )
        self.screen.blit(text_debug, (10, 10))
        if self.autoplay:
            self.screen.blit(self.text_autoplay, (10, 40))
        if self.state == STATE_PLAYING:
            tile_bpm = self.tiles[self.now_tile]['bpm']
            real_bpm = tile_bpm
            if self.now_tile == len(self.tiles) - 1:  # 结尾
                real_bpm /= (
                        self.tiles[self.now_tile]["beat"]
                        - self.tiles[self.now_tile - 1]["beat"]
                )
            elif self.now_tile != 0:  # 不是开头
                real_bpm /= (
                        self.tiles[self.now_tile + 1]["beat"]
                        - self.tiles[self.now_tile]["beat"]
                )
            if self.p + self.lp + self.ep + self.l + self.e + self.tl + self.te != 0:
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
            if self.timer < 0:
                minute = sec = 0
            else:
                minute = int((self.timer / 1000) / 60)
                sec = int(self.timer / 1000) % 60
            text_list = [
                "TileBPM: " + (f"{tile_bpm:.3f}".rjust(10)),
                "RealBPM: " + (f"{real_bpm:.3f}".rjust(10)),
                "KPS: " + (f"{real_bpm / 60:.3f}".rjust(10)),
                "XAcc: " + (f"{x_acc:.2f}%".rjust(10)),
                "Time: " + (f"{minute:0>2}:{sec:0>2}".rjust(10)),
            ]
        else:
            text_list = ["[Tips]", "Fullscreen: F11", "Autoplay: F12", "Play: Space", "Exit: Esc"]
        for i in range(len(text_list)):
            text = self.font_debug.render(
                text_list[i],
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
            ) if self.state == STATE_PLAYING else len(self.tiles) - 1
        # stop = len(self.tiles) - 1
        for index in range(stop, -1, -1):  # 倒序
            if not self.render_tile_check(index):
                continue

            if index + 1 < len(self.tiles):
                i = index + 1
                while i < len(self.tiles):
                    if not self.tiles[i]["midspin"]:
                        break
                    i += 1
                else:
                    i = index
            else:
                i = index

            tile = self.tiles[index]
            if index + 1 < len(self.tiles):
                next_tile = self.tiles[index + 1]
                hairclip = (
                        abs(tile["angle"] % 360 - next_tile["angle"] % 360) == 180
                )
            else:
                next_tile = None
                hairclip = False

            if index - 1 >= 0:
                last_tile = self.tiles[index - 1]
            else:
                last_tile = None

            
            border_color = tile["border_color"]
            color = tile["color"]
            if self.state == STATE_CHARTING:
                if self.active_tile != -1 and index == self.active_tile:
                    color = "#999999"

            alpha = 255
            if self.state == STATE_PLAYING:
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

            if next_tile and (tile["angle"] != next_tile["angle"] or next_tile["midspin"]):
                if tile["midspin"]:
                    half_sqr_border.fill(border_color[:7])
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
                        border_color[:7],
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
                        border_color[:7],
                        (length + border_length * 2, length + border_length * 2),
                        (length + border_length * 2) / 2,
                    )
                    if hairclip:
                        half_sqr_border.fill(border_color[:7])
                        new_half_sqr_border = pygame.transform.rotate(
                            half_sqr_border, next_tile["angle"]
                        )
                        surf_tile.blit(
                            new_half_sqr_border,
                            new_half_sqr_border.get_rect(
                                center=(
                                    length + border_length * 2,
                                    length + border_length * 2,
                                )
                                + length / 4 * move_step(-next_tile["angle"])
                            ),
                        )
                    else:
                        square_border.fill(border_color[:7])
                        if next_tile["midspin"]:
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
                                    - length / 2 * move_step2(-self.tiles[i]["angle"])
                                ),
                            )
                            new_square = pygame.transform.rotate(square, self.tiles[i]["angle"])
                            surf_tile.blit(
                                new_square,
                                new_square.get_rect(
                                    center=(
                                               length + border_length * 2,
                                               length + border_length * 2,
                                           )
                                           - length / 2 * move_step2(-self.tiles[i]["angle"])
                                ),
                            )
                            pygame.draw.circle(
                                surf_tile,
                                border_color[:7],
                                (length + border_length * 2, length + border_length * 2),
                                (length + border_length * 2) / 2,
                            )
                        new_square_border = pygame.transform.rotate(
                            square_border, next_tile["angle"]
                        )
                        surf_tile.blit(
                            new_square_border,
                            new_square_border.get_rect(
                                center=(
                                    length + border_length * 2,
                                    length + border_length * 2,
                                )
                                + length / 2 * move_step(-next_tile["angle"])
                            ),
                        )
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
                                - length / 2 * move_step(-tile["angle"])
                            ),
                        )

                if tile["midspin"]:
                    half_sqr.fill(color[:7])
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
                        color[:7],
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
                        color[:7],
                        (length + border_length * 2, length + border_length * 2),
                        length / 2,
                    )
                    if hairclip:
                        half_sqr.fill(color[:7])
                        new_half_sqr = pygame.transform.rotate(
                            half_sqr, tile["angle"]
                        )
                        surf_tile.blit(
                            new_half_sqr,
                            new_half_sqr.get_rect(
                                center=(
                                    length + border_length * 2,
                                    length + border_length * 2,
                                )
                                - length / 4 * move_step(-tile["angle"])
                            ),
                        )
                    else:
                        square.fill(color[:7])
                        new_square = pygame.transform.rotate(square, next_tile["angle"])
                        surf_tile.blit(
                            new_square,
                            new_square.get_rect(
                                center=(
                                    length + border_length * 2,
                                    length + border_length * 2,
                                )
                                + length / 2 * move_step(-(next_tile["angle"]))
                            ),
                        )
                        new_square = pygame.transform.rotate(
                            square, tile["angle"]
                        )
                        surf_tile.blit(
                            new_square,
                            new_square.get_rect(
                                center=(
                                    length + border_length * 2,
                                    length + border_length * 2,
                                )
                                - length / 2 * move_step(-tile["angle"])
                            ),
                        )
            else:
                rect_border.fill(border_color[:7])
                new_rect_border = pygame.transform.rotate(rect_border, next_tile["angle"] if next_tile else tile["angle"])
                surf_tile.blit(
                    new_rect_border,
                    new_rect_border.get_rect(
                        center=(length + border_length * 2, length + border_length * 2)
                    ),
                )
                rect.fill(color[:7])
                new_rect = pygame.transform.rotate(rect, next_tile["angle"] if next_tile else tile["angle"])
                surf_tile.blit(
                    new_rect,
                    new_rect.get_rect(
                        center=(length + border_length * 2, length + border_length * 2)
                    ),
                )

            new_surf_tile = surf_tile.copy()

            # 加/减速
            if last_tile and tile["bpm"] != last_tile["bpm"]:
                pygame.draw.circle(
                    new_surf_tile,
                    "#ff0000"
                    if last_tile["bpm"] < tile["bpm"]
                    else "#0000ff",
                    (length + border_length * 2, length + border_length * 2),
                    length / 2 * 0.6,
                )
            # 旋转
            if tile["twirl"]:
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
                pos = length * 2 * move_step(tile["angle"])
                pos.y *= -1
                self.screen.blit(
                    new_surf_tile,
                    new_surf_tile.get_rect(center=self.convert_pos(tile["pos"]) + pos)
                )
            else:
                self.screen.blit(
                    new_surf_tile,
                    new_surf_tile.get_rect(center=self.convert_pos(tile["pos"]))
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
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (2, 0),
            (3.5, 0),
            (5, 0),
            (4, 1),
            (5, 1),
            (6, 1),
            (7, 1),
        ]
        name = list("QWERV_NUIOP")

        # pos = [
        #     (0, 0),
        #     (1, 0),
        #     (0, 1),
        #     (1, 1),
        #     (2, 1),
        #     (3, 1),
        #     (2, 0),
        #     (3, 0),
        #     (4, 0),
        #     (5, 0),
        #     (4, 1),
        #     (5, 1),
        #     (6, 1),
        #     (7, 1),
        #     (6, 0),
        #     (7, 0)
        # ]
        # name = "LSft,Caps,Tab,1,2,E,C,_,RAlt,.,P,=,←,\\,Ret,RSft".split(",")
        if self.autoplay:
            if self.autoplay_keyrain and 0 <= self.timer < len(self.autoplay_keyrain[0]):
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
                (10 + pos[i][0] * 42, self.height - 10 - 40 - pos[i][1] * 42, 40, 40),
                0 if key_pressed[i] else 2,
            )
            text = self.font_debug.render(
                name[i], True, "#000000" if key_pressed[i] else "#ffffff"
            )
            if len(name[i]) > 1:
                text = pygame.transform.scale_by(text, 1 / math.sqrt(len(name[i])))
            self.screen.blit(
                text,
                text.get_rect(
                    center=(
                        (
                            10 + pos[i][0] * 42 + 20,
                            self.height - 10 - 40 - pos[i][1] * 42 + 20,
                        )
                    )
                ),
            )
        for i in range(len(self.keys)):
            for j in range(120):
                if self.keyrain[i][j] and pos[i][1]:
                    rect.fill((255, 255, 255, max(0, min(255, 1000 - j * 10))))
                    self.screen.blit(
                        rect, (10 + pos[i][0] * 42, self.height - 15 - 82 - j * 3)
                    )
        for i in range(len(self.keys)):
            for j in range(120):
                if self.keyrain[i][j] and not pos[i][1]:
                    small_rect.fill((255, 0, 255, max(0, min(255, 1000 - j * 10))))
                    self.screen.blit(
                        small_rect, (15 + pos[i][0] * 42, self.height - 15 - 82 - j * 3)
                    )

    def convert_pos(self, pos: Vec2, camera=True) -> Vec2:
        pos = pos.copy()
        if camera:
            pos -= self.camera_pos
        # pos = pos.x * move_step(90 - (self.camera_angle - 90)) + pos.y * move_step(0 - (self.camera_angle - 90))
        pos.x = pos.x * self.camera_sight + self.width // 2
        pos.y = pos.y * -self.camera_sight + self.height // 2
        return pos

    def convert_pos2(self, pos: Vec2, camera=True, screen=True) -> Vec2:
        pos = pos.copy()
        if screen:
            pos -= (self.width // 2, self.height // 2)
        pos.x /= self.camera_sight
        pos.y /= -self.camera_sight
        if camera:
            pos += self.camera_pos
        # pos = pos.x * move_step(90 - (self.camera_angle - 90)) + pos.y * move_step(0 - (self.camera_angle - 90))
        return pos

    def cleanup(self) -> None:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    path_to_beatmap = "2024/main.adofai"
    pitch = 100
    try:
        print("Adofai (Pygame ver.) 冰与火之舞 Pygame版 By Ckblt")
        print("支持按 Q W E R V 空格(Space) N U I O P 键")
        path_to_beatmap = input("输入谱面的路径 (Enter the path to the beatmap) : ")
        pitch = input("输入音高，默认100 (Enter the pitch) : ")
        if pitch == "":
            pitch = 100
        else:
            pitch = int(pitch)
    except ValueError:
        # traceback.print_exc()
        print("出错了！输入的音高不是整数。 (Please enter an integer)")
        input("按下回车键继续…… (Press the enter key to continue)")
        exit(1)

    try:
        print("加载中…… (Loading...)")
        theApp = App(path_to_beatmap, pitch)
        print("加载完成！你现在应该会看到一个Pygame窗口。 (Complete!)")
        theApp.execute()
    except (SystemExit, KeyboardInterrupt):
        pass
    except FileNotFoundError as e:
        traceback.print_exc()
        pygame.quit()
        print(
            f"出错了！我没有找到{e.filename}。这个错误可能是因为谱面的路径不对。 (Wrong path)"
        )
        input("按下回车键继续…… (Press the enter key to continue)")
    except:
        traceback.print_exc()
        pygame.quit()
        print("Error! 出错了！我不知道怎么错的，但就是出错了！具体出错情况如上。")
        input("按下回车键继续…… (Press the enter key to continue)")

"""
author: CkbltIsCoding
"""

import json
import math
import os
import sys
import time
import traceback
import re
from bisect import bisect_left, bisect_right
from copy import deepcopy
from tkinter import messagebox, filedialog, simpledialog
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
STATE_SELECTING = 3
STATE_LOADING = 4


class App:
    def __init__(self, _path_to_level: str, _pitch: int = 100) -> None:
        pygame.init()
        pygame.mixer.init()

        self.size = self.width, self.height = 1200, 800
        self.screen = pygame.display.set_mode(self.size, HWSURFACE | RESIZABLE)

        self.font_loading = pygame.font.SysFont("Consolas", 24)
        self.font_info = pygame.font.SysFont("Consolas", 24)
        self.font_title = pygame.font.SysFont("Dengxian", 36, True, True)
        self.font_acc = pygame.font.SysFont("Consolas", 18, True)

        self.music_path = ""
        self.offset = 0
        self.pitch = _pitch
        self.title = ""
        self.text_title = None

        self.path = _path_to_level
        self.level = None
        self.tiles = []
        self.bg_color = "#10131a"
        self.bg_image_path = ""
        self.orig_bg_image = None
        self.bg_image = None
        pygame.display.set_caption(
            "A dance of fire and ice (Pygame version) (Loading...)"
        )
        if self.path != "":
            self.process_data()
        pygame.display.set_caption("A dance of fire and ice (Pygame version)")

        self.running = True  # 是否运行
        self.fullscreen = False  # 全屏

        self.state = STATE_CHARTING if self.path else STATE_SELECTING  # 游戏状态
        self.pre_state = -1  # 上一帧的游戏状态

        # self.keys = [K_q, K_w, K_e, K_r, K_v, K_SPACE, K_n, K_u, K_i, K_o, K_p]  # 键
        self.keys = [K_LCTRL, K_CAPSLOCK, K_TAB, K_q, K_w, K_e, K_c, K_SPACE,
                     K_a, K_PERIOD, K_p, K_LEFTBRACKET, K_RIGHTBRACKET, K_BACKSLASH, K_RETURN, K_DOWN]  # 键
        self.key_pressed = [False for _ in range(len(self.keys))]
        self.key_rain = [[False for _ in range(120)] for _ in range(len(self.keys))]
        self.autoplay_key_rain = None
        if len(self.tiles) > 0:
            self.process_autoplay_key_rain()

        self.start_timer = 0
        if len(self.tiles) > 0:
            self.timer = -max(8 / self.tiles[0]["bpm"] * 60 * 1000, self.offset)
        else:
            self.timer = 0
        self.beat = 0
        self.player_beat = 0
        self.pre_beat = 0

        # 摄像机
        self.camera_pos = Vec2()
        self.camera_zoom = 100
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
        self.P = 25.0
        self.LEP = 30.0
        self.LE = 40.0

        self.clock = pygame.time.Clock()
        self.FPS = 120
        self.delta = 1

        self.keydown_event_count = 0

        self.text_autoplay = self.font_info.render("Autoplay", True, "#ffffff")

        self.text_tl = self.font_acc.render(
            "TL!!",
            True,
            "#ff0000",
        )
        self.text_l = self.font_acc.render(
            "Late!",
            True,
            "#ff6600",
        )
        self.text_lp = self.font_acc.render(
            "LP!",
            True,
            "#ffcc00",
        )
        self.text_p = self.font_acc.render(
            "P!",
            True,
            "#00ff00",
        )
        self.text_ep = self.font_acc.render(
            "EP!",
            True,
            "#ffcc00",
        )
        self.text_e = self.font_acc.render(
            "Early!",
            True,
            "#ff6600",
        )
        self.text_te = self.font_acc.render(
            "TE!!",
            True,
            "#ff0000",
        )

        self.dragging = False

        self.sound_ready = pygame.mixer.Sound("ready.wav")
        self.channel_ready = pygame.mixer.Channel(0)

        self.sound_beat = pygame.mixer.Sound("beat.wav")
        self.channel_beat = pygame.mixer.Channel(1)

        self.music_played = False

        self.init()

    def init(self):
        self.p = self.lp = self.ep = self.l = self.e = self.tl = self.te = 0
        self.keydown_event_count = 0
        self.timing = 0
        self.timing_offset = -40
        self.timing_list.clear()
        self.timing_sprites.clear()
        self.waiting_for_key = True
        self.key_pressed = [False for _ in range(len(self.keys))]
        self.key_rain = [[False for _ in range(120)] for _ in range(len(self.keys))]
        self.start_timer = 0
        if len(self.tiles) > 0:
            self.timer = -max(8 / self.tiles[0]["bpm"] * 60 * 1000, self.offset)
        else:
            self.timer = 0
        self.beat = 0
        self.player_beat = 0
        self.pre_beat = 0
        self.camera_pos = Vec2()
        self.camera_zoom = 100
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

    def process_data(self) -> bool:
        pygame.display.set_caption("A dance of fire and ice (Pygame version) (Loading...)")
        self.camera_pos = Vec2()
        self.camera_zoom = 100
        self.camera_angle = 0

        try:
            with open(
                    self.path, "r", encoding="utf-8-sig"
            ) as f:
                string = f.read()
                string = re.sub(",(?=\\s*?[}\\]])", "", string)  # 删除尾随逗号
                self.level = json.loads(string, strict=False)
        except UnicodeDecodeError:
            messagebox.showerror("错误", "该谱面似乎没有使用utf-8-sig编码，所以不能解析。")
            pygame.display.set_caption("A dance of fire and ice (Pygame version)")
            return False
        artist = re.sub("<[^>]*>", "", self.level["settings"]["artist"])
        song = re.sub("<[^>]*>", "", self.level["settings"]["song"])
        self.title = artist + (" - " if artist and song else "") + song
        self.offset = self.level["settings"]["offset"] * 100 / self.pitch + 50 * (
                100 / self.pitch - 1
        )
        self.bg_image_path = self.level["settings"]["bgImage"]
        if self.bg_image_path:
            self.orig_bg_image = pygame.image.load(
                os.path.join(os.path.dirname(self.path), self.bg_image_path)).convert()
            if self.orig_bg_image.get_size() != self.size:
                self.bg_image = pygame.transform.smoothscale(self.orig_bg_image, self.size)
            else:
                self.bg_image = self.orig_bg_image.copy()

        text_title_shadow = self.font_title.render(self.title, True, "#00000099")
        self.text_title = pygame.Surface(
            Vec2(text_title_shadow.get_size()) + (2, 2), SRCALPHA
        )
        self.text_title.blit(text_title_shadow, (2, 2))
        text_title = self.font_title.render(self.title, True, "#ffffff")
        self.text_title.blit(text_title, (0, 0))

        self.bg_color = "#" + self.level["settings"]["backgroundColor"]
        self.tiles = [{
            "angle": 0,
            "bpm": 0,
            "twirl": False,
            "orbit": CLOCKWISE,
            "midspin": False,
            "pause": 0,
            "pos": Vec2(),
            "ms": 0,
            "beat": 0,
            "color": [(0, "#" + self.level["settings"]["trackColor"])]
            if "trackColor" in self.level["settings"].keys()
            else "#debb7b",
            "border_color": [(0, "#" + self.level["settings"]["secondaryTrackColor"])]
            if "secondaryTrackColor" in self.level["settings"].keys()
            else "#443310",
            "actions": []
        }]
        path_data_dict = {'R': 0, 'p': 15, 'J': 30, 'E': 45, 'T': 60, 'o': 75, 'U': 90, 'q': 105, 'G': 120, 'Q': 135,
                          'H': 150, 'W': 165, 'L': 180, 'x': 195, 'N': 210, 'Z': 225, 'F': 240, 'V': 255, 'D': 270,
                          'Y': 285, 'B': 300, 'C': 315, 'M': 330, 'A': 345, '5': 555, '6': 666, '7': 777, '8': 888,
                          '!': 999}
        for index in range(len(self.level["angleData"] if "angleData" in self.level else self.level["pathData"])):
            if "angleData" in self.level:
                angle = self.level["angleData"][index]
            elif "pathData" in self.level:
                angle = path_data_dict[self.level["pathData"][index]]
            else:
                messagebox.showerror("错误", "该谱面没有 angleData 或者 pathData，所以不能解析。")
                self.level = None
                self.title = ""
                self.offset = 0
                self.text_title = None
                self.tiles.clear()
                return False

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
                    "color": [(0, "#" + self.level["settings"]["trackColor"])]
                    if "trackColor" in self.level["settings"].keys()
                    else [(0, "#debb7b")],
                    "border_color": [(0, "#" + self.level["settings"]["secondaryTrackColor"])]
                    if "secondaryTrackColor" in self.level["settings"].keys()
                    else [(0, "#443310")],
                    "actions": [],
                }
            )

        self.tiles[0]["bpm"] = self.level["settings"]["bpm"] * self.pitch / 100
        cnt999 = 0

        for action in self.level["actions"]:
            try:
                tile = self.tiles[action["floor"]]
                if tile["angle"] == 999:
                    tile = self.tiles[action["floor"] - 1]
                    cnt999 += 1
                match action["eventType"]:
                    case "SetSpeed":
                        if "speedType" not in action or action["speedType"] == "Bpm":
                            tile["bpm"] = action["beatsPerMinute"] * self.pitch / 100
                        elif action["speedType"] == "Multiplier":
                            tile["bpm"] = -action["bpmMultiplier"]
                    case "Twirl":
                        tile["twirl"] = True
                    case "Pause":
                        tile["pause"] = action["duration"]
                    case "RecolorTrack":
                        a = deepcopy(action)
                        a["floor"] -= cnt999
                        tile["actions"].append(a)
                    case "MoveCamera":
                        a = deepcopy(action)
                        a["floor"] -= cnt999
                        tile["actions"].append(a)
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

            tile["actions"] = sorted(tile["actions"],
                                     key=lambda action: action["duration"] if "duration" in action else -1)

        for tile in self.tiles:
            for action in tile["actions"]:
                if action["eventType"] == "RecolorTrack":
                    a = action["startTile"][0]
                    if action["startTile"][1] == "Start":
                        pass
                    elif action["startTile"][1] == "ThisTile":
                        a += action["floor"]
                    elif action["startTile"][1] == "End":
                        a += len(self.tiles)
                    b = action["endTile"][0]
                    if action["endTile"][1] == "Start":
                        pass
                    elif action["endTile"][1] == "ThisTile":
                        b += action["floor"]
                    elif action["endTile"][1] == "End":
                        b += len(self.tiles)
                    try:
                        for i in range(a, b + 1):
                            self.tiles[i]["color"].append((tile["beat"], "#" + action["trackColor"]))
                            self.tiles[i]["border_color"].append((tile["beat"],
                                                                 "#" + action["secondaryTrackColor"]))
                    except IndexError:
                        pass

        if (
                "songFilename" in self.level["settings"].keys()
                and self.level["settings"]["songFilename"] != ""
        ):
            self.music_path = os.path.join(
                os.path.dirname(self.path), self.level["settings"]["songFilename"]
            )
            out_file = str(self.pitch) + " " + os.path.splitext(os.path.split(self.music_path)[1])[0] + ".wav"
            out_file = os.path.join(os.path.split(self.music_path)[0], out_file)
            if self.pitch != 100:
                if not os.path.exists(out_file):
                    music.change_speed(self.music_path, out_file, self.pitch / 100)
                self.music_path = out_file
            out_file = "(new) " + os.path.splitext(os.path.split(self.music_path)[1])[0] + ".wav"
            out_file = os.path.join(os.path.split(self.music_path)[0], out_file)
            if not os.path.exists(out_file):
                if not music.add_sound(self.music_path, out_file, self.offset, [tile["ms"] for tile in self.tiles],
                                       self.process_data_render_callback):
                    pass
            self.music_path = out_file

            pygame.mixer_music.load(self.music_path)
            pygame.mixer_music.set_volume(0.3)
        else:
            out_file = str(self.pitch) + " " + os.path.splitext(os.path.split(self.path)[1])[0] + ".wav"
            out_file = os.path.join(os.path.split(self.path)[0], out_file)
            self.music_path = out_file
            if (not os.path.exists(self.music_path)
                    and not music.add_sound("", out_file, self.offset, [tile["ms"] for tile in self.tiles],
                                            self.process_data_render_callback)):
                pass
                # return False
            pygame.mixer_music.load(self.music_path)
            pygame.mixer_music.set_volume(0.3)

        pygame.display.set_caption("A dance of fire and ice (Pygame version)")

        return True

    def process_data_render_callback(self, ratio):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                return False
            if event.type == KEYDOWN:
                if event.dict["key"] == K_ESCAPE:
                    return False
        self.screen.fill("#000000")
        text = self.font_loading.render(f"Adding hit sounds... ({ratio * 100:.2f}%) (Press Esc to give up)",
                                        True,
                                        "#ffffff")
        self.screen.blit(text, text.get_rect(center=(self.width / 2, self.height / 2)))
        max_width, height = 300, 50
        width = max_width * ratio
        x, y = self.width / 2 - max_width / 2, self.height / 2 - height / 2 + 100
        pygame.draw.rect(self.screen, "#cccccc", (x, y, width, height))
        pygame.draw.rect(self.screen, "#ffffff", (x, y, max_width, height), 5)
        pygame.display.flip()
        self.clock.tick()
        return True

    def process_autoplay_key_rain(self):
        self.autoplay_key_rain = [[False for _ in range(round(self.tiles[-1]["ms"]) + 1000)].copy() for _ in self.keys]
        min_ms = 62
        max_ms = 125
        bpm = 2021
        limit_ms = 60 / bpm * 1000
        while limit_ms <= min_ms:
            limit_ms *= 2
        while limit_ms > max_ms:
            limit_ms /= 2
        bpm_change = []
        for index in range(len(self.tiles[2:])):
            tile_bpm = self.tiles[index]["bpm"]
            last_bpm = self.tiles[index - 1]["bpm"]
            if (tile_bpm % (bpm / 2) == 0 or bpm % tile_bpm == 0) and not (
                    last_bpm % (bpm / 2) == 0 or bpm % last_bpm == 0):
                bpm_change.append(index)
        count = 0
        right = True
        last_ms = 0
        for index in range(1, len(self.tiles)):
            tile = self.tiles[index]
            tile_ms = round(tile["ms"])
            if index in bpm_change:
                count = 0
                last_ms = tile["ms"]
            if tile_ms - self.tiles[index - 1]["ms"] >= limit_ms:
                count = 0
            if ((tile["ms"] - last_ms) / limit_ms % 2 < 1 and not right or
                    (tile["ms"] - last_ms) / limit_ms % 2 >= 1 and right):
                count = 0
                right = not right
            for ms in range(tile_ms, tile_ms + 100):
                if right:
                    if count < 4:
                        self.autoplay_key_rain[count + 10][ms] = True
                    elif count < 6:
                        self.autoplay_key_rain[count - 4 + 8][ms] = True
                    elif count < 8:
                        self.autoplay_key_rain[count - 6 + 14][ms] = True
                else:
                    if count < 4:
                        self.autoplay_key_rain[5 - count][ms] = True
                    elif count < 6:
                        self.autoplay_key_rain[7 - count + 4][ms] = True
                    elif count < 8:
                        self.autoplay_key_rain[1 - count + 6][ms] = True
            count += 1

    def process_autoplay_key_rain_old(self):
        self.autoplay_key_rain = [[False for _ in range(round(self.tiles[-1]["ms"]) + 1000)].copy() for _ in self.keys]
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
        #     bpm_change_index = bpm_change[bisect_right(bpm_change, index) - 1]
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
        #                 self.autoplay_key_rain[7 + count][i] = True
        #             elif count < 6:
        #                 self.autoplay_key_rain[4 + count][i] = True
        #     else:
        #         if right:
        #             right = False
        #             count = 0
        #         for i in range(round(tile["ms"]), round(tile["ms"]) + 30):
        #             if count < 4:
        #                 self.autoplay_key_rain[3 - count][i] = True
        #             elif count < 6:
        #                 self.autoplay_key_rain[4 - count][i] = True
        #
        #     count += 1
        rev = False
        right = True
        count = 0
        p_index = 0
        yk = False
        for i in range(round(self.tiles[-1]["ms"]) + 1000):
            if i < self.tiles[-1]["ms"]:
                index = bisect_right(self.tiles, i, key=lambda x: x["ms"]) - 1
            else:
                index = len(self.tiles) - 1
            bpm_change_index = bpm_change[bisect_right(bpm_change, index) - 1]
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
            if (i - self.tiles[bpm_change_index]["ms"]) % ms < ms / 2 and not rev or \
                    (i - self.tiles[bpm_change_index]["ms"]) % ms >= ms / 2 and rev:
                if not right:
                    right = True
                    count = 0
                if p_index != index:
                    for j in range(i, i + min(100, int(ms / 2.1))):
                        # if count < 4:
                        #     self.autoplay_key_rain[7 + count][j] = True
                        # elif count < 6:
                        #     self.autoplay_key_rain[5 + count - 4][j] = True
                        if count < 4:
                            self.autoplay_key_rain[10 + count][j] = True
                        elif count < 6:
                            self.autoplay_key_rain[8 + count - 4][j] = True
                        elif count < 8:
                            self.autoplay_key_rain[14 + count - 6][j] = True
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
                        #     self.autoplay_key_rain[3 - count][j] = True
                        # elif count < 6:
                        #     self.autoplay_key_rain[5 - (count - 4)][j] = True
                        if count < 4:
                            self.autoplay_key_rain[5 - count][j] = True
                        elif count < 6:
                            self.autoplay_key_rain[7 - count + 4][j] = True
                        elif count < 8:
                            self.autoplay_key_rain[1 - count + 6][j] = True
                        else:
                            rev = not rev
                            right = True
                            count = -1
                        # else:
                        #     print(index)
                        #     raise Exception()
                    count += 1
            p_index = index

        self.autoplay_key_rain = tuple(self.autoplay_key_rain)

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

        if event.type == WINDOWRESIZED:  # 重新设置窗口大小
            self.size = self.width, self.height = event.dict["x"], event.dict["y"]
            if self.bg_image_path and self.bg_image.get_size() != self.size:
                self.bg_image = pygame.transform.smoothscale(self.bg_image, self.size)

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
                if self.bg_image_path and self.bg_image.get_size() != self.size:
                    self.bg_image = pygame.transform.smoothscale(self.bg_image, self.size)
            elif event.dict["key"] == K_F12:  # 自动播放开关
                self.autoplay = not self.autoplay

            if self.state == STATE_PLAYING:
                if event.dict["key"] in self.keys:  # 打的键
                    self.keydown_event_count += 1
                    self.key_pressed[self.keys.index(event.dict["key"])] = True
                elif event.dict["key"] == K_ESCAPE:  # 回到编辑模式
                    pygame.mixer_music.stop()
                    self.timing_list.clear()
                    self.timing_sprites.clear()
                    self.timer = self.beat = 0
                    self.camera_angle = 0
                    self.state = STATE_CHARTING
            elif self.state == STATE_CHARTING:
                # angles45 = {K_d: 0, K_e: 45, K_w: 90, K_q: 135, K_a: 180, K_z: 225, K_s: 270, K_c: 315}

                if event.dict["key"] == K_ESCAPE:  # 退出程序
                    self.running = False
                elif event.dict["key"] == K_SPACE:  # 打谱模式
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
                        self.timer = round(self.tiles[self.active_tile]["ms"])
                elif event.dict["key"] == K_RIGHT:
                    if self.active_tile != -1 and self.active_tile + 1 < len(self.tiles):
                        self.active_tile += 1
                elif event.dict["key"] == K_LEFT:
                    if self.active_tile != -1:
                        self.active_tile -= 1
                elif event.dict["key"] == K_RETURN:  # 打开 .adofai 文件
                    file = filedialog.askopenfilename(defaultextension=".adofai")
                    if file:
                        self.path = file
                        self.process_data()
                elif event.dict["key"] == K_p:
                    flag = False
                    str_pitch = ""
                    while not str_pitch.isdigit():
                        if flag:
                            str_pitch = simpledialog.askstring("输入音高", "输入不是整数，请重新输入音高")
                        else:
                            str_pitch = simpledialog.askstring("输入音高", "请输入音高")
                        if str_pitch is None:
                            return
                        flag = True
                    self.pitch = int(str_pitch)
                    self.process_data()

                # elif event.dict["key"] in angles45:
                #     if self.active_tile != -1:
                #         self.add_tile(angles45[event.dict["key"]])

            elif self.state == STATE_SELECTING:
                if event.dict["key"] == K_RETURN:  # 打开 .adofai 文件
                    file = filedialog.askopenfilename(defaultextension=".adofai")
                    if file != "":
                        self.path = file
                        if self.process_data():
                            self.state = STATE_CHARTING

        if event.type == KEYUP:
            if event.dict["key"] in self.keys:
                self.key_pressed[self.keys.index(event.dict["key"])] = False

        if event.type == MOUSEBUTTONDOWN:
            if self.state == STATE_CHARTING:
                if event.dict["button"] == 1:
                    pos = self.conv_pos2world(Vec2(pygame.mouse.get_pos()))
                    for index in range(len(self.tiles)):
                        if pos.distance_squared_to(self.tiles[index]["pos"]) <= 0.5:
                            self.active_tile = index
                            break
                    else:
                        self.active_tile = -1
                        self.dragging = True
                        pygame.mouse.get_rel()
                elif event.dict["button"] == 4:
                    self.camera_zoom /= 1.1
                elif event.dict["button"] == 5:
                    self.camera_zoom *= 1.1

    def add_tile(self, angle):
        tile = self.tiles[self.active_tile]
        if (angle - tile["angle"]) % 360 == 180:
            if self.active_tile != 0:
                del self.tiles[self.active_tile]
                self.active_tile -= 1
        else:
            self.tiles.insert(self.active_tile + 1, {
                "angle": angle,
                "bpm": tile["bpm"],
                "twirl": False,
                "orbit": tile["orbit"],
                "midspin": False,
                "pause": 0,
                "pos": Vec2(),
                "ms": 0,
                "beat": 0,
                "color": "#" + self.level["settings"]["trackColor"]
                if "trackColor" in self.level["settings"].keys()
                else "#debb7b",
                "border_color": "#" + self.level["settings"]["secondaryTrackColor"]
                if "secondaryTrackColor" in self.level["settings"].keys()
                else "#443310",
            })
            self.active_tile += 1
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

    def loop(self) -> None:
        global STATE_PLAYING

        self.delta = self.clock.get_time()

        if self.state == STATE_PLAYING:
            # 计时器和音乐
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
                        pygame.mixer_music.rewind()
                        pygame.mixer_music.set_pos(self.offset / 1000 + self.tiles[self.active_tile]["ms"] / 1000)
                    elif -self.offset < self.timer <= 0 or self.offset == 0:
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
                for i in range(self.now_tile - self.pre_tile):
                    if self.autoplay:
                        self.timing_list.append([self.timing, 0])
                        self.judge()
                # self.channel_beat.play(self.sound_beat)  # 打的声音

            if not self.autoplay:  # 错过判定
                MS = 60 / min(500, self.tiles[self.player_now_tile]["bpm"]) * 1000
                LE = MS / 3
                LE = max(self.LE, LE)
                while (
                        self.timing > LE and self.player_now_tile < len(self.tiles) - 1
                ):
                    self.player_now_tile += 1
                    self.tl += 1
                    self.timing_list.append([LE + 5, 0])
                    pos = self.planet1_pos if self.planet_static != 1 else self.planet2_pos
                    self.timing_sprites.append(["TL!!", pos, 0])

                    self.calc_beat()
                    if self.player_now_tile + 1 < len(self.tiles):
                        self.timing = (
                                self.timer
                                - self.tiles[self.player_now_tile + 1]["ms"]
                                + self.timing_offset
                        )
                    MS = 60 / min(500, self.tiles[self.player_now_tile]["bpm"]) * 1000
                    LE = MS / 3
                    LE = max(self.LE, LE)

            # 打键的判定
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

            # Timing 列表和角色的处理
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

            # 键雨
            for i in range(len(self.key_rain)):
                self.key_rain[i].pop()
                if self.autoplay and self.autoplay_key_rain:
                    if 0 <= self.timer < len(self.autoplay_key_rain[0]):
                        self.key_rain[i].insert(0, self.autoplay_key_rain[i][self.timer])
                    else:
                        self.key_rain[i].insert(0, False)
                else:
                    self.key_rain[i].insert(0, self.key_pressed[i])

            self.pre_beat = self.beat
            self.pre_tile = self.now_tile
            self.player_pre_tile = self.player_now_tile
            self.pre_state = self.state
        elif self.state == STATE_CHARTING:
            self.camera()
            if pygame.mouse.get_pressed()[0] and self.dragging:  # 用鼠标移动摄像机
                rel = pygame.mouse.get_rel()
                self.camera_pos -= self.conv_pos2world(Vec2(rel), False, False)
            else:
                self.dragging = False

    def keydown_event(self) -> None:
        if self.waiting_for_key:
            if self.active_tile <= 0:
                self.start_timer = time.time()
            else:
                self.start_timer = time.time() - self.tiles[self.active_tile]["ms"] / 1000 + self.offset / 1000
                self.timer = self.start_timer
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
        MS = 60 / min(500, self.tiles[self.player_now_tile]["bpm"]) * 1000
        P = MS / 6
        LEP = MS / 4
        LE = MS / 3
        P = max(self.P, P)
        LEP = max(self.LEP, LEP)
        LE = max(self.LE, LE)
        if abs(self.timing) <= P:
            self.p += 1
            # self.timing_sprites.append(["P!", pos, 0])
        elif abs(self.timing) <= LEP:
            if self.timing > 0:
                self.lp += 1
                self.timing_sprites.append(["LP!", pos, 0])
            else:
                self.ep += 1
                self.timing_sprites.append(["EP!", pos, 0])
        elif abs(self.timing) <= LE:
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
                self.timing_list.append([-LE - 5, 0])
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
            self.now_tile = bisect_right(self.tiles, self.timer, key=lambda tile: tile["ms"])

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
        if self.state == STATE_CHARTING:
            pass
        elif self.state == STATE_PLAYING:
            # camera_sight = cbrt(self.tiles[self.now_tile]["bpm"]) / 500
            # camera_sight = max(20.0, min(camera_sight, 200.0))
            # self.camera_zoom += (camera_sight - self.camera_zoom) / 1000 * self.delta
            for tile in self.tiles:
                if self.beat < tile["beat"]:
                    break
                for action in tile["actions"]:
                    if action["eventType"] != "MoveCamera":
                        continue
                    # TODO: 适配MoveCamera事件的摄像机位置
                    if action["duration"] != 0 and self.beat - tile["beat"] < action["duration"]:
                        # if "position" in event and "relativeTo" in event:
                        #     if event["relativeTo"] == "Tile":
                        #         self.camera_pos = self.camera_pos + (Vec2(tile["pos"] + event["position"]) - self.camera_pos) * (
                        #             self.beat - tile["beat"]) / event["duration"]
                        #     elif event["relativeTo"] == "Player":
                        #         tile = self.tiles[self.now_tile]
                        #         if self.now_tile + 1 < len(self.tiles):
                        #             next_tile = self.tiles[self.now_tile + 1]
                        #             if next_tile["beat"] - tile["beat"] == 0:
                        #                 self.camera_pos = tile["pos"] + event["position"]
                        #             else:
                        #                 self.camera_pos = tile["pos"] + (next_tile["pos"] - tile["pos"]) * (
                        #                         self.beat - tile["beat"]) / (
                        #                                           next_tile["beat"] - tile["beat"]) + event["position"]
                        #         else:
                        #             self.camera_pos = tile["pos"] + event["position"]
                        if "zoom" in action:
                            self.camera_zoom = self.camera_zoom + (action["zoom"] - self.camera_zoom) * (
                                    self.beat - tile["beat"]) / action["duration"]
                        if "rotation" in action:
                            self.camera_angle = self.camera_angle + (action["rotation"] - self.camera_angle) * (
                                    self.beat - tile["beat"]) / action["duration"]
                    else:
                        # if "position" in event and "relativeTo" in event:
                        #     if event["relativeTo"] == "Tile":
                        #         self.camera_pos = Vec2(tile["pos"] + event["position"])
                        #     elif event["relativeTo"] == "Player":
                        #         tile = self.tiles[self.now_tile]
                        #         if self.now_tile + 1 < len(self.tiles):
                        #             next_tile = self.tiles[self.now_tile + 1]
                        #             if next_tile["beat"] - tile["beat"] == 0:
                        #                 self.camera_pos = tile["pos"] + event["position"]
                        #             else:
                        #                 self.camera_pos = tile["pos"] + (next_tile["pos"] - tile["pos"]) * (
                        #                         self.beat - tile["beat"]) / (
                        #                                           next_tile["beat"] - tile["beat"]) + event["position"]
                        #         else:
                        #             self.camera_pos = tile["pos"] + event["position"]
                        if "zoom" in action:
                            self.camera_zoom = action["zoom"]
                        if "rotation" in action:
                            self.camera_angle = action["rotation"]

            # 位置
            self.camera_pos += (
                                       self.tiles[self.now_tile]["pos"]
                                       - self.camera_pos
                               ) / (
                                       (self.tiles[self.now_tile]["bpm"] + 10000)
                                       / self.tiles[self.now_tile]["bpm"]
                               )
            # self.camera_pos = self.tiles[self.now_tile]["pos"].copy()
        elif self.state == STATE_SELECTING:
            pass

        # 防止缩放过大导致卡死
        self.camera_zoom = max(10, self.camera_zoom)

    def render(self) -> None:
        self.screen.fill(self.bg_color)
        if self.bg_image_path:
            self.screen.blit(self.bg_image, (0, 0))

        if self.state == STATE_CHARTING:
            self.render_tiles()
            # 砖块提示
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
                self.screen.blit(text, self.conv_pos2screen(self.tiles[self.active_tile]["pos"]))

        elif self.state == STATE_PLAYING:
            self.render_tiles()
            # 绘制行星
            pygame.draw.circle(
                self.screen,
                "#ff3333",
                self.conv_pos2screen(self.planet1_pos),
                self.planet_size * 19000 / self.camera_zoom / 2,
            )
            if not self.waiting_for_key:
                pygame.draw.circle(
                    self.screen,
                    "#3366ff",
                    self.conv_pos2screen(self.planet2_pos),
                    self.planet_size * 19000 / self.camera_zoom / 2,
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
                pos = self.conv_pos2screen(sprite[1])
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
                text = pygame.transform.scale_by(text, 190 / self.camera_zoom * 2)
                self.screen.blit(text, text.get_rect(center=pos))

            self.render_hit_margin()
            self.render_key_rain()
        elif self.state == STATE_SELECTING:
            pass

        self.render_text()

        pygame.display.flip()

    def render_hit_margin(self):
        MS = 60 / min(500, self.tiles[self.player_now_tile]["bpm"]) * 1000
        P = MS / 6
        LEP = MS / 4
        LE = MS / 3
        P = max(self.P, P)
        LEP = max(self.LEP, LEP)
        LE = max(self.LE, LE)
        # 绘制准度条
        pygame.draw.rect(
            self.screen,
            "#ff0000",
            (
                self.width // 2 - LE * 2 - 20,
                self.height - 40,
                LE * 4 + 40,
                30,
            ),
        )
        pygame.draw.rect(
            self.screen,
            "#ffcc00",
            (self.width // 2 - LE * 2, self.height - 40, LE * 4, 30),
        )
        pygame.draw.rect(
            self.screen,
            "#ffff00",
            (self.width // 2 - LEP * 2, self.height - 40, LEP * 4, 30),
        )
        pygame.draw.rect(
            self.screen,
            "#00ff00",
            (self.width // 2 - P * 2, self.height - 40, P * 4, 30),
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
        text = f"{self.te} {self.e} {self.ep} {self.p} {self.lp} {self.l} {self.tl}"
        if len(self.timing_list) != 0:
            text += f" Timing: {self.timing_list[-1][0]:.2f}ms"
        text_cnt = self.font_info.render(
            text,
            True,
            "#ffffff",
        )
        self.screen.blit(
            text_cnt,
            text_cnt.get_rect(centerx=self.width // 2, bottom=self.height - 40),
        )

    def render_text(self) -> None:
        if self.text_title:
            self.screen.blit(
                self.text_title, self.text_title.get_rect(centerx=self.width // 2, y=50)
            )

        # 左边的文字
        text_info = self.font_info.render(
            f"FPS: {self.clock.get_fps():.3f}/{self.FPS}",
            True,
            "#ffffff",
        )
        self.screen.blit(text_info, (10, 10))
        if self.autoplay:
            self.screen.blit(self.text_autoplay, (10, 40))

        # 右边的文字
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
        elif self.state == STATE_CHARTING:
            text_list = ["[Tips]", "Fullscreen: F11", "Autoplay: F12", "Play: Space", "Exit: Esc", "Pitch: P"]
        elif self.state == STATE_SELECTING:
            text_list = ["Please select a level!", "Press the ENTER key to select."]
        else:
            text_list = []
        for i in range(len(text_list)):
            text = self.font_info.render(
                text_list[i],
                True,
                "#ffffff",
            )
            self.screen.blit(
                text, text.get_rect(top=10 + 30 * i, right=self.width - 10)
            )

    def render_tiles(self) -> None:
        orig_length = self.planet_size * 19000 / self.camera_zoom
        global world_cam_border_1, world_cam_border_2
        world_cam_border_1 = self.conv_pos2world(Vec2(-orig_length, -orig_length))
        world_cam_border_2 = self.conv_pos2world(Vec2(self.width + orig_length, self.height + orig_length))

        max_length = 80
        length = min(orig_length, max_length)

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

        memory = {}  # 没多大卵用的东西

        # start = -1
        start = bisect_left(self.tiles, self.timer - 2000, key=lambda tile: tile["ms"]) - 1 - 1
        start = max(-1, min(start, len(self.tiles) - 1 - 1))
        stop = min(
            len(self.tiles) - 1,
            (self.now_tile if self.autoplay else self.player_now_tile) + 256,
        ) if self.state == STATE_PLAYING else len(self.tiles) - 1
        # stop = len(self.tiles) - 1
        for index in range(stop, start, -1):  # 倒序
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

            border_color = tile["border_color"][bisect_left(tile["border_color"], self.beat, key=lambda a: a[0]) - 1][1]
            color = tile["color"][bisect_left(tile["color"], self.beat, key=lambda a: a[0]) - 1][1]
            if self.state == STATE_CHARTING:
                if self.active_tile != -1 and index == self.active_tile:
                    color = "#999999"  # 选中的砖块呈现灰色

            alpha = 255
            if self.state == STATE_PLAYING:
                if index < (
                        self.now_tile if self.autoplay else self.player_now_tile
                ):  # 消失动画
                    alpha = 255 - (
                            self.timer - (self.tiles[index + 1]["ms"] if index != 0 else 0) - 200
                    )
                    # alpha = 255 - (
                    #         self.timer - (self.tiles[index]["ms"] if index != 0 else 0)
                    # )
                    if alpha <= 0:
                        break
                else:  # 出现动画
                    if index == 0:
                        alpha = 255
                    else:
                        alpha = 255 - (self.tiles[index]["ms"] - self.timer - 1000)
                        if alpha <= 0:
                            continue

            if next_tile:
                key = tile["angle"], next_tile["angle"], color, border_color
            else:
                key = tile["angle"], tile["angle"], color, border_color
            if key in memory and not tile["midspin"] and not next_tile["midspin"]:
                surf_tile = memory[key]
            else:
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
                                square.fill(color[:7])
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
                    new_rect_border = pygame.transform.rotate(rect_border,
                                                              next_tile["angle"] if next_tile else tile["angle"])
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
                # memory[key] = surf_tile  # 麻痹的 还有bug 干脆不用了

            new_surf_tile = surf_tile.copy()

            # 加/减速标志
            if last_tile and tile["bpm"] != last_tile["bpm"]:
                pygame.draw.circle(
                    new_surf_tile,
                    "#ff0000"
                    if last_tile["bpm"] < tile["bpm"]
                    else "#0000ff",
                    (length + border_length * 2, length + border_length * 2),
                    length / 2 * 0.6,
                )
            # 旋转标志
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

            # 旋转砖块
            new_surf_tile = pygame.transform.rotate(
                new_surf_tile, -self.camera_angle
            )
            # 缩放砖块
            if orig_length > max_length:
                new_surf_tile = pygame.transform.scale_by(new_surf_tile, orig_length / max_length)
            # 显示砖块
            if tile["midspin"]:
                pos = orig_length * 2 * move_step(tile["angle"] - self.camera_angle)
                pos.y *= -1
                self.screen.blit(
                    new_surf_tile,
                    new_surf_tile.get_rect(center=self.conv_pos2screen(tile["pos"]) + pos)
                )
            else:
                self.screen.blit(
                    new_surf_tile,
                    new_surf_tile.get_rect(center=self.conv_pos2screen(tile["pos"]))
                )

    def render_tile_check(self, index: int) -> bool:
        # if index < (self.now_tile if self.autoplay else self.player_now_tile):
        #     return False

        tile = self.tiles[index]

        if self.camera_angle % 90 != 0:  # 摄像机角度不是正的 就用这个判定砖块是否出现
            length = self.planet_size * 19000 / self.camera_zoom
            pos = self.conv_pos2screen(tile["pos"])
            if not (-length <= pos.x <= self.width + length and
                    -length <= pos.y <= self.height + length):
                return False
        else:  # 摄像机角度是正的 就用这个判定砖块是否出现
            global world_cam_border_1, world_cam_border_2
            min_x = min(world_cam_border_1.x, world_cam_border_2.x)
            max_x = max(world_cam_border_1.x, world_cam_border_2.x)
            min_y = min(world_cam_border_1.y, world_cam_border_2.y)
            max_y = max(world_cam_border_1.y, world_cam_border_2.y)
            x, y = tile["pos"]
            if not (min_x <= x <= max_x and min_y <= y <= max_y):
                return False

        return True


    def render_key_rain(self):
        rect = pygame.Surface((40, 3), SRCALPHA)
        small_rect = pygame.Surface((20, 3), SRCALPHA)
        pos = [
            (0, 0),
            (1, 0),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (2, 0),
            (3, 0),
            (4, 0),
            (5, 0),
            (4, 1),
            (5, 1),
            (6, 1),
            (7, 1),
            (6, 0),
            (7, 0)
        ]
        # name = "LSft,Caps,Tab,1,2,E,C,_,RAlt,.,P,=,←,\\,Ret,RSft".split(",")
        name = ["" for _ in range(16)]
        if self.autoplay:
            if self.autoplay_key_rain and 0 <= self.timer < len(self.autoplay_key_rain[0]):
                key_pressed = []
                for index in range(len(self.keys)):
                    key_pressed.append(self.autoplay_key_rain[index][self.timer])
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
            text = self.font_info.render(
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
                if self.key_rain[i][j] and pos[i][1]:
                    rect.fill((255, 255, 255, max(0, min(255, 1000 - j * 10))))
                    self.screen.blit(
                        rect, (10 + pos[i][0] * 42, self.height - 15 - 82 - j * 3)
                    )
        for i in range(len(self.keys)):
            for j in range(120):
                if self.key_rain[i][j] and not pos[i][1]:
                    small_rect.fill((255, 0, 255, max(0, min(255, 1000 - j * 10))))
                    self.screen.blit(
                        small_rect, (20 + pos[i][0] * 42, self.height - 15 - 82 - j * 3)
                    )


    def conv_pos2screen(self, pos: Vec2, camera=True, screen=True) -> Vec2:
        pos = pos.copy()
        if camera:
            pos -= self.camera_pos
        pos = pos.rotate(-self.camera_angle)
        pos.x /= self.camera_zoom / 19000
        pos.y /= -self.camera_zoom / 19000
        if screen:
            pos += (self.width // 2, self.height // 2)
        return pos


    def conv_pos2world(self, pos: Vec2, camera=True, screen=True) -> Vec2:
        pos = pos.copy()
        if screen:
            pos -= (self.width // 2, self.height // 2)
        pos.x *= self.camera_zoom / 19000
        pos.y *= -self.camera_zoom / 19000
        pos = pos.rotate(self.camera_angle)
        if camera:
            pos += self.camera_pos
        return pos


    def cleanup(self) -> None:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    debugging = False

    if not debugging:
        path_to_level = ""
    else:
        path_to_level = "Levels/2021/fixed.adofai"
    pitch = 100

    try:
        theApp = App(path_to_level, pitch)
        theApp.execute()
    except (SystemExit, KeyboardInterrupt):
        pass
    except FileNotFoundError as e:
        # traceback.print_exc()
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

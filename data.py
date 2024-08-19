class TileData(dict):
    def __init__(self, **kwargs):
        super().__init__(self)
        self["ang"] = kwargs.get("ang", 180)
        self["rot"] = kwargs.get("rot", False)
        self["bpm"] = kwargs.get("bpm", -1)
        self["x"] = kwargs.get("x", 0)
        self["y"] = kwargs.get("y", 0)
        self["color"] = kwargs.get("color", "#ffffff")


data = {"title": "Ludicin - Fallen Symphony", "delay": round(7 * 60 / 125 * 1000) + 70, "content": [TileData(bpm=125)]}


def tile(**kwargs):
    data["content"].append(TileData(**kwargs))


def pseudo(_type, _ang):
    data["content"].append(TileData(ang=_ang, rot=_type == 2 or _type == 4))
    data["content"].append(TileData(ang=180 - _ang, rot=_type == 3 or _type == 4))


def pseudo3(_ang):
    data["content"].append(TileData(ang=_ang))
    data["content"].append(TileData(ang=_ang))
    data["content"].append(TileData(ang=180 - _ang * 2))


pseudo(3, 15)
tile()
for i in range(4): pseudo(3, 15)
tile()
for i in range(2): pseudo(3, 15)
for i in range(3): tile()
for i in range(3):
    pseudo(3, 15)
    tile()
for i in range(2): tile()
pseudo(3, 15)
for i in range(1):
    for j in range(2): tile()
    for j in range(2): pseudo(3, 15)
for i in range(2): tile()
pseudo(3, 15)
for i in range(6):
    pseudo(3, 15)
    tile()
pseudo(3, 15)
for i in range(3): tile()
pseudo(3, 15)
tile()
for i in range(3): pseudo(3, 15)
for i in range(3):
    for j in range(2): tile()
    for j in range(2): pseudo(3, 15)
tile()
pseudo(3, 15)
pseudo(3, 15)
pseudo3(15)
for i in range(2):
    for j in range(2): tile()
    for j in range(2): pseudo(3, 15)
for i in range(3): tile()
for i in range(3):
    pseudo(3, 15)
    tile()
for i in range(2): tile()
for i in range(5): pseudo(3, 15)
for i in range(3): tile()
pseudo(3, 15)
for i in range(2): tile()
for i in range(2): pseudo(3, 15)
for i in range(3): tile()
pseudo(3, 15)
tile()
for i in range(3): pseudo(3, 15)
tile()
for i in range(3): pseudo(3, 15)
tile()
pseudo(3, 15)
pseudo(3, 15)
for i in range(2):
    data["content"].append(TileData(ang=15, bpm=125 / 2))
    data["content"].append(TileData(ang=360 - 15, rot=i == 0, y=1))
    data["content"].append(TileData(ang=360, y=1))

#

data["content"].append(TileData(ang=30, bpm=500))
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=120))
for i in range(31): tile()
for i in range(18):
    pseudo(4, 15)
    for j in range(7):
        tile()
for i in range(2):
    pseudo(3, 15)
    for j in range(7):
        tile()
for i in range(7):
    pseudo(2, 30)
    tile()
    data["content"].append(TileData(ang=30))
    data["content"].append(TileData(ang=60))
    data["content"].append(TileData(ang=90))
    for j in range(3):
        data["content"].append(TileData(ang=90))
        data["content"].append(TileData(ang=90, rot=True))
    pseudo(2, 30)
    tile(rot=i == 6)
for i in range(4):
    data["content"].append(TileData(ang=30, bpm=1000))
    data["content"].append(TileData(ang=330))
data["content"].append(TileData(ang=30, bpm=250))
data["content"].append(TileData(ang=330))

#

data["content"].append(TileData(ang=30, bpm=500))
data["content"].append(TileData(ang=150))
for i in range(15): tile()
pseudo(2, 30)
for i in range(10): tile()
tile(rot=True)
pseudo(3, 30)
for i in range(3): tile()
pseudo(3, 30)
for i in range(15): tile()
pseudo(1, 30)
for i in range(6): tile()
tile(rot=True)
for i in range(2):
    pseudo(3, 30)
    for j in range(3): tile()
for i in range(3):
    pseudo(1 if i == 0 else 2, 30)
    for j in range(7): tile()
for i in range(2):
    pseudo(2, 30)
    for j in range(3): tile()
pseudo(2, 30)
for i in range(11): tile()
data["content"].append(TileData(ang=180, rot=True))
tile()
for i in range(2):
    data["content"].append(TileData(ang=30, bpm=1000))
    data["content"].append(TileData(ang=330))
data["content"].append(TileData(ang=30, bpm=250))
data["content"].append(TileData(ang=330))
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=270))
data["content"].append(TileData(ang=180, bpm=500))
tile()
for i in range(2):
    data["content"].append(TileData(ang=90))
    data["content"].append(TileData(ang=90, rot=True))
for i in range(4):
    data["content"].append(TileData(ang=30, rot=i != 0))
    data["content"].append(TileData(ang=60, rot=i != 3, x=2 if i == 3 else 0))
for i in range(2):
    pseudo(3, 30)

#

for i in range(7):
    data["content"].append(TileData(ang=30, bpm=500))
    data["content"].append(TileData(ang=330))
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=150))
data["content"].append(TileData(ang=90, rot=True))
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=30, rot=True))
data["content"].append(TileData(ang=150))
tile()
for i in range(6):
    data["content"].append(TileData(ang=30, rot=i == 0))
    data["content"].append(TileData(ang=330))
for i in range(4):
    data["content"].append(TileData(ang=30, rot=i != 0, color="#999999"))
    data["content"].append(TileData(ang=60, rot=i != 3, color="#999999"))
data["content"].append(TileData(ang=30, bpm=500))
data["content"].append(TileData(ang=330))
for i in range(6):
    data["content"].append(TileData(ang=30))
    data["content"].append(TileData(ang=330))
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=150))
data["content"].append(TileData(ang=90, rot=True))
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=30, rot=True))
data["content"].append(TileData(ang=150))
tile()
for i in range(4):
    data["content"].append(TileData(ang=30, rot=True, color="#999999"))
    data["content"].append(TileData(ang=60, rot=i != 3, color="#999999"))
for i in range(4):
    data["content"].append(TileData(ang=30))
    data["content"].append(TileData(ang=330))
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=150))
for i in range(4):
    data["content"].append(TileData(ang=30, rot=True, bpm=1000, color="#333333"))
    data["content"].append(TileData(ang=60, rot=i != 3, color="#333333"))
for i in range(2):
    data["content"].append(TileData(ang=30))
    data["content"].append(TileData(ang=330))
for i in range(16):
    data["content"].append(TileData(ang=30))
    data["content"].append(TileData(ang=330, x=1 if i == 15 else 0))
data["content"].append(TileData(ang=30, bpm=500))
data["content"].append(TileData(ang=330, x=1))
for i in range(14):
    data["content"].append(TileData(ang=30, bpm=1000))
    data["content"].append(TileData(ang=330, x=1 if i == 15 else 0))
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=150))
for i in range(5):
    tile()
data["content"].append(TileData(ang=30, rot=True, bpm=1000))
data["content"].append(TileData(ang=150))
for j in range(5):
    tile()
pseudo(2, 30)
for j in range(3):
    tile()
pseudo(2, 30)
for j in range(5):
    tile()
pseudo(2, 30)
for j in range(5):
    tile()
pseudo(2, 30)
for j in range(3):
    tile()
for i in range(4):
    data["content"].append(TileData(ang=30, bpm=500))
    data["content"].append(TileData(ang=30))
    data["content"].append(TileData(ang=120, x=1))
for i in range(8):
    data["content"].append(TileData(ang=30, bpm=1000))
    data["content"].append(TileData(ang=30))
    data["content"].append(TileData(ang=120, x=1))
for i in range(16):
    tile(rot=i == 0)

#

for i in range(7):
    if i == 0:
        data["content"].append(TileData(ang=30, bpm=1000))
        data["content"].append(TileData(ang=150, rot=True))
    else:
        pseudo(3, 30)
    for i in range(3):
        tile()
for i in range(4): pseudo(3, 30)
for i in range(7):
    if i == 0:
        data["content"].append(TileData(ang=30, bpm=1000))
        data["content"].append(TileData(ang=150, rot=True))
    else:
        pseudo(3, 30)
    for j in range(3):
        tile()
for i in range(16):
    data["content"].append(TileData(ang=45, rot=i != 0, color="#333333"))
for i in range(7):
    pseudo(4 if i == 0 else 1 if i == 6 else 3, 30)
    for j in range(3):
        tile()
for i in range(4):
    data["content"].append(TileData(ang=90, rot=True, color="#666666"))
for i in range(8):
    data["content"].append(TileData(ang=45, rot=True, color="#333333"))
for i in range(4):
    pseudo(4 if i == 0 else 3, 30)
    for j in range(3):
        tile()
for i in range(2):
    data["content"].append(TileData(ang=30, bpm=500))
    data["content"].append(TileData(ang=240))
data["content"].append(TileData(ang=30, rot=True))
data["content"].append(TileData(ang=150))
data["content"].append(TileData(ang=30, rot=True))
data["content"].append(TileData(ang=150))
for i in range(2):
    tile()
tile(rot=True)

for i in range(7):
    if i == 0:
        data["content"].append(TileData(ang=30, bpm=1000))
        data["content"].append(TileData(ang=150, rot=True))
    else:
        pseudo(3, 30)
    for i in range(3):
        tile()
for i in range(4): pseudo(3, 30)
for i in range(7):
    if i == 0:
        data["content"].append(TileData(ang=30, bpm=1000))
        data["content"].append(TileData(ang=150, rot=True))
    else:
        pseudo(3, 30)
    for j in range(3):
        tile()
for i in range(16):
    data["content"].append(TileData(ang=45, rot=i != 0, color="#333333"))
for i in range(7):
    pseudo(4 if i == 0 else 1 if i == 6 else 3, 30)
    for j in range(3):
        tile()
for i in range(4):
    data["content"].append(TileData(ang=90, rot=True, color="#666666"))
for i in range(8):
    data["content"].append(TileData(ang=45, rot=True, color="#333333"))
data["content"].append(TileData(ang=30, bpm=500))
data["content"].append(TileData(ang=330))
for i in range(4):
    data["content"].append(TileData(ang=30, rot=True, color="#cccccc"))
    data["content"].append(TileData(ang=60, rot=i != 3, color="#cccccc"))
data["content"].append(TileData(ang=30, rot=True, bpm=500))
data["content"].append(TileData(ang=330))
for i in range(4):
    data["content"].append(TileData(ang=30, rot=True, color="#cccccc"))
    data["content"].append(TileData(ang=60, rot=i != 3, color="#cccccc"))

for i in range(2):
    data["content"].append(TileData(ang=30, bpm=500))
    data["content"].append(TileData(ang=240))
data["content"].append(TileData(ang=30, rot=True))
data["content"].append(TileData(ang=150))
data["content"].append(TileData(ang=30, rot=True))
data["content"].append(TileData(ang=150))
for i in range(3):
    tile()
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=330))
for i in range(6):
    data["content"].append(TileData(ang=30, rot=True, bpm=1000))
    data["content"].append(TileData(ang=60, rot=True))
    data["content"].append(TileData(ang=90, rot=True))
    tile()
    data["content"].append(TileData(ang=90, rot=True))
    data["content"].append(TileData(ang=90))
    tile()
for i in range(3):
    pseudo(3, 30)
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=150, rot=True, x=7))
for i in range(6):
    data["content"].append(TileData(ang=30, rot=True))
    data["content"].append(TileData(ang=60, rot=True))
    data["content"].append(TileData(ang=90, rot=True))
    tile()
    data["content"].append(TileData(ang=90, rot=True))
    data["content"].append(TileData(ang=90))
    tile()
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=60))
data["content"].append(TileData(ang=90))
tile()
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=90, rot=True))
tile()
for i in range(16):
    data["content"].append(TileData(ang=45, rot=i != 0, color="#333333"))
for i in range(6):
    data["content"].append(TileData(ang=30, rot=True))
    data["content"].append(TileData(ang=60, rot=True))
    data["content"].append(TileData(ang=90, rot=True))
    tile()
    data["content"].append(TileData(ang=90, rot=True))
    data["content"].append(TileData(ang=90))
    tile()
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=60))
data["content"].append(TileData(ang=90))
tile()
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=90, rot=True))
tile()
for i in range(8):
    data["content"].append(TileData(ang=90, rot=i != 0, color="#666666"))
for i in range(6):
    data["content"].append(TileData(ang=30, rot=True))
    data["content"].append(TileData(ang=60, rot=True))
    data["content"].append(TileData(ang=90, rot=True))
    tile()
    data["content"].append(TileData(ang=90, rot=True))
    data["content"].append(TileData(ang=90))
    tile()
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=60))
data["content"].append(TileData(ang=90))
tile()
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=90, rot=True))
tile()
for i in range(8):
    data["content"].append(TileData(ang=90, rot=i != 0, color="#666666"))

for i in range(6):
    data["content"].append(TileData(ang=30, rot=True))
    data["content"].append(TileData(ang=60, rot=True))
    data["content"].append(TileData(ang=90, rot=True))
    tile()
    data["content"].append(TileData(ang=90, rot=True))
    data["content"].append(TileData(ang=90))
    tile()
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=60))
data["content"].append(TileData(ang=90))
tile()
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=90, rot=True))
tile()
for i in range(3):
    pseudo(3, 30)
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=150, rot=True, x=7))
for i in range(6):
    data["content"].append(TileData(ang=30, rot=True))
    data["content"].append(TileData(ang=60, rot=True))
    data["content"].append(TileData(ang=90, rot=True))
    tile()
    data["content"].append(TileData(ang=90, rot=True))
    data["content"].append(TileData(ang=90))
    tile()
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=60))
data["content"].append(TileData(ang=90))
tile()
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=90, rot=True))
tile()
for i in range(16):
    data["content"].append(TileData(ang=45, rot=i != 0, color="#333333"))
for i in range(6):
    data["content"].append(TileData(ang=30, rot=True))
    data["content"].append(TileData(ang=60, rot=True))
    data["content"].append(TileData(ang=90, rot=True))
    tile()
    data["content"].append(TileData(ang=90, rot=True))
    data["content"].append(TileData(ang=90))
    tile()
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=60))
data["content"].append(TileData(ang=90))
tile()
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=90, rot=True))
tile()
for i in range(8):
    data["content"].append(TileData(ang=90, rot=i != 0, color="#666666"))
for i in range(6):
    data["content"].append(TileData(ang=30, rot=True))
    data["content"].append(TileData(ang=60, rot=True))
    data["content"].append(TileData(ang=90, rot=True))
    tile()
    data["content"].append(TileData(ang=90, rot=True))
    data["content"].append(TileData(ang=90))
    tile()
data["content"].append(TileData(ang=30))
data["content"].append(TileData(ang=60))
data["content"].append(TileData(ang=90))
tile()
data["content"].append(TileData(ang=90))
data["content"].append(TileData(ang=90, rot=True))
tile()
for i in range(8):
    data["content"].append(TileData(ang=90, rot=i != 0, color="#666666"))

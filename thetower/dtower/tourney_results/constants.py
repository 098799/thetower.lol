from enum import Enum
from typing import Optional

from pydantic import BaseModel

how_many_results_hidden_site = 20000
how_many_results_public_site = 1000
how_many_results_public_site_other = 500
how_many_results_legacy = 200
how_many_results_debug = 50

the_color = "#807e29"

stratas = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 100000]

colors = [
    "#FFF",
    "#992d22",
    "#e390dc",
    "#ff65b8",
    "#d69900",
    "#06d68a",
    "#3970ec",
    "#206c5b",
    "#ff0000",
    "#6dc170",
    "#00ff00",
    "#ffffff",
]
# colors = [the_color] * 11

strata_to_color = dict(zip(stratas, colors))

# position_stratas = [0, 10, 50, 100, 200, 2000][::-1]
# position_colors = ["#333333", "#5555FF", "green", the_color, "red", "#CCCCCC"][::-1]

# Just a placeholder, change me later to be dependant on patch!!!
position_stratas = [
    0,
    1,
    10,
    25,
    50,
    100,
    200,
    300,
    400,
    500,
    600,
    700,
    800,
    900,
    1000,
    1500,
    2000,
][::-1]
position_colors = [
    "#333333",
    "#cda6eb",
    "#7fffe8",  # 10
    "#00b194",
    "#0082ff",
    "#3fabff",  # 100
    "#8bcef9",
    "#ff1d05",
    "#ff6600",  # 400
    "#ff9500",
    "#ffc000",  # 600
    "#ffc000",
    "#fff200",  # 800
    "#fff200",
    "#fff200",
    "#fffa9f",  # 1500
    "#CCCCCC",
][::-1]

legend = "Legend"
champ = "Champions"
plat = "Platinum"
gold = "Gold"
silver = "Silver"
copper = "Copper"

sus_person = "sus!!!"

stratas_boundaries = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 100000]
colors_017 = [
    "#FFFFFF",
    "#992d22",
    "#e390dc",
    "#ff65b8",
    "#d69900",
    "#06d68a",
    "#3970ec",
    "#206c5b",
    "#ff0000",
    "#6dc170",
    "#00ff00",
]

stratas_boundaries_018 = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500, 4000, 100000]
colors_018 = [
    "#FFFFFF",
    "#a4daac",
    "#7bff97",
    "#67f543",
    "#19b106",
    "#ffc447",  # "#ff8000",
    "#ff9931",  # "#ff4200",
    "#ff5f23",  # "#ff0000",
    "#ff0000",
    "#88cffc",  # "#89d1ff",
    "#3da8ff",  # "#61b8ff",
    "#2b7df4",  # "#5c8ddb",
    "#0061ff",  # "#3082ff",
    "#05a99d",  # "#00b1a5",
    "#7efdd3",  # "#7fffd4",
    "#ffffff",
]
strata_to_color_018 = dict(zip(stratas_boundaries_018, colors_018))


class Graph(Enum):
    all = "all"
    last_16 = "last_16"


class Options(BaseModel):
    links_toggle: bool
    current_player: Optional[str] = None
    current_player_id: Optional[str] = None
    compare_players: Optional[list[str]] = None
    default_graph: Graph
    average_foreground: bool


medals = ["🥇", "🥈", "🥉"]


leagues = [legend, champ, plat, gold, silver, copper]


data_folder_name_mapping = {
    legend: legend,
    "data": champ,
    "plat": plat,
    "gold": gold,
    "silver": silver,
    "copper": copper,
}
league_to_folder = {value: key for key, value in data_folder_name_mapping.items()}


leagues_choices = [(league, league) for league in data_folder_name_mapping.values()]


us_to_jim = {
    legend: legend,
    champ: "Champion",
    plat: plat,
    gold: gold,
    silver: silver,
    copper: copper,
}


wave_border_choices = [
    0,
    250,
    500,
    750,
    1000,
    1250,
    1500,
    1750,
    2000,
    2250,
    2500,
    2750,
    3000,
    3500,
    4000,
    4500,
    5000,
    100000,
    1000000,
]

all_relics = {
    0: ("No Spoon", "2%", "Abs def"),
    1: ("Red Pill", "5%", "Health"),
    2: ("Copper Badge", "3%", "Damage"),
    3: ("Silver Badge", "5%", "Coins"),
    4: ("Gold Badge", "5%", "Crit"),
    5: ("Platinum Badge", "5%", "Lab Speed"),
    6: ("Champion Badge", "10%", "DPM"),
    7: ("Tower Master", "10%", "Health"),
    8: ("Flux (T1)", "2%", "Coins"),
    9: ("Lumin (T2)", "2%", "Lab Speed"),
    10: ("Pulse (T3)", "2%", "Crit"),
    11: ("Harmonic (T4)", "2%", "Damage"),
    12: ("Ether (T5)", "2%", "Health"),
    13: ("Nova (T6)", "5%", "Abs def"),
    14: ("Aether (T7)", "5%", "Coins"),
    15: ("Graviton (T8)", "5%", "DPM"),
    16: ("Fusion (T9)", "5%", "Health"),
    17: ("Plasma (T10)", "5%", "DPM"),
    18: ("Resonance (T11)", "10%", "Abs def"),
    19: ("Chrono (T12)", "10%", "Lab Speed"),
    20: ("Hyper (T13)", "10%", "Coins"),
    21: ("Arcane (T14)", "10%", "Damage"),
    22: ("Celestial (T15)", "10%", "Crit"),
    23: ("1 year", "2%", "DPM"),
    24: ("2 years", "2%", "Crit"),
    25: ("3 years", "2%", "DPM"),
    26: ("Dreamcatcher", "2%", "Coins"),
    27: ("Spirit Wolf", "2%", "Crit"),
    28: ("Bacteriophage", "2%", "Damage"),
    29: ("Neuron", "5%", "Health"),
    30: ("IonizedPlazma", "2%", "Abs def"),
    31: ("PlasmaArc", "5%", "Lab Speed"),
    32: ("HoneyDrop", "2%", "Damage"),
    33: ("Stinger", "5%", "Crit"),
    38: ("Ancient Tome", "2%", "Lab Speed"),
    39: ("Sundial", "5%", "Damage"),
    40: ("Spooky Bat", "2%", "Crit"),
    41: ("Man Skull", "5%", "Health"),
    42: ("Cherry", "2%", "Abs def"),
    43: ("Sakura Lantern", "5%", "Coins"),
    44: ("Tower Latte", "2%", "DPM"),
    45: ("Pumpkin", "5%", "Lab Speed"),
    46: ("Holy Joystick", "2%", "Damage"),
    47: ("Controller", "5%", "Crit"),
    48: ("Firework", "2%", "Health"),
    49: ("Cheers", "5%", "Abs def"),
    50: ("Palm Tree", "2%", "Lab Speed"),
    51: ("Pixel Cube Heart", "5%", "Health"),
    52: ("Dark Sight", "2%", "DPM"),
    53: ("Creepy Smile", "5%", "Damage"),
    54: ("Submarine", "2%", "Crit"),
    55: ("The Kraken", "5%", "Abs def"),
    56: ("Warp Gate", "2%", "Coins"),
    57: ("Star Ship", "5%", "Lab Speed"),
    58: ("Barnacle", "2%", "Health"),
    59: ("Wave", "5%", "Crit"),
    60: ("Pizza", "2%", "Damage"),
    61: ("Illuminati", "5%", "Abs def"),
    62: ("Prismatic Shard", "5%", "DPM"),
    63: ("Refraction Array", "2%", "Coins"),
    64: ("Cobweb", "2%", "Health"),
    65: ("The Fly", "5%", "Abs def"),
    66: ("Clip Ons", "2%", "Crit"),
    67: ("Code Stream", "5%", "Damage"),
    70: ("Hook", "2%", "DPM"),
    71: ("Fish", "5%", "Abs def"),
    72: ("Gale Winds", "2%", "Coins"),
    73: ("Flying House", "5%", "Abs def"),
    74: ("Rain Jacket", "2%", "Health"),
    75: ("Storm Clouds", "5%", "Crit"),
    76: ("Rabies", "2%", "Lab Speed"),
    77: ("Ebola", "5%", "Abs def"),
    78: ("Anubis", "2%", "Coins"),
    79: ("Sphinx", "5%", "Damage"),
    83: ("Remote Control", "2%", "DPM"),
    84: ("Cathode Ray Tube", "5%", "Coins"),
    85: ("Quantum (T16)", "10%", "Health"),
    86: ("Nebula (T17)", "10%", "DPM"),
    87: ("Singularity (T18)", "10%", "Lab Speed"),
    88: ("Comet", "2%", "Damage"),
    89: ("Planetary Rings", "5%", "Crit"),
    90: ("Lava Flow", "2%", "Health"),
    91: ("Ash Cloud", "5%", "Abs def"),
    96: ("Acorn", "2%", "DPM"),
    97: ("Scarf", "5%", "Abs def"),
    98: ("Cauldron", "2%", "Lab Speed"),
    99: ("Witch Hat", "5%", "Damage"),
    100: ("Abduction Room", "", ""),
    101: ("Crop Circle", "5%", "Crit"),
    102: ("Legend Badge", "10%", "Crit"),
}

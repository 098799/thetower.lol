from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

the_color = "#807e29"

stratas = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 100000]

colors = ["#FFF", "#992d22", "#e390dc", "#ff65b8", "#d69900", "#06d68a", "#3970ec", "#206c5b", "#ff0000", "#6dc170", "#00ff00", "#ffffff"]
# colors = [the_color] * 11

strata_to_color = dict(zip(stratas, colors))

position_stratas = [0, 10, 50, 100, 200][::-1]
position_colors = ["#333333", "#5555FF", "green", the_color, "red"][::-1]

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
    congrats_toggle: bool
    links_toggle: bool
    current_player: Optional[str]
    compare_players: Optional[List[str]]
    default_graph: Graph
    average_foreground: bool


medals = ["🥇", "🥈", "🥉"]


leagues = [champ, plat, gold, silver, copper]


data_folder_name_mapping = {
    "data": champ,
    "plat": plat,
    "gold": gold,
    "silver": silver,
    "copper": copper,
}
league_to_folder = {value: key for key, value in data_folder_name_mapping.items()}


leagues_choices = [(league, league) for league in data_folder_name_mapping.values()]


us_to_jim = {
    champ: "Champion",
    plat: plat,
    gold: gold,
    silver: silver,
    copper: copper,
}


wave_border_choices = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500, 4000, 4500, 5000, 100000, 1000000]

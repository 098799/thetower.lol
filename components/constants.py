import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

the_color = "#807e29"

stratas = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 10000]

colors = ["#992d22", "#e390dc", "#ff65b8", "#d69900", "#06d68a", "#3970ec", "#206c5b", "#ff0000", "#6dc170", "#00ff00", "#ffffff"]
# colors = [the_color] * 11

strata_to_color = dict(zip(stratas, colors))

position_stratas = [0, 10, 50, 100, 200][::-1]
position_colors = ["#333333", "#5555FF", "green", the_color, "red"][::-1]


hardcoded_nicknames = {
    "508E64777E74593A": "Davroar",
    "3AF60D885181322C": "Skye",
    "2319505BE01FA063": "Peach",
    "D2E91B297D898157": "ĐåÝøX",
    "BE82DF9283461C75": "silent",
    "7EA771A7A2DCFAA9": "silent too",
    "9C0FFCDC9EC303DB": "Brianator",
    "B9ADDEEDC5E85D1B": "Blaze",
    "3E5F96B750CEE6C4": "NanaSeiYuri",
    "8BD9973232D2CB4B": "this guy with a green discord pic",
    "9DDCD4902FE1A201": "TJ the weird lines lollipop",
    "33540FD38D7F3B6B": "Helasus23",
    "ECC7934F0D89CFDD": "Dr. Soelent",
    "CB5E6220889629A4": "Skraggle Rock",
    "960DF09E2901C702": "MUMnotsoPrfct",
    "463AC882BCB747CE": "XΣЯIƧӨ",
    "D89A1205670BBB54": "Neonblinder",
    "A87E159A44462308": "TeapotMaster",
    "BB8938ABCD564BD3": "Pasco (f2p)",
    "108021C0ABED93A7": "tight fisted himji",
    "E29694349117A9F5": "Axillion (f2p)",
    "8CEF3BEC794790BA": "KindaMiteyAncientSmileKyth ⭐ (f2p)",
    "47630203FD36A45C": "Beckswarsteiner",
    "9C2FCA80BB3E1B3F": "Charmander Main's Rival",
    "43C3D0DB28BD5726": "RathianRuby",
    "270281236E7EAF76": "Pikle",
}

rev_hardcoded_nicknames = {value: key for key, value in hardcoded_nicknames.items()}

# sus = {
#     "Kehtimmy",
#     "Chronic",
#     "joeljj",
#     "WillBravo7",
#     "Kehtimmy",
#     "legionair",
#     "EEnton",
#     "aaa",
#     "Naiqey",
#     "Psyko",
#     "5th",
#     "marcino",
#     "Jerry",
# }


sus_data = {
    ("Kehtimmy", "8E573E09E336FC9F"),
    ("Chronic", "D1805B42F5484DD"),
    ("joeljj", "10CBAF5DF160809F"),
    ("WillBravo7", "DAA662A9560A9AB9"),
    ("Kehtimmy", "8E573E09E336FC9F"),
    ("legionair", "B733058A1394D0DC"),
    ("EEnton", "D7F00B0832BF9752"),
    ("aaa", "644DB9D23AA27B71"),
    ("Naiqey", "1ED2E5712F3A316B"),
    ("Psyko", "691AE6AD71799E8F"),
    ("5th", "7EF5F28EF124CCD"),
    ("Jerry", "E032D681F1F87B07"),
    ("rolinha", "FDC77C6CAC67C3B"),
    ("Dolarima", "1646B7C05FE152C1"),
    ("karlo", "58B9F99F87E36133"),
    ("tatikare", "649C62F11FD7DB67"),
    ("wjrtjdfn", "915244990762E022"),
    ("____HoLiFak____", "D600A296D053717A"),
    ("dangotic", "2F78932FE2757930"),
    ("marcino", "B4AC0E8BBF6C9D45"),
    ("mon", "D02FF7093AD638"),
    ("Bozak", "9A9BDEA5D56E8B5F"),
    ("jakob", "693330CB30AC7AAA"),
    ("rafcixon", "58AF3CDEAC26FEB5"),
    ("TacoWarrior", "5052D480E8312586"),
}

rehabilitated = {}

sus_ids = {id_ for _, id_ in sus_data}


sus_person = "sus!!!"


class Patch(BaseModel):
    class Config:
        frozen = True

    version_minor: int
    start_date: datetime.date
    end_date: Optional[datetime.date]

    def __str__(self):
        return f"<Patch 0.{self.version_minor}>"


patch_015 = Patch(
    version_minor=15,
    start_date=datetime.datetime(2022, 9, 7).date(),
    end_date=datetime.datetime(2022, 10, 29).date(),
)
patch_016 = Patch(
    version_minor=16,
    start_date=datetime.datetime(2022, 11, 2).date(),
    end_date=datetime.datetime(2023, 2, 22).date(),
)
patch_018 = Patch(
    version_minor=18,
    start_date=datetime.datetime(2023, 2, 25).date(),
    end_date=datetime.datetime(2024, 2, 25).date(),
)


def date_to_patch(date: datetime.datetime) -> Optional[Patch]:
    if date >= patch_015.start_date and date <= patch_015.end_date:
        return patch_015
    if date >= patch_016.start_date and date <= patch_016.end_date:
        return patch_016
    if date >= patch_018.start_date:
        return patch_018


class Role(BaseModel):
    class Config:
        frozen = True

    wave_bottom: int
    wave_top: int
    patch: Patch
    color: str

    def __gt__(self, other):
        try:
            return self.wave_top > other.wave_top
        except (AttributeError, TypeError):
            return True

    def __ge__(self, other):
        try:
            return self.wave_top >= other.wave_top
        except (AttributeError, TypeError):
            return True


stratas_boundaries = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 10000]
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

stratas_boundaries_018 = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500, 4000, 10000]
colors_018 = [
    "#FFFFFF",
    "#a4daac",
    "#7bff97",
    "#67f543",
    "#19b106",
    "#ff9e30",
    "#ff8000",
    "#ff4200",
    "#ff0000",
    "#89d1ff",
    "#61b8ff",
    "#5c8ddb",
    "#3082ff",
    "#00b1a5",
    "#7fffd4",
    "#ffffff",
]

patch_to_roles: Dict[Patch, List[Role]] = {
    patch_015: [
        Role(
            wave_bottom=strata_bottom,
            wave_top=strata_top,
            patch=patch_015,
            color=color,
        )
        for strata_bottom, strata_top, color in zip(stratas_boundaries, stratas_boundaries[1:], colors_017)
    ],
    patch_016: [
        Role(
            wave_bottom=strata_bottom,
            wave_top=strata_top,
            patch=patch_016,
            color=color,
        )
        for strata_bottom, strata_top, color in zip(stratas_boundaries, stratas_boundaries[1:], colors_017)
    ],
    patch_018: [
        Role(
            wave_bottom=strata_bottom,
            wave_top=strata_top,
            patch=patch_018,
            color=color,
        )
        for strata_bottom, strata_top, color in zip(stratas_boundaries_018, stratas_boundaries_018[1:], colors_018)
    ],
}


def wave_to_role_in_patch(roles: List[Role], wave: int) -> Optional[Role]:
    for role in roles:
        if wave >= role.wave_bottom and wave < role.wave_top:
            return role


def wave_to_role(wave: int, patch: Optional[Patch]) -> Optional[Role]:
    if not patch:
        return None

    roles = patch_to_roles.get(patch)

    if not roles:
        return None

    return wave_to_role_in_patch(roles, wave)


class Options(BaseModel):
    congrats_toggle: bool
    links_toggle: bool
    current_player: Optional[str]

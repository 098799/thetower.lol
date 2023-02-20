stratas = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 10000]
colors = ["#992d22", "#e390dc", "#ff65b8", "#d69900", "#06d68a", "#3970ec", "#206c5b", "#ff0000", "#6dc170", "#00ff00", "#ffffff"]
strata_to_color = dict(zip(stratas, colors))

position_stratas = [10, 50, 100, 200][::-1]
position_colors = ["#5555FF", "green", "#664620", "red"][::-1]


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
}

rehabilitated = {
    ("marcino", "B4AC0E8BBF6C9D45"),
}

sus_ids = {id_ for _, id_ in sus_data}


sus_person = "sus!!!"

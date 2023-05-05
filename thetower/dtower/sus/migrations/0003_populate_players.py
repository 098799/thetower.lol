from django.db import migrations


def upgrade(apps, schema_editor):
    PlayerId = apps.get_model("sus", "PlayerId")
    KnownPlayer = apps.get_model("sus", "KnownPlayer")

    name_mapping = {
        **{
            "Davroar": ["508E64777E74593A"],
            "Skye": ["3AF60D885181322C"],
            "Peach": ["2319505BE01FA063"],
            "ĐåÝøX": ["D2E91B297D898157"],
            "silent": ["BE82DF9283461C75"],
            "Brianator": ["9C0FFCDC9EC303DB"],
            "Blaze": ["B9ADDEEDC5E85D1B"],
            "NanaSeiYuri": ["3E5F96B750CEE6C4"],
            "this (still) micro guy": ["8BD9973232D2CB4B"],
            "TJ the weird lines lollipop": ["9DDCD4902FE1A201"],
            "Helasus23": ["33540FD38D7F3B6B"],
            "Dr. Soelent": ["ECC7934F0D89CFDD"],
            "Skraggle Rock": ["CB5E6220889629A4"],
            "MUMnotsoPrfct": ["960DF09E2901C702"],
            "XΣЯIƧӨ": ["463AC882BCB747CE"],
            "Neonblinder": ["D89A1205670BBB54"],
            "TeapotMaster": ["A87E159A44462308"],
            "Pasco (f2p)": ["BB8938ABCD564BD3"],
            "tight fisted himji": ["108021C0ABED93A7"],
            "Axillion (f2p)": ["E29694349117A9F5"],
            "KindaMiteyAncientSmileKyth ⭐ (f2p)": ["8CEF3BEC794790BA"],
            "Beckswarsteiner": ["47630203FD36A45C"],
            "Charmander Main's Rival": ["9C2FCA80BB3E1B3F"],
            "RathianRuby": ["43C3D0DB28BD5726"],
            "Pikle": ["270281236E7EAF76"],
            "Cmoir": ["980FBDFF0196B1C5"],
            "AnBaSi": ["9147A44AAB2B4E9D"],
            "JCurse": ["18B32A67E70B6CCC"],
        },
        **{
            "IceTae": ["C06D09C980D38976", "BCCBAF556C357D63"],
            "this (still) micro guy": ["DB6B7A5083D902E1", "8BD9973232D2CB4B"],
            "hbcook86": ["7C5A2B3CAE5B4064", "354ECFF6FFB5D939"],
            "Benedykt_XVI": ["3EF6CD09C678E9A6", "1AE461A51B004EFE"],
            "BigT1313": ["F4C0BFA126CD6FFE", "A82D5C82F91BF16A"],
            "Cjack6": ["F942845F49057761", "703B60E5EF491F7B"],
            "silent": ["7EA771A7A2DCFAA9", "BE82DF9283461C75"],
            "Elroco": ["72FA31778F53D321", "BC7E8A3AFF874F2E"],
            "Feckless": ["75F65B8B0681C109", "B8BB70A3AC79A9B1"],
            "Ghandi": ["534399965DB7B1A6", "710604B507B275CA"],
            "HenrikM69": ["99F2D3BB75DC3EE0", "C8E276428E96AED2"],
            "Korea_Levin": ["A07E0104F92FC7A8", "2EDF2603B907C26A"],
            "Milamber33": ["198C4EB51559D98", "4A98A60A5D9E4E25"],
            "MonkeyFizzle": ["FAFC017441A7B856", "8EB93A63A86D71A0"],
            "MrPsion": ["C67B0E2370D7B27", "F3FE1D1AAFB6AFC1"],
            "Nemesiis": ["E686007F79ACA2B1", "19D7FD097ACC79FA"],
            "PappSvane": ["917548C764377F23", "A38C6072035BAABA"],
            "Sauron": ["97DA5F5E7FFCCEB", "E5E9CF913C126530"],
            "SweetLou": ["F5ECC1B9516C9914", "D84535DBE3F94200"],
            "Tainted_Lich": ["F57F1200B4CFE8D8", "7B3E8D42B31A76C8"],
            "Tower": ["B9AD93E941A4BC96", "A6CF24A8D9939FD0"],
            "Saudade": ["D207A2B3ABBA75AF", "2C807DB3AC91AFDD"],
            "TurtlePants": ["E93F2C796A9FB6F9", "2B34E2D0CEF90B99"],
            "Prep": ["DA698CA1D0A546CD", "175407440A9CC05E", "AAA9A8A0EC988FE7"],
        },
    }

    for name, ids in name_mapping.items():
        player = KnownPlayer.objects.create(name=name)

        for index, id in enumerate(ids):
            primary = True if index + 1 == len(ids) else False
            PlayerId.objects.create(id=id, player=player, primary=primary)


class Migration(migrations.Migration):
    dependencies = [("sus", "0002_knownplayer_playerid")]
    operations = [migrations.RunPython(upgrade)]

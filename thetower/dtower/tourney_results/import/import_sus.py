import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

from dtower.sus.models import SusPerson

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
    ("Kuath", "BBEC115D0E4D37CC"),
    ("delcos", "576ED3406DA40C03"),
    ("__Announement__", "65CF85638390169A"),
    ("FixBHSizePlease", "8EE7D9DC9D98D098"),
    ("GiveEldarARole", "E4459A4A57EA94E1"),
    ("PrepPodcastWhen", "B49E6C31D41017F6"),
    ("Destromath", "2D7215062839FEBF"),
    ("HappyEaster2Kaga", "3D1A244DE0C96487"),
    ("DiscordAndReddit", "944AE172F9F5822C"),
    ("AndEspeciallyTo", "E2D79490BDF34620"),
    ("PogAndTheModTeam", "EB87F9F35191164"),
    ("pyhrfjvyysbyybj", "54CCC8E03C5A748C"),
    ("Nyxanren", "68BACF4F539E714"),
    ("tower", "51A2288E5BA89CD0"),
}

for name, id_ in sus_data:
    SusPerson.objects.get_or_create(player_id=id_, name=name, sus=True)

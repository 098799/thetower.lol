import pytest

from dtower.sus.models import KnownPlayer, PlayerId


@pytest.mark.django_db
def test_only_one_primary_id():
    players = KnownPlayer.objects.all()
    davroar = players[0]

    # only id, the primary one
    assert davroar.ids.all().count() == 1
    old_id = davroar.ids.all()[0]
    assert old_id.primary is True

    new_id = PlayerId.objects.create(player=davroar, id="1111111111111111", primary=True)

    # still only one primary, the new one
    assert new_id.primary is True
    old_id.refresh_from_db()
    assert old_id.primary is False

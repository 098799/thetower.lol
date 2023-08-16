import pytest


@pytest.mark.django_db
def test_view(client):
    client.post("/sus/", json={})

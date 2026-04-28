"""test_views_smoke.py — Automatischer HTTP-200-Test aller Views.

Nutzt discover_smoke_urls() — kein manuelles URL-Pflegen nötig.
Neue Views werden automatisch aufgenommen.

Voraussetzung: pip install iil-testkit[smoke]>=0.4.0
"""
try:
    import pytest
    from iil_testkit.smoke import discover_smoke_urls
except ImportError as _e:
    raise ImportError(
        "iil-testkit[smoke]>=0.4.0 fehlt. Installieren: "
        "pip install iil-testkit[smoke]>=0.4.0,<1"
    ) from _e

# Einmal zur Collection-Zeit aufrufen — nicht 2× pro Test-Funktion
_SMOKE_URLS: list[str] = discover_smoke_urls()


@pytest.mark.parametrize("url", _SMOKE_URLS)
@pytest.mark.django_db
def test_should_view_return_200(url: str, auth_client) -> None:
    """Alle parameterfreien Views müssen HTTP 200 oder 302 liefern."""
    response = auth_client.get(url)
    assert response.status_code in (200, 302), (
        f"{url} → HTTP {response.status_code} (erwartet: 200 oder 302)"
    )


@pytest.mark.parametrize("url", _SMOKE_URLS)
@pytest.mark.django_db
def test_should_unauthenticated_redirect_to_login(url: str, api_client) -> None:
    """Geschützte Views müssen unauthentifiziert auf Login weiterleiten."""
    response = api_client.get(url)
    assert response.status_code in (200, 302), f"{url} → {response.status_code}"
    if response.status_code == 200:
        return  # Public view — OK
    location = response.get("Location", "")
    assert "/login" in location or "/accounts/login" in location, (
        f"{url} leitet auf {location!r} weiter statt auf Login"
    )

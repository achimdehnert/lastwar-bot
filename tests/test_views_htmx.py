"""test_views_htmx.py — HTMX-Partials und data-testid Enforcement (ADR-048).

HTMX_URLS werden automatisch aus Templates extrahiert (hx-post/hx-get Attribute).
Nur parameterfreie URLs (kein {{pk}}, kein {% url %}) werden geprüft.
"""
import pytest

from iil_testkit.assertions import assert_data_testids, assert_htmx_response


# Keine hx-* Attribute in Templates gefunden — manuell befüllen:
HTMX_URLS: list[str] = [

]


@pytest.mark.skipif(not HTMX_URLS, reason="HTMX_URLS leer — keine HTMX-Endpoints gefunden")
@pytest.mark.parametrize("url", HTMX_URLS)
@pytest.mark.django_db
def test_should_htmx_response_be_fragment(url: str, auth_client) -> None:
    """HTMX-Endpoints müssen Fragmente liefern, keine vollen Seiten."""
    response = auth_client.get(url, HTTP_HX_REQUEST="true")
    assert_htmx_response(response)


@pytest.mark.skipif(not HTMX_URLS, reason="HTMX_URLS leer — keine HTMX-Endpoints gefunden")
@pytest.mark.parametrize("url", HTMX_URLS)
@pytest.mark.django_db
def test_should_htmx_elements_have_data_testid(url: str, auth_client) -> None:
    """Alle hx-* Elemente müssen data-testid haben (ADR-048)."""
    response = auth_client.get(url)
    assert_data_testids(response)

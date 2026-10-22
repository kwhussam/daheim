import pytest

from app.ha_client.mock_client import MockHomeAssistantClient


@pytest.mark.asyncio
async def test_mock_client_health():
    mock = MockHomeAssistantClient()
    health = await mock.check_health()
    assert health.reachable is True
    assert health.mode == "mock"


@pytest.mark.asyncio
async def test_mock_client_get_or_create_area_is_idempotent():
    mock = MockHomeAssistantClient()
    area1 = await mock.get_or_create_area("Wohnzimmer")
    area2 = await mock.get_or_create_area("Wohnzimmer")
    assert area1 == area2
    areas = await mock.list_areas()
    assert len(areas) == 1


@pytest.mark.asyncio
async def test_mock_client_distinct_names_create_distinct_areas():
    mock = MockHomeAssistantClient()
    await mock.get_or_create_area("Küche")
    await mock.get_or_create_area("Bad")
    areas = await mock.list_areas()
    assert len(areas) == 2

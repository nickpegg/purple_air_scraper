import pytest

from purple_air_scraper import PM_2_5_AQI_TABLE, aqi


@pytest.mark.parametrize(
    "given,expected",
    [
        (0, 0),
        (10, 42),
        (12.1, 51),
        (88.4, 168),
        (400, 457),
        (666, 500),
    ]
)
def test_pm2_5_aqi(given: float, expected: float) -> None:
    assert int(aqi(given, PM_2_5_AQI_TABLE)) == expected

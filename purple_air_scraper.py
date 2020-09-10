import logging
import os
import sys
import time
from typing import List, Tuple, Sequence, Iterator
from argparse import ArgumentParser

import requests
from prometheus_client import Counter, Gauge, start_http_server

# Source for AQI calculation
# https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
#
# We really should be basing the AQI on the average PM value for the last 10 or 60
# minutes, but it's way easier to track instantaneous AQI. The difference is fairly
# small, assuming small jumps (<20 PM) in a 10 minute interval.


INTERVAL_S = 30

URL = "https://www.purpleair.com/json?show={id}"


PM_2_5_AQI_TABLE = [
    # PM2.5, AQI
    (0,     0),
    (12.1,  51),
    (35.5,  101),
    (55.5,  151),
    (150.5, 201),
    (250.5, 301),
    (350.5, 401),
]

PM_10_AQI_TABLE = [
    # PM10, AQI
    (0,     0),
    (55,    51),
    (155,   101),
    (255,   151),
    (355,   201),
    (425,   301),
    (505,   401),
]


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('purple_air_scraper')


# Types
AqiTable = Sequence[Tuple[float, float]]

# Stats
STAT_PREFIX = 'purpleair_'
SENSOR_LABELS = ["unit_id", "sensor_id", "label"]

FetchErrors = Counter(STAT_PREFIX + 'fetch_errors', "Errors fetching data from PurpleAir sensor")

Pm2_5 = Gauge(STAT_PREFIX + 'pm2_5', "2.5 micron particulate matter (ug/m^3)", SENSOR_LABELS)
Pm10 = Gauge(STAT_PREFIX + 'pm10_0', "10 micron particulate matter (ug/m^3)", SENSOR_LABELS)

Aqi2_5 = Gauge(STAT_PREFIX + 'aqi_pm2_5', "PM2.5 AQI", SENSOR_LABELS)
Aqi10 = Gauge(STAT_PREFIX + 'aqi_pm10_0', "PM10 AQI", SENSOR_LABELS)

Temp_f = Gauge(STAT_PREFIX + 'temp_f', "Temperature in degrees Fahrenheit", SENSOR_LABELS)
Humidity = Gauge(STAT_PREFIX + 'humidity', "% Humidity", SENSOR_LABELS)
Pressure = Gauge(STAT_PREFIX + 'pressure', "Pressure in millibar", SENSOR_LABELS)
LastSeen = Gauge(STAT_PREFIX + 'last_seen_seconds', "timestamp when this sensor was last seen", SENSOR_LABELS)

# PurpleAir sensor keys to Prometheus stats
SENSOR_MAP = {
    'pm2_5_atm': Pm2_5,
    'pm10_0_atm': Pm10,
    'temp_f': Temp_f,
    'pressure': Pressure,
    'humidity': Humidity,
    'LastSeen': LastSeen,
}


class Ticker():
    def __init__(self, interval: float):
        self.interval = interval
        self.go = True

    def stop(self) -> None:
        self.go = False

    def run(self) -> Iterator[bool]:
        logger.debug(f"Ticker running every {self.interval} seconds")
        while self.go:
            logger.debug("tick")
            start = time.time()
            yield True
            end = time.time()
            duration = end - start

            sleep_time = self.interval - duration
            if sleep_time < 0:
                logger.warning(f"Iteration took longer than {self.interval} seconds")
                sleep_time = 0
            logger.info(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)


def main() -> None:
    log_level = os.environ.get("PAS_LOGGING", 'info')
    prom_port = int(os.environ.get("PAS_PROM_PORT", '9101'))

    if "PAS_SENSOR_IDS" not in os.environ or not os.environ["PAS_SENSOR_IDS"]:
        logger.error(f"Missing env var: PAS_SENSOR_IDS")
        sys.exit(1)

    sensor_ids = list(map(int, os.environ["PAS_SENSOR_IDS"].split(',')))

    log_level = getattr(logging, log_level.upper())
    logger.setLevel(log_level)

    start_http_server(int(prom_port))
    for _ in Ticker(INTERVAL_S).run():
        for sensor_id in sensor_ids:
            collect(sensor_id)


def collect(parent_sensor_id: int) -> None:
    logger.info(f"Collecting data from sensor_id {parent_sensor_id}")

    url = URL.format(id=parent_sensor_id)

    logger.debug(f"Fetching {url}")
    response = requests.get(url)

    if response.status_code == 429:
        logger.warning("Throttled")
        return

    try:
        response.raise_for_status()
    except:
        logger.exception(f"Error fetching {url}")
        FetchErrors.inc()
        return

    try:
        results = response.json()
    except ValueError:
        logger.exception("Unable to parse response as JSON")
        FetchErrors.inc()
        return

    # Most units have two sensors in them, collect stats for each.
    sensor_label = ""
    for data in results['results']:
        sensor_id = data.get('ID', '')
        if not sensor_label:
            sensor_label = data.get('Label', '')

        # Most stats are copied
        for key, stat in SENSOR_MAP.items():
            if key in data:
                stat.labels(unit_id=parent_sensor_id, sensor_id=sensor_id, label=sensor_label).set(data[key])

        # Calculate AQI based on PM2.5 and PM10
        if 'pm2_5_atm' in data:
            pm2_5_aqi = aqi(float(data['pm2_5_atm']), PM_2_5_AQI_TABLE)
            Aqi2_5.labels(unit_id=parent_sensor_id, sensor_id=sensor_id, label=sensor_label).set(pm2_5_aqi)
        if 'pm10_0_atm' in data:
            pm10_aqi = aqi(float(data['pm10_0_atm']), PM_10_AQI_TABLE)
            Aqi10.labels(unit_id=parent_sensor_id, sensor_id=sensor_id, label=sensor_label).set(pm10_aqi)


def aqi(pm: float, table: AqiTable) -> float:
    # Find bucket we're in
    pm_min = 0.0
    pm_max = 0.0
    aqi_min = 0.0
    aqi_max = 0.0
    for table_pm, table_aqi in table:
        if table_pm > pm:
            pm_max = table_pm
            aqi_max = table_aqi
            break
        aqi_min = table_aqi
        pm_min = table_pm

    aqi = (aqi_max - aqi_min) * (pm - pm_min) / (pm_max - pm_min) + aqi_min
    if aqi > 500:
        # top of scale
        aqi = 500
    return aqi


if __name__ == "__main__":
    main()

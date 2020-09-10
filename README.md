# Purple Air Scraper

Scrapes the `purpleair.com/json` endpoint for a particular sensor and exposes the stats
via a Prometheus HTTP endpoint.

Calculates the instantaneous AQI from the PM 2.5 and PM 10.0 values. This is a little
different from how PurpleAir or the EPA calculates the AQI, since those are calculated
from a time-based average of PM values (10 minutes for PA, 1 hour for EPA). Doing an
instantaneous calculation is much simpler, and yields a pretty close value to what a 10
minute PM average would yield assuming no giant jumps in PM (<20 ug/m^3).

Kudos to the EPA for [publishing a
doc](https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf)
on how AQI is calculated as well as the AQI level tables.

## Usage
To use this script you'll need a sensor ID, which can be gotten from the
[PurpleAir map](https://www.purpleair.com/map). Find your favorite sensor, click on it
to bring up the sensor popup. At the bottom of the popup is a "Get This Widget" link
which will pop up another thing when you hover over it, click the "JSON" link.

That will take you to a URL like `https://www.purpleair.com/json?key=<key>&show=<id>`. 
The `<id>` is what you'll need to set as an environment variable to configure the
script.

## Configuration
This script is configurable via environment variables, which is handy when running as a
Docker container.

### `PAS_SENSOR_IDS` (required)
Comma-separated list of IDs of the sensors to scrape, gotten from the PurpleAir /json
URL for your sensor

### `PAS_LOGGING`
Log level of the script, defaults to 'info', accepts any [Python logging level
name](https://docs.python.org/3/howto/logging.html#logging-levels)

### `PAS_PROM_PORT`
The port to run the Prometheus HTTP server on, defaults to 9101

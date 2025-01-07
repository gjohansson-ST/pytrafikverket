[![size_badge](https://img.shields.io/github/repo-size/gjohansson-ST/pytrafikverket?style=for-the-badge&cacheSeconds=3600)](https://github.com/gjohansson-ST/pytrafikverket)
[![version_badge](https://img.shields.io/github/v/release/gjohansson-ST/pytrafikverket?label=Latest%20release&style=for-the-badge&cacheSeconds=3600)](https://github.com/gjohansson-ST/pytrafikverket/releases/latest)
[![download_badge](https://img.shields.io/pypi/dm/pytrafikverket?style=for-the-badge&cacheSeconds=3600)](https://github.com/gjohansson-ST/pytrafikverket/releases/latest)
![GitHub Repo stars](https://img.shields.io/github/stars/gjohansson-ST/pytrafikverket?style=for-the-badge&cacheSeconds=3600)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/gjohansson-ST/pytrafikverket?style=for-the-badge&cacheSeconds=3600)
![GitHub License](https://img.shields.io/github/license/gjohansson-ST/pytrafikverket?style=for-the-badge&cacheSeconds=3600)

[![Made for Home Assistant](https://img.shields.io/badge/Made_for-Home%20Assistant-blue?style=for-the-badge&logo=homeassistant)](https://github.com/home-assistant)

[![Sponsor me](https://img.shields.io/badge/Sponsor-Me-blue?style=for-the-badge&logo=github)]([https://github.com/hacs/integration](https://github.com/sponsors/gjohansson-ST))
![Discord](https://img.shields.io/discord/872446427664625664?style=for-the-badge&label=Discord&cacheSeconds=3600)

# pytrafikverket

Retrieve values from public API at the Swedish Transport Administration (Trafikverket).

Development and testing done with 3.13

## Code example

```python

from pytrafikverket import TrafikverketTrain, StationInfo
import aiohttp
import asyncio
from datetime import datetime


async def main(loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        train_api = TrafikverketTrain(session, "api_key_here")
        stations = await train_api.async_search_train_stations("kristianstad")
        for station in stations:
            print(station.name + " " + station.signature)

        from_station = await train_api.async_get_train_station("Sölvesborg")
        to_station = await train_api.async_get_train_station("Kristianstad C")
        product_description = "SJ Regional"  # Optional search field
        print("from_station_signature: " + from_station.signature)
        print("to_station_signature:   " + to_station.signature)
        train_stop = await train_api.async_get_train_stop(
            from_station, to_station, datetime(2022, 4, 11, 12, 57), product_description
        )
        print(train_stop.get_state())


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))

```

## CLI example
<!-- blacken-docs:off -->
```python

trafikverket_cli -key <api_key> -method search-for-station -station "Kristianstad"
trafikverket_cli -key <api_key> -method get-next-train-stop -from-station "Kristianstad C" -to-station "Sölvesborg"
trafikverket_cli -key <api_key> -method get-next-train-stop -from-station "Kristianstad C" -to-station "Sölvesborg" -train-product "SJ Regional"
trafikverket_cli -key <api_key> -method get-train-stop -from-station "Kristianstad C" -to-station "Sölvesborg" -date-time "2017-05-19T16:38:00"
trafikverket_cli -key <api_key> -method get-weather -station "Nöbbele"
trafikverket_cli -key <api_key> -method search-for-ferry-route -route "sund"
trafikverket_cli -key <api_key> -method get-ferry-route -route "Adelsöleden"
trafikverket_cli -key <api_key> -method get-next-ferry-stop -from-harbor "Ekerö"
trafikverket_cli -key <api_key> -method get-next-ferry-stop -from-harbor "Furusund" -date-time "2019-12-24T00:00:00"

```
<!-- blacken-docs:on -->

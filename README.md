# pytrafikverket
python module for communicating with the swedish trafikverket api

Development and testing done with 3.10

## Code example
```python
from pytrafikverket import TrafikverketTrain, StationInfo
import aiohttp
import asyncio
import async_timeout
from datetime import datetime

async def main(loop):
	async with aiohttp.ClientSession(loop=loop) as session:
		train_api = TrafikverketTrain(session, "api_key_here")
		stations = await train_api.async_search_train_stations("kristianstad")
		for station in stations:
			print(station.name + " " + station.signature)

		from_station = await train_api.async_get_train_station("Sölvesborg")
		to_station = await train_api.async_get_train_station("Kristianstad C")
		product_description = "SJ Regional" # Optional search field
		print("from_station_signature: " + from_station.signature)
		print("to_station_signature:   " + to_station.signature)
		train_stop = await train_api.async_get_train_stop(from_station, to_station, datetime(2022, 4, 11, 12, 57), product_description);
		print(train_stop.get_state())

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
```

## CLI example
```bash
$ py pytrafikverket.py -key <api_key> -method search-for-station -station "Kristianstad"
$ py pytrafikverket.py -key <api_key> -method get-next-train-stop -from-station "Kristianstad C" -to-station "Sölvesborg"
$ py pytrafikverket.py -key <api_key> -method get-next-train-stop -from-station "Kristianstad C" -to-station "Sölvesborg" -train-product "SJ Regional"
$ py pytrafikverket.py -key <api_key> -method get-train-stop -from-station "Kristianstad C" -to-station "Sölvesborg" -date-time "2017-05-19T16:38:00"
$ py pytrafikverket.py -key <api_key> -method get-weather -station "Nöbbele"
$ py pytrafikverket.py -key <api_key> -method search-for-ferry-route -route "sund"
$ py pytrafikverket.py -key <api_key> -method get-ferry-route -route "Adelsöleden"
$ py pytrafikverket.py -key <api_key> -method get-next-ferry-stop -from-harbor "Ekerö"
$ py pytrafikverket.py -key <api_key> -method get-next-ferry-stop -from-harbor "Furusund" -date-time "2019-12-24T00:00:00"
```

# pytrafikverket
python module for communicating with the swedish trafikverket api

## Code example
```python
from trafikverket_train import TrafikverketTrain, StationInfo
import aiohttp
import asyncio
import async_timeout
from datetime import datetime

async def main(loop):
	async with aiohttp.ClientSession(loop=loop) as session:
		train_api = TrafikverketTrain(session, "api_key_here")
		stations = await train_api.search_train_stations("kristianstad")
		for station in stations:
			print(station.name + " " + station.signature)

		from_station = await train_api.get_train_station("Sölvesborg")
		to_station = await train_api.get_train_station("Kristianstad C")
		print("from_station_signature: " + from_station.signature)
		print("to_station_signature:   " + to_station.signature)
		train_stop = await train_api.get_train_stop(from_station, to_station, datetime(2017, 5, 15, 12, 57));
		print(train_stop.get_state())

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
```

## CLI example
```bash
$ py pytrafikverket.py -key [api_key_here] -method search-for-station -station "Kristianstad"
$ py pytrafikverket.py -key [api_key_here] -method get-next-train-stop -from-station "Kristianstad C" -to-station "Sölvesborg"
$ py pytrafikverket.py -key [api_key_here] -method get-train-stop -from-station "Kristianstad C" -to-station "Sölvesborg" -date-time "2017-05-19T16:38:00"
$ py pytrafikverket.py -key [api_key_here] -method get-weather -station "Nöbbele"
$ py pytrafikverket.py -key [api_key_here] -method search-for-ferry-route -route "sund"
$ py pytrafikverket.py -key [api_key_here] -method get-ferry-route -route "Adelsöleden"
$ py pytrafikverket.py -key [api_key_here] -method get-next-ferry-stop -from-harbor "Ekerö" 
$ py pytrafikverket.py -key [api_key_here] -method get-next-ferry-stop -from-harbor "Furusund" -date-time "2019-12-24T00:00:00"
```

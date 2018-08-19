from datetime import datetime
import argparse
import asyncio
import aiohttp
import async_timeout
from pytrafikverket.trafikverket_train import TrafikverketTrain
from pytrafikverket.trafikverket_weather import TrafikverketWeather
from pytrafikverket.trafikverket import Trafikverket

SEARCH_FOR_STATION = "search-for-station"
GET_TRAIN_STOP = "get-train-stop"
GET_NEXT_TRAIN_STOP = "get-next-train-stop"
GET_WEATHER = "get-weather"

async def async_main(loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        #parse arguments!
        parser = argparse.ArgumentParser(description="CLI used to get data from trafikverket")
        parser.add_argument("-key", type=str)
        parser.add_argument("-method", choices=(SEARCH_FOR_STATION,
                                                GET_TRAIN_STOP,
                                                GET_NEXT_TRAIN_STOP,
                                                GET_WEATHER))
        parser.add_argument("-station", type=str)
        parser.add_argument("-from-station", type=str)
        parser.add_argument("-to-station", type=str)
        parser.add_argument("-date-time", type=str)

        args = parser.parse_args()

        train_api = TrafikverketTrain(session, args.key)
        weather_api = TrafikverketWeather(session, args.key)
        with async_timeout.timeout(10):
            if args.method == SEARCH_FOR_STATION:
                if args.station is None:
                    raise ValueError("-station is required")
                stations = await train_api.async_search_train_stations(args.station)
                for station in stations:
                    print(station.name + " " + station.signature)
            elif args.method == GET_TRAIN_STOP:
                from_station = await train_api.async_get_train_station(args.from_station)
                to_station = await train_api.async_get_train_station(args.to_station)
                print("from_station_signature: " + from_station.signature)
                print("to_station_signature:   " + to_station.signature)
                time = datetime.strptime(args.date_time, Trafikverket.date_time_format)
                train_stop = await train_api.async_get_train_stop(from_station, to_station, time)

                print("id: %s, canceled: %s, advertised time: %s, " %
                      (train_stop.id, train_stop.canceled, train_stop.advertised_time_at_location) +
                      "estimated time: %s, time: %s, state: %s" %
                      (train_stop.estimated_time_at_location, train_stop.time_at_location,
                       train_stop.get_state()))
            elif args.method == GET_NEXT_TRAIN_STOP:
                from_station = await train_api.async_get_train_station(args.from_station)
                to_station = await train_api.async_get_train_station(args.to_station)
                print("from_station_signature: " + from_station.signature)
                print("to_station_signature:   " + to_station.signature)
                if args.date_time is not None:
                    time = datetime.strptime(args.date_time, Trafikverket.date_time_format)
                else:
                    time = datetime.now()
                train_stop = await train_api.async_get_next_train_stop(from_station, to_station, time)

                print("id: %s, canceled: %s, advertised time: %s, " %
                      (train_stop.id, train_stop.canceled, train_stop.advertised_time_at_location) +
                      "estimated time: %s, time: %s, state: %s" %
                      (train_stop.estimated_time_at_location, train_stop.time_at_location,
                       train_stop.get_state()))
            elif args.method == GET_WEATHER:
                if args.station is None:
                    raise ValueError("-station is required with name of Weather station (ex. -station \"Nöbbele\")")
                weather = await weather_api.async_get_weather(args.station)
                print("Name: %s, id: %s, road temp: %s , air temp: %s, " %
                      (weather.station_name, weather.station_id, weather.road_temp, weather.air_temp) + 
                      "humidity: %s, precipitation: %s, wind direction %s degrees / " %
                      (weather.humidity, weather.precipitationtype, weather.winddirection) +
                      "%s, wind force: %s m/s (10 min avg)" %
                      (weather.winddirectiontext, weather.windforce))



def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main(loop))

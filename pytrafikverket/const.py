"""Constants for the pytrafikverket library."""

from __future__ import annotations

API_URL = "https://api.trafikinfo.trafikverket.se/v2/data.xml"

SWEDEN_TIMEZONE = "Europe/Stockholm"
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
DATE_TIME_FORMAT_FOR_MODIFIED = "%Y-%m-%dT%H:%M:%S.%fZ"

SEARCH_FOR_STATION = "search-for-station"
GET_TRAIN_STOP = "get-train-stop"
GET_NEXT_TRAIN_STOP = "get-next-train-stop"
GET_WEATHER = "get-weather"
GET_FERRY_ROUTE = "get-ferry-route"
SEARCH_FOR_FERRY_ROUTE = "search-for-ferry-route"
GET_NEXT_FERRY_STOP = "get-next-ferry-stop"
DATE_TIME_INPUT = "%Y-%m-%dT%H:%M:%S"

CAMERA_INFO_REQUIRED_FIELDS = [
    "Name",
    "Id",
    "Active",
    "Deleted",
    "Description",
    "Direction",
    "HasFullSizePhoto",
    "Location",
    "ModifiedTime",
    "PhotoTime",
    "PhotoUrl",
    "Status",
    "Type",
]
ROUTE_INFO_REQUIRED_FIELDS = ["Id", "Name", "Shortname", "Type.Name"]
DEVIATION_INFO_REQUIRED_FIELDS = [
    "Deviation.Id",
    "Deviation.Header",
    "Deviation.EndTime",
    "Deviation.StartTime",
    "Deviation.Message",
    "Deviation.IconId",
    "Deviation.LocationDescriptor",
]
FERRY_STOP_REQUIRED_FIELDS = [
    "Id",
    "Deleted",
    "DepartureTime",
    "Route.Name",
    "DeviationId",
    "ModifiedTime",
    "FromHarbor",
    "ToHarbor",
    "Info",
]
STATION_INFO_REQUIRED_FIELDS = ["LocationSignature", "AdvertisedLocationName"]
TRAIN_STOP_REQUIRED_FIELDS = [
    "ActivityId",
    "Canceled",
    "AdvertisedTimeAtLocation",
    "EstimatedTimeAtLocation",
    "TimeAtLocation",
    "OtherInformation",
    "Deviation",
    "ModifiedTime",
    "ProductInformation",
]
WEATHER_REQUIRED_FIELDS = [
    "Name",  # string, replaced
    "Id",  # string, replaced
    "ModifiedTime",  # datetime, new, Tidpunkt då dataposten ändrades i cachen
    "Observation.Sample",  # datetime, replaced, Tidpunkt som observationen avser, inklusive tidzon för att hantera sommartid och normaltid. # codespell:ignore
    "Observation.Air.Temperature.Value",  # float, replaced, Lufttemperatur. Value [C]
    "Observation.Air.RelativeHumidity.Value",  # float, replaced, Relativ luftfuktighet. Andel av den fukt som luften kan bära. Vid 100% är luften mättad. Value [%] # codespell:ignore
    "Observation.Air.Dewpoint.Value",  # float, new, Daggpunkt, den temperatur där vatten kondenserar. Value [C] # codespell:ignore
    "Observation.Air.VisibleDistance.Value",  # float, new, Den sträcka det finns sikt. Value [m]
    "Observation.Wind.Direction.Value",  # int, replaced, Mått på vindriktning vid en viss tidpunkt. Medelvärde över tiominutersperiod t.o.m. tidpunkten. Value [grader]
    "Observation.Wind.Height",  # int, new, Vindsensorns höjdplacering [m]
    "Observation.Wind.Speed.Value",  # float, replaced, Mått på vindhastighet vid en viss tidpunkt. Medelvärde över tiominutersperiod t.o.m. tidpunkten. Value [m/s]
    "Observation.Aggregated30minutes.Wind.SpeedMax.Value",  # float, replaced, Högst uppmätt 3-sekundersmedelvärde under perioden. Value [m/s]
    "Observation.Weather.Precipitation",  # string, replaced, Vilken typ av nederbörd som detekterats # codespell:ignore
    "Observation.Aggregated30minutes.Precipitation.TotalWaterEquivalent.Value",  # float, replaced, Mängd vatten som nederbörden under perioden motsvarar. Value [mm] # codespell:ignore
    "Observation.Aggregated30minutes.Precipitation.Rain",  # bool, new, Förekomst av regn.
    "Observation.Aggregated30minutes.Precipitation.Snow",  # bool, new, Förekomst av snö.
    "Observation.Surface.Temperature.Value",  # float, replaced, Vägytans temperatur. Value [C] # codespell:ignore
    "Observation.Surface.Ice",  # bool, new, Förekomst av is på vägytan.
    "Observation.Surface.IceDepth.Value",  # float, new, Isdjup på vägytan. Value [mm]
    "Observation.Surface.Snow",  # bool, new, Förekomst av snö på vägytan.
    "Observation.Surface.SnowDepth.Solid.Value",  # float, new, Mängd snö. Value [mm]
    "Observation.Surface.SnowDepth.WaterEquivalent.Value",  # float, new, Mängd vatten som snön motsvarar i smält form. Value [mm] # codespell:ignore
    "Observation.Surface.Water",  # bool, new, Förekomst av vatten på vägytan.
    "Observation.Surface.WaterDepth.Value",  # float, new, Vattendjup på vägytan. Value [mm]
]  # Precipitation possible values are: no, rain, freezing_rain, snow, sleet, yes

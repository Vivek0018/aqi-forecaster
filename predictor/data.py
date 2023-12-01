import itertools
import json
import warnings
from typing import Any, Dict, List, Tuple, Union

import numpy
import pandas
import requests
from ratelimit import limits, sleep_and_retry

# 1000 calls per second is the limit allowed by API
CALLS: int = 1000
RATE_LIMIT: int = 1

from .decodedata import get_data_from_id

def _as_float(x: Any) -> float:
    """Convert x into a float. If unable, convert into numpy.nan instead.

    Naming and functionality inspired by R function as.numeric()"""
    try:
        return float(x)
    except (TypeError, ValueError):
        return numpy.nan

class URLs:
    """Class that contains the endpoint urls for the WAQI API

    This class should not be instantiated. It only contains class level attributes,
    and no methods at all. It is a static dataclass.

    Attributes:
        search_aqi_url (str): The endpoint used for retrieving air quality data.
        find_stations_url (str): The endpoint used for
         retrieving a collection of air quality measuring stations.
        find_coordinates_url (str): The endpoint used for
         retrieving geographical information
    """

    # Base API endpoint.
    _base_url: str = "https://api.waqi.info/"

    # For air quality data search by location.
    search_aqi_url: str = f"{_base_url}feed/"

    # For search for air quality measuring stations in area.
    find_stations_url: str = f"{_base_url}search/"

    # For Map Queries
    find_coordinates_url: str = f"{_base_url}map/"


class Ozon3:
    """Primary class for Ozon3 API

    This class contains all the methods used for data collection.
    This class should be instantiated, and methods should be called from the
    instance.

    Attributes:
        token (str): The private API token for the WAQI API service.
    """

    _search_aqi_url: str = URLs.search_aqi_url
    _find_stations_url: str = URLs.find_stations_url
    _default_params: List[str] = [
        "aqi",
        "pm2.5",
        "pm10",
        "o3",
        "co",
        "no2",
        "so2",
        "dew",
        "h",
        "p",
        "t",
        "w",
        "wg",
    ]

    def __init__(
        self, token: str = "", output_path: str = ".", file_name: str = "air_quality"
    ):
        """Initialises the class instance and sets the API token value

        Args:
            token (str): The users private API token for the WAQI API.
        """
        self.token: str = token
        self._check_token_validity()

    def _check_token_validity(self) -> None:
        """Check if the token is valid"""
        test_city: str = "london"
        r = self._make_api_request(
            f"{self._search_aqi_url}/{test_city}/?token={self.token}"
        )

        self._check_status_code(r)
        if json.loads(r.content)["status"] != "ok":
            warnings.warn("Token may be invalid!")

    @sleep_and_retry
    @limits(calls=CALLS, period=RATE_LIMIT)
    def _make_api_request(self, url: str) -> requests.Response:
        """Make an API request

        Args:
            url (str): The url to make the request to.

        Returns:
            requests.Response: The response from the API.
        """
        r = requests.get(url)
        return r

    def _check_status_code(self, r: requests.Response) -> None:
        """Check the status code of the response"""
        if r.status_code == 200:
            pass
        elif r.status_code == 401:
            raise Exception("Unauthorized!")
        elif r.status_code == 404:
            raise Exception("Not Found!")
        elif r.status_code == 500:
            raise Exception("Internal Server Error!")
        else:
            raise Exception(f"Error! Code {r.status_code}")



    def get_city_station_options(self, city: str) -> pandas.DataFrame:
        """Get available stations for a given city
        Args:
            city (str): Name of a city.

        Returns:
            pandas.DataFrame: Table of stations and their relevant information.
        """
        # NOTE, HACK, FIXME:
        # This functionality was born together with historical data feature.
        # This endpoint is outside WAQI API's specification, thus not using
        # _check_and_get_data_obj private method above.
        # If exists, alternative within API's spec is more than welcome to
        # replace this implementation.
        r = requests.get(f"https://search.waqi.info/nsearch/station/{city}")
        res = r.json()

        city_id, country_code, station_name, city_url, score = [], [], [], [], []

        for candidate in res["results"]:
            city_id.append(candidate["x"])
            country_code.append(candidate["c"])
            station_name.append(candidate["n"])
            city_url.append(candidate["s"].get("u"))
            score.append(candidate["score"])

        return pandas.DataFrame(
            {
                "city_id": city_id,
                "country_code": country_code,
                "station_name": station_name,
                "city_url": city_url,
                "score": score,
            }
        ).sort_values(by=["score"], ascending=False)

    def get_historical_data(
        self, city: str = None, city_id: int = None  # type: ignore
    ) -> pandas.DataFrame:
        """Get historical air quality data for a city

        Args:
            city (str): Name of the city. If given, the argument must be named.
            city_id (int): City ID. If given, the argument must be named.
                If not given, city argument must not be None.

        Returns:
            pandas.DataFrame: The dataframe containing the data.
        """
        if city_id is None:
            if city is None:
                raise ValueError("If city_id is not specified, city must be specified.")

            # Take first search result
            search_result = self.get_city_station_options(city)
            if len(search_result) == 0:
                return 404

            first_result = search_result.iloc[0, :]

            city_id = first_result["city_id"]
            station_name = first_result["station_name"]
            country_code = first_result["country_code"]

            # warnings.warn(
            #     f'city_id was not supplied. Searching for "{city}" yields '
            #     f'city ID {city_id} with station name "{station_name}", '
            #     f'with country code "{country_code}". '
            #     "Ozon3 will return air quality data from that station. "
            #     "If you know this is not the correct city you intended, "
            #     "you can use get_city_station_options method first to "
            #     "identify the correct city ID."
            # )
        else:
            if city is not None:
                warnings.warn(
                    "Both arguments city and city_id were supplied. "
                    "Only city_id will be used. city argument will be ignored."
                )

        df = get_data_from_id(city_id)
        if "pm25" in df.columns:
            # This ensures that pm25 data is labelled correctly.
            df.rename(columns={"pm25": "pm2.5"}, inplace=True)

        # Reset date index and rename the column appropriately
        # df = df.reset_index().rename(columns={"index": "date"})
        # print(df)

        return [df ,city , station_name, country_code]

def getCityData(city_name):
    o = Ozon3('a36388df93e27e7fb00282d007eae2e68c561a61')
    
    data = o.get_historical_data(city=city_name)
    
    return data


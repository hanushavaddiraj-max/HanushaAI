import requests
from typing import Any, Callable, Set, Dict, List, Optional
import json
import os
from dotenv import load_dotenv
load_dotenv()

def get_weather(location):
    """
    Fetches the weather information for the specified location.

    :param location (str): The location to fetch weather for.
    :return: Weather information as a string of characters.
    :rtype: str
    """
    
   #calling open weather map API for information retrieval
   #fetching latitude and longitude of the specific location respectively
    url = "http://api.openweathermap.org/geo/1.0/direct?q=" + location + "&limit=1&appid=YOUR_API_KEY"
    response=requests.get(url)
    get_response=response.json()
    latitude=get_response[0]['lat']
    longitude = get_response[0]['lon']

    url_final = "https://api.openweathermap.org/data/2.5/weather?lat=" + str(latitude) + "&lon=" + str(longitude) + "&appid=YOUR_API_KEY"
    final_response = requests.get(url_final)
    final_response_json = final_response.json()
    weather=final_response_json['weather'][0]['description']
    return weather

def get_user_info(user_id: int) -> str:
    """Retrieves user information based on user ID.

    :param user_id (int): ID of the user.
    :rtype: int

    :return: User information as a JSON string.
    :rtype: str
    """
    mock_users = {
        1: {"name": "Alice", "email": "alice@example.com"},
        2: {"name": "Bob", "email": "bob@example.com"},
        3: {"name": "Charlie", "email": "charlie@example.com"},
    }
    user_info = mock_users.get(user_id, {"error": "User not found."})
    return json.dumps({"user_info": user_info})

user_functions: Set[Callable[..., Any]] = {
    get_weather,
    get_user_info
}
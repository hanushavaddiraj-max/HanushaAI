import requests
from typing import Any, Callable, Set, Dict, List, Optional
import json
import os
from dotenv import load_dotenv
load_dotenv()



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
    
    get_user_info
}
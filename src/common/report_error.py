import json
import os
from datetime import datetime
from typing import Dict

from src import config


def report_error(content: Dict[str, any]) -> None:
    """
    Save the error message to the logs folder
    Args:
        content: the error message

    Returns:
        None
    """
    if not os.path.exists(config.ERROR_LOGS_LOCATION):
        os.makedirs(config.ERROR_LOGS_LOCATION)

    date_time_now = datetime.now().strftime("%d_%m_%Y__%H_%M_%S.json")

    formatted_error = json.dumps(content, indent=4, default=str)

    with open(
        os.path.join(
            config.ERROR_LOGS_LOCATION, date_time_now
        ),
        'w'
    ) as file:
        file.write(formatted_error)

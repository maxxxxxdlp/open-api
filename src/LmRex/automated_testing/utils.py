import json
import os
from datetime import datetime
from typing import Dict
from LmRex.config import frontend_config as settings


def report_error(content: Dict[str, any]) -> None:
    if not os.path.exists(settings.ERROR_LOGS_LOCATION):
        os.makedirs(settings.ERROR_LOGS_LOCATION)

    date_time_now = datetime.now().strftime("%d_%m_%Y__%H_%M_%S.json")

    formatted_error = json.dumps(content, indent=4, default=str)

    with open(
            os.path.join(
                settings.ERROR_LOGS_LOCATION, date_time_now
            ),
            'w'
    ) as file:
        file.write(formatted_error)

import json
import os
from datetime import datetime
from typing import Dict
import settings


def report_error(content:Dict[str,any]) -> None:

	if not os.path.exists('my_folder'):
		os.makedirs('my_folder')

	date_time_now = datetime.now().strftime("%d_%m_%Y__%H_%M_%S")

	formatted_error = json.dumps(content, indent=4)

	with open(os.path.join(settings.ERROR_LOGS_LOCATION, date_time_now) ,'w') as file:
		file.write(formatted_error)
import os
from datetime import datetime
from src.gui_wrapper import settings


def report_error(content) -> None:

	if not os.path.exists('my_folder'):
		os.makedirs('my_folder')

	date_time_now = datetime.now().strftime("%d_%m_%Y__%H_%M_%S")

	with open(os.path.join(settings.ERROR_LOGS_LOCATION, date_time_now) ,'wb') as file:
		file.write(content)
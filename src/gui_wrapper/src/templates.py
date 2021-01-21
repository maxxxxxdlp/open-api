import os

import settings
from string import Template


def _read_template(template_path):
	with open(os.path.join(settings.TEMPLATES_DIR, template_path)) as template:
		return template.read()

def render(template_path, **kwargs):
	return Template(
		_read_template(template_path)
	).substitute(**kwargs)

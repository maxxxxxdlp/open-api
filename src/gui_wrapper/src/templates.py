import settings
from jinja2 import FileSystemLoader, Environment, select_autoescape

env = Environment(
	loader=FileSystemLoader(settings.TEMPLATES_DIR),
)


def load(path: str):
	return env.get_template(path).render


def render(path: str, **kwargs):
	load(path)(**kwargs)

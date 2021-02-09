from LmRex.config import frontend_config as settings
from jinja2 import FileSystemLoader, Environment

env = Environment(
    loader=FileSystemLoader(settings.TEMPLATES_DIR),
)


def load(path: str, ):
    """
    Loads the template and returns its ref
    Args:
        path(str): path to a template relative to the templates dir

    Returns:
        Ref of the template
    """
    return env.get_template(path).render


def render(path: str, **kwargs):
    """
    Loads and renders a template
    Useful for when a template would only be used once
    Args:
        path(str): path to a template relative to the templates dir
        **kwargs: arguments to forward to the template

    Returns:

    """
    load(path)(**kwargs)

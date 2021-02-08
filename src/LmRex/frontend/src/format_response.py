from typing import Dict, List
from LmRex.frontend.src import templates

field = templates.load('field.html')
field__boolean = templates.load('field__boolean.html')
field__dict = templates.load('field__dict.html')
field__string = templates.load('field__string.html')
field__text = templates.load('field__text.html')


def format_list(values: List[any]) -> str:
    if not values:
        return '[]'
    else:
        return format_dict(
            fields=dict(
                [
                    ('[%d]' % index, value) for index, value in enumerate(values)
                ]
            ),
            is_list_of_values=True
        )


def format_string(value: str) -> str:
    if type(value) is str and ('\n' in value or len(value) > 80):
        return field__text(value=value)
    else:
        return field__string(value=value)


def format_value(value: any) -> str:
    if type(value) is bool:
        return field__boolean(value=value)
    if type(value) is list:
        return format_list(values=value)
    if type(value) is dict:
        return format_dict(fields=value)
    else:
        return format_string(value=value)


def format_dict(fields: Dict[str, any], is_list_of_values: bool = False) -> str:
    if not fields:
        return '{}'
    else:
        return field__dict(
            fields=[
                field(label=label, value=format_value(value)) for label, value in fields.items()
            ],
            is_list_of_values=is_list_of_values
        )


def format_response(_endpoint: str, response: Dict[str, any]) -> str:
    return format_dict(response)

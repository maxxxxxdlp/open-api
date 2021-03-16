from typing import Dict, List
from flask import render_template


def format_list(values: List[any]) -> str:
    """
    Formats a list
    Args:
        values: list

    Returns:
        str:
            formatted list
    """
    if not values:
        return '[]'
    else:
        return format_dict(
            fields=dict(
                [
                    ('[%d]' % index, value) for index, value in
                    enumerate(values)
                ]
            ),
            is_list_of_values=True
        )


def format_string(value: str) -> str:
    """
    Formats a string
    Args:
        value: str

    Returns:
        str:
            formatted string
    """
    return render_template(
        'field__text.html' \
        if type(value) is str and ('\n' in value or len(value) > 80) \
        else 'field__string.html',
        value=value
    )


def format_value(value: any) -> str:
    """
    Formats a value, depending on its type
    Args:
        value: any

    Returns:
        str:
            formatted value
    """
    if type(value) is bool:
        return render_template('field__boolean.html',value=value)
    if type(value) is list:
        return format_list(values=value)
    if type(value) is dict:
        return format_dict(fields=value)
    else:
        return format_string(value=value)


def format_dict(fields: Dict[str, any], is_list_of_values: bool = False) -> str:
    """
    Formats a dict
    Args:
        fields (Dict[str,any]): dictionary to format
        is_list_of_values (bool):
            whether a dictionary is a list with numeric indexes

    Returns:
        str:
            formatted list
    """
    if not fields:
        return '{}'
    else:
        return render_template(
            'field__dict.html',
            fields=[
                render_template(
                    'field.html',
                    label=label,
                    value=format_value(value)
                ) for label, value
                in fields.items()
            ],
            is_list_of_values=is_list_of_values
        )


def format_response(_endpoint: str, response: Dict[str, any]) -> str:
    """
    Formats the response object
    Args:
        _endpoint (str): name of the endpoint
        response (Dict[str,any]): response object

    Returns:
        str:
            formatted response
    """
    return format_dict(response)

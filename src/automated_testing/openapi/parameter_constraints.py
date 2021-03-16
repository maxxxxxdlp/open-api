# TODO: compare results between explicit and implicit default params
from typing import Callable, List, Dict


def get_gbif_records(
        path: str,
        response: Dict[str, any]
) -> List[Dict[str, any]]:
    """
    Get GBIF response from the response object
    that may include other providers
    Args:
        path (str): path of the current endpoint
        response (Dict[str,any]): response object

    Returns:
        GBIF response object

    """
    return response['records'] if 'gbif' in path \
        else response['records'][0]['GBIF']['records']


def gbif_count(
        parameter_value: bool,
        path: str,
        response: Dict[str, any]
) -> bool:
    """
    Check that `gbif_count` parameter affected the response object in an
    expected way
    Args:
        parameter_value (bool): the value of the `gbif_count` parameter
        path (str): path of the current endpoint
        response (Dict[str,any]): response object

    Returns:
        bool:
            whether validation was successful
    """
    for record in get_gbif_records(path, response):
        if (
            not parameter_value and (
                'occurrence_count' in record or
                'occurrence_url' in record
            )
        ) or \
        (
            parameter_value and (
                'occurrence_count' not in record or
                'occurrence_url' not in record
            )
        ):
            return False
    return True


def gbif_accepted(
        parameter_value: bool,
        path: str,
        response: Dict[str, any]
) -> bool:
    """
    Check that `gbif_accepted` parameter affected the response object in an
    expected way
    Args:
        parameter_value (bool): the value of the `gbif_accepted` parameter
        path (str): path of the current endpoint
        response (Dict[str,any]): response object

    Returns:
        bool:
            whether validation was successful
    """
    for record in get_gbif_records(path, response):
        if parameter_value and record['status'] != 'ACCEPTED':
            return False
    return True


# TODO: finish this one once `occ` endpoints are fixed
def count_only(
        parameter_value: bool,
        path: str,
        response: Dict[str, any]
) -> bool:
    """
    Check that `count_only` parameter affected the response object in an
    expected way
    Args:
        parameter_value (bool): the value of the `count_only` parameter
        path (str): path of the current endpoint
        response (Dict[str,any]): response object

    Returns:
        bool:
            whether validation was successful
    """
    pass


parameter_constraints: Dict[
    str,
    Callable[[bool, str, Dict[str, any]], bool]
] = {
    'gbif_count':    gbif_count,
    'gbif_accepted': gbif_accepted,
}

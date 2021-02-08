# TODO: compare results between explicit and implicit default params
from typing import Callable, List, Dict


def get_gbif_records(
        path: str,
        response: Dict[str, any]
) -> List[Dict[str, any]]:
    return response['records'] if 'gbif' in path \
        else response['records'][0]['GBIF']['records']


def gbif_count(
        parameter_value: bool,
        path: str,
        response: Dict[str, any]
) -> bool:
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
    pass


parameter_constraints: dict[
    str,
    Callable[[bool, str, Dict[str, any]], bool]
] = {
    'gbif_count':    gbif_count,
    'gbif_accepted': gbif_accepted,
}

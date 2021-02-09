import json
import os
from LmRex.config import frontend_config as settings

with open(os.path.join(
            settings.COLLECTION_STATS_LOCATION,
            'stats_sample.json'
        )
    ) as list_of_collections_file:
    list_of_collections = json.loads(list_of_collections_file.read())


expand_path = lambda key, partial_path: os.path.join(
        settings.COLLECTION_STATS_RELATIVE_LOCATION,
        partial_path
    ) \
    if 'path' in key \
    else partial_path


def fetch_collection_data(collection_location:str):
    """
    Fetches a stats.json file for a particular collection
    Args:
        collection_location: the location of the stat.json file

    Returns:

    """
    with open(
        collection_location.replace(
            '/DATA/datasets',
            settings.COLLECTION_STATS_LOCATION
        )
    ) as collection_data_file:
        collection_data = json.loads(collection_data_file.read())

    return {
        key:expand_path(key,value)
        for key,value in collection_data.items()
    }
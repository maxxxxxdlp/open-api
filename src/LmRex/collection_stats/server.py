import cherrypy
from LmRex.collection_stats.src.fetch_data import fetch_collection_data
from LmRex.config import frontend_config as settings
from LmRex.frontend.src.templates import load
from LmRex.collection_stats.src.fetch_data import list_of_collections

template = load('list_of_collections.html')
main_template = load('index.html')
collection_template = load('collection_stats.html')

class Root(object):
    @cherrypy.expose
    def index(self) -> str:
        return main_template(
            title='S^N',
            content=template(collections=list_of_collections)
        )


class API(object):
    @cherrypy.expose
    def fetch_data(self, collection_name: str) -> str:
        return collection_template(
            fetch_collection_data(collection_name)
        )


config = {
    '/': {
        'tools.staticdir.on':    True,
        'tools.staticdir.dir':   settings.COLLECTION_STATS_BASE_DIR,
        'tools.staticdir.index': 'index.html',
    },
}

cherrypy.tree.mount(Root(), '/', config)
cherrypy.tree.mount(API(), '/api/', config)
cherrypy.engine.start()
cherrypy.engine.block()

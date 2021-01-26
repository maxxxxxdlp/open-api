import cherrypy
import settings
from src import ui
from src import templates
from src import api

main_template = templates.load('index.html')


class Root(object):
	@cherrypy.expose
	def index(self) -> str:
		return main_template(title='S^N', content=ui.menu())

	@cherrypy.expose
	def routes(self, tag: str) -> str:
		return main_template(title=tag, content=ui.tag(tag))

	@cherrypy.expose
	def endpoint(self, tag: str, route: int) -> str:
		return main_template(title=tag, content=ui.endpoint(tag, route))


class API(object):
	@cherrypy.expose
	def fetch_response(self, url: str) -> str:
		return api.fetch_response(url)


config = {
	'/': {
		'tools.staticdir.on':    True,
		'tools.staticdir.dir':   settings.BASE_DIR,
		'tools.staticdir.index': 'index.html',
	},
}

cherrypy.tree.mount(Root(), '/', config)
cherrypy.tree.mount(API(), '/api/', config)
cherrypy.engine.start()
cherrypy.engine.block()

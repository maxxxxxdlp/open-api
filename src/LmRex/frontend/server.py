import cherrypy
from LmRex.config import frontend_config as settings
from LmRex.frontend.src import ui
from LmRex.frontend.src import templates
from LmRex.frontend.src import api

main_template = templates.load('index.html')


class Root(object):
	@cherrypy.expose
	def index(self) -> str:
		return main_template(title='S^N', content=ui.menu())

	@cherrypy.expose
	def routes(self, tag: str) -> str:
		return main_template(title=tag, content=ui.tag(tag))

	@cherrypy.expose
	def endpoint(self, tag: str, route: str) -> str:
		return main_template(title=tag, content=ui.endpoint(tag, int(route)-1))


class API(object):
	@cherrypy.expose
	def fetch_response(self, endpoint: str, url: str) -> str:
		return api.fetch_response(endpoint, url)


config = {
	'/': {
		'tools.staticdir.on':    True,
		'tools.staticdir.dir':   settings.FRONTEND_BASE_DIR,
		'tools.staticdir.index': 'index.html',
	},
}

cherrypy.tree.mount(Root(), '/', config)
cherrypy.tree.mount(API(), '/api/', config)
cherrypy.engine.start()
cherrypy.engine.block()

import os
import cherrypy
import settings
from src import templates


class Root(object):
	@cherrypy.expose
	def index(self):
		return templates.render('index.html', title='S^N', content='<b>__hello__</>')


cherrypy.tree.mount(Root(), '/', {
	'/': {
		'tools.staticdir.on':    True,
		'tools.staticdir.dir':   settings.BASE_DIR,
		'tools.staticdir.index': 'index.html',
	},
})
cherrypy.engine.start()
cherrypy.engine.block()

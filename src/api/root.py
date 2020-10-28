"""This module provides REST services for service objects"""
import cherrypy

from LmRex.api.testres import SpecifyArk


# .............................................................................
@cherrypy.expose
class ApiRootV2:
    """Top level class containing services"""
    spark = SpecifyArk()

    # ................................
    def __init__(self):
        pass

    # ................................
    def index(self):
        """Service index method."""
        return "Index of api root"

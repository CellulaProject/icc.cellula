""" Cornice services.
"""
from cornice import Service
from pyramid.response import Response
from pyramid.view import view_config

#hello = Service(name='hello', path='/', description="Simplest app")

# @hello.get()

@view_config(route_name='home',renderer='templates/index.pt')
def get_info(request):
    """Returns Helo."""
    #return Response("<html><body><H>Hello world</H></body></html>")
    return { 'title':'Суперсистема'}



def includeme(config):
    #config.scan("icc.cellula.views")
    config.scan()
    config.add_route('home', "/")
    
""" Cornice services.
"""
from cornice import Service


hello = Service(name='hello', path='/', description="Simplest app")

@hello.get()
def get_info(request):
    """Returns Helo."""
    return "<H>Hello world</H>"


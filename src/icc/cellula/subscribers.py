from pyramid.renderers import get_renderer
#from pyramid.events import subscriber, BeforeRender

#@subscriber(BeforeRender)
def add_base_template(event):
    """Add base template.
    """

    main = get_renderer('templates/index.pt').implementation()

    event.update({'main': main})

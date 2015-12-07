from pyramid.renderers import get_renderer
#from pyramid.events import subscriber, BeforeRender

#@subscriber(BeforeRender)
def add_base_template(event):
    """Add base template.
    """

    main = get_renderer('templates/index.pt').implementation()
    test = get_renderer('templates/main.pt').implementation()
    event.update({'main': main, 'test':test})

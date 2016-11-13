from zope.interface import Interface


class IExtractor(Interface):
    """Extractor interface.
    """

    def extract(content, headers=None):
        """Returns a dictionary of keywords with vlues,
        describing content.
        Parameter headers used to support some metadata heuristics,
        shich as Content-Type, file name of the content, etc.
        """

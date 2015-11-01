from zope.interface import Interface

class IIndexer(Interface):
    """Defines indexer interface."""

    def put(text_content, fields):
        """Put text_content into index accomplied with
        attributes. Returns int ID taken from fields. """

    def remove(hash_id):
        """Remove hash_id tagged text_content.
        Returns True if removal has a success."""

    def search(query):
        """Search stored text_contents according to
        the query."""

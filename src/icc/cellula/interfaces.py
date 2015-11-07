from zope.interface import Interface, Attribute

class IApplication (Interface):
    pass

class IQueue (Interface):
    """Marker interface to denote processing Queues."""

class IWorker (Interface):
    """Denote interface for a
    processing worker"""

    queue = Attribute("A multiprocessing.Queue name the worker associated with.")

    def process(task):
        """Process a task"""

    def equeue(task):
        """Put a task in the queue"""

class ITask (Interface):
    """Describes a task to be processed by a worker."""

    procedure = Attribute("A procedure to run.")
    args = Attribute("Proceeing procedure's parameters.")
    kwargs = Attribute("Proceeing procedure's keyword parameters.")
    queue = Attribute("A multiprocessing.Queue name the task associated with.")

    def enqueue(task):
        """Add a new task to the queue."""

    def run():
        """Processing code to be run."""

    def set_queue(queue):
        """Inform the task with queue name it associated with."""

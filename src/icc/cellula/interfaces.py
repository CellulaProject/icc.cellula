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

    procedure = Attribute("A procedure to run")
    args = Attribute("Proceeing procedure's parameters")
    kwargs = Attribute("Proceeing procedure's keyword parameters")
    queue = Attribute("A Queue name the task associated with")
    processing = Attribute("Processing resource: thread or process")
    priority = Attribute("Priority of the task")
    phase = Attribute("Phase of task processing")
    result = Attribute("Result obtained during run, it is set when the result is enqueued int the task result queue")

    def enqueue(task):
        """Add a new task to the queue."""

    def run():
        """Processing code to be run."""

    def set_queue(queue):
        """Inform the task with queue name it associated with."""

    def prepare():
        """Make some preparation before processing.
        This can, e.g., do some processing in the
        thread before sending the task to other process.
        """

    def finalize():
        """Do sonethinf after processing. E.g. join results
        obtained in a foreign process."""

class ISingletonTask(ITask):
    """Marker interface to define task that
    may occur in the task queue only onece for
    its class."""

class ITerminationTask(Interface):
    """A marker interface to mark lowest priority task
    terminating workers"""

class ILock(Interface):
    """Marker lock interface."""

class IMailer(Interface):
    """MArk a component to be mailer
    """

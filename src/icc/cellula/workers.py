from icc.cellula.interfaces import IWorker, ITask
from zope.interface import implementer
from zope.component import getUtility

def GetQueue(name):
    """Find a queue utility. A helper procedure."""
    return getUtility(IQueue, name=name)

@implementer(IWorker)
class Worker(object):
    """A processing worker.
    """

    def __init__(self, queue):
        """
        """
        self.queue=queue

@implementer(ITask)
class Task(object):
    """Task is processed by workers.
    It can be defined with procedure and its paramaters or
    by redefining run method.
    """

    def __init__(self, procedure=None, args=None, kwargs=None queue=None):
        """
        """
        self.set_queue(queue)
        self.procedure=procedure
        self.args=args
        self.kwargs=kwargs

    def set_queue(self, name):
        self.queue=name

    def run(self):
        if procedure == None:
            return
        n=self.queue
        kw=self.kwargs
        k={}
        if kw!=None:
            k.update(kw)
        if n:
            q=GetQueue(n)
            if not 'queue' in k:
                k['queue']=q
        a=self.args
        if a==None:
            a=tuple()

        return apply(self.procedure, args=a, keywords=k)

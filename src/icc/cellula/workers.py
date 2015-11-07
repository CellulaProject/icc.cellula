from icc.cellula.interfaces import IWorker, ITask, ITerminationTask, IQueue
from zope.interface import implementer, Interface
from zope.component import getUtility, queryUtility
import queue
import threading

def GetQueue(name, query=False):
    """Find a queue utility. A helper procedure."""
    if query:
        return queryUtility(IQueue, name=name)
    else:
        return getUtility(IQueue, name=name)

@implementer(IWorker)
class ThreadWorker(object):
    """A processing worker.
    """

    def run(self):
        print ("Started thread worker.")
        tasks=GetQueue('tasks')
        results=GetQueue('results', query=True)
        while True:
            print ("a thread worker is waiting for a task")
            task=tasks.get()
            print ("a thread worker got a task")
            if ITerminationTask.providedBy(task):
                q.task_done()
                return
            task.phase="prepare"
            task.prepare()
            task.phase="run"
            rc=task.run()
            if rc!=None and results != None:
                task.result=rc
                results.put(task)
            task.phase="finalize"
            task.finalize()
            task.phase=None
            tasks.task_done()

    def __call__(self):
        return self.run()

@implementer(ITask)
class Task(object):
    """Task is processed by workers.
    It can be defined with procedure and its paramaters or
    by redefining run method.
    """
    priority = 5
    processing = "thread"

    def __init__(self, procedure=None, args=None, kwargs=None, queue=None, foreign=False):
        """
        """
        self.set_queue(queue)
        self.procedure=procedure
        self.args=args
        self.kwargs=kwargs
        self.phase=None

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
        # foreign !!!
        return apply(self.procedure, args=a, keywords=k)

    def enqueue(self, task):
        if self.processing=="process" and self.phase=="run":
            raise RuntimeError ("cannot enqueue new task in foreign process")
        q=GetQueue("tasks")
        return q.put(task, block=False)

    def prepare(self):
        pass

    def finalize(Self):
        pass

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

@implementer(ITerminationTask)
class TerminationTask(object):
    """Task, whose process preduces worker
    processing cycle to be terminated."""
    priority=100
    processing="thread"
    def __init__(self, *args, **kwargs):
        pass

@implementer(IWorker)
class QueueThread(threading.Thread):
    """The thread processing task Queue
    """

    def __init__(self):
        """
        """
        threading.Thread.__init__(self)
        self.thread_pool=[]
        self.process_pool=[]
        config = getUtility(Interface, "configuration")["workers"]
        self.threads=int(config.get("threads",2))
        self.processes=int(config.get("processes",2))

    def run(self):
        for i in range(self.threads):
            w=ThreadWorker()
            t=threading.Thread(target=w)
            self.thread_pool.append(t)
            t.start()
        # Create process pool
        # join process pool
        while True:
            if not self.join_worker():
                break

    def join_worker(self):
        if self.process_pool:
            # join a process
            return True
        if self.thread_pool:
            t=self.thread_pool.pop()
            t.join()
            return True
        return False

    def terminate(self):
        q=GetQueue('tasks')
        for t in self.thread_pool:
            q.put(TerminationTask(), block=False)
        for p in self.process_pool:
            q.put(TerminationTask(), block=False)

class PriorityQueue(queue.PriorityQueue):

    def put(self, task, *args, **kwargs):
        print ("Q. Put:", task)
        return queue.PriorityQueue.put(self, (task.priority, task), *args, **kwargs)

    def get(self, *args, **kwargs):
        priority,task=queue.PriorityQueue.get(self,*args,**kwargs)
        print ("Q. Get:", task)
        return task

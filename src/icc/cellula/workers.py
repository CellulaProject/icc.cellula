from icc.cellula.interfaces import IWorker, ITask, ITerminationTask, IQueue, ISingletonTask
from zope.interface import implementer, Interface
from zope.component import getUtility, queryUtility
import queue
import threading
import logging
import os, io, traceback
import time

logger=logging.getLogger('icc.cellula')

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
        logger.debug("Started thread worker.")
        tasks=GetQueue('tasks')
        results=GetQueue('results', query=True)
        self.waiting=False
        while True:
            logger.debug("waiting for a task.")
            logger.debug("Queue %s has %d tasks." % (tasks, tasks.qsize()))
            self.waiting=True
            task=tasks.get()
            self.waiting=False
            logger.info("got a task %s" % task)
            if ITerminationTask.providedBy(task):
                task_done()
                return
            task.phase="prepare"
            try:
                task.prepare()
            except BaseException as e:
                #traceback.print_exception(type, value, err.__traceback__)
                f=io.StringIO()
                traceback.print_exc(file=f)
                logger.error(f.getvalue())
                logger.error('{!r}; cancelling main task run.'.format(e))
                task.task_done()
                continue
            task.phase="run"
            try:
                rc=task.run()
            except BaseException as e:
                f=io.StringIO()
                traceback.print_exc(file=f)
                logger.error(f.getvalue())
                logger.error('{!r}; some code did not run correctly, proceed with finalization.'.format(e))
                rc=None
            if rc!=None and results != None:
                task.result=rc
                results.put(task)
            task.phase="finalize"
            try:
                task.finalize()
            except BaseException as e:
                f=io.StringIO()
                traceback.print_exc(file=f)
                logger.error(f.getvalue())
                logger.error('{!r}; finalization failde try next task.'.format(e))
            task.phase=None
            tasks.task_done()

    def __call__(self):
        return self.run()

class ProcessWorker(ThreadWorker):
    pass # FIXME stub

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

    def __lt__(self, other):
        return self.priority < other.priority

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
        self.workers=[]
        config = getUtility(Interface, "configuration")["workers"]
        self.threads=int(config.get("threads",2))
        self.processes=int(config.get("processes",2))
        logger.debug("Configured: %d threads and %d processes, Queue: %s. PID=%d. %s" %
                     (
                         self.threads,
                         self.processes,
                         self,
                         os.getpid(),
                         time.time()
                     )
        )

    def run(self):
        for i in range(self.threads):
            w=ThreadWorker()
            t=threading.Thread(target=w, name=w.__class__.__name__+"-%d" % i)
            #t=threading.Thread(target=w)
            self.thread_pool.append(t)
            self.workers.append(w)
            t.start()
        logger.info("List of ThreadWorkers:" + str(self.thread_pool))
        for i in range(self.processes):
            w=ProcessWorker()
            p=threading.Thread(target=w, name=w.__class__.__name__+"-%d" % i)
            self.process_pool.append(t)
            self.workers.append(w)
            p.start()
        if not self.thread_pool:
            #we are the only thread
            logger.info("Scrifice myself for processing.")
            w=ThreadWorker()
            w()
            # Must not reach, by idea.
        while True:
            if not self.join_worker():
                break

    def waiting(self):
        n=0
        for w in self.workers:
            if w.waiting:
                n+=1
        return n

    def processing(self):
        n=0
        for w in self.workers:
            if not w.waiting:
                n+=1
        return n

    def join_worker(self):
        if self.process_pool:
            p=self.process_pool.pop()
            p.join()
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

    def __init__(self, maxsize=0):
        queue.PriorityQueue.__init__(self, maxsize=maxsize)
        self.singletons={}

    def put(self, task, *args, **kwargs):
        logger.debug("Q. Put: " + str(task))
        if ISingletonTask.providedBy(task):
            if task.__class__ in self.singletons:
                return True
            self.singletons[task.__class__]=task
        return queue.PriorityQueue.put(self, task, *args, **kwargs)

    def get(self, *args, **kwargs):
        task=queue.PriorityQueue.get(self,*args,**kwargs)
        logger.debug("Q. Get:" + str(task))
        if ISingletonTask.providedBy(task):
            del self.singletons[task.__class__]
        return task

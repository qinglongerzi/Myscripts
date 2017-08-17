#!/usr/bin/env python

import threading
import multiprocessing
import os

class MyThread(threading.Thread):
    """docstring for MyThread"""
    def __init__(self, thread_id, work_queue, msg_for_proc, args):
        super(MyThread, self).__init__()
        self.thread_id = thread_id
        self.work_queue = work_queue
        self.msg_for_proc = msg_for_proc
        self.args = args
    
    def _do_something(self, args):
        # do something
        pass

    def run(self):
        while not self.work_queue.empty():
            # do something
            self._do_something(self.args)
            self.msg_for_proc.put('sth')
            self.work_queue.task_done()

class MyWorker(multiprocessing.Process):
    """docstring for MyWorker"""
    def __init__(self, worker_id, work_queue, msg_for_proc, thread_count, flag_for_proc, args):
        super(MyWorker, self).__init__()
        self.worker_id = worker_id
        self.work_queue = work_queue
        self.msg_for_proc = msg_for_proc
        self.thread_count = thread_count
        self.flag_for_proc = flag_for_proc
        self.args = args

    def _start_thread(self, thread_count):
        thread_pool = [
            MyThread('%s thread-%d' % (self.worker_id, i),
                     self.work_queue,
                     self.msg_for_proc.
                     self.args
                )
            for i in range(thread_count)
        ]

        for t in thread_pool:
            t.start()
        return thread_pool

    def _wait_for_finish(self):
        main_thread = threading.currentThread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            t.join()

    def run(self):
        if self.flag_for_proc.is_set() is not True:
            #do somthing
            pass
        self._start_thread(self.thread_count)
        self._wait_for_finish()
        

class ProcBase(object):
    """docstring for ProcBase"""
    def __init__(self, arg):
        super(ProcBase, self).__init__()
        self.arg = arg
        self.flag_for_proc = multiprocessing.Event()
        self.flag_for_thread = threading.Event()


    def some_methor(self, args):
        # do something
        pass

    def get_work_queue(self, w_list):
        q = multiprocessing.JoinableQueue()
        if order != 'alpha':
            shuffle(w_list)
        for i in w_list:
            q.put(i)
        return q

    def get_msg_for_proc_like_list(self):
        return q = multiprocessing.Queue()

    def get_msg_for_proc_like_dict(self, *keys):
        q_dict = {}
        for k in keys:
            q_dict[k] = multiprocessing.Queue()
        return q_dict

    def set_proc_flag(self):
        self.flag_for_proc.set()

    def set_thread_flag(self):
        self.flag_for_thread.set()

    def start_worker(self, proc_count, thread_count, work_queue, msg_for_proc, args):
        worker_pool = [
            MyWorker('proc-%d' % i,
                     work_queue,
                     msg_for_proc,
                     thread_count,
                     self.flag_for_proc,
                     args
                )
            for i in range(proc_count)
        ]
        for w in worker_pool:
            w.start()
        return worker_pool


class MyMaster(multiprocessing.Process, ProcBase):
    """docstring for MyMaster"""
    def __init__(self, w_list, args):
        multiprocessing.Process.__init__(self)
        JobBase.__init__(self)
        self.arg = args
        self.proc_count = x
        self.thread_count = y
        self.work_queue = self.get_work_queue(w_list)
        self.msg_for_proc = self.get_msg_for_proc_like_list()
        
    def _do_something(self, args):
        # do something
        pass

    def run(self):
        worker_pool = self.start_worker(self.proc_count, self.thread_count, self.work_queue, self.msg_for_proc, self.args)
        # do something
        self.set_proc_flag()
        self.work_queue.join()
        for w in worker_pool:
            w.join()

class SuperMaster(multiprocessing.Process):
    """docstring for SuperMaster"""
    def __init__(self, w_list, arg):
        super(SuperMaster, self).__init__()
        self.arg = arg
        self.w_list = w_list
        
    def run(self):
        master = MyMaster(self.w_list, self.arg)
        master.start()
        # pid 1 will wait for finish
        os._exit(0)

from datetime import date, datetime, timedelta
from time import sleep
from threading import Thread

class MultiProcesso(Thread):
        def __init__(self, margs=2, group=None, target=None, name=None,
                 args=(), kwargs=None):
            super().__init__(group=None, target=None, name=None,
                 args=args, kwargs=None)
            #self.x = x
            print(margs)
            self.margs = margs
	
        def run(self):
            target(self.margs)

def inicia_Threading():
    while 1:
        sleep(1)
        J = MultiProcesso(name='a', target=target, margs=1)
        J.start()
      
def target(x):
    sleep(5)
    print(datetime.now())
    print(x)
  
T = MultiProcesso(name='b',target=inicia_Threading)
T.start()
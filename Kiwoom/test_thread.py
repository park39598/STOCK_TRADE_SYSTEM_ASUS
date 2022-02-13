from PyQt5.QtCore import QThread, pyqtSignal
import time
import math
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import sys

class main():
    def __init__(self):
        self.test1 = test_task('1', 1)
        self.test2 = test_task('2', 1)
        self.test1.trigger.connect(self.test_func)
        self.test2.trigger.connect(self.test_func)
        self.test1.start()
        self.test2.start()
        self.print_list = []
        self.mutex = QMutex()

    def test_func(self, string):
        self.mutex.lock()
        self.print_list.append(string)
        print(string)
        time.sleep(0.2)
        self.mutex.unlock()

class test_task(QThread):
    trigger = pyqtSignal(list)
    dict_updata = pyqtSignal(str)
    def __init__(self, name, sleep):
        super().__init__()
        self.name = name
        #print(self.name)
        self.sleep = sleep
        self.mutex = QMutex()
        self.cnt=0
    def run(self):
        while True:
            self.cnt=self.cnt+1
            #self.mutex.lock()
            #self.logging.logger.debug("data acquiring")
            time.sleep(self.sleep)
            self.trigger.emit([self.name,self.cnt])
            #print("{}".format(self.name))# portfolio 20개 관리
            #self.mutex.unlock()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = main()

    #kiwoom.quant_algo_fnc('마법공식2')
    app.exec_()

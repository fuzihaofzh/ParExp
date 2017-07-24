import multiprocessing
from cStringIO import StringIO
import sys
import os
import re
import signal
import time
import re
from itertools import *
from datetime import datetime
def colorText(text, color):
    colorMap = {
        'RED' : '\033[31m',
        'GREEN' : '\033[32m',
        'BROWN' : '\033[33m',
        'BLUE' : '\033[34m',
        'PURPLE' : '\095[34m',
        'FAIL' : '\033[91m',
        'ENDC' : '\033[0m',
        'BOLD' : '\033[1m',
        'UNDERLINE' : '\033[4m',
    }
    if color not in colorMap:
        print("Font color does not exists.")
        return text
    return colorMap[color] + text + colorMap['ENDC']
class FileWriter():
    def __init__(self, fileName):
        self.fileName = fileName
    def __enter__(self):
        self.FileHandler = open(self.fileName, 'w+')
        return self
    def __exit__(self, *args):
        self.FileHandler.close()
    def write(self, info):
        self.FileHandler.write(info)
        self.FileHandler.flush()
    def fileno(self):
        return self.FileHandler.fileno()
    def flush(self):
        self.FileHandler.flush()
class PELogger():
    def __init__(self, fileName):
        self.lock = multiprocessing.Lock()
        self.fileName = fileName
    def log(self, info):
        self.lock.acquire()
        try:
            with open(self.fileName, 'a+') as f:
                f.write(info + '\n')
        finally:
            self.lock.release()
def _RunFuncHelper(func, kargs, expName, logFolder):
    print colorText("Start Experiment: ", "BLUE"), expName
    with FileWriter(os.path.join(logFolder, expName + '.log')) as logfile:
        _stdout = sys.stdout
        _stderr = sys.stderr
        sys.stdout = logfile
        sys.stderr = logfile
        try:
            funcret = func(**kargs)
            _stdout.write(colorText("Finish Experiment: ", "GREEN") + expName + '\n')
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logfile.write(tb)
            funcret = tb
            _stdout.write(colorText("Failed Experiment: ", "RED") + expName + '\n')
        finally:
            pass
            sys.stdout = _stdout
            sys.stderr = _stderr
    return funcret
class Extractor():
    def __init__(self, reg, stdout, addStamp):
        self.reg = re.compile(reg)
        self.expNames = []
        self.logPaths = []
        self.logReaders = []
        self.logExtractorStdout = stdout
        self.addStamp = addStamp
        self.extractedLog = ""
    def initExtractor(self):
        map(lambda x: open(x, "a+"), self.logPaths)
        self.logReaders = map(lambda x: open(x, "r+"), self.logPaths)
    def extract(self):
        expNames, timeStamp = [''] * len(self.expNames), [''] * len(self.expNames)
        if self.addStamp:
            expNames = map(lambda x: '[' + x + ' ' , self.expNames)
            timeStamp = [datetime.now().strftime('%Y/%m/%d-%H:%M:%S]')] * len(self.expNames)
        searchedLogs = '\n'.join(imap(lambda z: ''.join([z[2], z[1], z[0]]), ifilter(lambda y: len(y[0]) > 0, zip(imap(lambda x: '\n'.join(self.reg.findall(x.read())), self.logReaders), timeStamp, expNames))))
        if len(searchedLogs.strip()) > 0:
            self.logExtractorStdout.write(searchedLogs.strip() + '\n')
            self.logExtractorStdout.flush()
        self.extractedLog += searchedLogs
    def close(self):
        self.logExtractorStdout.close()
    def addExpInfo(self, name, path):
        self.expNames.append(name)
        self.logPaths.append(path)
    def getExtractedLog(self):
        return self.extractedLog
def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
class ParExp():
    def __init__(self, procNum = 5, logFolder = 'log'):
        self.logFolder = logFolder
        self.procNum = procNum
        self.reset()
        self.results = None
        if not os.path.exists(self.logFolder):
            os.makedirs(self.logFolder)
    def reset(self):
        self.pool = None
        self.helperReturn = []
        self.expNames = []
        self.logExtractors = []
        self.addable = True
        self.extractedInfo = ""
    def getTimeStamp(self):
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    def getExtractedInfo(self):
        return self.extractedInfo
    def add(self, func, argsMap):
        if not self.addable:
            self.reset()
            self.addable = True
        if self.pool is None:
            self.pool = multiprocessing.Pool(self.procNum, init_worker)
        expName = '_'.join([self.getTimeStamp(), str(func)] + [i + 'EQ' + str(argsMap[i]) for i in argsMap])
        expName = re.sub('<(function |)', '', expName)
        expName = re.sub(' (instance |object |)at(\d|\w| )+>', '', expName)
        expName = re.sub('[\%\/\<\>\^\|\?\&\#\*\\\:\" \n]', '', expName)
        self.expNames.append(expName)
        for extractor in self.logExtractors:
            extractor.addExpInfo(expName, os.path.join(self.logFolder, expName + '.log'))
        self.helperReturn.append(self.pool.apply_async(_RunFuncHelper, (func, argsMap, expName, self.logFolder)))
    def join(self):
        self.addable = False
        try:
            self.pool.close()
            for extractor in self.logExtractors:
                extractor.initExtractor()
            while(not all(map(lambda x: x.ready(), self.helperReturn))):
                time.sleep(1)
                map(lambda x: str(x.extract()), self.logExtractors)
        except KeyboardInterrupt:
            print "Keyboard Interrupted by User."
            self.pool.terminate()
            self.pool.join()
            self.results = None
        else:
            self.pool.join()
            self.pool = None
            rert = map(lambda x:x.get(), self.helperReturn)
            self.results = rert
            self.extractedInfo = map(lambda x: x.getExtractedLog(), self.logExtractors)
    def map(self, func, parLst):
        for par in parLst:
            self.add(func, par)
        self.join()
    def getResults(self):
        return self.results
    def addExtractor(self, reg, stdout = sys.stdout, addStamp = False):
        self.logExtractors.append(Extractor(reg, stdout, addStamp))
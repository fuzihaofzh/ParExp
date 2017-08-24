import unittest
import uuid
from ParExp import *
import os
import shutil
def worker1(par):
    print "Print some thing."
    print "The value of par: {par}".format(par = par)
    return par
def runcmd(par):
    import subprocess
    ocmd = ["cat", par]
    print ocmd
    subprocess.call(ocmd, stdout = sys.stdout, stderr = sys.stderr)
    return par
def haveExpName(par, myExpName):
    print "The exp name is: ", myExpName
    return myExpName
class ParExpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logDir = "test_" + str(uuid.uuid1())
        os.mkdir(cls.logDir)
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.logDir, ignore_errors=True)
        print "exit.."
    def setUp(self):
        print "In method: ", self._testMethodName
    def testBasic(self):
        pe = ParExp(10, self.logDir)
        pe.map(worker1, [{"par": 1}, {"par": 2}, {"par": 3}])
        self.assertEqual(pe.getResults(), [1, 2, 3])
        content = map(lambda x: open(os.path.join(self.logDir, x + ".log")).read(), pe.expNames)
        self.assertTrue(all(map(lambda x: "Print some thing.\nThe value of par:" in x, content)))
    def testRerun(self):
        pe = ParExp(10, self.logDir)
        pe.map(worker1, [{"par": 1}, {"par": 2}, {"par": 3}])
        self.assertEqual(pe.getResults(), [1, 2, 3])
        pe.map(worker1, [{"par": 1}, {"par": 2}, {"par": 3}])
        self.assertEqual(pe.getResults(), [1, 2, 3])
        content = map(lambda x: open(os.path.join(self.logDir, x + ".log")).read(), pe.expNames)
        self.assertTrue(all(map(lambda x: "Print some thing.\nThe value of par:" in x, content)))
    def testExtractor(self):
        pe = ParExp(10, self.logDir)
        logFileName = os.path.join(self.logDir, "test_" + str(uuid.uuid1()) + ".log")
        pe.addExtractor("The value", open(logFileName, "w"))
        pe.map(worker1, [{"par": 1}, {"par": 2}, {"par": 3}])
        self.assertEqual(pe.getResults(), [1, 2, 3])
        logContent = open(logFileName, "r").read()
        self.assertTrue("The value" in logContent)
        self.assertTrue(not any(map(lambda x: x in logContent, pe.expNames)))
    def testExtractorWithStamp(self):
        pe = ParExp(10, self.logDir)
        logFileName = os.path.join(self.logDir, "test_" + str(uuid.uuid1()) + ".log")
        pe.addExtractor("The value", open(logFileName, "w"), True)
        pe.map(worker1, [{"par": 1}, {"par": 2}, {"par": 3}])
        self.assertEqual(pe.getResults(), [1, 2, 3])
        logContent = open(logFileName, "r").read()
        self.assertTrue(all(map(lambda x: x in logContent, pe.expNames)) and "The value" in logContent)
    def testExtractorGetAll(self):
        pe = ParExp(10, self.logDir)
        logFileName = os.path.join(self.logDir, "test_" + str(uuid.uuid1()) + ".log")
        pe.addExtractor("The value", open(logFileName, "w"))
        pe.map(worker1, [{"par": 1}, {"par": 2}, {"par": 3}])
        self.assertEqual(pe.getResults(), [1, 2, 3])
        extractedInfo = pe.getExtractedInfo()
        logContent = open(logFileName, "r").read()
        self.assertEqual(logContent.strip(), extractedInfo[0].strip())
        self.assertTrue("The value" in logContent)
        self.assertTrue(not any(map(lambda x: x in logContent, pe.expNames)))
    def testTwoExtractor(self):
        pe = ParExp(10, self.logDir)
        logFileName = os.path.join(self.logDir, "test_" + str(uuid.uuid1()) + ".log")
        pe.addExtractor("The value", open(logFileName, "a+"))
        pe.addExtractor("Print some.+", open(logFileName, "a+"))
        pe.map(worker1, [{"par": 1}, {"par": 2}, {"par": 3}])
        self.assertEqual(pe.getResults(), [1, 2, 3])
        logContent = open(logFileName, "r").read()
        self.assertTrue("The value" in logContent)
        self.assertTrue("Print some" in logContent)
        self.assertEqual(pe.getExtractedInfo(), ['The value\nThe value\nThe value', 'Print some thing.\nPrint some thing.\nPrint some thing.'])
        self.assertTrue(not any(map(lambda x: x in logContent, pe.expNames)))
    def testRunCmd(self):
        pe = ParExp(10, self.logDir)
        fileName = os.path.join(self.logDir, "test_" + str(uuid.uuid1()) + ".txt")
        with open(fileName, "w") as f:
            f.write("test str\nnext line!")
        pe.map(runcmd, [{"par": fileName}, {"par": fileName}, {"par": fileName}])
        self.assertEqual(pe.getResults(), [fileName, fileName, fileName])
        content = map(lambda x: open(os.path.join(self.logDir, x + ".log")).read(), pe.expNames)
        self.assertTrue(all(map(lambda x: "test str\nnext line!" in x, content)))
        self.assertTrue(all(map(lambda x: "cat" in x, content)))
        self.assertTrue(all(map(lambda x: fileName in x, content)))
    def testExpNamePar(self):
        pe = ParExp(10, self.logDir)
        logFileName = os.path.join(self.logDir, "test_" + str(uuid.uuid1()) + ".log")
        pe.addExtractor("The exp name is: .+", open(logFileName, "a+"))
        pe.map(haveExpName, [{"par": 1}, {"par": 2}, {"par": 3}], passExpNameVar = "myExpName")
        logContent = open(logFileName, "r").read()
        self.assertTrue(all(map(lambda x: x in logContent, pe.expNames)))
if __name__ == '__main__':
    unittest.main()

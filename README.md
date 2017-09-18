# ParExp
A Parallel Experiment Lib

## Usage
```
from ParExp import ParExp
def worker1(par):
    print "Print some thing."
    print "The value of par: {par}".format(par = par)
    return par
if __name__ == '__main__':
    pe = ParExp(10, "logs")
    pe.addExtractor("The value.+", open("logs/trainResult.txt", "w"), True)
    pe.map(worker1, [{"par" : 0.02}, {"par" : 0.05}, {"par" : 0.1}])
```



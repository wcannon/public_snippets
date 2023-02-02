#!/usr/bin/env python3

mylist = "a b c d e f g h i j k l".split()

bsize = 3
start = 0
end = bsize
rounds = len(mylist) // bsize
modulo = len(mylist) % bsize # check if we need to grab extra

for i in range(rounds):
    #print(f"start: {start}")
    #print(f"end: {end}")
    tl = mylist[start:end]
    print(tl)
    start += bsize
    end += bsize
if modulo:
    tl = mylist[start:]
    print(tl)
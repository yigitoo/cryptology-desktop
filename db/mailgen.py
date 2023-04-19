import numpy as np
isimler = ["fatma","mehmet","ahmet","ali","nisan","irem","efe","ayaz","ayşe","yiğit","ramazan","orkun","zeynep","salih","deniz","nehir","elif","enes","ege","muhammed","eren","berra","hatice"]
l = []
for _ in range(100):
    if int(np.random.randint(10))%2:
        s = np.random.choice(isimler) + np.random.choice(isimler) +'@gmail.com'
    else:
        s = np.random.choice(isimler) + str(np.random.randint(1000000)) +'@gmail.com'

    l.append(s)
o = ""
for i in l:
    o+=i+'\n'
open('maillist.csv','w+').write(o)
d = open('soru.txt','r').read()
dict = {}
sorular = []
alar = []
bler = []
cler = []
dler = []
eler = []
l = d.split('\n')
for i in range(len(l)):
    if i % 7 == 0:
        sorular.append(l[i])
    if i % 7 == 1:
        alar.append(l[i])
    if i % 7 == 2:
        bler.append(l[i])
    if i % 7 == 3:
        cler.append(l[i])
    if i % 7 == 4:
        dler.append(l[i])
    if i % 7 == 5:
        eler.append(l[i])

dogrular = [1, 2, 3, 4, 5, 5, 4, 3, 2, 1, 1, 2, 3, 4, 5]
x = zip(dogrular, sorular,alar,bler,cler,dler,eler)
x = list(x)
y = []
for i in x:
    y.append(list(i))

liste = []
for i in range(len(y)):
     liste.append({
        "numb": i+1,
        "question": y[i][1],
        "answer": y[i][y[i][0] + 1],
        "options": [
            y[i][2],
            y[i][3],
            y[i][4],
            y[i][5],
            y[i][6]
        ]

    })

print(liste)


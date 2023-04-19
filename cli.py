#!/bin/python3
import numpy as np
from scipy.io.wavfile import write
from PIL import Image
import os
import moviepy.video.io.ImageSequenceClip
import cv2
from scipy.io import wavfile
from scipy.io.wavfile import write
from natsort import natsorted
import sys
import contextlib
import wave
import threading
from concurrent.futures import ThreadPoolExecutor
from itertools import groupby
import json
from multiprocessing.pool import Pool

u200d = '‍'
key = []
morse_dict = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', ' ': '-.--.-.', '0': '-----',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '&': '.-...', "'": '.---.', '@': '.--.-.', ')': '-.--.-', '(': '..--.-',
    ':': '-.---', ',': '-..--', '=': '-...-', '!': '-.-.--', '.': '.-.-.-',
    '-': '-....-', '+': '.-.-.', '"': '.-..-.', '?': '..--..', '/': '-..-.',
    'Ğ': '...-.-', 'Ü': '.-...-', 'Ş': '.----.', 'Ç': '.-.--.',
    'İ': '-..---', '\n': '--..-.', 'Ö': '-.--.',
    '’': '.-.-..', '‘': '--.-.-',
    ';': '--..--'
}


f = open('d.txt','w')
o = ""
d = {}
rd = {}
additions = ['ı','ğ','ü','ş','ö','ç','Ğ','Ü','Ş','Ö','Ç','İ']
for i in range(33,127):
    d[str(i-32)] = chr(i)
    rd[chr(i)] = str(i-32)

for i in range(len(additions)):
    d[str(95+i)] = additions[i]
    rd[additions[i]] = str(95+i)

def lower(s):
    if s == "I":
        return "ı"
    else:
        return s.lower()
    
def upper(s):
    if s == "i":
        return "İ"
    else:
        return s.upper()    
    
def clear_dirs():
    dirs = ['dirs/imgs', 'dirs/imgs2', 'dirs/imgsr', 'dirs/wavs', 'dirs/wavr', 'dirs/framesr']
    if os.name == "nt":
        for i in dirs:
            os.system(f"rd /s {i}")
            os.system(f"mkdir {i}")
            os.system(f'cd {i}')
            os.system(f'echo.>.gitkeep')
            os.system('cd ..')
    if os.name == "posix":
        for i in dirs:
            os.system(f"rm -f {i}/* #&& touch {i}/.gitkeep")

rdict = {}
for i in morse_dict:
    rdict[morse_dict[i]] = i

    # md.pop(md[-1])
    # md.append(md[-1][:1])


def saveul(s):
    r = ""
    for i in s:
        r += str(int(i.isupper()))
    return r

def strint(s):
    l = len(s)
    o = 0
    for i in range(l):
        o += int(rd[s[i]])*106**(i)
    return o

def intstr(s):
    o = ""
    for i in range(np.ceil(np.log(s,106))):
        o += d[str(s//106**(i)%106)]
    return o

def compbin(bin):
    first = bin[0]
    l = []
    o = ""
    for _, group in groupby(bin):
        l.append(len(''.join(group)))

    # print(l)
    for i in l:
        if i >= 10:
            if not i % 9 == 0:
                for _ in range(i//9):
                    o += "90"
                o += str(i % 9)
            else:
                for _ in range(i//9-1):
                    o += "90"
                o += str(9)
        else:
            o += str(i)
    o += first
    return o


def decompbin(s):
    first = s[-1]
    l = s[:-1]
    o = ""
    if first == "1":
        for i in range(len(l)):
            currentbin = int(i % 2 == 0)
            o += str(currentbin)*int(l[i])
            # print(o)
    if first == "0":
        for i in range(len(l)):
            currentbin = int(i % 2 != 0)
            o += str(currentbin)*int(l[i])
    return o


def text_to_morse(text):
    morse = []
    for i in text:
        try:
            morse.append(morse_dict[upper(i)])
        except:
            morse.append(morse_dict[i])
        
    return ' '.join(morse)


def morse_to_text(text: str = None):
    #morse_text = text.split()
    #result = ""
    # for char in morse_text:
    #    result+=rdict[char]
    # print(result)
    return rdict[text]



def rgb2wve(n):
    s = 0
    s += int(n[0]*256**2)
    s += int(n[1]*256)
    s += int(n[2])
    return s


def wve2rgb(ln):
    n1 = ln // 256 // 256 % 256
    n2 = ln // 256 % 256
    n3 = ln % 256
    return np.array([n1, n2, n3])


def arr2rgb(arr):
    arr2 = []
    for i in range(len(arr)):
        arr2.append(wve2rgb(arr[i]*10**6))
    return arr2


def find_shape_difference(inp):
    l = inp.__len__()
    l2 = (np.ceil(np.sqrt(l)))**2
    return l2-l, int(np.sqrt(l2))


def arr2image(arr):
    fsd = find_shape_difference(arr)
    s = np.random.choice(255, 3)
    new_array = np.append(arr, ([255, 0, 0]*int(fsd[0])))
    new_array = new_array.reshape(fsd[1], fsd[1], 3)
    return new_array


def savearrayasimg(ar, out):
    ar = np.array(ar, dtype=np.uint8)
    img = Image.fromarray(ar)
    img = img.convert('RGB')
    img.save(out)


def frames2video(folder, out):
    imgs = [os.path.join(folder, i)
            for i in os.listdir(folder)
            if i.endswith(".png")]
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(imgs, fps=60,)
    clip.write_videofile(out, logger=None)


def video2images(vid):
    v = cv2.VideoCapture(vid)
    v.set(cv2.CAP_PROP_FPS, 1)
    s = 1
    c = 0
    while s:
        s, img = v.read()
        try:
            cv2.imwrite(f'dirs/framesr/{c}.png', img)
        except:
            pass
        c += 1


def get_duration(fname):
    with contextlib.closing(wave.open(fname, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return duration


def decodewavs(folder):
    ar2 = ""
    for i in natsorted(os.listdir(folder)):
        len = get_duration(fname="".join([folder, "/", i]))
        if len >= 0.1 and len <= 0.25:
            ar2 += "."
        if len <= 0.5 and len > 0.25:
            ar2 += "-"
        if len == 1:
            ar2 += " "
    return ar2


def img2wavc(img):
    img = Image.open(img)
    img = img.convert('RGB')
    ar = np.asarray(img)
    ar2 = np.array([])
    for i in ar.flatten():
        ar2 = np.append(ar2, i)
    ar2 = np.array_split(ar2, len(ar2)/3)
    for i in range(len(ar2)):
        ar2[i] = rgb2wve(ar2[i])
    return np.array(ar2)


def wavs2img(folder):
    for i in natsorted(os.listdir(folder)):
        key.append(str(i[0]))
        samplerate, data = wavfile.read(os.path.join(folder, i))
        ar = arr2rgb(data)
        ar = arr2image(ar)
        savearrayasimg(ar, out=f"dirs/imgs/{i}".replace(".wav", ".png"))


def createsound(c, n):
    k = 1
    if c == ".":
        fs = int(np.random.uniform(200, 500, (1, 1)))
        samplerate = 22050
        k = int(np.random.uniform(4, 10, (1, 1)))
    if c == "-":
        fs = int(np.random.uniform(0.5, 0.9, (1, 1)))
        samplerate = 44100
        k = int(np.random.uniform(3, 4, (1, 1)))
    if c == " ":
        fs = int(np.random.uniform(800, 1000, (1, 1)))
        samplerate = 88200
        k = 1
    samplerate = 44100
    t = np.linspace(0., 1., samplerate)
    amplitude = np.iinfo(np.int16).max
    data = amplitude * np.sin(2. * np.pi * fs * t)
    data = data[0:len(data)//k]
    write(f"./dirs/wavs/{n}.wav",
          samplerate, data.astype(np.int16))


def morse2wavs(data):
    for char in range(len(data)):
        if data[char] == ".":
            createsound(".", char)
        if data[char] == "-":
            createsound("-", char)
        if data[char] == " ":
            createsound(" ", char)


def unitedwavs(folder):
    ar2 = np.array([])
    for i in natsorted(os.listdir(folder)):
        sr, d = wavfile.read(os.path.join(folder, i))
        ar2 = np.append(ar2, np.append(d, 0.31415))
    write('uw.wav', data=ar2, rate=44100)
    return ar2


def resizeimgs(folder):
    list = natsorted(os.listdir(folder))
    for i in list:
        ar = np.asarray(Image.open(os.path.join(folder, i)))
        s = ar.shape
        key[list.index(i)] += str(str(s[0])+str(np.random.randint(10))+str(s[1]))
        k = 300
        ta = k**2-s[1]**2
        ar = ar.flatten()
        sa = np.array([])
        sa = np.append(sa, tuple(np.random.choice(255, 3*(ta))))
        # ar = np.append(ar, [0]*ta*3)
        ar = np.append(ar, sa)
        ar = np.array(ar, dtype=np.uint8)
        img = Image.fromarray(ar.reshape(300, 300, 3))
        img.save(f'dirs/imgs2/{i}')




def originsizeimgs(folder):
    for i in natsorted(os.listdir(folder)):
        indexes = []
        iar = np.asarray(Image.open(os.path.join(folder, i)))
        ar = iar.flatten()
        ar = np.split(ar, len(ar)/3)
        np.savetxt('ard0.csv', ar)
        for j in range(len(ar[0])):
            if (ar[j] == [0, 0, 0]).any():
                indexes.append(j)
        ar = np.delete(ar, indexes)
        np.savetxt('ard0.csv', ar)
        img = Image.fromarray(ar)
        img = img.convert('RGB')
        img.save(f'dirs/imgsr/{i}.png')


def parseul(l):
    l2 = list(l)
    cl = []
    s = 5
    for i in range(0, len(l2), s):
        cl.append(l2[i:i+s])
    l3 = []
    for i in cl:
        l4 = ''
        for j in i:
            l4 += j
        l3.append(l4)
    return l3


def encryptul(l):
    o = ""
    for i in l:
        o += chr(int(i)+10000)
    return o


def sizeviakey(folder, key):
    l = natsorted(os.listdir(folder))
    key = solvekey(key)[0]
    for i in l:
        img = Image.open(os.path.join(folder, i))
        ar = np.asarray(img).flatten()

        vfi = key[l.index(i)]
        vfis = vfi[1:]
        vfis = vfis[: int(np.ceil(len(vfis)/2))-1]
        s = [int(vfis), int(vfis), 3]
        ar = ar[: 3*int(s[0])**2]
        ar = np.array(np.array_split(ar, len(ar)/3))
        ar = ar.reshape(s)
        img = Image.fromarray(ar, 'RGB')
        img = img.convert('RGB')
        img.save(f'dirs/imgsr/{i}')


def encryptkey(key):
    ar2 = []
    for vfi in key.split('\u200d'):
        vfis = vfi[1:]
        vfis = vfis[:int(np.ceil(len(vfis)/2))-1]
        a = str(vfis) + str(np.floor(np.random.uniform(10, 99, (1, 1))[0][0]))
        ar2.append(chr(int(float(a))%1114111))
    r = ""
    for i in ar2:
        r += i
    return r


def decryptkey(key):
    ar2 = []
    for i in key:
        val = str(ord(i))
        val = val[:-2]
        c = str(key.index(i) % 10)
        c += val+"0"+val
        ar2.append(c)
    r = ""
    for i in ar2[:-1]:
        r += i+'\u200d'
    return r


def setkey(key, keyf):
    r = ""
    for i in key:
        r += i+'\u200d'
    ar2 = []
    for i in range(len(r)):
        ar2.append(str(str(r[i])))
    # for i in range(len(ar2)):
        # ar2[i] = chr(int(i))
    # r = ""
    for i in ar2:
        r += i

    # r = encryptkey(r)
    open(keyf, 'w+').write(r)    
    return r


def encryptkeyfile(keyf, val):
    k = open(keyf, 'r')
    key = k.read()
    key = encryptkey(key)
    k = open(keyf, 'w')
    k.write(key+'\n'+encryptul(parseul(str(int(compbin(saveul(val)))))))


def solvekey(key):
    ar = key.split("\u200d")
    return ar, ar[-1]


def changeul(s, val):
    r = ""
    for i in range(len(s)):
        if val[i] == "1":
            r += upper(s[i])
        if val[i] == "0":
            r += lower(s[i])
    return r

def spkeydec(vfn, kf, passwd):
    vf = open(vfn,'rb')
    enckey = vf.read().split(b'\xe2\x80\x8d')[1:]
    key = ""
    for i in enckey:
        key+=chr(int(i)-int(strint(passwd)))
    open(kf,'w+').write(key)
    complete_decryption(vfn,kf)
    
def spkeyenc(data, vfn, kf, passwd):
    complete_encryption(data,vfn, kf)
    vf = open(vfn,'ab')
    kf = open(kf,'r+')
    toadd = ""
    for i in kf.read():
        toadd+=u200d+str(ord(i)+strint(passwd))
    vf.write(toadd.encode())
    
def complete_encryption(data, outvideo, keyf):
    os.system(f'rm -rf {outvideo}')  # aynı isimde dosya varsa siler
    morse_data = text_to_morse(data)  # veriyi mors koduna çevirir
    morse2wavs(morse_data)  # mors kodunu wav dosyalarına çevirir
    wavs2img('dirs/wavs')  # wav dosyalarını resme çevirir
    resizeimgs('dirs/imgs')# resimleri eşit boyda olmak üzere yeniden boyutlandırır
    # unitedwavs('wavs')  # wav dosyalarını birleştirir
    frames2video('dirs/imgs2', outvideo)# resimleri ardı ardına koyarak video oluşturur
    setkey(key, keyf)  # videoyu çözmek için gerekli olan anahtarı oluşturur
    encryptkeyfile(keyf, data)  # anahtar dosyasını şifreler


def tothread(n):
    ar = img2wavc(f'dirs/imgsr/{n}')
    write(filename=f'dirs/wavr/{n}'.replace('.png', '.wav'), data=ar, rate=44100)


def complete_decryption(vid, keyf):
    video2images(vid)
    dk = open(keyf, 'r').read()
    try:
        sizeviakey('dirs/framesr', decryptkey(dk))
    except ValueError:
        raise SystemExit("Girdiğin anahtar yanlış!")
    imgdir = natsorted(os.listdir('dirs/imgsr'))
    def w3thread():
        global pool
        pool = Pool(8)
        for i in imgdir:
            pool.apply_async(tothread, (i,))
        pool.close()
        pool.join()

    def wthread():
        threads = []
        for i in imgdir:
            t = threading.Thread(target=tothread, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def wothread():
        for i in imgdir:
            tothread(i)

    def w2thread():
        processes = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for i in imgdir:
                processes.append(executor.submit(tothread, i))

    w3thread()
    md = decodewavs('dirs/wavr')
    # md.append(md[-1][:1])
    s = ""
    o = ""
    o2 = []
    for i in md:
        s += i
    print(md)
    print(len(md))
    ml = s.split(' ')

    if len(md) > 34:
        ml[-1] = ml[-1][:-1]

    for j in range(len(ml)):
        try:
            o2.append(morse_to_text(ml[j]))
        except KeyError:
            if not j == len(ml)-1:
                o2.append(morse_to_text(ml[j]))
            else:
                o2.append(morse_to_text(ml[j][:-1]))
    for i in o2:
        o += i
    print(dk)
    ud = ""
    for i in (solvekey(dk)[1].split('\n')[1]):
        ud += str(ord(i)-10000)
    print(ud)
    print(changeul(o, decompbin(str((ud)))))


if __name__ == "__main__":
    config = json.load(open('config.json', 'r'))
    ifname = config['fileToEncrypt']
    ofname = config['outVideoFile']
    kfname = config['keyFile']
    data = open(ifname, 'r').read()
    outVideo = ofname
    if len(sys.argv) == 1:
        raise SystemExit("Argüman belirtmeniz gerekli")
    if sys.argv[1] in ["--clear", "-cls", "--cls", "-clear", "-C"]:
        clear_dirs()
        
    if sys.argv[1] == ["-e", "-ce", "--complete-enc"]:
        clear_dirs()
        complete_encryption(data, outVideo, kfname)
    if sys.argv[1] == ["-d", "-cd", "--complete-dec"]:
        complete_decryption(outVideo, kfname)
        
    if sys.argv[1] == "-ced" or (sys.argv[1] == "-c" and sys.argv[2] == "-d"):
        clear_dirs()
        complete_encryption(data, outVideo, kfname)
        complete_decryption(outVideo, kfname)

    if sys.argv[1] in ["-h", "--h", "--help", "-help"] :
        guide = open('guide.txt', 'r').read()
        print(guide)
        guide.close()

    if sys.argv[1] == "-s":
        b = input('C/D: ')
        p = input('password: ')
        if b == "C":
            spkeyenc(data, outVideo, kfname, p)
        if b == "D":
            spkeydec(outVideo, kfname, p)
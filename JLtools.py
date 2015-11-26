__author__ = 'Jonathan'

import json, csv
import tarfile
import pandas
import xlrd
import scipy
import numpy

def tarunzip(filegz):
    tar = tarfile.open(filegz)
    tar.extractall()
    tar.close()

def csvhead(fieldnamz,csvfile):
    id_write = csv.DictWriter(csvfile, fieldnames=fieldnamz, lineterminator = '\n')
    #print(fieldnamz)
    id_write.writeheader()
    return id_write

def unqidsD(listElem, IDdict, ID):
    if listElem not in IDdict[ID]:
        IDdict[ID].append(listElem)
        for key in IDdict:
            if key != ID:
                IDdict[key].append(0)

def unqidsL(listElem, IDlst):
    if listElem not in IDlst:
        IDlst.append(listElem)

def listPos(value, lst):
    posn = [i for i,y in enumerate(lst) if y == value]
    return posn

def listDict(source,value):
    for entry in source:
            try:
                out = entry[value]
            except:
                pass
    return out

def unqLstCSV(csvfl, lstDict):
    keys = sorted(lstDict.keys())
    with open(csvfl, 'w') as keyfile:
        cswr = csv.writer(keyfile)
        cswr.writerow(keys)
        cswr.writerows(zip(*[lstDict[key] for key in keys]))
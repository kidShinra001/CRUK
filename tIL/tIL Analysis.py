__author__ = 'Jonathan'

#add functionality to check for duplicates, many similar error rates occurring for users. :S Try to identify which classifications are giving same error rates...

import json, re, csv
import matplotlib.pyplot as plt
import JLtools as jl
import pandas as pd
from copy import deepcopy

def create_GSlist(GSfl):
    GoldList = {}
    with open("tIL GSimages.csv") as GS_file:
        reader = csv.reader(GS_file)
        for row in reader:
            for entry in row:
                GoldList[entry[0:len(entry)-4]]={'count':0, 'errorList':[], 'error':'N/A'}
    return GoldList

GoldList = create_GSlist("tIL GSimages.csv")

def pull_GSdata(GoldList):
    m = 0
    GSdata = dict()
    for file in GoldList.keys():
        #file = file[0:len(file)-4]
        data_file = 'Gold_Std_GiStIL_data/' + file + '.xlsx'
        GSdata[file] = jl.pandas.read_excel(data_file, sheetname='Sheet1', header=None, names=['x','y']).sort_values(by=['x'], ascending='True')
        m += 1
    return GSdata
        #if m == 1:
        #    break

GSdata = pull_GSdata(GoldList)

n = 0
n2 = 0
n3 = 0
n4 = 0
time2 = 0
Images = set()
IDlist = {'N/A':{'count':0, 'errorList':[], 'error':'N/A'}}

with open("sanitized_impossible_line_2015-11-11/impossible_line_classifications.json") as source_file:
    for row in source_file:

        data = json.loads(row)
        inp = data['annotations'][0]['results']
        time = data['created_at']['$date']

        if time > 1437609600000: #after launch date
            if n >= 0:
                # if (time-time2) < 5000:
                #     print(time-time2)
                #     n3 += 1
                # time2 = time

                inp = eval(inp)
                try:
                    uid = inp['userid']
                except:
                    uid = 'N/A'
                #print(uid)
                if uid not in IDlist.keys():
                    IDlist[uid]={'count':0, 'errorList':[], 'error':'N/A'}
                IDlist[uid]['count'] += 1

                coord = jl.pandas.DataFrame(columns=('x1', 'x2', 'y'))
                pos = 0

                for entry in inp['processedresults']:
                    avey = (float(entry['point1']['y']) + float(entry['point2']['y']))/2
                    if float(entry['point1']['x']) < float(entry['point2']['x']):
                        coord.loc[pos] = [float(entry['point1']['x']),float(entry['point2']['x']),avey]
                    else:
                        coord.loc[pos] = [float(entry['point2']['x']),float(entry['point1']['x']),avey]
                    pos += 1
                coord.sort_values(by=['x2'], ascending='True')

                #print(coord)

                fl = inp['filename'][0:len(inp['filename'])-4]
                Images.add(fl)

                lth = int(len(coord))

                #print(fl)

                print(n)



                if fl in GoldList and uid != 'N/A':
                    n2 += 1
                    GoldList[fl]['count'] += 1

                    GScoord = deepcopy(GSdata[fl])

                    startx = GScoord['x'][0]
                    GScoord['x'] -= startx
                    coord['x1'] -= startx
                    coord['x2'] -= startx
                    if coord['x1'][0] < 0:
                        coord['x1'][0] = 0
                    xmax = max(GScoord['x'])
                    GScoord['x'] /= xmax
                    coord['x1'] /= xmax
                    coord['x2'] /= xmax
                    coord = coord[(coord.x1<=1) | (coord.x2<=1)]
                    coord.x2[coord.x2 >1] = 1
                    coord.x1[coord.x1 >1] = 1
                    coord['x2'][len(coord)-1] = 1
                    GScoord['x2']=GScoord['x'].shift()
                    GScoord['x2'][0]=0

                    calc = []
                    xco = 1
                    xs = list(coord['x1'])+list(coord['x2'])+list(GScoord['x'])

                    while xco > 0:
                        yco = coord['y'][(coord['x2']>=xco) & (coord['x1']<xco)]
                        relxs = [x for x in xs if x<xco]
                        xco2 = max(relxs)
                        if len(yco) >0:
                            avy = sum(yco)/len(yco)
                            GSy = float(GScoord['y'][(GScoord['x']>=xco) & (GScoord['x2']<xco)])

                        calc.append(abs(xco-xco2)*abs(GSy-avy))
                        xco = xco2



                    IDlist[uid]['errorList'].append(sum(calc))
                    IDlist[uid]['error']= (sum(IDlist[uid]['errorList'])/len(IDlist[uid]['errorList'])*100)

                    GoldList[fl]['errorList'].append(sum(calc))
                    GoldList[fl]['error']= (sum(GoldList[fl]['errorList'])/len(GoldList[fl]['errorList'])*100)

                #plt.plot(xs[0:lth],ys[0:lth],'ro')
                #plt.show()

            n += 1

            #if n == 4600:
            #    break
        else:
            n4 += 1

def build_panda(source, field1, out_file):
    errors = jl.pandas.DataFrame(columns=(field1, '% Error', 'Errors'))
    pos = 0
    for entry in source:
        errors.loc[pos] = [entry, source[entry]['error'], source[entry]['errorList']]
        pos += 1

    errlist = errors[errors['% Error'] != 'N/A']
    print(sum(errlist['% Error'])/len(errlist), min(errlist['% Error']), errlist[field1][errlist['% Error'].idxmin()], max(errlist['% Error']), errlist[field1][errlist['% Error'].idxmax()])

    errors.to_csv(out_file)

build_panda(IDlist, 'UserID', 'tIL UserErrors.csv')
build_panda(GoldList, 'File', 'tIL GSErrors.csv')

print('records: ' + str(n), 'GS: ' + str(n2), n3, 'skipped: ' + str(n4))

#     plt.hist(GSco)
#     plt.title('tIL Gold Std Classifications')
#     plt.xlabel('number of classificatons/image')
#     plt.ylabel('frequency')
#     plt.show()
#
# with open('tILkey.csv', 'w') as keyfile:
#     fieldnamz = ['ID', 'count']
#     headwr = jl.csvhead(fieldnamz,keyfile)
#     for rw in range(len(IDlist['UID'])):
#         headwr.writerow({'ID': IDlist['UID'][rw], 'count': IDlist['count'][rw]})
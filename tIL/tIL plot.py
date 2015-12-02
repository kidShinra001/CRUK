__author__ = 'Jonathan'

import JLtools as jl
import matplotlib.pyplot as plt
import statistics

#change way to calc error based on different aggregations

data_file = 'tIL GSErrors.json'

TryList = jl.pandas.read_json(data_file)
#print(TryList.loc[0])
a = TryList[TryList['count']>0]
#print(a['coords'].loc[0])
#aa = a['coords']
#print(aa.loc[0])
#print(aa)
#ab = a['File']
n = 0

def pull_GSdata(GoldList):
    m = 0
    GSdata = dict()
    for file in GoldList:
        #file = file[0:len(file)-4]
        data_file = 'Gold_Std_GiStIL_data/' + file + '.xlsx'
        GSdata[file] = jl.pandas.read_excel(data_file, sheetname='Sheet1', header=None, names=['x','y'])#.sort_values(by=['x'], ascending='True')
        i = 0
        pre_entry = 0
        for enty in GSdata[file]['x']:
            if (enty < pre_entry) & (pre_entry != 0):
                GSdata[file].loc[i, 'x'] = pre_entry
            i += 1
            pre_entry = enty
        m += 1
        z = TryList[TryList['File'] == file]['corrections'].iloc[0]
        GSdata[file]['x'] -= z[0]
        GSdata[file]['x'] /= z[1]
    return GSdata
        #if m == 1:
        #    break

GSdata = pull_GSdata(list(a['File']))

for k, item in a.iterrows():
    flnm = item.File
    errr = item.error
    users = item['count']
    print(flnm)
    b =jl.pandas.DataFrame(item.coords)#.sort_values(by='x1')
    #print(b)
    cc = list(b['x1']) + list((b['x2']))
    c = list(set(cc)) #this needs to include x2 too
    #print(min(c))
    xco = max(c)
    lsty = 0
    outpt = jl.pandas.DataFrame(columns=['x','y'])
    while xco > 0:
        #print (xco)
        e = [i for i in c if i < xco]
        xco2 = xco

        xco = max(e)
        ys = b['y'][(b['x1']>=xco2) & (b['x2']<=xco)]
        meany = sum(ys)/len(ys)
        medy = statistics.median(ys)
        #print(lsty, meany)
        printy = round(meany, 2)#round(meany, 2)
        if lsty == meany:
            #print('*1*')
            outpt.loc[len(outpt)-1] = [xco, printy]
        else:
            #print('*2*')
            outpt.loc[len(outpt)] = [xco2, printy]
            outpt.loc[len(outpt)] = [xco, printy]
        #print(outpt)
        lsty = meany
    #print(outpt)
    #for i in outpt.iterrows():
    #    print(i)

    plt.plot(outpt['x'],outpt['y'], 'r.-', GSdata[flnm]['x'], GSdata[flnm]['y'], 'b.-')
    plt.ylim(0,1)
    plt.title(flnm + ' (Error = ' + str(round(errr,2)) + '%, n = ' + str(users) + ')')
    plt.xlabel('Chromosome position')
    plt.ylabel('Gene Dosage')
    plt.savefig('GS_comparison_mean/' + flnm + 'err' + str(round(errr,2)) + '.jpg')
    plt.close()

    n += 1
    #if n == 1:
    #    break
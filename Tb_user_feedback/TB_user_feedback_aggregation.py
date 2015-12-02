__author__ = 'Jonathan'
import pandas as pd
from collections import Counter
import numpy
import xlrd
import time

nom = 'MVP_01-03'
s = pd.read_csv('mvp-01-03-feedback-fri-oct-16-103622-2015.csv')
s.head()
#print(s.keys())
# pattern = '%Y-%m-%d %H:%M:%S'
# pos = 0
# for dtime in s['Date/time']:
#     s['Date/time'][pos] = int(time.mktime(time.strptime(dtime[0:19], pattern)))
#     pos += 1
# t = s['Date/time']
# print(t)
j = 0
outcomes = pd.DataFrame(columns=('question','very poor', 'poor', 'good', 'very good', 'no', 'maybe', 'yes'))

for k in s.keys():
   if j in [0,1,2,3,4,8]:
       count = Counter(s.iloc[:,j])
       ress=[k, 0, 0, 0, 0, 0, 0 ,0]
       for i in count.keys():
           if i in ['Very unconfident', 'Very difficult', 'Very unmotivated', 'Very dull']:
               ress[1]=(count[i])
           #print(ress)
           elif i in ['Moderately unconfident', 'Moderately difficult', 'Moderately unmotivated', 'Moderately dull']:
               ress[2]=(count[i])
           elif i in ['Moderately confident', 'Moderately easy', 'Moderately motivated', 'Moderately interesting']:
               ress[3]=(count[i])
           elif i in ['Very confident', 'Very easy', 'Very motivated', 'Very interesting']:
               ress[4]=(count[i])
           elif i == 'No':
               ress[5]=(count[i])
           elif i == 'Maybe':
               ress[6]=(count[i])
           elif i == 'Yes':
               ress[7]=(count[i])
       outcomes.loc[len(outcomes)] = ress
        #mxcount = max(count.values())
        #answ = [i for i in count.keys() if count[i] == mxcount]
        #print(k, ', '.join(answ))
        #print(mxcount, count)
   j += 1
print(outcomes)

outcomes.to_csv(nom + '_qual_feedback.csv', index=False)
__author__ = 'Jonathan'

# pull user responses from CVS files and aggregate those with predetermined answers, to output an overview to CSV.
# Can also filter results by time.

# WILL REQUIRE EXTENSIVE CHANGES FOR DIFFERENT QUESTIONNAIRES

import pandas as pd
from collections import Counter
import numpy
import xlrd
import time

# name the project being analysed and give the file to read from
nom = 'MVP_03'
source_data = pd.read_csv('mvp-01-03-feedback-fri-oct-16-103622-2015.csv')
source_data.head()

# filter input data based on Date-time by converting to timestamp, could make this into a loop in future
# used to separate TB1 r1, r2, r3 data sourced from the same file

pattern = '%Y-%m-%d %H:%M:%S' #defines the form of date-time input: YYYY-MM-DD hh:mm:ss
pos = 0
#convert Date-times to timestamps
for dtime in source_data['Date/time']:
    source_data['Date/time'][pos] = int(time.mktime(time.strptime(dtime[0:19], pattern)))
    pos += 1

#define two time intervals to retain data from
start = '2015-08-04 12:00:00'
end = '2015-08-18 12:00:00'
start2 = '2016-01-01 12:00:00'
end2 = '2016-01-02 12:00:00'

#convert time intervals to timestamps
start = int(time.mktime(time.strptime(start, pattern)))
end = int(time.mktime(time.strptime(end, pattern)))
start2 = int(time.mktime(time.strptime(start2, pattern)))
end2 = int(time.mktime(time.strptime(end2, pattern)))

# filter input data to only include data from within intervals
source_data = source_data[((source_data['Date/time']<end) & (source_data['Date/time']>start))].append(source_data[((source_data['Date/time']<end2) & (source_data['Date/time']>start2))])

question_num = 0

# define dataframe to output responses
outcomes = pd.DataFrame(columns=('question','very poor', 'poor', 'good', 'very good', 'no', 'maybe', 'yes'))

# loop through each question and separate out different answers
for key in source_data.keys():
   if question_num in [0,1,2,3,4,8]: # only possible for certain questions
       # creates a dictionary with keys for each answer given and values as the number of occurrences for each
       count = Counter(source_data.iloc[:,question_num])
       #print(count)

       # create an output list for results from each different answer
       # LIST ORDER MUST CORRELATE WITH COLUMNS IN outcomes DataFrame
       question_responses_line=[key, 0, 0, 0, 0, 0, 0 ,0]

       # Classify different answers and write to correct part of ress list.
       # Could introduce RegExps to do this more precisely

       # loop through all answers to each question
       # need to do it this way as not all possible answers may have been used for each question
       for q_answer in count.keys():
           if q_answer in ['Very unconfident', 'Very difficult', 'Very unmotivated', 'Very dull', 'Very boring']:
               question_responses_line[1]+=(count[q_answer]) # NOTE USE OF '+=' as multiple answers can be combined into the same entry
           #print(ress)
           elif q_answer in ['Moderately unconfident', 'Moderately difficult', 'Moderately unmotivated', 'Moderately dull', 'Quite unconfident', 'Quite difficult', 'Quite unmotivated', 'Quite dull']:
               question_responses_line[2]+=(count[q_answer])
           elif q_answer in ['Moderately confident', 'Moderately easy', 'Moderately motivated', 'Moderately interesting', 'Quite confident', 'Quite easy', 'Quite motivated', 'Quite interesting']:
               question_responses_line[3]+=(count[q_answer])
           elif q_answer in ['Very confident', 'Very easy', 'Very motivated', 'Very interesting']:
               question_responses_line[4]+=(count[q_answer])
           elif q_answer == 'No':
               question_responses_line[5]=(count[q_answer])
           elif q_answer == 'Maybe':
               question_responses_line[6]=(count[q_answer])
           elif q_answer == 'Yes':
               question_responses_line[7]=(count[q_answer])

       # write the ress list into the outcomes DataFrame for the current question
       outcomes.loc[len(outcomes)] = question_responses_line

   question_num += 1
print(outcomes)

# print completed frame to CSV file, note the use of the project name to differentiate outputs
# defining index ensures numbers aren't printed as identifier column within CSV
outcomes.to_csv(nom + '_qual_feedback.csv', index=False)
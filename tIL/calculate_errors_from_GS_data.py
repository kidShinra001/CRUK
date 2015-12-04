# Process tIL data to calculate user errors by comparison to gold standard files
# gold std files are each separate CSV files within a folder

# could add functionality to save best and worst userID

__author__ = 'Jonathan'

import json, re, csv
import matplotlib.pyplot as plt
import JLtools as jl
import pandas as pd
from copy import deepcopy

# obtain list of gold std images and create a GoldList dictionary entry for each one
def create_GSlist(GSfl):
    GoldList = {}
    with open("tIL GSimages.csv") as GS_file:
        reader = csv.reader(GS_file)
        for row in reader:
            for entry in row:
                GoldList[entry[0:len(entry)-4]]={'count':0, 'coords': jl.pandas.DataFrame(columns=('x1', 'x2', 'y')), 'errorList':[], 'error':'N/A', 'corrections':[]}
    return GoldList

GoldList = create_GSlist("tIL GSimages.csv")
# Gold List for each gold std image has:
# count (of classification number)
# coords (of both ends of every horizontal line plotted by users)
# errorList (list of error values for each user)
# error (average overall error for image)
# corrections (x-max and start-x values used to standardise plots)

# create a GSdata dictionary of dataframes for gold standard coordinate information
def pull_GSdata(GoldList):
    GSdata = dict()
    for file in GoldList.keys():
        #file = file[0:len(file)-4]
        data_file = 'Gold_Std_GiStIL_data/' + file + '.xlsx'
        GSdata[file] = jl.pandas.read_excel(data_file, sheetname='Sheet1', header=None, names=['x','y'])
        i = 0
        pre_entry = 0

        # check data accuracy by scanning through all x coordinates
        for current_entry in GSdata[file]['x']:
            if (current_entry < pre_entry) & (pre_entry != 0): #a gold std plot should not double back on itself
            # if it does, this corrects it (bit of a fudge)
                GSdata[file].loc[i, 'x'] = pre_entry
            i += 1
            pre_entry = current_entry

    return GSdata

GSdata = pull_GSdata(GoldList)

number_of_classifications = 0
number_of_GS_classifications = 0
number_of_classifications_before_start = 0

Images = set() # count the number of images processed
IDlist = {'N/A':{'count':0, 'errorList':[], 'error':'N/A'}} # track information for each users error rate

with open("sanitized_impossible_line_2015-11-11/impossible_line_classifications.json") as source_file:
    for row in source_file:

        data = json.loads(row)
        inp = data['annotations'][0]['results'] # pull input information on coordinates and results
        time = data['created_at']['$date'] # pull time of classification

        if time > 1437609600000: # only do classifications after launch date
            inp = eval(inp)

            # pull user ID
            try:
                uid = inp['userid']
            except:
                uid = 'N/A'

            # compile list of user IDs
            # could probably be made more efficient using sets
            if uid not in IDlist.keys():
                IDlist[uid]={'count':0, 'errorList':[], 'error':'N/A'}
            IDlist[uid]['count'] += 1

            # create dataframe to build coordinate information
            coord = jl.pandas.DataFrame(columns=('x1', 'x2', 'y'))
            pos = 0

            # build table of coordinate info from user annotations
            # results are stored as x and y keys within point one and point two keys within results dictionary
            # processed results use real, non-normalised numbers
            # raw results have x between 0 and 1 and y between ?1 and 40?
            for entry in inp['processedresults']:
                # y should be constant as lines must be horizontal so calculate one value by averaging end points
                # could just pick either one of the two
                avey = (float(entry['point1']['y']) + float(entry['point2']['y']))/2

                #compile entries for coordinate table as smallest x, largest x, y value (not all lines go in the same direction)
                if float(entry['point1']['x']) < float(entry['point2']['x']):
                    coord.loc[pos] = [float(entry['point1']['x']),float(entry['point2']['x']),avey]
                else:
                    coord.loc[pos] = [float(entry['point2']['x']),float(entry['point1']['x']),avey]
                pos += 1

            coord.sort_values(by=['x2'], ascending='True')

            # COULD MOVE ALL OF THIS UP TO ONLY DO ALL OF THIS ON GOLD STD DATA - (why did I not do this??)
            # get name of file to check if in Gold Std list
            fl = inp['filename'][0:len(inp['filename'])-4]

            Images.add(fl) # add any new image to the set of images
            lth = int(len(coord)) # count how many lines are in this classification

            print(number_of_classifications)



            if fl in GoldList and uid != 'N/A':
                number_of_GS_classifications += 1
                GoldList[fl]['count'] += 1

# this section is all about cleaning the data and standardising to fit with each other

                # make a completely separate copy of GS info
                # could have pre-corrected all the GS data then used the stored scaling factors to fix the coord data
                # this way involves a lot of duplicated calculation (BAD FOR BIG DATA)
                GScoord = deepcopy(GSdata[fl])

                # scale GS data and classification data to same axes
                # put both x and y between 0 and 1, maes calculations of proportions easier
                start_x = GScoord['x'][0] # comparison only starts at first point of gold std info

                GScoord['x'] -= start_x # set start of GS info to 0 on both GS and classifiction data
                coord['x1'] -= start_x
                coord['x2'] -= start_x

                if coord['x1'][0] < 0: # any user lines that start before GS data are dumped
                    coord['x1'][0] = 0

                # rescale remaining data so maximum is 1 on both data items
                x_max = max(GScoord['x'])
                GScoord['x'] /= x_max
                coord['x1'] /= x_max
                coord['x2'] /= x_max

                coord = coord[(coord.x1<=1) | (coord.x2<=1)] # remove any lines beyond the end

                coord.x2[coord.x2 >1] = 1 # truncate any lines that reach beyond the end
                coord.x1[coord.x1 >1] = 1

                coord['x2'][len(coord)-1] = 1 # ensure final line ends at 1

                GScoord['x2']=GScoord['x'].shift() # create x2, by shifting x1 of GS data so that items are now all horizontal lines
                GScoord['x2'][0]=0

# iterate backwards through all x-coordinates where either GS or classification changes occur and recalculate the corresponding y error

                list_of_segment_errors = []
                x_coord_1 = 1 # initial x coordinate

                # all other x coordinates mentioned specifically in either GS or classification
                xs = list(coord['x1'])+list(coord['x2'])+list(GScoord['x'])

                # initiate dataframe to collect information for average line segment through each part of the graph
                averaged_classification_coords = jl.pandas.DataFrame(columns=('x1', 'x2', 'y'))

                # need to know the value of y at every value of x. This only changes at points where a line starts or ends,
                # so only need to recalculate the y value at the points where a line starts or ends
                # hence finding y at all x points mentioned in the source data allows calculation of errors for all points

                # continually reduce through x coordiantes from 1 to 0 to identify the average y value
                # for each section of the plot
                while x_coord_1 > 0:

                    # create list of all line segments from classification that are present at current x value
                    y_coord = coord['y'][(coord['x2']>=x_coord_1) & (coord['x1']<x_coord_1)]

                    # create reduced list of x coordinates, that are before the current one
                    # select the next largest x value as the next coordinate to calculate from
                    remaining_xs = [x for x in xs if x<x_coord_1]
                    x_coord_2 = max(remaining_xs)

                    # if there are any line segments in the classification overlapping the current x coordinate
                    # calculate the average y value
                    # identify corresponding GS y value
                    if len(y_coord) >0:
                        averaged_y_coord = sum(y_coord)/len(y_coord)
                        goldstd_y_coord = float(GScoord['y'][(GScoord['x']>=x_coord_1) & (GScoord['x2']<x_coord_1)])

                    list_of_segment_errors.append(abs(x_coord_1-x_coord_2)*abs(goldstd_y_coord-averaged_y_coord))
                    averaged_classification_coords.loc[len(averaged_classification_coords)] = [x_coord_1, x_coord_2, averaged_y_coord]

                    x_coord_1 = x_coord_2 # move to focus on previous x value for next loop


                # output error for the current classification and use to calculate overall running error
                # errors here are categorised by user
                IDlist[uid]['errorList'].append(sum(list_of_segment_errors))
                IDlist[uid]['error']= (sum(IDlist[uid]['errorList'])/len(IDlist[uid]['errorList'])*100)

                # output the same info as above but categorised by GS sample
                GoldList[fl]['errorList'].append(sum(list_of_segment_errors))
                GoldList[fl]['error'] = (sum(GoldList[fl]['errorList'])/len(GoldList[fl]['errorList'])*100)

                # store all raw coordinate data from each classification of each GS image to allow plotting of user average
                gl = GoldList[fl]['coords'].append(deepcopy(averaged_classification_coords), ignore_index = True)
                GoldList[fl]['coords'] = gl

                # store correction factors to allow easy reconversion between scaled and raw data values
                GoldList[fl]['corrections'] = [start_x, x_max]

            number_of_classifications += 1

        else:
            number_of_classifications_before_start += 1

# function to build a DataFrame from dictionaries to output information and write to file
# probably should have just done them as pandas in the first place
def build_panda(source, field1, out_file):

    # args: source - dictionary of data to put into panda
    #       field1 - name of the key from the dictionary e.g. user ID, subject ID
    #       out_file - name for files to create (both JSON and CSV)

    pos = 0
    for entry in source:
        # create an empty dataframe if this is the first line of the data
        if pos == 0:
            errors = jl.pandas.DataFrame(columns=[[field1] + list(source[entry].keys())])#(field1, '% Error', 'Errors'))

        # start a list that will contain the line of data to dump into each row of the dataframe
        dump = [entry]
        # add all relevant data from all subkeys in dictionary to list
        for key in source[entry].keys():
            dump.append(source[entry][key])

        # write list to new line of output file
        errors.loc[pos] = dump
        pos += 1

    # calculate average, min, max errors for each user/image with error information and print the IDs of the best & worst
    errlist = errors[errors['error'] != 'N/A'] # filter out any users/images where there is no info to calculate errors from
    print(sum(errlist['error'])/len(errlist), min(errlist['error']), errlist[field1][errlist['error'].idxmin()], max(errlist['error']), errlist[field1][errlist['error'].idxmax()])

    # write to files
    errors.to_csv(out_file + '.csv')
    errors.to_json(out_file + '.json')

# files for all users
build_panda(IDlist, 'UserID', 'tIL UserErrors')
# files for all GS images
build_panda(GoldList, 'File', 'tIL GSErrors')

print('records: ' + str(number_of_classifications), 'GS: ' + str(number_of_GS_classifications))
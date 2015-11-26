__author__ = 'Jonathan'

# use this to unzip a source data folder if needed
"""import tarfile
tar = tarfile.open("sanitized_cancer_gene_runner_2015-10-07.tar.gz")
tar.extractall()
tar.close()"""

import json, csv

# creates a dictionary of lists to store all information about unqiue IDs and the number of records they are part of:
IDlist = {'UID':['N/A'], 'unique': [0], 'dupl': [0], 'test': [0]}

# a list of dictionaries, each entry contains a dictionary of data from a different row in the source file
# new entries are added at the end and old entries are written from the start
events = []

# counting variables used to track progress
# these two are needed
x = 0 # measures current last position in the events list (oscillates below 100)
n = 0 # counts which source file line the code has reached (rises steadily, GiS data reaches ~3 088 000)
# these three are used in debugging, they are not essential to core function
n2 = 0
n3 = 0
n4 = 0

# open output CSV file to write data
with open('GiS_Data.csv', 'w') as csvfile:
    # create fieldnames and print to output file as header
    fieldnamz = ['user_id', 'sample_id', 'created_date', 'pathData']
    id_write = csv.DictWriter(csvfile, fieldnames=fieldnamz)
    #print(fieldnamz)
    id_write.writeheader()
    # open output JSON file to write data
    with open('GiS_Data.json', 'w') as jsonfile:
        #open input file
        with open("sanitized_cancer_gene_runner_2015-10-07/cancer_gene_runner_classifications.json") as source_file:

            #process each line separately, there are too many for anything else
            for line in source_file:

                """here data are read from file and the relevant data extracted to the events list, unique userIDs are
                also collected in a separate list and used to tally how many duplicates come from different users"""

                # load single data line from json
                data = (json.loads(line))

                # try to find the UserID if present (some don't have one for some reason..., hence N/A)
                try:
                    events.append({'rawUID': data['user_id']['$oid']})
                except:
                    events.append({'rawUID': 'N/A'})

                # x gives the current position of the last entry in the events list
                # as the list constantly gains and loses entries there is no way to predict how x changes each time
                x = len(events)-1

                # if the UserID is new add it to the dictionary of IDs
                if events[x]['rawUID'] not in IDlist['UID']:
                    IDlist['UID'].append(events[x]['rawUID'])
                    IDlist['unique'].append(0)
                    IDlist['dupl'].append(0)
                    IDlist['test'].append(0)

                # find the position of the current UserID in the ID list, needed to track number of unique vs. duplicate values
                # i is the index within the userID list that corresponds to y which is the current userID
                IDpos = [i for i,y in enumerate(IDlist['UID']) if y == events[x]['rawUID']]

                # store the location of the userID in the UserID list to know where to tally unique/duplicate values
                events[x]['position_in_ID'] = IDpos[0]

                # find creation timestamp if it exists (it always does)
                try:
                    events[x]['create_date'] = (str(data['created_at']['$date']))
                except:
                    events[x]['create_date'] = 'NaN'

                # find graph data (pathData) and sample ID (fileNm) within the annotations section
                try:
                    annData = data['annotations']
                    # each named dictionary entry is (maddeningly) a separate dictionary within a list
                    # hence cycle through each list entry to find the ones needed
                    for entry in annData:
                        try:
                            events[x]['pathData'] = entry['pathData']
                        except:
                            pathData = 'N/A'

                        try:
                            events[x]['fileNm'] = entry['fileName']
                        except:
                            fileNm = 'N/A'
                except:
                    pathData = 'N/A'
                    fileNm = 'N/A'

                # rows are compared on the basis of both userID and sampleID to test for uniqueness
                events[x]['identifier'] = (events[x]['rawUID'] + ' ' + events[x]['fileNm'])

                """duplicate events have the same UserID and sampleID and occur within 3 minutes of each other
                an event that occurred more than 3 minutes before the most recent event will definitely not be
                a duplicate. As such, these old rows can definitely be written to file"""

                # if x is 0 there is only one entry currently in events, so no need to do comparisons
                if x > 0:
                    # duplicate entries are only removed if they occur within 3 minutes of the original hence entries older than that can be written to file
                    # if there are more than 3 mins between the current first event and the newest event the oldest event can be written to file
                    while int(events[x]['create_date']) - int(events[0]['create_date']) > 18000:
                        # if the sampleID in the file isn't a test file then write it to file
                        if '.txt' in events[0]['fileNm']:
                            n2 += 1 # tracks number of lines output

                            #output to both CSV and JSON
                            id_write.writerow({'user_id': events[0]['rawUID'], 'created_date': events[0]['create_date'], 'sample_id': events[0]['fileNm'], 'pathData': events[0]['pathData']})
                            json.dump({'user_id': events[0]['rawUID'], 'created_date': events[0]['create_date'], 'sample_id': events[0]['fileNm'], 'pathData': events[0]['pathData']}, jsonfile)
                            jsonfile.write('\n') #insert a line break to the JSON file so it can be read line-wise again

                            # add one to the tally of unique assignments made by the userID from the line being written
                            IDlist['unique'][events[0]['position_in_ID']] += 1

                        # if the sampleID is a test value
                        else:
                            n4 += 1 # tracks number of lines removed as test samples
                            IDlist['test'][events[0]['position_in_ID']] += 1 # update test data tally for this userID

                        # delete the row that was just written/excluded
                        del events[0]
                        # a row has been deleted so also reduce x
                        x -= 1

                """having eliminated any old events, the newest event must be compared to any remaining events to identify
                duplicates. If a duplicate exists then the newest event is removed. Only the first event is retained"""

                # since x may have been reduced several times above, check it is still above 0 for the next comparisons
                if x > 0:
                    # m tracks the index of the event being compared to the newest event (x)
                    m = x-1 # start by comparing the newest row to the previous row (duplicates are most often adjacent)

                    # if the m th event isn't a duplicate move back through the list to the beginning checking for others
                    while m >= 0:
                        # identify duplicates by matching UserID & sampleID
                        if events[m]['identifier'] == events[x]['identifier']:

                            # if there is a match the newest event is deleted and tallied as a test or duplicate run
                            # the sampleID determines whether it's a test or a duplicate
                            if '.txt' in events[x]['fileNm']:
                                IDlist['dupl'][events[0]['position_in_ID']] += 1
                                n3 += 1
                            else:
                                IDlist['test'][events[0]['position_in_ID']]+= 1
                                n4 += 1
                            del events[x]
                            break # if a duplicate has been found and the current event deleted there is no need to keep searching

                        # if a duplicate isn't found then check by comparing to the previous event
                        else:
                            m -=1

                # advancing n and printing it helps keep track of file progess
                n += 1
                print(n, x)

                # this block helps with debugging as it crashes the file read after a limited number of rows
                #if n == 1000:
                #    break
                #print(n)

            """at the end of the file, any remaining lines must not be duplicates so also need to be written to the
            output files"""

            for item in range(len(events)):
                # only data that isn't test data gets written to file
                if '.txt' in events[item]['fileNm']:
                    n2 += 1
                    id_write.writerow({'user_id': events[item]['rawUID'], 'created_date': events[item]['create_date'], 'sample_id': events[item]['fileNm'], 'pathData': events[item]['pathData']})
                    json.dump({'user_id': events[item]['rawUID'], 'created_date': events[item]['create_date'], 'sample_id': events[item]['fileNm'], 'pathData': events[item]['pathData']}, jsonfile)
                    jsonfile.write('\n')
                    IDlist['unique'][events[item]['position_in_ID']] += 1
                elif '.txt' not in events[item]['fileNm']:
                    IDlist['test'][events[item]['position_in_ID']] += 1
                    n4 += 1

print(n2, n3, n4) # output number of unique, duplicate and test events processed

"""Output the userID list and the associated data on number of rows to a CSV file"""

with open('GiSkey.csv', 'w') as keyfile:
    fieldnamz = ['ID', 'unique', 'duplicate', 'test_data']
    headwr = csv.DictWriter(keyfile, fieldnames=fieldnamz)
    headwr.writeheader()
    for rw in range(len(IDlist['UID'])):
        headwr.writerow({'ID': IDlist['UID'][rw], 'unique': IDlist['unique'][rw], 'duplicate': IDlist['dupl'][rw], 'test_data': IDlist['test'][rw]})
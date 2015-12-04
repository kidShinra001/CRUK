# creates plots of GS data against averaged classification data for each GS image
# RUN tIL analysis FIRST TO CREATE SOURCE FILES

__author__ = 'Jonathan'

import JLtools as jl
import matplotlib.pyplot as plt
import statistics

#change way to calc error based on different aggregations not just mean

data_file = 'tIL GSErrors.json'
# recover data from classifications to plot against GS
GS_sample_info = jl.pandas.read_json(data_file)
GS_sample_error_data = GS_sample_info[GS_sample_info['count']>0]

# pull error data for each GS sample into dictionary to plot against classification data
# this function is pretty much duplicated from tIL analysis
def pull_GSdata(GoldList):
    # args: GoldList - list of all GS image IDs

    # empty dictionary for output data
    GSdata = dict()

    # iterate through GS files and recover coordinate data from files
    for file in GoldList:
        data_file = 'Gold_Std_GiStIL_data/' + file + '.xlsx'
        GSdata[file] = jl.pandas.read_excel(data_file, sheetname='Sheet1', header=None, names=['x','y'])#.sort_values(by=['x'], ascending='True')

        # correct any parts of GS data to avoid looping back
        i = 0
        x_value_1 = 0
        for x_value_2 in GSdata[file]['x']:
            if (x_value_2 < x_value_1) & (x_value_1 != 0):
                GSdata[file].loc[i, 'x'] = x_value_1
            i += 1
            x_value_1 = x_value_2

        # use correction factors (x_max and start_x) from source files to standardise GS data to axes of 0 to 1.
        list_of_correction_factors = GS_sample_info[GS_sample_info['File'] == file]['corrections'].iloc[0]
        GSdata[file]['x'] -= list_of_correction_factors[0]
        GSdata[file]['x'] /= list_of_correction_factors[1]
    return GSdata

GSdata = pull_GSdata(list(GS_sample_error_data['File']))

# now run through all GS images where error data are available and create plots
for k, item in GS_sample_error_data.iterrows():
    flnm = item.File
    errr = item.error
    users = item['count']

    # need a list of x values to iterate through and calculate points to plot from
    all_classification_line_coords =jl.pandas.DataFrame(item.coords)
    all_classification_x_endpoints = list(all_classification_line_coords['x1']) + list((all_classification_line_coords['x2']))
    non_dup_x_endpoints = list(set(all_classification_x_endpoints))

    # progressively reduce x values and calculate y coordinates for current region between two x values
    x_coord_1 = max(non_dup_x_endpoints) # largest x coord
    last_y = 0 # used to see if current line segment can be combined with previous i.e. has same average y, or different
    outpt = jl.pandas.DataFrame(columns=['x','y']) # output coordinate set for plotting
    while x_coord_1 > 0:
        # from starting x coordinate, find all line segments that run between it and the next line end point
        x_values_below_current_x1 = [i for i in non_dup_x_endpoints if i < x_coord_1]
        x_coord_2 = x_coord_1
        x_coord_1 = max(x_values_below_current_x1)

        # find all relevant y coordinates and aggregate into one average value
        y_coords_at_current_x = all_classification_line_coords['y'][(all_classification_line_coords['x1']>=x_coord_2) & (all_classification_line_coords['x2']<=x_coord_1)]
        mean_y = sum(y_coords_at_current_x)/len(y_coords_at_current_x)
        median_y = statistics.median(y_coords_at_current_x)

        # create neat version of y for plotting and display
        print_y = round(mean_y, 2)

        # compare y value of previous average line segment with previous y value
        # if y values are the same then simply extend the current line rather than starting a new one
        if last_y == mean_y:
            outpt.loc[len(outpt)-1] = [x_coord_1, print_y] # change existing end point
        # if y value is different then define start and end coordinates for new line segment
        else:
            outpt.loc[len(outpt)] = [x_coord_2, print_y] # new start point
            outpt.loc[len(outpt)] = [x_coord_1, print_y] # new end point

        # save current y before moving on to next one
        last_y = mean_y

    # prepare plot GS data in blue and averaged user data in red
    plt.plot(outpt['x'],outpt['y'], 'r.-', GSdata[flnm]['x'], GSdata[flnm]['y'], 'b.-')
    # standardise graph height to 0 to 1 (otherwise noise looks significant)
    plt.ylim(0,1)
    # add titles and labels (title includes average error for plot and number of classifications)
    plt.title(flnm + ' (Error = ' + str(round(errr,2)) + '%, n = ' + str(users) + ')')
    plt.xlabel('Chromosome position')
    plt.ylabel('Gene Dosage')
    # save plot to file and close - file name includes error value
    plt.savefig('GS_comparison_mean/' + flnm + 'err' + str(round(errr,2)) + '.jpg')
    plt.close()
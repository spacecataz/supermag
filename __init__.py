#!/usr/bin/env python

'''
This file contains tools for reading and handling Supermag data files.
'''
import numpy as np

def read_statinfo(filename):
    '''
    Open and parse an "ascii" formatted file of station information as provided
    by supermag.
    '''
    pass
    
def read_supermag(filename, calc_H=False, calc_):

    '''
    Read a complicated supermag file and return a dictionary of 'time'
    and numpy arrays of magetometer delta-Bs for each mag in the file.

    TO-DO:
    --add magnetometer list as an entry
    --Include deltaB as standard calculation
    --Make calculations of deltaB, H-components optional.
    '''

    import datetime as dt
    from matplotlib.dates import date2num
    from scipy.interpolate import interp1d
    
    f = open(filename, 'r')

    # Skip header:
    line = f.readline()
    while 'Selected parameters' not in line: line = f.readline()
    head = f.readline()
    
    # Get station list:
    stats  = head.split()[-1].split(',')
    nStats = len(stats)

    # Now, slurp rest of lines and count number of records.
    f.readline() # Skip last header line.
    lines = f.readlines()

    # Get number of lines:
    nTime = int(len(lines)/(nStats+1))

    # Create container of data:
    data = {}
    data['time'] = np.zeros(nTime, dtype=object)
    for s in stats: # Initialize with Bad Data Flag
        data[s] = np.zeros( [3,nTime] )+999999.

    # Read data:
    for j in range(nTime):
        # Get time:
        data['time'][j] = dt.datetime.strptime(
            ''.join(lines.pop(0).split()[:-1]), '%Y%m%d%H%M%S')
        
        # Get values:
        for i in range(nStats):
            if lines[0][:3] not in stats: continue
            parts = lines.pop(0).split()
            data[parts[0]][:,j] = parts[1:4]

    # Filter bad data.
    t = date2num(data['time'])
    for s in stats:
        data[s][data[s]>=999999.] = np.nan

        # Interpolate over bad data:
        for idir in range(3):
            bad = np.isnan(data[s][idir,:])
            good= np.logical_not(bad)
            data[s][idir,bad] = interp1d(t[good], data[s][idir,good],
                                         fill_value='extrapolate')(t[bad])
            
    # Get time in seconds:
    dt = np.array([x.total_seconds() for x in np.diff(data['time'])])
    
    # Calc H and time derivatives:
    for s in stats:
        # Horizontal field magnitude:
        data[s+'_H'] = np.sqrt(data[s][0,:]**2 + data[s][1,:]**2)

        # Get dB_n/dt and dB_e/dt:
        dbn, dbe = np.zeros(dt.size+1),np.zeros(dt.size+1)

        # Central diff:
        dbn[1:-1] = (data[s][0,2:]-data[s][0,:-2])/(dt[1:]+dt[:-1])
        dbe[1:-1] = (data[s][1,2:]-data[s][1,:-2])/(dt[1:]+dt[:-1])
        # Forward diff:
        dbn[0]=(-data[s][0,2]+4*data[s][0,1]-3*data[s][0,0])/(dt[1]+dt[0])
        dbe[0]=(-data[s][1,2]+4*data[s][1,1]-3*data[s][1,0])/(dt[1]+dt[0])
        # Backward diff:
        dbn[-1]=(3*data[s][0,-1]-4*data[s][0,-2]+data[s][0,-3])/(dt[-1]+dt[-2])
        dbe[-1]=(3*data[s][1,-1]-4*data[s][1,-2]+data[s][1,-3])/(dt[-1]+dt[-2])

        # Create |dB/dt|_h:
        data[s+'_dH'] = np.sqrt(dbn**2 + dbe**2)


    return data


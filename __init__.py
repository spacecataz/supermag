#!/usr/bin/env python

'''
This module contains tools for reading and handling Supermag data files.

Dependencies: Numpy, Scipy, and Matplotlib.

TO-DO:
--Add test suite
--Add example code
'''
import numpy as np

def read_statinfo(filename):
    '''
    Open and parse an "ascii" formatted file of station information as provided
    by supermag.  
    '''
    pass
    
class SuperMag(dict):
    '''
    This class is for reading, handling, and plotting the contents of a supermag-generated
    ascii-formatted data file.  The underlying object works like a dictionary: individual 
    stations can be accessed by referencing their 3-letter station code.

    TO-DO:
    --Allow user to select how to handle bad data: mask data or interpolate.
    --Make calculations of deltaB, H-components optional.
    --Move calculations (calc_H, etc.) to object methods.    
    '''

    def __init__(self, filename, *args, **kwargs):
        '''
        Instantiate object, read file, populate object.
        '''

        # Initialize as empty dict
        super(dict, self).__init__(*args, **kwargs)
        
        # Store filename within object:
        self.filename = filename
        
        self._read_supermag()
        
    def _read_supermag(self):
        '''
        Read a complicated supermag file and return a dictionary of 'time'
        and numpy arrays of magetometer delta-Bs for each mag in the file.
        '''

        import re
        import datetime as dt
        from matplotlib.dates import date2num
        from scipy.interpolate import interp1d
    
        f = open(self.filename, 'r')
        
        # Skip header:
        line = f.readline()
        nSkip = 1
        while 'Selected parameters' not in line:
            nSkip+=1
            line = f.readline()
        head = f.readline()
    
        # Get station list:
        stats  = head.split()[-1].split(',')
        nStats = len(stats)

        # Save this information within object:
        self.stations = stats
        self.nstats   = nStats
        
        # Now, slurp rest of lines and count number of records.
        f.readline() # Skip last header line.
        lines = f.readlines()
        f.close()
        
        # Get number of lines.  The issue is that the number
        # of lines does not scale directly with number of stations.
        # Bad data entries may be omitted, leading to irregular
        # file sizes.  As such, we need to search the hard way.
        nTime = 0
        for l in lines:
            nTime += 1*bool(re.match('^\d{4}\s+\d{2}\s+\d{2}\s+', l))

        # Create container arrays for all data:
        self['time'] = np.zeros(nTime, dtype=object)
        for s in stats: # Initialize with Bad Data Flag
            self[s] = np.zeros( [3,nTime] )+999999.

        # Re-open file, skip header, and work line by line.
        f = open(self.filename, 'r')
        for i in range(nSkip+2):
            f.readline()
        
        # Read data by looping over "records": chunks of text that start
        # with the current time and go until all stations with data for that
        # epoch have been listed.  Not all stations will have entries for
        # each record, so we need to account for that.
        line = f.readline()
        for j in range(nTime):
            # Get time:
            self['time'][j] = dt.datetime.strptime(
                ''.join(line.split()[:-1]), '%Y%m%d%H%M%S')
        
            # Get values.  Loop through lines until we are on a line
            # without a station name. 
            line = f.readline()
            while line[:3] in stats:
                parts = line.split()
                self[parts[0]][:,j] = parts[1:4]
                line = f.readline()

        # close our file.
        f.close()
        
        # Filter bad data.
        t = date2num(self['time'])
        for s in stats:
            self[s][self[s]>=999999.] = np.nan

        # Interpolate over bad data: COMMENTED OUT FOR TIME BEING.
        #for idir in range(3):
        #    bad = np.isnan(self[s][idir,:])
        #    good= np.logical_not(bad)
        #    self[s][idir,bad] = interp1d(t[good], self[s][idir,good],
        #                                 fill_value='extrapolate')(t[bad])
            
        # Get time in seconds:
        dt = np.array([x.total_seconds() for x in np.diff(self['time'])])
    
        # Calc H component (following Pulkkinen et al 2013, NON STANDARD!!!)
        # OFF BY DEFAULT
        calc_H=False
        calc_dbdt=False 
        if calc_H:
            for s in stats:
                # Horizontal field magnitude:
                self[s+'_H'] = np.sqrt(self[s][0,:]**2 + self[s][1,:]**2)

        # Calculate time derivatives if required:
        if calc_dbdt:
            for s in stats:
                # Get dB_n/dt and dB_e/dt:
                dbn, dbe = np.zeros(dt.size+1),np.zeros(dt.size+1)

                # Central diff:
                dbn[1:-1] = (self[s][0,2:]-self[s][0,:-2])/(dt[1:]+dt[:-1])
                dbe[1:-1] = (self[s][1,2:]-self[s][1,:-2])/(dt[1:]+dt[:-1])
                # Forward diff:
                dbn[0]=(-self[s][0,2]+4*self[s][0,1]-3*self[s][0,0])/(dt[1]+dt[0])
                dbe[0]=(-self[s][1,2]+4*self[s][1,1]-3*self[s][1,0])/(dt[1]+dt[0])
                # Backward diff:
                dbn[-1]=(3*self[s][0,-1]-4*self[s][0,-2]+self[s][0,-3])/(dt[-1]+dt[-2])
                dbe[-1]=(3*self[s][1,-1]-4*self[s][1,-2]+self[s][1,-3])/(dt[-1]+dt[-2])
                
                # Create |dB/dt|_h:
                if s+'H' in stats:
                    self[s+'_dH'] = np.sqrt(dbn**2 + dbe**2)
                    
        # Return true on success:
        return True


#!/usr/bin/env python

'''
This module contains tools for reading and handling Supermag data files.

Dependencies: Numpy, Scipy, and Matplotlib.

TO-DO:
--Add test suite
--Add example code
'''

import re
import datetime as dt
import warnings
import numpy as np

# Set install directory:
install_dir = '/'.join(__loader__.path.split('/')[:-1])+'/'

# Create a map of position of values in file based on file version.
# Maps Version Number :to: Index of First Variable
# This skips perfunctory values that we don't use.
# Defaults to latest version if revision is unrecognized.
varmap = {2:1, 5:-6, 6:-6}
varmap['unrecognized'] = varmap[max(varmap.keys())]

def _convert_entry(value):
    '''
    Helper function for reading and loading station info file.
    Looks at a value from the file, converts strings to floats or 
    removes quotes from strings.
    '''

    if '"' in value:
        return value.strip('"')
    else:
        return float(value)
    
def read_statinfo(filename='default'):
    '''
    Open and parse an "ascii" formatted file of station information as provided
    by supermag.  All information saved as a dictionary where each key is 
    the station name.

    *filename* sets the location of the information file.  Default behavior
    is to use the file contained with the package.
    '''

    # Set file name path:
    if filename == 'default':
        filename=install_dir+'station_info.txt'

    # Open file:
    f = open(filename,'r')
    
    # Skip header:
    trash = ''
    while '===' not in trash:
        trash = f.readline()

    # Load data header:
    trash = f.readline()
    header = trash.lower().split()
        
    # Read rest of lines; close file:
    lines = f.readlines()
    f.close()

    # Create empty data container to store station info:
    data = {}

    # Read rest of data:
    for l in lines:
        # Split on tabs:
        parts = l.split('\t')
        # Some lines have double-tabs which give blank entries in parts:
        while '' in parts: parts.remove('')

        # Create new entry within main data structure for
        # each station:
        data[parts[0]] = {}
        for key, value in zip( header[1:], parts[1:] ):
            data[parts[0]][key] = _convert_entry(value)

    return data

class IndexFile(dict):
    '''
    This class is for reading and handling the geomagnetic index files from
    the SuperMag website.  This class inherits from, and therefore works 
    similar to, dictionary objects that use a key-value pair.

    Parameters
    ==========
    filename : string
        The name of the SuperMag index file to read and load.

    Other Parameters
    ================

    Example
    =======
    >>> # From one directory above the repository location:
    >>>  x = supermag.IndexFile('./supermag/data/example_index.txt')
    >>> x.keys()
    >>> x['SMU']
    dict_keys(['time', 'SML', 'SMU'])

    array([107., 113., 116., ..., 157., 156., 158.])

    '''
    def __init__(self, filename, load_info=True, *args, **kwargs):
        '''
        Instantiate object, read file, populate object.
        '''

        # Initialize as empty dict
        super(dict, self).__init__(*args, **kwargs)
        
        # Store filename within object:
        self.filename = filename

        # Read data file:
        self._read_indexfile()

    def _read_indexfile(self):

        # Open, read, and close file:
        with open(self.filename, 'r') as f:
            # Skip bulk of header.
            while '==' not in f.readline(): continue
            head  = f.readline()  # Read varnames & units
            lines = f.readlines() # Slurp rest of data.

        # Parse variable names besides time:
        varnames = [x[0] for x in re.findall('\<(.+?)\s*(\(\w+\))?\>',head)[6:]]

        # Build containers:
        nLines = len(lines)
        self['time'] = np.zeros(nLines, dtype=object)
        for v in varnames: self[v] = np.zeros(nLines)

        # Parse data and fill container:
        for i,l in enumerate(lines):
            parts = l.split()
            self['time'][i] = dt.datetime.strptime(
                ' '.join(parts[:6]), '%Y %m %d %H %M %S')
            for v, x in zip(varnames,parts[6:]):
                self[v][i] = x
            
class SuperMag(dict):
    '''
    This class is for reading, handling, and plotting the contents of a 
    supermag-generated ascii-formatted data file.  The underlying object works 
    like a dictionary: individual stations can be accessed by referencing 
    their 3-letter station code.

    Parameters
    ==========
    filename : string
        The name of the SuperMag file to read and load into the data structure.

    Other Parameters
    ================
    load_info : bool
        Load the station info (name, lat, lon, etc.) from a separate file.
        If station info is loaded, each station's local time is saved as
        `self['station']['lt']`.

    Example
    =======
    >>> # From one directory above the repository location:
    >>> x = supermag.SuperMag('supermag/data/example_v5.txt')
    >>> print(x.stations)
    >>> x['ALE'].keys()

    ['ALE', 'AND', 'BOR', 'BEL', 'BDV', 'BMT', 'BNG', 'ASP']
    dict_keys(['time', 'ALE', 'AND', 'BOR', 'BEL', 'BDV', 'BMT', 'BNG', 'ASP'])


    TO-DO:
    --Allow user to select how to handle bad data: mask data or interpolate.
    --Make calculations of deltaB, H-components optional.
    --Move calculations (calc_H, etc.) to object methods.    
    '''

    def __init__(self, filename, load_info=True, *args, **kwargs):
        '''
        Instantiate object, read file, populate object.
        '''

        # Initialize as empty dict
        super(dict, self).__init__(*args, **kwargs)
        
        # Store filename within object:
        self.filename = filename

        # Read data file:
        self._read_supermag()

        # Add station info to each station if required.
        # Calculate local time for each station:
        if load_info:
            # Calculate hours to use for local time determination.
            hours = np.array(
                [x.hour+x.minute/60.+x.second/3600 for x in self['time']])
            
            info = read_statinfo()
            for s in self:
                if s in info:
                    self[s]['geolon'] = info[s]['geolon']
                    self[s]['geolat'] = info[s]['geolat']
                    self[s]['name']   = info[s]['station-name']
                    # Calculate local time, do not let it go over 24 hours.
                    self[s]['lt'] = hours+info[s]['geolon']*24/360
                    self[s]['lt'][self[s]['lt']>=24]-=24
                    
    def _read_supermag(self):
        '''
        Read a complicated supermag file and return a dictionary of 'time'
        and numpy arrays of magetometer delta-Bs for each mag in the file.
        '''

        from matplotlib.dates import date2num
        from scipy.interpolate import interp1d
    
        f = open(self.filename, 'r')

        # Set default revision:
        self.vers = 'unrecognized'
        
        # Skip header: jump to point where file lists stations.
        # Find format version, too.
        line = f.readline() # Read first line.
        nSkip = 1
        while 'Selected' not in line:
            nSkip+=1
            if 'Revision' in line:
                self.vers = int(line.split(':')[-1])
            line = f.readline()

        # Warn if unrecognized revision:
        if self.vers == 'unrecognized':
            warnings.warn("Unrecognized file format revision.  "+
                          "Check validity of file read.")
            
        # From the revision, get the index offset to read variables:
        iOff = varmap[self.vers]
            
        # Grab line with station list in it:
        head = line if 'Stations' in line else f.readline()

        # Parse station list:
        stats  = head.split()[-1].split(',')
        nStats = len(stats)

        # Save this information within object:
        self.stations = stats
        self.nstats   = nStats

        # Skip remainder of header; count skipped lines:
        while '==' not in line and 'Parameters' not in line:
            line = f.readline()
            nSkip+=1

        
        # Now, slurp rest of lines and count number of records.
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
            self[s] = {}  # Start with empty dictionary
            for x in ['bx','by','bz','bx_geo', 'by_geo','bz_geo']:
                self[s][x] = np.zeros( [nTime] )+999999.

        # Re-open file, skip header, and work line by line.
        f = open(self.filename, 'r')
        for i in range(nSkip+1*(self.vers==2)):
            f.readline()

        # Read data by looping over "records": chunks of text that start
        # with the current time and go until all stations with data for that
        # epoch have been listed.  Not all stations will have entries for
        # each record, so we need to account for that.
        line = f.readline()
        for j in range(nTime):
            # Get time:
            self['time'][j] = dt.datetime.strptime(
                ''.join(line.split()[:6]), '%Y%m%d%H%M%S')
        
            # Get values.  Loop through lines until we are on a line
            # without a station name. 
            line = f.readline()
            while line[:3] in stats:
                parts = line.split()
                self[parts[0]]['bx'][j] = parts[iOff  ]
                self[parts[0]]['by'][j] = parts[iOff+1]
                self[parts[0]]['bz'][j] = parts[iOff+2]
                self[parts[0]]['bx_geo'][j] = parts[iOff+3]
                self[parts[0]]['by_geo'][j] = parts[iOff+4]
                self[parts[0]]['bz_geo'][j] = parts[iOff+5]
                line = f.readline()

        # close our file.
        f.close()
        
        # Filter bad data.
        t = date2num(self['time'])
        for s in stats:
            for x in ['bx','by','bz']:
                self[s][x][self[s][x]>=999999.] = np.nan

        # Interpolate over bad data: COMMENTED OUT FOR TIME BEING.
        #for idir in range(3):
        #    bad = np.isnan(self[s][idir,:])
        #    good= np.logical_not(bad)
        #    self[s][idir,bad] = interp1d(t[good], self[s][idir,good],
        #                                 fill_value='extrapolate')(t[bad])
            
        # Get time in seconds:
        dtime = np.array([x.total_seconds() for x in np.diff(self['time'])])
    
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
                dbn, dbe = np.zeros(dtime.size+1),np.zeros(dtime.size+1)

                # Central diff:
                dbn[1:-1] = (self[s][0,2:]-self[s][0,:-2])/(dtime[1:]+dtime[:-1])
                dbe[1:-1] = (self[s][1,2:]-self[s][1,:-2])/(dtime[1:]+dtime[:-1])
                # Forward diff:
                dbn[0]=(-self[s][0,2]+4*self[s][0,1]-3*self[s][0,0])/(dtime[1]+dtime[0])
                dbe[0]=(-self[s][1,2]+4*self[s][1,1]-3*self[s][1,0])/(dtime[1]+dtime[0])
                # Backward diff:
                dbn[-1]=(3*self[s][0,-1]-4*self[s][0,-2]+self[s][0,-3])/(dtime[-1]+dtime[-2])
                dbe[-1]=(3*self[s][1,-1]-4*self[s][1,-2]+self[s][1,-3])/(dtime[-1]+dtime[-2])
                
                # Create |dB/dt|_h:
                if s+'H' in stats:
                    self[s+'_dH'] = np.sqrt(dbn**2 + dbe**2)
                    
        # Return true on success:
        return True


    def calc_btotal(self):
        '''
        Calculate the magnitude of the perturbation for each magnetometer.
        Save as self['station name']['b'].
        '''

        # Loop through each magnetometer in the object.
        # Skip the time array.
        for mag in self.keys():
            if mag=='time': continue
            # Total perturbation is just the pythagorean sum!
            self[mag]['b'] = np.sqrt(
                self[mag]['bx']**2+
                self[mag]['by']**2+
                self[mag]['bz']**2)

        return True

#!/usr/bin/env python3

'''
A Spacepy-based API for obtaining SuperMAG data that interfaces with
Spacepy's DataModel and other tools.

Geomagnetic indexes: use `fetch_index`.
'''

import json
import urllib

import numpy as np

from spacepy.datamodel import dmarray, SpaceData
from matplotlib.dates import num2date

# Global vars:
baseurl = 'https://supermag.jhuapl.edu/services/'

# Variable name list as they appear in the returned structure:
index_vars = 'tval,SME,SML,SMLmlat,SMLmlt,SMLglat,SMLglon'.split(',') + \
    'SMU,SMUmlat,SMUmlt,SMUglat,SMUglon,smr'.split(',')
# Variable name list formatted for the HTTP request:
index_keys = ','.join(["sme", "sml", "smu", "mlat", "mlt", "glat",
                       "glon", "num", "smr", "ltsmr", "ltnum"])


def sm_to_dm(rawlines, varlist):
    '''
    Convert supermag JSON data into a datamodel object.

    Parameters
    ----------
    rawlines : list
        A list of the raw response from the SuperMAG get request.

    varlist : list
        A list of variables to extract and save. The return data often
        includes far more data than is needed; only the variables named
        in this list will be returned.
    '''

    npts = len(rawlines)

    data = SpaceData()
    for k in varlist:
        data[k] = dmarray(np.zeros(npts))

    for i, l in enumerate(rawlines):
        for k in varlist:
            data[k][i] = l[k]

    # Create time vector.
    data['time'] = num2date(data['tval']/(3600*24))

    return data


def fetch_index(start, end, logon):
    '''
    Fetch SuperMAG geomagnetic indexes and derived products.
    '''

    # Get extent in seconds:
    extent = int((end - start).total_seconds())

    # Build url for fetching:
    url = f"{baseurl}indices.php?fmt=json&python&nohead&" + \
          f"start={start:%Y-%m-%dT%H:%M}&extent={extent:012d}&" + \
          f"logon={logon}&indices={index_keys}"

    # Request data.
    resp = urllib.request.urlopen(url)

    # Parse data.
    data = sm_to_dm(json.loads(resp.read()), index_vars)

    return data


def fetch_mag(start, end, logon, station, baseline='all'):
    '''
    Fetch magnetometer data for a single statoin.

    Parameters
    ----------
    start, end : datetime or Ticktock
        Start and stop time of the interval to fetch.
    logon : str
        SuperMAG user name to access data.
    station : str
        IAGA code for station to fetch, e.g., EYR
    baseline : str, defaults to 'all'
        Select baseline subtraction: 'all' for annual and diurnal, 'yearly'
        for annual only, 'none' for no baseline subtraction.

    Returns
    -------

    Examples
    --------
    '''

    # Upper that case:
    station = station.upper()

    # Get extent in seconds:
    extent = int((end - start).total_seconds())

    # Build url for fetching:
    url = f"{baseurl}data-api.php?fmt=json&python&nohead&" + \
          f"start={start:%Y-%m-%dT%H:%M}&extent={extent:012d}&" + \
          f"logon={logon}&all&station={station}"

    # Request data.
    resp = urllib.request.urlopen(url)
    rawlines = json.loads(resp.read())

    # Count points:
    npts = len(rawlines)

    # Create container:
    data = SpaceData(attrs={'IAGA': rawlines[0]['iaga']})

    # Pre-populate arrays:
    data['nez'] = dmarray(np.zeros([npts, 3]), {'units': 'nT'})
    data['geo'] = dmarray(np.zeros([npts, 3]), {'units': 'nT'})
    data['tval'] = dmarray(np.zeros(npts), {'units': 's'})

    # Parse and sort:
    for i, line in enumerate(rawlines):
        data['tval'][i] = line['tval']
        data['nez'][i, :] = [line['N']['nez'],
                             line['E']['nez'],
                             line['Z']['nez']]
        data['geo'][i, :] = [line['N']['geo'],
                             line['E']['geo'],
                             line['Z']['geo']]

    # Create time vector.
    data['time'] = num2date(data['tval']/(3600*24))

    return data


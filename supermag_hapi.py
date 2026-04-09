#!/usr/bin/env python3

'''
A submodule for interfacing with the SuperMAG HAPI server.

For more information about the HAPI server, see the docstring for
`hapiserv_info`
'''

from datetime import datetime

import numpy as np
from spacepy.datamodel import dmarray, SpaceData

hapiserv = 'https://supermag.jhuapl.edu/hapi'


def convert_hapi_t(time):
    '''
    Convert HAPI time stamps into arrays of datetime objects.
    '''

    from dateutil.parser import parse

    return np.array([parse(t.decode('utf-8')) for t in time])


def hapiserv_info():
    '''
    This function serves as a source of information about the SuperMAG HAPI
    server.

    The datasets are split into two main groups: individual magnetometer
    data sets and geomagnetic index data sets.

    Magnetometer datasets have the following naming scheme:
    [station code]/baseline_[baseline removal option]/PT[time res]

    Baseline choices are 'baseline_none', 'baseline_yearly' (yearly trends
    removed), or 'baseline_all' (yearly and daily trends removed).

    Datasets of 'XYZ' are geographic coordinates (X=North, Y=East, Z=vertical
    down); 'NEZ' are local geomagnetic coordinates (N=North, E=East,
    Z=vertical down).
    '''

    pass


def fromHAPI(server, dataset, variables, tstart, tend):
    '''
    Given a HAPI data record response, translate the result into a Spacepy
    SpaceData object.
    '''

    result = SpaceData()


def fetch_hapi_mags(maglist, tstart, tend):
    '''

    '''

    # Examples from CDAWeb:
    swedat, magdat = 'AC_H0_SWE', 'AC_H0_MFI'
    swevar = 'Np,Tpr,alpha_ratio,V_GSM'
    magvar = 'BGSM,SC_pos_GSM'

    t1, t2 = tstart.isoformat(), tend.isoformat()
    swe, meta = hapi(hapiserv, dataset, parameters, t1, t2)

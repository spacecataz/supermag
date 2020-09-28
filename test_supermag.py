#!/usr/bin/env python
'''

'''

import numpy as np
import datetime as dt
import unittest

import supermag

datadir = supermag.install_dir+'data/'

# Define test case classes to group related tests together:
class TestSuperMag(unittest.TestCase):

    # First and last times in example files:
    knownTime = [dt.datetime(2001, 1, 1, 0, 0),
                 dt.datetime(2001, 1, 1, 23, 58)]

    # First and last magnetometer values for stations ALE, BOR:
    knownALE = {'bx':[-8.6,10.7],'by':[5.8,-4.9], 'bz':[-2.6,-5.6]}
    knownBOR = {'bx':[-2.3, 5.9],'by':[0.6, 1.7], 'bz':[ 2.6,-2.8]}
    
    def testV2(self):
        ''' Test the Version2 file format '''
        data = supermag.SuperMag(datadir+'example_v2.txt')

        # Test file version detection:
        self.assertEqual(data.vers, 2)
        
        # Test first and last time entries:
        self.assertEqual(data['time'][0],  self.knownTime[0] )
        self.assertEqual(data['time'][-1], self.knownTime[-1])

        # Test against known magnetic field values:
        for x in ['bx','by','bz']:
            # Station ALE:
            self.assertEqual(data['ALE'][x][ 0], self.knownALE[x][ 0])
            self.assertEqual(data['ALE'][x][-1], self.knownALE[x][-1])
            # Station BOR:
            self.assertEqual(data['BOR'][x][ 0], self.knownBOR[x][ 0])
            self.assertEqual(data['BOR'][x][-1], self.knownBOR[x][-1])
                             
    def testV5(self):
        ''' Test the Version2 file format '''
        data = supermag.SuperMag(datadir+'example_v5.txt')

        # Test file version detection:
        self.assertEqual(data.vers, 5)
        
        # Test first and last time entries:
        self.assertEqual(data['time'][0],  self.knownTime[0] )
        self.assertEqual(data['time'][-1], self.knownTime[-1])
        
        # Test against known magnetic field values:
        for x in ['bx','by','bz']:
            # Station ALE:
            self.assertEqual(data['ALE'][x][ 0], self.knownALE[x][ 0])
            self.assertEqual(data['ALE'][x][-1], self.knownALE[x][-1])
            # Station BOR:
            self.assertEqual(data['BOR'][x][ 0], self.knownBOR[x][ 0])
            self.assertEqual(data['BOR'][x][-1], self.knownBOR[x][-1])
            
if __name__=='__main__':
    unittest.main()

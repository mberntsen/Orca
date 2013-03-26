#!/usr/bin/python
"""G1203A Controller library

This module contains the basic controller interface and output management.
"""
__author__ = 'Martijn Berntsen <mxberntsen@hotmail.com>'
__version__ = '0.1'

# Standard modules

import GPIBInterface
from collections import namedtuple
import re

ORCAPosition = namedtuple('ORCAPosition', 'rail reach height bend twist grip side')
ORCAErrorItem = namedtuple('ORCAErrorItem', 'errorno description')
ORCASPollResult = namedtuple('ORCASPollResult', 'busy auto bit2 teachenter uninitialized error bit6 bit7')

class G1203AController:
  """Base class for a Lightbox controller."""
  GPIBADDRESS = 2
  
  def __init__(self, interface, **kwds):
    """Initializes the BaseController for Lightbox."""
    self.interface = interface
  #  super(BaseController, self).__init__()

  # ############################################################################
  # Info methods, some to be overridden for differing devices.
  #
  def Info(self):
    """Returns a dictionary of Lightbox controller info."""
    return {'controller': type(self).__name__,
            'device': self._DeviceInfo()}

  def _DeviceInfo(self):
    """Returns a batch of hardware-specific info."""
    return {'GPIB Address': self.GPIBADDRESS}

  def _StartUp(self):
    self.interface.Output(2, 'SU')
    #print 'ORCA startup'

  def _ShutDown(self):
    self.interface.Output(2, 'SD')
    #print 'ORCA shutdown'
  
  def _EnableTeach(self):
    self.interface.Output(2, 'ET')
    #print 'ORCA teachpendant enabled'

  def _DisableTeach(self):
    self.interface.Output(2, 'DT')
    #print 'ORCA teachpendant disabled'

  def _EnableCalibration(self):
    self.interface.Output(2, 'EC')
    
  def _LocateOnA(self):
    self.interface.Output(2, 'LO 0')
    #print 'ORCA locating on A...'

  def _LocateOnB(self):
    self.interface.Output(2, 'LO 1')
    #print 'ORCA locating on B...'

  def _OutputError(self):
    self.interface.Output(2, 'OE')
    errorlist = []
    re_float = re.compile('^(\d+) (.+)$')
    #while True:
    error = self.interface.Enter(2)
    print 'len=%d, e=%s' % (len(error), error)
      
      #if len(error) == 0:
      #  break;
    esplit = re_float.match(error)
    errorlist.append(ORCAErrorItem(int(esplit.group(1)), esplit.group(2)))
      #if int(esplit.group(1)) == 0:
      #  break
    return errorlist

  def _RequestActualPosition(self):
    self.interface.Output(2, 'RA')
    pos = self.interface.Enter(2).split()
    return ORCAPosition(float(pos[0]), float(pos[1]), float(pos[2]), float(pos[3]), float(pos[4]), float(pos[5]), pos[6])

  def _RequestPosition(self):
    self.interface.Output(2, 'RP')
    pos = self.interface.Enter(2).split()
    return ORCAPosition(float(pos[0]), float(pos[1]), float(pos[2]), float(pos[3]), float(pos[4]), float(pos[5]), pos[6])
  
  def _SPoll(self):
    ret = int(self.interface.SPoll(2).rstrip('\n\r'))
    return ORCASPollResult((ret & 1) == 1, (ret & 2) == 2, (ret & 4) == 4, (ret & 8) == 8, (ret & 16) == 16, (ret & 32) == 32, (ret & 64) == 64, (ret & 128) == 128)

  def _OutputStatus(self):
    self.interface.Output(2, 'OS')
    pos = self.interface.Enter(2).split()
    return pos

  def _Goto(self, p):
   self.interface.Output(2, 'MA %1.2f %1.2f %1.2f %1.2f %1.2f %1.2f' % (p.rail, p.reach, p.height, p.bend, p.twist, p.grip))

  def _IsBusy(self):
    ret = self._SPoll()
    return ret.busy or ret.auto

  def _SetSpeed(self, speed):
    self.interface.Output(2, 'SS %d' % speed)


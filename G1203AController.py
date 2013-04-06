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
import sys
import time

ORCAPosition = namedtuple('ORCAPosition', 'rail reach height bend twist grip side')
ORCAErrorItem = namedtuple('ORCAErrorItem', 'errorno description')
ORCASPollResult = namedtuple('ORCASPollResult', 'busy auto bit2 teachenter uninitialized error bit6 bit7')
ORCAForce = namedtuple('ORCAForce', 'twist grip')

class G1203AController:
  """Base class for a Lightbox controller."""
  
  def __init__(self, address, interface, **kwds):
    """Initializes the BaseController for Lightbox."""
    self.interface = interface
    self.address = address
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
    self.interface.Output(self.address, 'SU')
    #print 'ORCA startup'

  def _ShutDown(self):
    self.interface.Output(self.address, 'SD')
    #print 'ORCA shutdown'
  
  def _EnableTeach(self):
    self.interface.Output(self.address, 'ET')
    #print 'ORCA teachpendant enabled'

  def _DisableTeach(self):
    self.interface.Output(self.address, 'DT')
    #print 'ORCA teachpendant disabled'

  def _EnableCalibration(self):
    self.interface.Output(self.address, 'EC')
    
  def _FinishCalibration(self):
    self.interface.Output(self.address, 'FC')
    
  def _LocateOnA(self):
    self.interface.Output(self.address, 'LO 0')
    #print 'ORCA locating on A...'

  def _LocateOnB(self):
    self.interface.Output(self.address, 'LO 1')
    #print 'ORCA locating on B...'

  def _OutputError(self):
    self.interface.Output(self.address, 'OE')
    errorlist = []
    re_float = re.compile('^(\d+) (.+)$')
    #while True:
    error = self.interface.Enter(self.address)
      #if len(error) == 0:
      #  break;
    #print 'len=%d, e=%s' % (len(error), error)
    esplit = re_float.match(error)
    #if esplit != None:
    #  errorlist.append(ORCAErrorItem(int(esplit.group(1)), esplit.group(2)))
      #if int(esplit.group(1)) == 0:
      #  break
    #self.interface.Enter(self.address)
    return ORCAErrorItem(int(esplit.group(1)), esplit.group(2))

  def _OutputTracebuffer(self):
    self.interface.Output(self.address, 'OT')
    tracebuffer = ''
    while True:
      ret = self.interface.Enter(self.address)
      if len(ret) == 0:
        break
      tracebuffer += ret
    return tracebuffer

  def _OutputPrintbuffer(self):
    self.interface.Output(self.address, 'OP')
    tracebuffer = ''
    while True:
      ret = self.interface.Enter(self.address)
      if len(ret) == 0:
        break
      tracebuffer += ret
    return tracebuffer

  def _OX(self):
    self.interface.Output(self.address, 'OX')
    tracebuffer = ''
    while True:
      ret = self.interface.Enter(self.address)
      if len(ret) == 0:
        break
      tracebuffer += ret
    return tracebuffer

  def _OutputStatus(self):
    self.interface.Output(self.address, 'OS')
    time.sleep(.050)
    pos = self.interface.Enter(self.address).split()
    return pos

  def _RequestActualPosition(self):
    self.interface.Output(self.address, 'RA')
    pos = self.interface.Enter(self.address).split()
    return ORCAPosition(float(pos[0]), float(pos[1]), float(pos[2]), float(pos[3]), float(pos[4]), float(pos[5]), pos[6])
  
  def _RequestTeachPosition(self, readback=True):
    self.interface.Output(self.address, 'RT')
    if readback:
      pos = self.interface.Enter(self.address).split()
      return ORCAPosition(float(pos[0]), float(pos[1]), float(pos[2]), float(pos[3]), float(pos[4]), float(pos[5]), '')
  
  def _RequestForce(self):
    self.interface.Output(self.address, 'RF')
    pos = self.interface.Enter(self.address).split()
    return ORCAForce(int(pos[0]), int(pos[1]))

  def _RequestPosition(self):
    self.interface.Output(self.address, 'RP')
    pos = self.interface.Enter(self.address).split()
    return ORCAPosition(float(pos[0]), float(pos[1]), float(pos[2]), float(pos[3]), float(pos[4]), float(pos[5]), pos[6])
  
  def _SPoll(self):
    stat = self.interface.SPoll(self.address)
    #print stat
    if stat == '':
      return False
    ret = int(stat.rstrip('\n\r'))
    return ORCASPollResult((ret & 1) == 1, (ret & 2) == 2, (ret & 4) == 4, (ret & 8) == 8, (ret & 16) == 16, (ret & 32) == 32, (ret & 64) == 64, (ret & 128) == 128)

  def _Goto(self, p):
   self.interface.Output(self.address, 'MA %1.2f %1.2f %1.2f %1.2f %1.2f %1.2f' % (p.rail, p.reach, p.height, p.bend, p.twist, p.grip))

  def _IsBusy(self):
    ret = self._SPoll()
    return ret.busy or ret.auto

  def _SetSpeed(self, speed):
    self.interface.Output(self.address, 'SS %d' % speed)

  def _SetToolOffset(self, a, b, c):
    self.interface.Output(self.address, 'TO %1.2f %1.2f %1.2f' % (a, b, c))

  def _FL(self, angle, bend, speed):
    self.interface.Output(self.address, 'FL %1.2f %d %d' % (angle, bend, speed))
    #self.interface.Output(self.address, 'FL')

  def _SetForce(self, twist, grip):
    self.interface.Output(self.address, 'SF %d %d' % (twist, grip))

  def _ST(self, int1, int2):
    self.interface.Output(self.address, 'ST %d %d' % (int1, int2))

  def _SR(self, int1=4):
    self.interface.Output(self.address, 'SR %d' % (int1))

  def _WristLock(self):
    self.interface.Output(self.address, 'WL')

  def _WristUnlock(self):
    self.interface.Output(self.address, 'WU')

  def _SimpleStartup(self, side):
    #while True:
    #  pos = self.interface.Enter(self.address)
    #  print pos
    #  if len(pos) == 0:
    #    break
    #self.interface.flush()
    #time.sleep(0.5)
  
    #print self._SPoll()
    ret = self._OutputStatus()
    #print ret
    if ret[2] == 'MODE(TCH)':
      self._DisableTeach()

    while True:
      if not self._SPoll().error:
        break
      print 'ORCA in error:'
      e = self._OutputError()
      print '%3d %s' % (e.errorno, e.description)
      if e.errorno == 38:
        self._ShutDown()
        print 'shutdown 38' 

    ret = self._OutputStatus()
    if ret[1] == 'ARM(OFF)':
      self._StartUp()

    if ret[2] == 'MODE(---)':
      sys.stdout.write('start locating')
      if side == 'A':
        self._LocateOnA()
      else:
        self._LocateOnB()
      while True:
        s = self._SPoll()
        if s.error:
          break
        if not s.uninitialized:
          break
        time.sleep(1)
        sys.stdout.write('.')
        sys.stdout.flush()
      if s.error:
        print 'error'
        print self._OutputError()
        return 1
      print 'done'
    
    return 0



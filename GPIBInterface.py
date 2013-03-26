#!/usr/bin/python
"""Serial GPIB interface library

This module contains the basic controller interface and output management.
"""
__author__ = 'Martijn Berntsen <mxberntsen@hotmail.com>'
__version__ = '2.0'

# Standard modules
import serial
import sys

class ConnectionError(Exception):
  """A problem connecting to the USB serial light controller."""


class GPIBInterface:
  """Base class for a Lightbox controller."""
  FREQUENCY = 100
  GAMMA = 1
  LAYERS = 3
  OUTPUTS = 5

  def __init__(self, conn_info, **kwds):
    """Initializes the BaseController for Lightbox."""
    #super(GPIBInterface, self).__init__()
    self.connection = self._Connect(conn_info)

  # ############################################################################
  # Info methods, some to be overridden for differing devices.
  #
  def Info(self):
    """Returns a dictionary of Lightbox controller info."""
    return {'controller': type(self).__name__,
            'device': self._DeviceInfo()}

  def _DeviceInfo(self):
    """Returns a batch of hardware-specific info."""
    return {'type': 'serial',
            'baudrate': self.connection.baudrate,
            'port': self.connection.port}

  # ############################################################################
  # Connecting to attached hardware, also a convencience 'attempt to connect'
  #
  @staticmethod
  def _Connect(conn_info):
    """Connects to the given serial device."""
    try:
      #print 'Connecting to %s' % conn_info['device']
      return serial.Serial(port=conn_info['device'],
                           baudrate=conn_info.get('baudrate', 38400),
                           timeout=conn_info.get('timeout', 0.25))
    except serial.SerialException:
      raise ConnectionError('Could not open device %s.' % conn_info['device'])

  def Command(self, command):
    """Sends the given command to the device over the serial connection."""
    try:
      self.connection.write(command + '\n')
    except serial.SerialException:
      raise ConnectionError('Could not send command.')

  def Output(self, addr, data):
    self.Command('OUTPUT %d;%s' % (addr, data))

  def Enter(self, addr):
    self.Command('ENTER %d' % (addr))
    #while True:
    #  sys.stdout.write('%02X ' % ord(self.connection.read()))
    #  sys.stdout.flush()
    return self.connection.readline()
    #return self.connection.read(self.connection.inWaiting())
    #print self.connection.readline()
    #print self.connection.inWaiting()

  def SPoll(self, addr):
    self.Command('SPOLL %d' % (addr))
    return self.connection.readline()




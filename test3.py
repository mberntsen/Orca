#!/usr/bin/python
"""ORCA test code"""
__author__ = 'Martijn Berntsen <mxberntsen@hotmail.com>'
__version__ = '0.1'

# Standard modules

import G1203AController
import GPIBInterface
import time
import re
import sys
import math

def main():
  """Processes commandline input to setup the demo."""
  import optparse
  import sys
  
  parser = optparse.OptionParser()
  parser.add_option('-p', '--pendant', default=False, action="store_true",
                    help='enter teach pendant mode')
  parser.add_option('-c', '--calibrate', default=False, action="store_true",
                    help='enter calibration mode')
  parser.add_option('-s', '--side', default='A', help='Side to initialize on.')
  options, _arguments = parser.parse_args()

  gpib = GPIBInterface.GPIBInterface({'device' : '/dev/ttyS0'})
  gpib.connection.flushInput()
  gpib.Command("EOL R,X,10")
  gpib.Command("TIMEOUT 2,.1")
  
  G1203A = G1203AController.G1203AController(5, gpib)
  #OrcaAchter = G1203AController.G1203AController(2, gpib)
  #print G1203A._OutputError()

  #pos = gpib.Enter(5)
  #print pos
  #s = G1203A._SPoll()
  #print s
  #exit(1)

  ret = G1203A._SimpleStartup(side='A')
  if ret == 0:
    print 'init done'
  else:
    print 'init fail: %d' % ret
    exit(1)
  #achterste orca moet op B geinit worden

  if options.calibrate:
    G1203A._EnableCalibration()
    while True:
      stat = G1203A._SPoll()
      if stat.teachenter:
        G1203A._FinishCalibration()
        while True:
          s = G1203A._SPoll()
          print s
          if not s.uninitialized:
            break
          if s.error:
            e = G1203A._OutputError()
            print 'error %d %s' % (e.errorno, e.description)
          time.sleep(1)
        G1203A._RequestTeachPosition(False)
      if stat.error:
        e = G1203A._OutputError()
        print 'error %d %s' % (e.errorno, e.description)    
  
  G1203A._SetToolOffset(0, 4.4, 0)  

  if options.pendant:
    G1203A._EnableTeach()
    print '   rail   reach  height    bend   twist    grip'
    while True:
      s = G1203A._SPoll()
      if s.teachenter:
        p = G1203A._RequestTeachPosition()
        print '%7.2f %7.2f %7.2f %7.2f %7.2f %7.2f' % (p.rail, p.reach, p.height, p.bend, p.twist, p.grip)
      if s.error:
        e = G1203A._OutputError()
        print 'error %d %s' % (e.errorno, e.description)
      time.sleep(.1)
        
  #p = G1203A._RequestActualPosition()
  #print p
  #G1203A._Goto(G1203AController.ORCAPosition(p.rail, p.reach, p.height, p.bend, 90, p.grip, ''))
  #s = G1203A._SPoll()
  #while True:
  #  s = G1203A._SPoll()
  #  #print s
  #  if not s.busy:
  #    break
  #  time.sleep(0.25)
    
  s = G1203A._SPoll()
  print s
  #SA = ??

  gpib.Output(5, 'SF 10 10') 
  #G1203A._EnableTeach()
  #1e is angle
  #2e is bend (0 = keep, 1 = mirror)
  #3e is speed
  while True:
    s = G1203A._SPoll()
    print s
    if s.error:
      e = G1203A._OutputError()
      print 'error %d %s' % (e.errorno, e.description)
    #if not s.busy:
    #  break
    time.sleep(0.25)
  #G1203A._Goto(G1203AController.ORCAPosition(p.rail, p.reach, p.height, p.bend, 90, p.grip, ''))
  #while True:
  #  s = G1203A._SPoll()
  #  #print s
  #  if not s.busy:
  #    break
  #  time.sleep(0.25)
  
  #flipangle (0 .. 135)
  #flipwidth?
  
if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nEnd of demonstration.'



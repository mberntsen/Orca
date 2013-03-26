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
import numpy as np
import cv2
from priodict import priorityDictionary
import dijkstra

def main():
  """Processes commandline input to setup the demo."""
  import optparse
  import sys
  parser = optparse.OptionParser()
  parser.add_option('-c', '--controller', default='NewController',
                    help='Controller class to instantiate.')
  options, _arguments = parser.parse_args()

  gpib = GPIBInterface.GPIBInterface({'device' : '/dev/ttyS0'})
  gpib.connection.flushInput()
  gpib.Command("EOL R,X,10")
  gpib.Command("TIMEOUT 2,.1")
  
  G1203A = G1203AController.G1203AController(gpib)
  
  ret = G1203A._OutputStatus()
  if ret[2] == 'MODE(TCH)':
    G1203A._DisableTeach()

  while True:
    if not G1203A._SPoll().error:
      break
    print 'ORCA in error:'
    errors = G1203A._OutputError()
    for e in errors:
      print '%3d %s' % (e.errorno, e.description)
      if e.errorno == 38:
        G1203A._ShutDown()
        print 'shutdown 38' 

  ret = G1203A._OutputStatus()
  if ret[1] == 'ARM(OFF)':
    G1203A._StartUp()

  if ret[2] == 'MODE(---)':
    sys.stdout.write('start locating')
    G1203A._LocateOnB()
    while G1203A._SPoll().uninitialized:
      time.sleep(1)
      sys.stdout.write('.')
      sys.stdout.flush()
    print 'done'

  #G1203A._EnableTeach()
  
  G1203A._SetSpeed(100)
  p1 = G1203A._RequestPosition()
  print p1
  p2 = G1203AController.ORCAPosition(-200, 30, 0, -90, -180, p1.grip, '')
  print p2
  G1203A._Goto(p2)
  while G1203A._IsBusy():
    time.sleep(0.25) 
  
  #capture from camera at location 0
  cap = cv2.VideoCapture(0)
  #set the width and height, and UNSUCCESSFULLY set the exposure time
  cap.set(3,1280)
  cap.set(4,1024)
  cap.set(15, 0.01)

  threshold3 = 200
  enabletouching = False
  cycle = 0
  par1 = 1500
  par2 = 5

  while True:  
    ret, im = cap.read()
    hsv = cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    [h,s,v] = cv2.split(hsv)
    #ret,th1 = cv2.threshold(h,threshold1,255,cv2.THRESH_BINARY_INV)
    #ret,th2 = cv2.threshold(h,threshold2,255,cv2.THRESH_BINARY)
    ret,th3 = cv2.threshold(v,threshold3,255,cv2.THRESH_BINARY)
    #m1 = cv2.multiply(th1,th2)
    #m2 = cv2.multiply(m1,th3)
  
    m2 = cv2.medianBlur(th3,5)
    #m2 = cv2.blur(m2,(5, 5))
    edges = cv2.Canny(m2,150,300)
    cimg = cv2.cvtColor(edges,cv2.COLOR_GRAY2BGR)
    circles = cv2.HoughCircles(edges,cv2.cv.CV_HOUGH_GRADIENT,1,70,param1=par1,param2=par2,minRadius=31,maxRadius=33)
    if circles is not None:
      #print circles   
      circles = np.uint16(np.around(circles))
      for i in circles[0,:]:
        cv2.circle(cimg,(i[0],i[1]),i[2],(255,0,0),1)  # draw the outer circle
        #cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),3)     # draw the center of the circle 
    cv2.imshow('Circles', cimg)
    #cv2.imshow('edges', edges)
    #cv2.imshow('m1', m1)
    #cv2.imshow('m2', m2)
    #cv2.imshow('th1', th1)
    #cv2.imshow('th2', th2)
    #cv2.imshow('th3', th3)
    #cv2.imshow('h', h)
    #cv2.imshow('s', s)
    #cv2.imshow('v', v)
    #cv2.imshow('im', im)
    key = cv2.waitKey(50)
    #print key
    if key == 1048603: #Esc
      break
    if key == 1048679: #g
      enabletouching = True
    if key == 1048680: #h
      enabletouching = False
    if enabletouching and (cycle == 5):
      for i in circles[0,:]:
        print 'px=%d py=%d' % (i[0], i[1])
        nx = -200 + ((i[0] - 321) * 0.0472)
        ny = 30 + ((358 - i[1]) * 0.0450)
        if (ny < 45) and (ny > 25) and (nx < -185) and (nx > -215):
          p3 = G1203AController.ORCAPosition(nx, ny, 0, -90, -180, p1.grip, '')
          #print p3
          G1203A._Goto(p3)
          #time.sleep(0.5)
          while G1203A._IsBusy():
            time.sleep(0.25) 
      G1203A._Goto(p2)
      while G1203A._IsBusy():
        time.sleep(0.25)
    if key == 1048689:
      par1 = par1 + 50
    if key == 1048673:
      if par1 > 50:
        par1 = par1 - 50
    if key == 1048695:
      par2 = par2 + 1
    if key == 1048691:
      if par2 > 1:
        par2 = par2 - 1
    if key == 1048677:
      threshold3 = threshold3 + 10
    if key == 1048676:
      threshold3 = threshold3 - 10
    if key != -1:
      print 'threshold = %d, par1 = %d par2 = %d' % (threshold3, par1, par2)
    cycle = cycle + 1
    if cycle > 5:
      cycle = 0

  cv2.destroyAllWindows() 
  cv2.VideoCapture(0).release()

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nEnd of demonstration.'



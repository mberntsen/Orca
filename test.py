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
import math

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

  print cv2.__version__

  while True:  
    ret, img = cap.read()
    hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    [h,s,v] = cv2.split(hsv)
    #ret,th3 = cv2.threshold(v,threshold3,255,cv2.THRESH_BINARY)
    #m2 = cv2.medianBlur(th3,5)
    #edges = cv2.Canny(m2,150,300)
    
    #img2 = m2.copy()
    #img2 = edges.copy()
    #m2 = cv2.medianBlur(edges,5)
    img2 = cv2.blur(v,(5,5))
    #img2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #img2 = v.copy()

    detector = cv2.FeatureDetector_create('MSER')
    fs = detector.detect(img2)
    fs.sort(key = lambda x: -x.size)

    def supress(x):
      for f in fs:
        distx = f.pt[0] - x.pt[0]
        disty = f.pt[1] - x.pt[1]
        dist = math.sqrt(distx*distx + disty*disty)
        if (f.size > x.size) and (dist<f.size/2):
          return True

    sfs = [x for x in fs if not supress(x)]

    for f in sfs:
      cv2.circle(img, (int(f.pt[0]), int(f.pt[1])), int(f.size/2), (255,0,0), 2, cv2.CV_AA)
      cv2.circle(img, (int(f.pt[0]), int(f.pt[1])), int(f.size/2), (0,255,0), 1, cv2.CV_AA)

    h, w = img.shape[:2]
    vis = np.zeros((h, w*2+5), np.uint8)
    vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
    img3 = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)
    vis[:h, :w] = img3
    vis[:h, w+5:w*2+5] = img

    cv2.imshow("image", vis)
    #cv2.imshow("v", img2)
    key = cv2.waitKey(1)
    #print key
    if key == 27: #Esc
      break
    if key == 122: #z
      x0 = int(sfs[0].pt[0])
      y0 = int(sfs[0].pt[1])
      print 'x0 = %4d, y0 = %4d' % (x0, y0)
    if key == 103: #g
      for f in sfs:
        print 'px = %4d py = %4d' % (f.pt[0], f.pt[1])
        nx = -200 + ((f.pt[0] - x0) * 0.0472)
        ny = 30 + ((y0 - f.pt[1]) * 0.0450)
        if (ny < 45) and (ny > 25) and (nx < -185) and (nx > -215):
          p3 = G1203AController.ORCAPosition(nx, ny, 0, -90, -180, p1.grip, '')
          #print p3
          G1203A._Goto(p3)
          while G1203A._IsBusy():
            time.sleep(0.25) 
      G1203A._Goto(p2)
      while G1203A._IsBusy():
        time.sleep(0.25)

  cv2.destroyAllWindows() 
  cv2.VideoCapture(0).release()

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nEnd of demonstration.'



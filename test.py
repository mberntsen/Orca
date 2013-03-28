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
  scalex = 14.2 / 313
  scaley = 16.1 / 353

  print 'scalex = %1.5f, scaley = %1.5f' % (scalex, scaley)

  print cv2.__version__

  while True:  
    ret, img = cap.read()
    hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    [h,s,v] = cv2.split(hsv)
    et,th3 = cv2.threshold(v,threshold3,255,cv2.THRESH_BINARY)
    m2 = cv2.medianBlur(th3,9)
    m2 = cv2.medianBlur(m2,9)
    #edges = cv2.Canny(m2,150,300)
    
    img2 = m2.copy()
    contours1,hierarchy1 = cv2.findContours(img2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    #contours1,hierarchy1 = cv2.findContours(img2,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
	  
    points = []
    i = 0
    for cnt in contours1:
      area = cv2.contourArea(cnt)
      if area > 50:
        M = cv2.moments(cnt)
        centroid_x = M['m10']/M['m00']
        centroid_y = M['m01']/M['m00']
        if area > 2500:
          points.append([centroid_x, centroid_y, area])
          cv2.circle(img, (int(centroid_x), int(centroid_y)), 36, (255,0,0), 1, cv2.CV_AA)
          cv2.putText(img,str(unichr(ord('a') + i)), (int(centroid_x),int(centroid_y)), cv2.FONT_HERSHEY_PLAIN, 5.0, (255, 0, 0), thickness = 3)
          i = i + 1
        if area < 500:
          x0 = centroid_x
          y0 = centroid_y
          cv2.circle(img, (int(centroid_x), int(centroid_y)), 15, (0,255,0), 1, cv2.CV_AA)

    h, w = img.shape[:2]
    vis = np.zeros((h, w*2+5), np.uint8)
    vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
    img3 = cv2.cvtColor(m2, cv2.COLOR_GRAY2BGR)
    vis[:h, :w] = img3
    vis[:h, w+5:w*2+5] = img

    cv2.imshow("image", vis)
    key = cv2.waitKey(10)
    if key == 27: #Esc
      break
    if key == 122: #z
      print 'x0 = %4d, y0 = %4d' % (x0, y0)
    if key == 103: #g
      #G = {}
      #for i in range(0, len(points)):
      #  G2 = {}
      #  for j in range(0, len(points)):
      #    if i != j:
      #      dx = points[i][0] - points[j][0]
      #      dy = points[i][1] - points[j][1]
      #      d = int(math.sqrt((dx * dx) + (dy * dy)))
      #      G2[str(unichr(ord('a') + j))] = d
      #  G[str(unichr(ord('a') + i))] = G2
      for p in points:
        nx = -200 + ((p[0] - x0) * scalex)
        ny = 30 + ((y0 - p[1]) * scaley)
        if (ny < 45) and (ny > 25) and (nx < -185) and (nx > -215):
          p3 = G1203AController.ORCAPosition(nx, ny, 0, -90, -180, p1.grip, '')
          print 'px = %5d, py = %5d, x = %5.2f, y = %5.2f' % (p[0], p[1], nx, ny)
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



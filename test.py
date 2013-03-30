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
  
#action="store_false", dest="verbose", default=True,
#                  help="don't print status messages to stdout")
  parser = optparse.OptionParser()
  parser.add_option('-p', '--pendant', default=False, action="store_true",
                    help='exit with pendant enabled.')
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

  if options.pendant:
    G1203A._EnableTeach()
    while not G1203A._SPoll().teachenter:
      time.sleep(0.25)
    p1 = G1203A._RequestPosition()
    print p1
    exit(1)
    
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
  cap.set(15, 0.1)

  threshold3 = 53
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
    [hue,saturation,value] = cv2.split(hsv)
    et,th3 = cv2.threshold(value,threshold3,255,cv2.THRESH_BINARY)
    et,th4 = cv2.threshold(saturation,20,255,cv2.THRESH_BINARY)
    m2 = cv2.medianBlur(th3,9)
    h2 = cv2.multiply(th4, m2)
    h3 = cv2.multiply(hue, th4, scale=1.0/256)
    #cv2.imshow('test', h3)
    #h2 = cv2.multiply(m2,th4)
    #ca = cv2.multiply(m2,th4)
    #m2 = cv2.medianBlur(m2,9)
    #edges = cv2.Canny(m2,150,300)
    
    img2 = m2.copy()
    contours1,hierarchy1 = cv2.findContours(img2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    #contours1,hierarchy1 = cv2.findContours(img2,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
	  
    points = []
    i = 0
    for cnt in contours1:
      area = cv2.contourArea(cnt)
      length = cv2.arcLength(cnt, True)
      if (area > 2000) and (length > 170) and (length < 240):
        M = cv2.moments(cnt)
        centroid_x = M['m10']/M['m00']
        centroid_y = M['m01']/M['m00']
        if True:
          [x,y,w,h] = cv2.boundingRect(cnt)
          roi1 = hue[y:y+h,x:x+w]
          roi2 = saturation[y:y+h,x:x+w]
          #mask = np.zeros(roi.shape,np.uint8)
          #cv2.drawContours(mask,[cnt],0,255,-1)
          mask = th3[y:y+h,x:x+w]
          mean = cv2.mean(roi1,mask = mask)
          mean2 = cv2.mean(roi2,mask = mask)
          cointype = -1
          color = (128, 128, 128)#BGR
          #rood          
          #if (mean[0] > 0) and (mean[0] < 10) and (mean2[0] > 150) and (mean2[0] < 256):
          #  cointype = 0
          #  color = (0, 0, 255)
          satlimit = 70
          #oranje          
          if (mean[0] > 10) and (mean[0] < 40) and (mean2[0] > satlimit) and (mean2[0] < 256):
            cointype = 1
            color = (128, 128, 255)
          #blauw         
          if (mean[0] > 85) and (mean[0] < 120) and (mean2[0] > satlimit) and (mean2[0] < 256):
            cointype = 2
            color = (255, 0, 0)
          #paars        
          if (mean[0] > 150) and (mean[0] < 180) and (mean2[0] > satlimit) and (mean2[0] < 256):
            cointype = 3
            color = (255, 0, 255)
          #groen          
          if (mean[0] > 60) and (mean[0] < 85) and (mean2[0] > satlimit) and (mean2[0] < 256):
            cointype = 4
            color = (0, 255, 0)
          #wit          
          if (mean2[0] > 0) and (mean2[0] < satlimit):
            cointype = 5
            color = (255, 255, 255)
          
          #ca = cv2.multiply(roi,mask)
          #cv2.imshow('image%d' % len(points), ca)
          points.append([centroid_x, centroid_y, area, cointype, length])
          cv2.circle(img, (int(centroid_x), int(centroid_y)), 36, color, 1, cv2.CV_AA)
          #cv2.drawContours(img, [cnt], 0, (255,0,0))
          #cv2.putText(img,'%d, %d' % (int(area), int(length)), (int(centroid_x)-30,int(centroid_y)+10), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,0,0), thickness = 3)
          cv2.putText(img,'%d, %d' % (int(mean[0]), int(mean2[0])), (int(centroid_x)-30,int(centroid_y)+10), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,0,0), thickness = 3)
          i = i + 1

      if (area > 310) and (area < 650):
      #if area > 200:
        M = cv2.moments(cnt)
        centroid_x = M['m10']/M['m00']
        centroid_y = M['m01']/M['m00']
        x0 = centroid_x
        y0 = centroid_y
        cv2.circle(img, (int(centroid_x), int(centroid_y)), 15, (255,255,255), 1, cv2.CV_AA)
        cv2.putText(img,'%d, %d' % (int(area), int(length)), (int(centroid_x)-30,int(centroid_y)+10), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,0,0), thickness = 3)
          

    h, w = img.shape[:2]
    vis = np.zeros((h, w*2+5), np.uint8)
    vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
    #vis = cv2.cvtColor(th4, cv2.COLOR_GRAY2BGR)
    img3 = cv2.cvtColor(m2, cv2.COLOR_GRAY2BGR)
    vis[:h, :w] = img3
    vis[:h, w+5:w*2+5] = img

    cv2.imshow("image", vis)
    key = cv2.waitKey(10)
    if key == 27: #Esc
      break
    if key == 122: #z
      print 'x0 = %4d, y0 = %4d' % (x0, y0)
    if key == 104: #h
      print points
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
      #x0 = 0
      #y0 = 0
      #for p in points:
      #  if p[3] == 0:
      #    x0 = p[0]
      #    y0 = p[1]
      if True:#x0 != 0:
        for p in points:
          if p[3] == 0:
            continue
          nx = -200 + ((p[0] - x0) * scalex)
          ny = 30 + ((y0 - p[1]) * scaley)
          if (ny < 43) and (ny > 25) and (nx < -185) and (nx > -215):
            #vlak boven munt open
            p3 = G1203AController.ORCAPosition(nx, ny, -14, -90, -180, 4, '')
            print 'px = %5d, py = %5d, x = %5.2f, y = %5.2f' % (p[0], p[1], nx, ny)
            G1203A._Goto(p3)
            while G1203A._IsBusy():
              time.sleep(0.25) 
            #naar munt open
            p3 = G1203AController.ORCAPosition(nx, ny, -23.9, -90, -180, 4, '')
            print 'px = %5d, py = %5d, x = %5.2f, y = %5.2f' % (p[0], p[1], nx, ny)
            G1203A._Goto(p3)
            while G1203A._IsBusy():
              time.sleep(0.25) 
            #dicht
            p3 = G1203AController.ORCAPosition(nx, ny, -23.9, -90, -180, 2, '')
            print 'px = %5d, py = %5d, x = %5.2f, y = %5.2f' % (p[0], p[1], nx, ny)
            G1203A._Goto(p3)
            while G1203A._IsBusy():
              time.sleep(0.25) 
            #omhoog
            p3 = G1203AController.ORCAPosition(nx, ny, -14, -90, -180, 2, '')
            print 'px = %5d, py = %5d, x = %5.2f, y = %5.2f' % (p[0], p[1], nx, ny)
            G1203A._Goto(p3)
            while G1203A._IsBusy():
              time.sleep(0.25) 
            #naar bakje
            xpos = -134
            if p[3] == 1:
              xpos = -142
            if p[3] == 2:
              xpos = -150
            if p[3] == 3:
              xpos = -158
            if p[3] == 4:
              xpos = -166
            if p[3] == 5:
              xpos = -174
            p3 = G1203AController.ORCAPosition(xpos, 25, -14, -90, -180, 2, '')
            print 'px = %5d, py = %5d, x = %5.2f, y = %5.2f' % (p[0], p[1], nx, ny)
            G1203A._Goto(p3)
            while G1203A._IsBusy():
              time.sleep(0.25) 
            #open
            p3 = G1203AController.ORCAPosition(xpos, 25, -14, -90, -180, 4, '')
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



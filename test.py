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

def rotatepoint(xCenter, yCenter, x, y, Angle):
  xRot = xCenter + math.cos(Angle) * (x - xCenter) - math.sin(Angle) * (y - yCenter)
  yRot = yCenter + math.sin(Angle) * (x - xCenter) + math.cos(Angle) * (y - yCenter)
  return np.array([int(xRot),int(yRot)])

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
  
  G1203A = G1203AController.G1203AController(2, gpib)
  
  G1203A._SimpleStartup('B')

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
  p2 = G1203AController.ORCAPosition(-195, 30, 0, -90, -180, p1.grip, '')
  print p2
  G1203A._Goto(p2)
  while G1203A._IsBusy():
    time.sleep(0.25) 
  
  #G1203A._SetSpeed(10)
  #capture from camera at location 0
  cap = cv2.VideoCapture(0)
  #set the width and height, and UNSUCCESSFULLY set the exposure time
  cap.set(3,1280)
  cap.set(4,800)
  #cap.set(5,20)
  #cap.set(15, 0.1)
  #for i in range(0, 16):
  #  print '%d = %f' % (i, cap.get(i))


  #G1203A._DisableTeach()

  threshold3 = 20
  enabletouching = False
  cycle = 0
  par1 = 1500
  par2 = 5
  scalex = 298.0 / 966
  scaley = 210.5 / 684
  scalexy = (scalex + scaley) / 2.0
  startrun = False
  doall = False
  finishall = False


  print 'scalex = %1.5f, scaley = %1.5f, scalexy = %1.5f' % (scalex, scaley, scalexy)

  print cv2.__version__
  
  h = 800
  w = 1280
  angles = 120

  bgvalue = np.zeros((h, w), np.uint8)

  cv2.namedWindow("image", cv2.WINDOW_NORMAL)
  #cv2.namedWindow("big", cv2.WINDOW_NORMAL)
  #cv2.namedWindow("coin", cv2.WINDOW_NORMAL)
  #cv2.namedWindow("coinpolar", cv2.WINDOW_NORMAL)
  #cv2.namedWindow("hsgraph", cv2.WINDOW_NORMAL)
  
  #vis = np.zeros((h*2, w*2), np.uint8)
  vis = np.zeros((h, w*2), np.uint8)

  vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
  coinpolar = np.zeros((150,angles), np.uint8)
  coin = np.zeros((300, 300), np.uint8)
  
  gripmask = np.zeros((300,300), np.uint8)
  pt1 = (30,115)
  pt2 = (80,185)
  cv2.rectangle(gripmask, pt1, pt2, 255, -1)
  pt1 = (220,115)
  pt2 = (270,185)
  cv2.rectangle(gripmask, pt1, pt2, 255, -1)
  pmx = np.empty((150,angles), dtype=np.float32);
  pmy = np.empty((150,angles), dtype=np.float32);
  for i in range(pmx.shape[0]):
    for j in range(pmx.shape[1]):
      alpha = -j * (math.pi / (angles/2))
      pmx[i,j] = 150 + i * math.sin(alpha)
      pmy[i,j] = 150 + i * math.cos(alpha)
  gripmaskpolar = cv2.remap(gripmask, pmx, pmy, cv2.INTER_LINEAR)

  edgemask = np.zeros((h, w), np.uint8)
  cv2.rectangle(edgemask, (1,1), (w-2, h-2), 255)
  
  th3big = np.array([[255]*(w+300)]*(h+300), np.uint8)

  runmode = 0
  
  while True:  
    x0 = 0
    y0 = 0
  
    for i in range(0, 5):
      cap.grab()

    ret, img = cap.retrieve()
    #img3 = img.copy()#cv2.subtract(img, bgimg)
    hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    [hue,saturation,value] = cv2.split(hsv)
    value2 = cv2.subtract(value, bgvalue)
    img3 = cv2.cvtColor(cv2.merge((hue, saturation, value2)), cv2.COLOR_HSV2BGR)
    et,th3 = cv2.threshold(value2,threshold3,255,cv2.THRESH_BINARY)
    th3big[150:h+150,150:w+150] = th3
    
    img2 = th3.copy()
    contours1,hierarchy1 = cv2.findContours(img2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    
    points = []
    
    hsgraph = np.zeros((256,256), np.uint8)
          
    i = 0
    fishes = []
    zeros = []
    for cnt in contours1:
      [x,y,z] = cnt.shape
      if x > 40:
        cntmask = np.zeros((h, w), np.uint8)
        cv2.drawContours(cntmask, [cnt], 0, 255,3)
        edgeres = cv2.multiply(cntmask, edgemask)
        overlap = cv2.countNonZero(edgeres)
        if overlap == 0:
          ellipse = cv2.fitEllipse(cnt)
          [[ex,ey],[ew,el],ea] = ellipse
          if ew > 5:
            roundness = el/ew
            if roundness < 1.1:
              d_avg = (ew + el) / 2
              d_mm = d_avg * scalexy
              #cv2.putText(img3,'d = %.1f mm = %.0f px' % (d_mm, 2 * d_avg), (int(ex)-30,int(ey)+10), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 3)
              if d_mm > 10 and d_mm < 14:
                zeros.append([ex,ey,d_avg,cnt]) 
              if d_mm > 20 and d_mm < 40:
                fishes.append([ex,ey,d_avg,cnt])
        else:
          cv2.drawContours(img3, [cnt], 0, (0,0,255), 3)
          
    if len(fishes) == 0:
      runmode = 0
   
    if len(zeros) == 1:
      zero = zeros[0]
      zerox = zero[0]
      zeroy = zero[1]
      cv2.circle(img3, (int(zerox), int(zeroy)), int(zero[2]/2), (255,255,255), 3, cv2.CV_AA)

      for fishe in fishes:
        nx = -200 + ((fishe[0] - zerox) * scalex * 0.1)
        ny = 27.5 + ((zeroy - fishe[1]) * scaley * 0.1)

        if (fishe[1] > 40) or (fishe[1] < 25) or (fishe[0] > -185) or (fishe[0] < -215):
          cv2.circle(img3, (int(fishe[0]), int(fishe[1])), int(fishe[2]/2), (0, 255, 0), 3, cv2.CV_AA)
        x = int(fishe[0])-150
        y = int(fishe[1])-150
        coin = th3big[y+150:y+450,x+150:x+450]
        coinpolar = cv2.remap(coin, pmx, pmy, cv2.INTER_LINEAR)
        a3 = np.zeros((150,angles), np.uint8)
        c = np.zeros(angles//2, np.uint16)
        d1 = np.zeros(angles//2, np.uint16)
        d2 = np.zeros(angles//2, np.uint16)

        for i in range(0,angles//2):
          a2 = np.roll(gripmaskpolar, i, axis=1)
          a3 = np.multiply(coinpolar,a2)
          c[i] = np.count_nonzero(a3)

        u = 0
        for i in range(0,angles):
          u+=1
          if c[i%(angles//2)] > 0: 
            u = 0
          d1[i%(angles//2)] = u
        
        u = 0
        for i in range(angles-1,-1,-1):
          u+=1
          if c[i%(angles//2)] > 0:
            u = 0
          d2[i%(angles//2)] = u
        
        top_i = -1
        top_d = 0
        for i in range(0,angles//2):
          if d1[i] > d2[i]:
            d1[i] = d2[i]
          if d1[i] > top_d:
            top_d = d1[i]
            top_i = i

        if top_i >= 0:
          angledeg = (360 / angles) * top_i
          if angledeg > 90:
            angledeg -= 180
          anglerad = (math.pi / 180) * angledeg
          #cv2.putText(img3,'a = %.2f' % (angledeg), (int(fishe[0])-30,int(fishe[1])+34), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 3)
          pm1 = rotatepoint(int(fishe[0]), int(fishe[1]), int(fishe[0]) - 50, int(fishe[1]), anglerad)
          pm2 = rotatepoint(int(fishe[0]), int(fishe[1]), int(fishe[0]) + 50, int(fishe[1]), anglerad)  
          cv2.line(img3, (pm1[0], pm1[1]), (pm2[0], pm2[1]), (255, 0, 255), 3, cv2.CV_AA)
          
          x = int(fishe[0])-50
          y = int(fishe[1])-50
          coinh = hue[y:y+100,x:x+100]
          coins = saturation[y:y+100,x:x+100]
          coinv = value[y:y+100,x:x+100]
          coinm = th3[y:y+100,x:x+100]
          means = int(cv2.mean(coinh,coinm)[0])
          meanh = int(cv2.mean(coins,coinm)[0])
          meanv = int(cv2.mean(coinv,coinm)[0])
          hsgraph[meanh,means] = 255
          #cv2.putText(img3,'h(%d)s(%d)v(%d)' % (meanh, means, meanv), (int(fishe[0])-30,int(fishe[1])+60), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 3)
          cointype = -1
          if means < 90:
            if meanh < 70:
              cointype = 1
            if meanh >= 70:
              if means >= 45:
                cointype = 2
              else:
                cointype = 3
          if means >= 90 and means < 138:
            cointype = 4
          if means > 138:
            cointype = 5
          cv2.putText(img3,'%d' % (cointype), (int(fishe[0])-5,int(fishe[1])-5), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 3)
          points.append([int(fishe[0]), int(fishe[1]), angledeg, cointype])

    img4 = cv2.cvtColor(th3, cv2.COLOR_GRAY2BGR)
    vis[:h, :w] = img4
    vis[:h, w:w*2] = img3
    #vis[h:h*2, :w] = cv2.cvtColor(hue, cv2.COLOR_GRAY2BGR)
    #vis[h:h*2, w:w*2] = cv2.cvtColor(saturation, cv2.COLOR_GRAY2BGR)

    cv2.putText(vis,'fishes %d' % len(fishes), (5,24), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,255), thickness = 2)
    cv2.putText(vis,'zeros %d' % len(zeros), (5,48), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,255), thickness = 2)
    cv2.putText(vis,'points %d' % len(points), (5,72), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,255), thickness = 2)
    cv2.putText(vis,'runmode %d' % runmode, (5,96), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,255), thickness = 2)

    cv2.imshow("image", vis)
    #cv2.imshow("coin", coin)
    #cv2.imshow("coinpolar", coinpolar)
    #cv2.imshow("hsgraph", hsgraph)
    
    key = cv2.waitKey(1)
    if key == 27: #Esc
      break
    if key == 122: #z
      bgvalue = value.copy()
    if key == 104: #h
      print "      x       y angle"
      for p in points:
        print "%7.2f %7.2f %5d" % (p[0], p[1], p[2])
    if key == ord('p'):
      G1203A._SetSpeed(10)
      p3 = G1203AController.ORCAPosition(-200, 27.5, -23.9+0.6, -90, -180, 4, '')
      G1203A._Goto(p3)
      while G1203A._IsBusy():
        time.sleep(0.25) 
      time.sleep(0.5) 
      G1203A._ShutDown()
      time.sleep(0.5) 
      break
        
    if key == ord('0'):
      if len(zeros) != 1:
        print 'no reference found!'
      else:
        runmode = 0
    if key == ord('1'):
      if len(zeros) != 1:
        print 'no reference found!'
      else:
        runmode = 1
    if key == ord('2'):
      if len(zeros) != 1:
        print 'no reference found!'
      else:
        runmode = 2
    if key == ord('3'):
      if len(zeros) != 1:
        print 'no reference found!'
      else:
        #for i in range(0,10):
        #  print "%d..." % (10 - i)
        #  time.sleep(1)
        runmode = 3

    if runmode > 0:
           
      for p in points:
        zerox = zero[0]
        zeroy = zero[1]
        nx = -200 + ((p[0] - zerox) * scalex * 0.1)
        ny = 27.5 + ((zeroy - p[1]) * scaley * 0.1)
            
        #vlak boven munt open
        p3 = G1203AController.ORCAPosition(nx, ny, -14, -90, p[2] - 180, 4, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
         
        while True:   
          key = cv2.waitKey(1)
          if key == ord('0'):
            runmode = 0
          if key == ord('1'):
            runmode = 1
          if key == ord('2'):
            runmode = 2
          if key == ord('3'):
            runmode = 3
          
          if runmode != 1:
            break
          if key == ord('g'):
            break
   
          time.sleep(0.05)

        if runmode == 0:
          break

        #naar munt open
        p3 = G1203AController.ORCAPosition(nx, ny, -23.9+0.6, -90, p[2] - 180, 4, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        #dicht
        p3 = G1203AController.ORCAPosition(nx, ny, -23.9+0.6, -90, p[2] - 180, 2, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        #omhoog
        p3 = G1203AController.ORCAPosition(nx, ny, -14, -90, p[2] - 180, 2, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        
        cointype = p[3]
        #cointype  0,    1,    2,    3,    4,    5
        xpos = [-130, -138, -146, -154, -162, -170]
        ypos = [  25,   25,   25,   25,   25,   25]

        p3 = G1203AController.ORCAPosition(xpos[cointype], ypos[cointype], -14, -90, 0, 2, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        #open
        p3 = G1203AController.ORCAPosition(xpos[cointype], ypos[cointype], -14, -90, 0, 4, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 

      G1203A._Goto(p2)
      while G1203A._IsBusy():
        time.sleep(0.25)
      if runmode < 3:
        runmode = 0

  cv2.destroyAllWindows() 
  #cv2.VideoCapture(0).release()

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nEnd of demonstration.'



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
  p2 = G1203AController.ORCAPosition(-195, 30, 0, -90, 180, p1.grip, '')
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
  scalex = 14.2 / 313
  scaley = 16.1 / 353
  startrun = False
  doall = False
  finishall = False


  print 'scalex = %1.5f, scaley = %1.5f' % (scalex, scaley)

  print cv2.__version__
  
  h = 800
  w = 1280

  bgvalue = np.zeros((h, w), np.uint8)

  vis = np.zeros((h*2, w*2), np.uint8)
  vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
  cv2.namedWindow("image", cv2.WINDOW_NORMAL)
  #cv2.resizeWindow("image1",1280,800)
  #cv2.imshow("image1", vis)
  vis2 = np.zeros((160, 640), np.uint8)
  cv2.imshow("image2", vis2)   
  tr = np.zeros((150, 200), np.uint8)
  tr2 = cv2.cvtColor(tr, cv2.COLOR_GRAY2BGR)
  coin = np.zeros((300, 300), np.uint8)
  cv2.imshow("coin", coin)
  pmx = np.empty(tr.shape, dtype=np.float32);
  pmy = np.empty(tr.shape, dtype=np.float32);
  for i in range(pmx.shape[0]):
    for j in range(pmx.shape[1]):
      pmx[i,j] = 150 + i * math.sin(j * (2 * 3.141592654 / 200))
      pmy[i,j] = 150 + i * math.cos(j * (2 * 3.141592654 / 200))

          
      
  runmode = 0
  
  gripmask = np.zeros((h, w), np.uint8)
  cv2.rectangle(gripmask, (1,1), (w-2, h-2), 255)
      
  while False:
    cap.grab()
    ret, img = cap.retrieve()
    vis[:h, :w] = img
    hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    [hue,sat,val] = cv2.split(hsv)
    huegray = cv2.cvtColor(hue, cv2.COLOR_GRAY2BGR)
    satgray = cv2.cvtColor(sat, cv2.COLOR_GRAY2BGR)
    valgray = cv2.cvtColor(val, cv2.COLOR_GRAY2BGR)
    vis[:h, w:w*2] = huegray
    vis[h:h*2, :w] = satgray
    vis[h:h*2, w:w*2] = valgray
    cv2.imshow("image1", vis)
    key = cv2.waitKey(1)

  #while False:
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
    #et,th4 = cv2.threshold(saturation,20,255,cv2.THRESH_BINARY)
    #m2 = cv2.medianBlur(th3,9)
    #m4 = m2.copy()
    #h2 = cv2.multiply(th4, m2)
    #h3 = cv2.multiply(hue, th4, scale=1.0/256)
    
    img2 = th3.copy()
    contours1,hierarchy1 = cv2.findContours(img2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    
    points = []
    #gripmask = np.zeros((480, 640), np.uint8)
          
    i = 0
    fishes = []
    zeros = []
    for cnt in contours1:
      [x,y,z] = cnt.shape
      #print x
      if x > 40:
        cntmask = np.zeros((h, w), np.uint8)
        cv2.drawContours(cntmask, [cnt], 0, 255,3)
        gripres = cv2.multiply(cntmask, gripmask)
        overlap = cv2.countNonZero(gripres)
        if overlap == 0:
          ellipse = cv2.fitEllipse(cnt)
          #cv2.ellipse(img3,ellipse,(0,255,0),1)
          [[ex,ey],[ew,el],ea] = ellipse
          roundness = el/ew
          if roundness < 1.1:
            d_avg = (ew + el) / 2
            #cv2.ellipse(img3,((ex,ey),(d_avg,d_avg),0),(255,0,0),1)
            cv2.putText(img3,'d = %.1f' % (d_avg), (int(ex)-30,int(ey)+10), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 3)
            if d_avg > 35 and d_avg < 45:
              zeros.append([ex,ey,d_avg,cnt]) 
            if d_avg > 75 and d_avg < 100:
              fishes.append([ex,ey,d_avg,cnt])
        else:
          cv2.drawContours(img3, [cnt], 0, (0,0,255), 3)
          
    if len(fishes) == 0:
      runmode = 0
   
    if len(zeros) == 1:
      zero = zeros[0]
#      M = cv2.moments(zeros[0])
#      x0 = M['m10']/M['m00']
#      y0 = M['m01']/M['m00']
      cv2.circle(img3, (int(zero[0]), int(zero[1])), int(zero[2]/2), (255,255,255), 3)

#      for fishe in fishes:
      if len(fishes) > 0:
        fishe = fishes[0]
#        M = cv2.moments(cnt)
#        centroid_x = M['m10']/M['m00']
#        centroid_y = M['m01']/M['m00']
#        nx = -200 + ((centroid_x - x0) * scalex)
#        ny = 30 + ((y0 - centroid_y) * scaley)
        if (fishe[1] > 40) or (fishe[1] < 25) or (fishe[0] > -185) or (fishe[0] < -215):
          cv2.circle(img3, (int(fishe[0]), int(fishe[1])), int(fishe[2]/2), (0, 255, 0), 3)#, cv2.CV_AA)
        x = int(fishe[0])-150
        y = int(fishe[1])-150
        coin = value2[y:y+300,x:x+300]
        tr = cv2.remap(coin, pmx, pmy, cv2.INTER_LINEAR)
        et,tr1 = cv2.threshold(tr,threshold3,1,cv2.THRESH_BINARY)
        r = int(fishe[2]/2) + 5
        vsummat = tr1[r:150,0:200]
        cv2.imshow("vsummat", vsummat)
        vsum = np.sum(vsummat,0,np.uint8)
        et,vsumth = cv2.threshold(vsum,0,255,cv2.THRESH_BINARY)
        vsumth2 = np.add(vsumth[0:100],vsumth[100:200])
        cv2.imshow("vsumth", vsumth2)
        vdist = np.zeros(150,np.uint8)
        print "blaat"
        t = 0
        for i in range(0,100):
          t = t + 1
          if vsumth2[i] > 0:
            t = 0
          vdist[i] = t
        t = 0
        for i in range(0,100):
          t = t + 1
          if vsumth2[99-i] > 0:
            t = 0
          if vdist[99-i] > t:
            vdist[99-i] = t
        for i in range(0,100):
          print vdist[i]
        tr2 = cv2.cvtColor(tr1, cv2.COLOR_GRAY2BGR)
        cv2.line(tr2,(0,int(fishe[2]/2)),(200,int(fishe[2]/2)),(255,0,0),1)
        
        
        
#          cv2.putText(img3,'%d, %d' % (int(nx), int(ny)), (int(centroid_x)-30,int(centroid_y)+10), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 3)
#          continue

#        cv2.circle(img3, (int(centroid_x), int(centroid_y)), 36, (255, 0, 0), 1, cv2.CV_AA)
          
#        for angledeg in [0,15,-15,30,-30,45,-45,60,-60,75,-75,90]:
#          angle = (angledeg * 3.141592654) / 180
#          pm1 = rotatepoint(centroid_x, centroid_y, centroid_x - 79, centroid_y - 23, angle)
#          pm2 = rotatepoint(centroid_x, centroid_y, centroid_x - 79 + 41, centroid_y - 23, angle)
#          pm3 = rotatepoint(centroid_x, centroid_y, centroid_x - 79 + 41, centroid_y + 23, angle)
#          pm4 = rotatepoint(centroid_x, centroid_y, centroid_x - 79, centroid_y + 23, angle)
#          cnt2 = np.array([pm1, pm2, pm3, pm4])
#          pm1 = rotatepoint(centroid_x, centroid_y, centroid_x + 79, centroid_y - 23, angle)
#          pm2 = rotatepoint(centroid_x, centroid_y, centroid_x + 79 - 41, centroid_y - 23, angle)
#          pm3 = rotatepoint(centroid_x, centroid_y, centroid_x + 79 - 41, centroid_y + 23, angle)
#          pm4 = rotatepoint(centroid_x, centroid_y, centroid_x + 79, centroid_y + 23, angle)
#          cnt3 = np.array([pm1, pm2, pm3, pm4])
#          gripmask = np.zeros((480, 640), np.uint8)
#          cv2.fillConvexPoly(gripmask, cnt2, 255)
#          cv2.fillConvexPoly(gripmask, cnt3, 255)
#          gripres = cv2.multiply(m2, gripmask)
#          overlap = cv2.countNonZero(gripres)
#          if overlap == 0:
#            break

#        if overlap == 0:
#          points.append([centroid_x, centroid_y, angledeg])
#          pm1 = rotatepoint(centroid_x, centroid_y, centroid_x - 50, centroid_y, angle)
#          pm2 = rotatepoint(centroid_x, centroid_y, centroid_x + 50, centroid_y, angle)  
#          cv2.line(img3, (pm1[0], pm1[1]), (pm2[0], pm2[1]), (0, 255, 0), 5, cv2.CV_AA)
#          #cv2.circle(img3, (int(centroid_x), int(centroid_y)), 36, (255, 0, 0), 1, cv2.CV_AA)
#          #cv2.putText(img3,'%d' % overlap, (int(centroid_x)-30,int(centroid_y)+10), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,0,255), thickness = 3)

    img4 = cv2.cvtColor(th3, cv2.COLOR_GRAY2BGR)
    #img5 = cv2.cvtColor(value2, cv2.COLOR_GRAY2BGR)
    vis[:h, :w] = img4
    vis[:h, w:w*2] = img3
    vis[h:h*2, :w] = cv2.cvtColor(hue, cv2.COLOR_GRAY2BGR)
    vis[h:h*2, w:w*2] = cv2.cvtColor(saturation, cv2.COLOR_GRAY2BGR)

    cv2.putText(vis,'fishes %d' % len(fishes), (5,12), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 1)
    cv2.putText(vis,'zeros %d' % len(zeros), (5,36), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 1)
    cv2.putText(vis,'runmode %d' % runmode, (5,60), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,255,0), thickness = 1)

    cv2.imshow("image", vis)
    cv2.imshow("coin", coin)
    cv2.imshow("polar", tr2)

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
      p3 = G1203AController.ORCAPosition(-200, 30, -23.9, -90, 0, 4, '')
      G1203A._Goto(p3)
      while G1203A._IsBusy():
        time.sleep(0.25) 
      G1203A._ShutDown()
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
      print "meanh means meanm  type"
           
      for p in points:
        nx = -200 + ((p[0] - x0) * scalex)
        ny = 30 + ((y0 - p[1]) * scaley)
        #camera boven munt
        p3 = G1203AController.ORCAPosition(nx, ny - 6.3, -14, -90, 0, 4, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        #camera boven munt dichtbij
        p3 = G1203AController.ORCAPosition(nx, ny - 6.3, -20, -90, 0, 4, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
            
        for i in range(0, 5):
          cap.grab()
        ret, img = cap.retrieve()
        hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        [hue,saturation,value] = cv2.split(hsv)
        et,th3 = cv2.threshold(value,threshold3,255,cv2.THRESH_BINARY)
        et,th4 = cv2.threshold(saturation,100,255,cv2.THRESH_BINARY)
        m2 = cv2.medianBlur(th3,9)
        m3 = cv2.multiply(th4, m2)
        roi1 = hue[160:320,260:420]
        roi2 = saturation[160:320,260:420]
        roi3 = img[160:320,260:420]
        mask = m3[160:320,260:420]
        meanh = int(cv2.mean(roi1,mask = mask)[0])
        means = int(cv2.mean(roi2,mask = mask)[0])
        meanm = int(cv2.mean(mask)[0])
        vis2 = np.zeros((160, 640), np.uint8)
        vis2 = cv2.cvtColor(vis2, cv2.COLOR_GRAY2BGR)
        roi1bgr = cv2.cvtColor(roi1, cv2.COLOR_GRAY2BGR)
        roi2bgr = cv2.cvtColor(roi2, cv2.COLOR_GRAY2BGR)
        roi3bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        vis2[:160, :160] = roi1bgr
        vis2[:160, 160:320] = roi2bgr
        vis2[:160, 320:480] = roi3bgr
        vis2[:160, 480:640] = roi3
        cv2.imshow("image2", vis2)
            
        cointype = 0
        #color2 = [(128, 128, 128),(128, 128, 255),(255, 0, 0),(255, 0, 255),(0, 255, 0),(255, 255, 255)]#BGR
        colors = ["unknown", "orange", "blue", "purple", "green", "white"]
        #oranje          
        if (meanh > 5) and (meanh < 40) and (means > 90) and (means < 256):
          cointype = 1
        #blauw         
        if (meanh > 95) and (meanh < 120) and (means > 90) and (means < 256):
          cointype = 2
        #paars        
        if (meanh > 130) and (meanh < 180) and (means > 90) and (means < 256):
          cointype = 3
        #groen          
        if (meanh > 75) and (meanh < 95) and (means > 90) and (means < 256):
          cointype = 4
        #wit          
        if (meanm > 0) and (meanm < 15):
          cointype = 5
        
        print "%5d %5d %5d %10s" % (meanh, means, meanm, colors[cointype])
            
        #vlak boven munt open
        p3 = G1203AController.ORCAPosition(nx, ny, -20, -90, p[2], 4, '')
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
        p3 = G1203AController.ORCAPosition(nx, ny, -23.9, -90, p[2], 4, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        #dicht
        p3 = G1203AController.ORCAPosition(nx, ny, -23.9, -90, p[2], 2, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        #omhoog
        p3 = G1203AController.ORCAPosition(nx, ny, -14, -90, p[2], 2, '')
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        
        #cointype  0,    1,    2,    3,    4,    5
        xpos = [-134, -142, -150, -158, -166, -174]
        ypos = [  25,   25,   25,   25,   25,   25]

        p3 = G1203AController.ORCAPosition(xpos[cointype], ypos[cointype], -14, -90, 0, 2, '')
        #print 'px = %5d, py = %5d, x = %5.2f, y = %5.2f' % (p[0], p[1], nx, ny)
        G1203A._Goto(p3)
        while G1203A._IsBusy():
          time.sleep(0.25) 
        #open
        p3 = G1203AController.ORCAPosition(xpos[cointype], ypos[cointype], -14, -90, 0, 4, '')
        #print 'px = %5d, py = %5d, x = %5.2f, y = %5.2f' % (p[0], p[1], nx, ny)
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



"""    ret,th3 = cv2.threshold(v,threshold3,255,cv2.THRESH_BINARY)
    
    m2 = cv2.medianBlur(th3,5)
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
      cycle = 0"""


import numpy as np
import datetime
import cv2
import math

a = np.array([[3]*4]*5)
print a

#t1 = datetime.datetime.now()
angles = 120
coin = np.zeros((300,300), np.uint8)
p1 = (190,0)
p2 = (299,299)
cv2.rectangle(coin, p1, p2, 255, -1)

gripmask = np.zeros((300,300), np.uint8)
cv2.circle(coin, (150,150), 50, 255, -1)
p1 = (120,30)
p2 = (180,80)
cv2.rectangle(gripmask, p1, p2, 255, -1)
p1 = (120,220)
p2 = (180,270)
cv2.rectangle(gripmask, p1, p2, 255, -1)
#cv2.imshow("coin", coin)
#cv2.imshow("gripmask", gripmask)
pmx = np.empty((150,angles), dtype=np.float32);
pmy = np.empty((150,angles), dtype=np.float32);
for i in range(pmx.shape[0]):
  for j in range(pmx.shape[1]):
    alpha = j * (math.pi / (angles/2))
    pmx[i,j] = 150 + i * math.sin(alpha)
    pmy[i,j] = 150 + i * math.cos(alpha)
gripmaskpolar = cv2.remap(gripmask, pmx, pmy, cv2.INTER_LINEAR)
#cv2.imshow("coinpolar", coinpolar)
#cv2.imshow("gripmaskpolar", gripmaskpolar)

t1 = datetime.datetime.now()
coinpolar = cv2.remap(coin, pmx, pmy, cv2.INTER_LINEAR)
a3 = np.zeros((150,angles), np.uint8)
c = np.zeros(angles//2, np.uint16)
d = np.zeros(angles//2, np.uint16)
u = 0
t2 = datetime.datetime.now()
for i in range(0,angles//2):
  a2 = np.roll(gripmaskpolar, i, axis=1)
  a3 = np.multiply(coinpolar,a2)
  c[i] = np.count_nonzero(a3)
  u+=1
  if c[i] > 0: 
    u = 0
  d[i] = u

u = 0
top_i = -1
top_d = 0
for i in range((angles//2)-1,-1,-1):
  u+=1
  if c[i] > 0:
    u = 0
  if d[i] > u:
    d[i] = u
  if d[i] > top_d:
    top_d = d[i]
    top_i = i

t3 = datetime.datetime.now()

print d
print '%d @ %d' % (top_d, top_i)

print t2-t1
print t3-t2

#cv2.waitKey(0)

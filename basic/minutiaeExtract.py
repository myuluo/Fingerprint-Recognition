#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 20 15:12:33 2016

@author: zhangzimou

functions for minutiae extraction
    minutiae extraction
    minutiae validation and minutiae direction calculation
    singular points extraction
"""

import cv2
from matplotlib import pyplot as plt
import numpy as np
from numpy.lib.stride_tricks import as_strided as ast
from numpy.fft import fft2
from numpy.fft import ifft2
from numpy.fft import fftshift
from scipy.signal import convolve2d
import preprocess as pre

blockSize=15
def minutiaeExtract(img,imgfore):   
    """minutiae extraction: ending and bifurcation    
    img: thinned image
    imgfore: foreground image
    return: minutiae, directions
    """
    image=img.copy()
    P1=image[1:-1,1:-1]
    valid=np.where(P1==1)
    #P1:center; P2-P9:neighbors
    P1,P2,P3,P4,P5,P6,P7,P8,P9 = P1[valid],image[2:,1:-1][valid], image[2:,2:][valid], image[1:-1,2:][valid], image[:-2,2:][valid], image[:-2,1:-1][valid],image[:-2,:-2][valid], image[1:-1,:-2][valid], image[2:,:-2][valid]
    CN=pre.transitions_vec(P2,P3,P4,P5,P6,P7,P8,P9)
    ending_index=np.where(CN==1)
    bifur_index=np.where(CN==3)
    ending=np.asarray((valid[0][ending_index]+1,valid[1][ending_index]+1))
    bifur=np.asarray((valid[0][bifur_index]+1,valid[1][bifur_index]+1))
    #delete minutiae near the edge of the foreground
    kernel = np.ones((8,8),np.uint8)
    imgfore=cv2.erode(imgfore,kernel,iterations=4)
    edge1,edge2=np.where(imgfore[ending[0],ending[1]]==0),np.where(imgfore[bifur[0],bifur[1]]==0)
    ending=np.delete(ending.T,edge1[0],0)
    bifur=np.delete(bifur.T,edge2[0],0)
    #delete minutiae near the edge of the image
    edgeDistance=20
    valid1=(ending[:,0]>=edgeDistance) * (ending[:,0]<=img.shape[0]-edgeDistance)
    valid2=(ending[:,1]>=edgeDistance) * (ending[:,1]<=img.shape[1]-edgeDistance)
    ending=ending[np.where(valid1 * valid2)]
    valid1=(bifur[:,0]>=edgeDistance) * (bifur[:,0]<=img.shape[0]-edgeDistance)
    valid2=(bifur[:,1]>=edgeDistance) * (bifur[:,1]<=img.shape[1]-edgeDistance)
    bifur=bifur[np.where(valid1 * valid2)]              
    #validate minutiae and calculate directions at the same time
    ending,theta1=validateMinutiae(image,ending,1)
    bifur,theta2=validateMinutiae(image,bifur,0)
    return ending,bifur,theta1,theta2



def validateMinutiae(imgB,minutiae,ifending,blockSize=21):
    """validate minutiae, and calculate directions at the same
    return: validated minutiae, directions of minutiae
    """
    fill_output=np.asarray(map(lambda x:pre.fill(imgB[x[0]-blockSize/2:x[0]+blockSize/2+1,
                                       x[1]-blockSize/2:x[1]+blockSize/2+1],
                                    (blockSize/2,blockSize/2),ifending), minutiae ))
    imgF,position=fill_output[:,0],fill_output[:,1]
    CN=np.asarray(map(lambda x:pre.countCrossNum(x,ifending),imgF))
    if (ifending):
        valid=np.where(CN==1)
        position=position[valid]
        theta=np.asarray(map(lambda x:np.arctan2(blockSize/2-x[0],blockSize/2-x[1]),position))
        return minutiae[valid],theta
    else:
        valid=np.where(CN==3)
        position=position[valid]
        theta=np.asarray(map(bifurDirec,position))        
        return minutiae[valid],theta
def bifurDirec(position,blockSize=15):
    theta=np.arctan2(blockSize/2-position[:,0],blockSize/2-position[:,1])
    d=np.zeros(3)
    for i in range(3):
        d[i]=np.sum(np.abs(theta[i]-np.delete(theta,i)))
    return theta[np.argmax(d)]
                 
                 
def singular(img,imgfore):
    """ Poincare Index method
    img: enhanced image
    imgfore: foreground image
    return: core and delta position
    """
    blockSize=8
    theta=pre.calcDirection(img,blockSize,method='block-wise')
    P =[ theta[2:,1:-1], theta[2:,2:], theta[1:-1,2:], theta[:-2,2:], theta[:-2,1:-1],theta[:-2,:-2], theta[1:-1,:-2], theta[2:,:-2]]

    N,M=img.shape
    N1,M1=theta.shape
    delta=np.zeros((N1-2,M1-2))
    for i in range(8):
        if i==7:
            de=P[0]-P[7]
        else:
            de=P[i+1]-P[i]
        de[np.where(de<=-np.pi/2)]+=np.pi
        de[np.where(de>np.pi/2)]-=np.pi
        delta+=de
    delta /= 2*np.pi
    delta_new=np.zeros(theta.shape)
    delta_new[1:-1,1:-1]=delta
    delta=delta_new
    
    delta_extend=np.zeros(img.shape)
    delta_extend[::blockSize,::blockSize]=delta
    # decrease the area of the foreground
    imgfore=cv2.boxFilter(imgfore,-1,(29,29))
    imgfore[np.where(imgfore>0)]=255
    invalid=np.where(imgfore!=0)
    # delete the singular outside the foreground
    delta_extend[invalid]=0
    # find core and delta position   
    core_index=np.where((delta_extend<=0.55)*(delta_extend>=0.45))
    delta_index=np.where((delta_extend<=-0.45)*(delta_extend>=-0.55))                 
    return core_index, delta_index          
                 
                 
                 
                 
                 
                 
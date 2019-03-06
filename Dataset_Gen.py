#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 12 13:01:42 2019

@author: aramazzi
"""

import glob
from scipy.misc import imread 
from scipy.misc import imsave
from scipy.misc import toimage
from scipy.misc import imresize
from scipy import ndimage
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp

import os

datasetA ='SYNTHIA-SEQS-02-FALL/RGB/Stereo_Left/Omni_B/*.png'
datasetB ='SYNTHIA-SEQS-02-FALL/Depth/Stereo_Left/Omni_B/*.png'
datasetC ='SYNTHIA-SEQS-02-FALL/GT/COLOR/Stereo_Left/Omni_B/*.png'

destination = 'created_dataset/'

dataA = glob.glob(datasetA)
dataA = sorted(dataA)

dataB = glob.glob(datasetB)
dataB = sorted(dataB)

dataC = glob.glob(datasetC)
dataC = sorted(dataC)

count =1500 
for i,j,k in zip(dataA,dataB,dataC):
    count+=1
    print(count)
    img_A = imread(j)
    img_B = imread(i)
    img_C = imread(k)
    out = np.zeros((np.shape(img_B)[0],np.shape(img_B)[1]*3,3))
    
    if img_B.shape[2] == 3:
        out[:,0:np.shape(img_B)[1],0] = img_B[:,:,0]
        out[:,0:np.shape(img_B)[1],1] = img_B[:,:,1]
        out[:,0:np.shape(img_B)[1],2] = img_B[:,:,2]
    else:
    	out[:,0:np.shape(img_B)[1],0] = img_B
    	out[:,0:np.shape(img_B)[1],1] = img_B
    	out[:,0:np.shape(img_B)[1],2] = img_B
    
    if img_A.shape[2] == 3:        
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],0] = img_A[:,:,0]
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],1] = img_A[:,:,1]
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],2] = img_A[:,:,2]        
    else:
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],0] = img_A
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],1] = img_A
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],2] = img_A
        
    if img_C.shape[2] == 4:        
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],0] = img_C[:,:,0]
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],1] = img_C[:,:,1]
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],2] = img_C[:,:,2]        
    else:
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],0] = img_C
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],1] = img_C
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],2] = img_C
        
    toimage(out, cmin=0, cmax=255).save(destination+str(count)+'.jpg')
    

datasetA ='SYNTHIA-SEQS-02-FALL/RGB/Stereo_Left/Omni_F/*.png'
datasetB ='SYNTHIA-SEQS-02-FALL/Depth/Stereo_Left/Omni_F/*.png'
datasetC ='SYNTHIA-SEQS-02-FALL/GT/COLOR/Stereo_Left/Omni_F/*.png'

dataA = glob.glob(datasetA)
dataA = sorted(dataA)

dataB = glob.glob(datasetB)
dataB = sorted(dataB)

dataC = glob.glob(datasetC)
dataC = sorted(dataC)


for i,j,k in zip(dataA,dataB,dataC):
    count+=1
    print(count)
    img_A = imread(j)
    img_B = imread(i)
    img_C = imread(k)
    out = np.zeros((np.shape(img_B)[0],np.shape(img_B)[1]*3,3))
    
    if img_B.shape[2] == 3:
        out[:,0:np.shape(img_B)[1],0] = img_B[:,:,0]
        out[:,0:np.shape(img_B)[1],1] = img_B[:,:,1]
        out[:,0:np.shape(img_B)[1],2] = img_B[:,:,2]
    else:
    	out[:,0:np.shape(img_B)[1],0] = img_B
    	out[:,0:np.shape(img_B)[1],1] = img_B
    	out[:,0:np.shape(img_B)[1],2] = img_B
    
    if img_A.shape[2] == 3:        
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],0] = img_A[:,:,0]
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],1] = img_A[:,:,1]
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],2] = img_A[:,:,2]        
    else:
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],0] = img_A
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],1] = img_A
    	out[:,np.shape(img_B)[1]:2*np.shape(img_B)[1],2] = img_A
        
    if img_C.shape[2] == 4:        
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],0] = img_C[:,:,0]
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],1] = img_C[:,:,1]
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],2] = img_C[:,:,2]        
    else:
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],0] = img_C
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],1] = img_C
    	out[:,2*np.shape(img_B)[1]:3*np.shape(img_B)[1],2] = img_C
        
    toimage(out, cmin=0, cmax=255).save(destination+str(count)+'.jpg')
    
        

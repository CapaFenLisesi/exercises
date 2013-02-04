#!/usr/bin/python2
# -*- coding:utf-8 -*-
# Author: Sebastian Weber, 5 PI Universitaet Stuttgart
# some additions by: Patrick Kreissl, ICP Universitaet Stuttgart

from __future__ import division
from libs.simlib import Plotter, Params
import numpy as np
import subprocess
import os.path

# SETUP ###################################################################################################
print '==Setup=='

params = Params()

params.Ising_J = 1
params.Ising_H = 0

params.MC_Seed = 42
params.MC_Sweeps = 10000

params.T_Start = 2
params.T_Stop = 2.4
params.T_StepSize = 0.005 # only 0.02 would be needed

Ising_L = [4,16,64]
Binning_K = [50,200,800]

useCache = True

p = Plotter(show = True, pdf = False, pgf = False, latex=False, name='2binder')

# FUNCTIONS ###############################################################################################
#===Error analysis===
def binning(allValues,k):
    nBlocks=len(allValues)//k

    allBlocks = allValues[:nBlocks*k].reshape((-1,k))
    meanBlocks = np.mean(allBlocks,axis=1)
    meanValue = np.mean(meanBlocks)
    
    variance = np.mean((meanBlocks-meanValue)**2)/(nBlocks-1)
    
    return np.sqrt(variance)

def errorAll(func,arr,k):
    n = len(arr)
    result = np.empty(n)
    for i in range(n): result[i] = func(arr[i],k)
    return result

#===Finite Size Scaling===
def binderpar(mu):
    n = np.shape(mu)[0]
    result = np.empty(n)   
    for i in range(n): result[i] = 1 - 1./3 * np.mean(mu[i,:]**4)/np.mean(mu[i,:]**2)**2
    return result

#===Others===
def load(Ising_L):
    params.Ising_L = Ising_L
    filename = './cache/ising_'+params.id()+'.csv'
    fileexists = os.path.isfile(filename)
    
    if fileexists and useCache:
        print ' Data file found.'
    else:
        print ' Run c++ program ...'
        cmd = './c/Release/SimPhys_W6_C'
        if not os.path.isfile(cmd): cmd = './c/Debug/SimPhys_W6_C'
        if not os.path.isfile(cmd): raise Exception("C++ program not found.")
        args = params.args()
        args +=' -o "'+filename+'"'
        
        proc = subprocess.Popen(cmd+args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(proc.stdout.readline, ''): print ' >> '+line,
        proc.wait()
        print ' Data file created.'
    print ' Data loaded.'
    
    return np.loadtxt(filename);

def unique(arr):
    order = np.lexsort(arr.T)
    arr = arr[order]
    diff = np.diff(arr, axis=0)
    ui = np.ones(len(arr), 'bool')
    ui[1:] = (diff != 0).any(axis=1)
    return arr[ui]

# CALCULATIONS ############################################################################################
print '\n==Calculations=='    
#===Metropolis===
T = []
A = []
arrE = []
arrM = []
E = []
M = []
errE = []
errM = []
U = []

for i in range(len(Ising_L)):
    arr = load(Ising_L[i])
    V = Ising_L[i]**2 
    T.append(arr[::2,0])
    A.append(arr[::2,1])
    arrE.append(arr[::2,2:]/V)
    arrM.append(arr[1::2,2:]/V)
    E.append(np.mean(arrE[i],axis=1))
    M.append(np.mean(arrM[i],axis=1))
    errE.append(errorAll(binning,arrE[i],Binning_K[i]))
    errM.append(errorAll(binning,arrM[i],Binning_K[i]))
    U.append(binderpar(arrM[i]))

print 'Finished calculations.'

# PLOTS ###################################################################################################
print '\n==Plots=='

p.new(title='Binder parameter',xlabel='Temperature',ylabel='Binder parameter')
n = np.shape(T)[0]
for i in range(n): p.plot(T[i],U[i],label='for L = %s'%Ising_L[i])

p.new(title='Binder parameter',xlabel='1/Temperature = beta*k_B',ylabel='Binder parameter')
n = np.shape(T)[0]
for i in range(n): p.plot(1./T[i],U[i],label='for L = %s'%Ising_L[i])

p.make(ncols=2)

print 'Finished plots.'

#!/usr/bin/python2
# -*- coding:utf-8 -*-
# Author: Sebastian Weber, 5 PI Universitaet Stuttgart

from __future__ import division
from libs.simlib import Plotter
import numpy as np

'''
=== SETUP ===
'''
n = 4
J = 1
H = 0
TStart = 1
TStop = 5
TStep = 0.1
MCSteps = 10000
k = 200
np.random.seed(13)

useExact = True
useMC = True

p = Plotter(show = True, pdf = False, pgf = False, latex=False, name='ising')

'''
=== FUNCTIONS ===
'''
def unique(arr):
    order = np.lexsort(arr.T)
    arr = arr[order]
    diff = np.diff(arr, axis=0)
    ui = np.ones(len(arr), 'bool')
    ui[1:] = (diff != 0).any(axis=1)
    return arr[ui]

itmp = np.arange(-1,n-1)

#==Exact===
def generateAllStates(n=n):
    nsqrt = n*n
    possibilities = np.mgrid[[slice(-1,3,2) for _ in range(nsqrt)]] # Vectorization makes the calculation fast as hell.
    configurations = possibilities.reshape(n,n,-1).T 
    return configurations

def calcEFromAll(configurations, J=J, H=H, n=n, i=itmp):
    E = -J*np.sum(np.sum(configurations*configurations[:,:,i]+configurations*configurations[:,i,:],axis=1),axis=1)
    E -= H*np.sum(np.sum(configurations,axis=1),axis=1) # Attention: Numpy doesn't like "E /= n**2". It applies integer division!
    return E

def calcMFromAll(configurations, n=n):
    M = np.sum(np.sum(configurations,axis=1),axis=1)
    return M

def calcMean(O,E,T,n=n):
    Exp = np.exp(-E/T)
    PartitionFunction = np.sum(Exp)
    Exp = np.exp(-E/T)
    Mean=np.sum(O*Exp)/PartitionFunction/n**2
    return Mean

#==MC===
def metropolisMC(N,Phi,T, n=n, i=itmp):
    # Calculate start values
    E = (-J*np.sum(Phi*Phi[:,i]+Phi*Phi[i,:])-H*np.sum(configuration)) # Energy
    M = np.sum(Phi) # Magnetization
    P = np.exp(-E/T) # Probability
    
    # Initialize variables
    arrayE = np.empty(N+1)
    arrayM = np.empty(N+1)
    arrayP = np.empty(N+1)
    arrayE[0] = E
    arrayM[0] = M
    arrayP[0] = P
    actrate=0
    
    for i in range(1,N+1):
        # Select a spin
        k, l = np.random.randint(0,n,2)
        k_p = k+1
        l_p = l+1
        if k_p >= n: k_p = 0
        if l_p >= n: l_p = 0
        
        # Performe a trial move
        newE = E+2*Phi[k,l]*(J*(Phi[k-1,l]+Phi[k_p,l]+Phi[k,l-1]+Phi[k,l_p])+H)
        newP = np.exp(-newE/T)
        
        # Attempt to accept the move
        r = np.random.uniform(0,1)
        if r < min(1,newP/P):
            
            # If move accepted, save new values
            E = newE
            P = newP
            M = M-2*Phi[k,l]
            Phi[k,l] *= -1
            actrate+=1

        # Write current values in array
        arrayE[i] = E
        arrayM[i] = M
        arrayP[i] = P

    return arrayE/n**2, arrayM/n**2, arrayP, actrate/N

#===ERROR ANALYSIS===
def binning(allValues,k = k):
    nBlocks=len(allValues)//k

    allBlocks = allValues[:nBlocks*k].reshape((-1,k))
    meanBlocks = np.mean(allBlocks,axis=1)
    meanValue = np.mean(meanBlocks)
    
    variance = np.mean((meanBlocks-meanValue)**2)/(nBlocks-1)
    
    return np.sqrt(variance)

def jackknife(allValues, k = k):
    nBlocks=len(allValues)//k

    allBlocks = allValues[:nBlocks*k].reshape((nBlocks,-1))
    sumBlocks = np.sum(allBlocks,axis=1)
    sumValue = np.sum(sumBlocks)

    meanJBlocks = (sumValue-sumBlocks)/((nBlocks-1)*k)
    meanValue = sumValue/(nBlocks*k)
    
    variance = np.mean((meanJBlocks-meanValue)**2)*(nBlocks-1)
    
    return np.sqrt(variance)

def errorAll(func,arr,k = k):
    n = len(arr)
    result = np.empty(n)
    for i in range(n): result[i] = func(arr[i],k)
    return result

'''
=== CALCULATIONS ===
'''
T = np.arange(TStart, TStop+TStep, TStep)


#==Exact===
if useExact:
    configurations = generateAllStates(n)

    M = calcMFromAll(configurations)
    E = calcEFromAll(configurations)
    
    meanE = np.empty_like(T)
    meanM = np.empty_like(T)
    meanMabs = np.empty_like(T)
    for i in range(len(T)):
        meanE[i] = calcMean(E,E,T[i])
        meanM[i] = calcMean(M,E,T[i])
        meanMabs[i] = calcMean(abs(M),E,T[i])
    
    print 'Finished exact calculation.'

#==MC===
if useMC:
    configuration = 2*np.random.randint(0,2,(n,n))-np.ones((n,n))
    
    arrayE = np.empty((len(T),MCSteps+1))
    arrayM = np.empty((len(T),MCSteps+1))
    arrayP = np.empty((len(T),MCSteps+1))
    arrayA = np.empty(len(T))
    
    for i in range(len(T)):
        arrayE[i], arrayM[i], arrayP[i], arrayA[i] = metropolisMC(MCSteps,configuration,T[i])
    
    MC_meanE = np.mean(arrayE,axis=1)
    MC_meanM = np.mean(arrayM,axis=1)
    MC_meanMabs = np.mean(abs(arrayM),axis=1)
    MC_acceptance = np.mean(arrayA)
    MC_E = arrayE.ravel()
    MC_M = arrayM.ravel()
    MC_P = arrayP
    print 'Finished metropolis calculation (acceptance=%s).'%(MC_acceptance)

    MC_errmE = errorAll(binning,arrayE)
    MC_errmM = errorAll(binning,arrayM)
    MC_errmMabs = errorAll(binning,abs(arrayM))
    
    print 'Finished error calculation.'

'''
=== PLOTS ===
'''

p.new(title='Mean energy',xlabel='Temperature',ylabel='Energy')
if useExact:
    p.plot(T,meanE,label='exact')
if useMC:
    p.errorbar(T, MC_meanE, yerr=MC_errmE, label='metropolis')

p.new(title='Mean magnetization',xlabel='Temperature',ylabel='Magnetization')
if useExact:
    p.plot(T,meanM,label='exact')
if useMC:
    p.errorbar(T, MC_meanM, yerr=MC_errmM, label='metropolis')

p.new(title='Mean absolute magnetization',xlabel='Temperature',ylabel=r'$\vert Magnetization \vert$')
if useExact:
    p.plot(T,meanMabs,label='exact')
if useMC:
    p.errorbar(T, MC_meanMabs, yerr=MC_errmMabs, label='metropolis')

p.new(title='Energy(magnetization)',xlabel='Magnetization',ylabel='Energy')
if useExact:
    [X, Y] = unique(np.array([M,E]).T/n**2).T
    p.plot(X,Y,'o',label='exact')
if useMC:
    [X, Y] = unique(np.array([MC_M,MC_E]).T).T
    p.plot(X,Y,'^',label='metropolis')

if useMC:
    '''
    p.new(title='Frequency of probabilities as a function of temperature',xlabel='log(Probability)',ylabel='Temperature')
    temp = (T*np.ones_like(arrayP).T).T
    H, xedges, yedges = np.histogram2d(temp.flatten(), np.log10((1/np.sum(arrayP,axis=1)*arrayP.T*len(arrayP[1])).T).flatten(), bins=(len(T),100))
    p.imshow(H, extent=[yedges[0], yedges[-1], xedges[0], xedges[-1]], interpolation='nearest',aspect='auto',origin='lower')
    '''
    
    p.new(title='Frequency of energies as a function of temperature',xlabel='Energy',ylabel='Temperature')
    temp = (T*np.ones_like(arrayE).T).T
    H, xedges, yedges = np.histogram2d(temp.flatten(), arrayE.flatten(), bins=(len(T),100))
    p.imshow(H, extent=[yedges[0], yedges[-1], xedges[0], xedges[-1]], interpolation='nearest',aspect='auto',origin='lower')
    
    p.new(title='Frequency of magnetizations as a function of temperature',xlabel='Magnetization',ylabel='Temperature')
    temp = (T*np.ones_like(arrayM).T).T
    H, xedges, yedges = np.histogram2d(temp.flatten(), arrayM.flatten(), bins=(len(T),100))
    p.imshow(H, extent=[yedges[0], yedges[-1], xedges[0], xedges[-1]], interpolation='nearest',aspect='auto',origin='lower')
    
    p.new(title='Binning error',xlabel='k',ylabel='error')
    ks = np.arange(1,300,1)
    error = np.empty((len(ks),len(arrayE)))
    for i in range(len(ks)):
        error[i] = errorAll(binning,arrayE,ks[i])
    p.plot(ks,error)
    
    p.new(title='Difference between binning and jackknife error',xlabel='k',ylabel='error')
    ms = np.arange(1,300,1)
    error = np.empty((len(ms),len(arrayE)))
    for i in range(len(ms)):
        error[i] = errorAll(jackknife,arrayE,ms[i])-errorAll(binning,arrayE,ks[i])
    p.plot(ms,error)

print 'Finished plots.'
p.make(ncols=2)
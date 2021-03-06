#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import os, sys, pickle
import numpy as np
#import scipy as sp
#import scipy.signal
from libs.simlib import Plotter

"""==== PARAMETERS ===="""
# path to simulation File
datafilename = "./data/series.dat"
p = Plotter(show = True, pdf = True, pgf = False, name='series')

"""=== LOADING DATA ==="""
# check whether datafilename is given/data file exists
if len(datafilename) == 0:
    print "ERROR: No path to data file given."
    sys.exit(1)
if not os.path.exists(datafilename):
    print "ERROR: '%s' doesn't exist." % datafilename
    sys.exit(1)

# read from datafile
print "Reading data from '%s.'" % datafilename
datafile = open(datafilename, 'r')
s0, s1, s2, s3, s4  = pickle.load(datafile)
datafile.close()

"""==== DEFINITIONS ==="""
def variance(x):
    out = (x-np.mean(x))**2
    out = np.sum(out)
    return out/len(x)/(len(x)-1)

def mean(x): return np.sum(x)/len(x)

# autocorrelation function, normalized
def acf_n(x):
    N = len(x)
    x -= mean(x)
    out = np.zeros((N))
    for i in range(N):
        out[i] = np.mean(x[i:N]*x[0:N-i])
    #out -= np.mean(x)**2
    return out/out[0]
              
# integrated autocorrelation function
def acf_int(x):
    N = len(x)
    x0 = acf(x)
    out = np.zeros((N))
    for i in range(N):
        if i == 0: out[i] = x0[0]
        else: out[i] = out[i-1]+x0[i]
    return out

# cross correlation via fft
def ccr(a, b):
    return np.fft.irfft(np.fft.rfft(a).conjugate()*np.fft.rfft(b))

# autocorrelation via ccr
def acf(x):
    x0 = x - np.mean(x)
    x0 = np.append(x0, np.zeros((len(x))))
    out = ccr(x0, x0)
    out = out [0:len(x)]
    out /= np.arange(len(x), 0, -1)
    return (out/out[0])

# estimation of autocorrelation time
def est_act(x):
    tau = 0.5
    kmax = 1
    xcor = acf(x)
    while kmax < 6*tau:
        tau += xcor[kmax]
        kmax += 1
    return tau, kmax
       
# automatic error analysis via autocorrelation analysis
def aea(x):
    N = len(x)
    tau, kmax = est_act(x)
    errtau = tau*np.sqrt(2*(2*kmax+1)/N)
    return np.mean(x), np.sqrt(variance(x)), tau, errtau, int(12*(tau/errtau)**2)

# BINNING ANALYSIS
# blocking of given time series x and block size k
def block(x, k):
    N = len(x)    
    x = x[0:N-N%k]
    N = len(x)
    B = int(N/k)
    out = np.zeros((B))
    for i in range(B):
        out[i] = np.mean(x[i*k:(i+1)*k])
    return out

# compute block variance for given time series x and block size k
def cbv(x, k):
    b = block(x, k)
    b -= np.mean(b)
    return np.sum(b*b)/(len(b)-1)

# estimated autocorrelation time from blocking/blocking tau
def est_act_b(x, k): return 0.5*k*cbv(x,k)/np.var(x)

# estimate error of mean value using block variance
def eem(x, k): return np.sqrt(cbv(x, k)/(len(x)//k))

# compute sequences of block variance for plotting
def cbv_seq(x):
    k = 2000
    t = np.zeros((2000))
    for i in range(k):
        t[i] = est_act_b(x, i+1)
    return t

# compute sequences of estimated error of mean value using block variance
def eem_seq(x):
    k = 2000
    t = np.zeros((2000))
    for i in range(k):
        t[i] = eem(x, i+1)
    return t

# WORKING, BUT VERY SLOW
# blocking for jackknifing
def block_j(x,k):
    N = len(x)    
    x = x[0:N-N%k]
    N = len(x)
    B = N//k
    out = np.zeros((B,k))
    for i in range(B):
        out[i,:] = x[i*k:(i+1)*k]
    return out

# Jackknife error
def jke(x, k):
    xb = block_j(x, k)
    #Nb = len(xb[:,0])
    Nb = np.shape(xb)[0]
    Oj = np.mean(x)
    out = 0
    for i in range(Nb):
        h = (np.append(xb[0:i,:],xb[i+1:,:]) - Oj)
        out += np.dot(h,h)
    return np.sqrt(out*(Nb-1)/Nb)

    
# compute sequences of estimated error of mean value using block variance
def jke_seq(x):
    k = 2000
    t = np.zeros((2000))
    for i in range(k):
        t[i] = jke(x, i+1)
    return t


"""=== AUTOCORRELATE DATASETS ==="""
print "Computing normalized autocorrelation function of..."
print "... dataset 1"
acfn0 = acf_n(s0)
print "... dataset 2"
acfn1 = acf_n(s1)
print "... dataset 3"
acfn2 = acf_n(s2)
print "... dataset 4"
acfn3 = acf_n(s3)
print "... dataset 5"
acfn4 = acf_n(s4)

print "Computing normalized autocorrelation function (via fft) of..."
print "... dataset 1"
acf0 = acf(s0)
print "... dataset 2"
acf1 = acf(s1)
print "... dataset 3"
acf2 = acf(s2)
print "... dataset 4"
acf3 = acf(s3)
print "... dataset 5"
acf4 = acf(s4)

print "Computing integrated autocorrelation function (via fft) of..."
print "... dataset 1"
acfi0 = acf_int(s0)
print "... dataset 2"
acfi1 = acf_int(s1)
print "... dataset 3"
acfi2 = acf_int(s2)
print "... dataset 4"
acfi3 = acf_int(s3)
print "... dataset 5"
acfi4 = acf_int(s4)

"""=== AUTOMATIC ERROR ANALYSIS ==="""
print "Computing automatic error analysis function of..."
print "| used dataset | mean value | error of mean value | est. autocor. time | error of autocor. time | N_eff | "
print "... dataset 1:", aea(s0)
print "... dataset 2:", aea(s1)
print "... dataset 3:", aea(s2)
print "... dataset 4:", aea(s3)
print "... dataset 5:", aea(s4)

"""=== BINNING ANALYSIS ==="""
print "Computing blocking taus of..."
print "... dataset 1"
bts0 = cbv_seq(s0)
print "... dataset 2"
bts1 = cbv_seq(s1)
print "... dataset 3"
bts2 = cbv_seq(s2)
print "... dataset 4"
bts3 = cbv_seq(s3)
print "... dataset 5"
bts4 = cbv_seq(s4)

print "Computing blocking estimated error of mean value of..."
print "... dataset 1"
ems0 = eem_seq(s0)
print "... dataset 2"
ems1 = eem_seq(s1)
print "... dataset 3"
ems2 = eem_seq(s2)
print "... dataset 4"
ems3 = eem_seq(s3)
print "... dataset 5"
ems4 = eem_seq(s4)

"""=== JACKKNIFE ANALYSIS ==="""
print "Computing jackknife error of mean value of..."
print "... dataset 1"
jks0 = jke_seq(s0)
print "... dataset 2"
jks1 = jke_seq(s1)
print "... dataset 3"
jks2 = jke_seq(s2)
print "... dataset 4"
jks3 = jke_seq(s3)
print "... dataset 5"
jks4 = jke_seq(s4)



"""==== PLOTTING ===="""
print "Plotting..."

# first 1000 values of the data series s0, s1, s2, s3, s4 over time
p.new(xlabel='time',ylabel='value')
p.plot(s0[0:1000], label='dataset 1')
p.plot(s1[0:1000], label='dataset 2')
p.plot(s2[0:1000], label='dataset 3')
p.plot(s3[0:1000], label='dataset 4')
p.plot(s4[0:1000], label='dataset 5')

# plot autocorrelation of s0, s1, s2, s3, s4 over k
p.new(xlabel='k',ylabel='normalized autocorrelation')
p.plot(acfn0[0:100000], label='acf of dataset 1')
p.plot(acfn1[0:100000], label='acf of dataset 2')
p.plot(acfn2[0:100000], label='acf of dataset 3')
p.plot(acfn3[0:100000], label='acf of dataset 4')
p.plot(acfn4[0:100000], label='acf of dataset 5')

# plot autocorrelation via fft  of s0, s1, s2, s3, s4 over k
p.new(xlabel='k',ylabel='normalized autocorrelation via fft')
p.plot(acf0[0:100000], label='acf of dataset 1')
p.plot(acf1[0:100000], label='acf of dataset 2')
p.plot(acf2[0:100000], label='acf of dataset 3')
p.plot(acf3[0:100000], label='acf of dataset 4')
p.plot(acf4[0:100000], label='acf of dataset 5')

# plot autocorrelation via fft  of s0, s1, s2, s3, s4 over k, ZOOM to relevant interval
p.new(xlabel='k',ylabel='normalized autocorrelation via fft')
p.plot(acf0[0:10000], label='acf of dataset 1')
p.plot(acf1[0:10000], label='acf of dataset 2')
p.plot(acf2[0:10000], label='acf of dataset 3')
p.plot(acf3[0:10000], label='acf of dataset 4')
p.plot(acf4[0:10000], label='acf of dataset 5')

# plot integrated autocorrelation via fft  of s0, s1, s2, s3, s4 over k
p.new(xlabel='k',ylabel='integrated autocorrelation function via fft')
p.plot(acfi0[0:100000], label='acf of dataset 1')
p.plot(acfi1[0:100000], label='acf of dataset 2')
p.plot(acfi2[0:100000], label='acf of dataset 3')
p.plot(acfi3[0:100000], label='acf of dataset 4')
p.plot(acfi4[0:100000], label='acf of dataset 5')

# plot integrated autocorrelation via fft  of s0, s1, s2, s3, s4 over k, ZOOM to relevant interval
p.new(xlabel='k',ylabel='integrated autocorrelation function via fft')
p.plot(acfi0[0:10000], label='acf of dataset 1')
p.plot(acfi1[0:10000], label='acf of dataset 2')
p.plot(acfi2[0:10000], label='acf of dataset 3')
p.plot(acfi3[0:10000], label='acf of dataset 4')
p.plot(acfi4[0:10000], label='acf of dataset 5')

# plot blocking tau over block size k
p.new(xlabel='block size k',ylabel='blocking tau')
p.plot(bts0[0:2000], label='bt of dataset 1')
p.plot(bts1[0:2000], label='bt of dataset 2')
p.plot(bts2[0:2000], label='bt of dataset 3')
p.plot(bts3[0:2000], label='bt of dataset 4')
p.plot(bts4[0:2000], label='bt of dataset 5')

# plot blocking eem over block size k
p.new(xlabel='block size k',ylabel='est. err. of mean value')
p.plot(ems0[0:2000], label='eem of dataset 1')
p.plot(ems1[0:2000], label='eem of dataset 2')
p.plot(ems2[0:2000], label='eem of dataset 3')
p.plot(ems3[0:2000], label='eem of dataset 4')
p.plot(ems4[0:2000], label='eem of dataset 5')

# plot jke over block size k
p.new(xlabel='block size k',ylabel='jackknife error')
p.plot(jks0[0:2000], label='jke of dataset 1')
p.plot(jks1[0:2000], label='jke of dataset 2')
p.plot(jks2[0:2000], label='jke of dataset 3')
p.plot(jks3[0:2000], label='jke of dataset 4')
p.plot(jks4[0:2000], label='jke of dataset 5')


p.make()

print "Finished..."
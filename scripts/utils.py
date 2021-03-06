import collections
import os
import glob
import pandas as pd
import numpy as np
import scipy
from numpy.lib import stride_tricks

from scipy.io import wavfile as wav
from scipy.fftpack import fft, ifft
from scipy.io.wavfile import write
from scipy import signal
from scipy import stats, signal
from scipy.signal                 import lfilter, hamming
from scipy.fftpack.realtransforms import dct
from scipy.signal import butter, lfilter, freqz


from matplotlib.pyplot import figure
from matplotlib import pyplot as plt
import pylab

import librosa

from sklearn.preprocessing import StandardScaler
from sklearn import svm
from sklearn.cross_validation import StratifiedKFold, ShuffleSplit, cross_val_score
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import librosa.display

import warnings
warnings.filterwarnings('ignore')

import math

class ZoomPan:
    def __init__(self):
        self.press = None
        self.cur_xlim = None
        self.cur_ylim = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.xpress = None
        self.ypress = None


    def zoom_factory(self, ax, base_scale = 2.):
        def zoom(event):
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            xdata = event.xdata # get event x location
            ydata = event.ydata # get event y location

            if event.button == 'down':
                # deal with zoom in
                scale_factor = 1 / base_scale
            elif event.button == 'up':
                # deal with zoom out
                scale_factor = base_scale
            else:
                # deal with something that should never happen
                scale_factor = 1
                print(event.button)

            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

            relx = (cur_xlim[1] - xdata)/(cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - ydata)/(cur_ylim[1] - cur_ylim[0])

            ax.set_xlim([xdata - new_width * (1-relx), xdata + new_width * (relx)])
            ax.set_ylim([ydata - new_height * (1-rely), ydata + new_height * (rely)])
            ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest
        fig.canvas.mpl_connect('scroll_event', zoom)

        return zoom

    def pan_factory(self, ax):
        def onPress(event):
            if event.inaxes != ax: return
            self.cur_xlim = ax.get_xlim()
            self.cur_ylim = ax.get_ylim()
            self.press = self.x0, self.y0, event.xdata, event.ydata
            self.x0, self.y0, self.xpress, self.ypress = self.press

        def onRelease(event):
            self.press = None
            ax.figure.canvas.draw()

        def onMotion(event):
            if self.press is None: return
            if event.inaxes != ax: return
            dx = event.xdata - self.xpress
            dy = event.ydata - self.ypress
            self.cur_xlim -= dx
            self.cur_ylim -= dy
            ax.set_xlim(self.cur_xlim)
            ax.set_ylim(self.cur_ylim)

            ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest

        # attach the call back
        fig.canvas.mpl_connect('button_press_event',onPress)
        fig.canvas.mpl_connect('button_release_event',onRelease)
        fig.canvas.mpl_connect('motion_notify_event',onMotion)

        #return the function
        return onMotion


#def freqMod(freq):


def covariance(seq1, seq2, plot_true):
    seq1 = np.array(seq1)
    seq2 = np.array(seq2)

    cov = np.cov(seq1, seq1)
    if plot_true == True:
        plt.plot(cov)
    return cov  


def correlation(array1, array2, input_size, plot_true):
    if input_size == 1:
        cor = np.correlate(array1, array2, "full")
        if plot_true == True: 
            plt.plot(cor)

    if input_size == 2: 

        cor = signal.correlate2d(array1, array2, boundary='symm', mode='same')      
        if plot_true == True:
            plt.plot(corr)

    return cor          


def mfcc(y,sr, n_mfcc,plotFlag,save_flag,filename):
    
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    write('../test_audio/fut.wav', sr, y)       #write file under test

    librosa.display.specshow(mfccs, x_axis='time')
    plt.colorbar()
    plt.title(filename + ':MFCC: First ' + str(len(y)) + ' iterations' + ' with no. of coeffs = ' + str(n_mfcc))
    plt.tight_layout()
        
    if save_flag:
        pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'MFCC.png')    
    if plotFlag:
        plt.show()

def melSpectrogram(y, sr, n_mels, max_freq, plotFlag,flag_hp, save_flag, filename):
    if flag_hp:
        y_harm, y_perc = librosa.effects.hpss(y)
        figure()
        S = librosa.feature.melspectrogram(y=y_harm, sr=sr, n_mels=n_mels, fmax=max_freq)
        librosa.display.specshow(librosa.amplitude_to_db(S, ref=np.max),y_axis='mel', fmax=max_freq,x_axis='time')
        plt.colorbar(format='%+2.0f dB')
        plt.title('../results/' + filename + '_' + str(len(y)) + 'i_' + 'melspectrogram.png')
        plt.tight_layout()

        if save_flag:
            pylab.figure(figsize=(70, 70))
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'melspectrogram.png')

        figure()
        S = librosa.feature.melspectrogram(y=y_perc, sr=sr, n_mels=n_mels, fmax=max_freq)
        librosa.display.specshow(librosa.amplitude_to_db(S,ref=np.max),y_axis='mel', fmax=max_freq,x_axis='time')
        plt.colorbar(format='%+2.0f dB')
        plt.title('../results/' + filename + '_' + str(len(y)) + 'i_' + 'melspectrogram.png')
        plt.tight_layout()

        if save_flag:
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'melspectrogram.png')

        if plotFlag:
            plt.show()                

    else:     
        figure()
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, fmax=max_freq)
        librosa.display.specshow(librosa.amplitude_to_db(S, ref=np.max),y_axis='mel', fmax=max_freq,x_axis='time')
        plt.colorbar(format='%+2.0f dB')
        plt.title('../results/' + filename + '_' + str(len(y)) + 'i_' + 'melspectrogram.png')
        plt.tight_layout()

        if save_flag:
            #pylab.figure(figsize=(70, 70))
            #pylab.savefig('test.eps', format='eps', dpi=900) # This does, too
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'melspectrogram.png')

        if plotFlag:
            plt.show()    

def spectrogram(y, hop_length, sr, plotFlag,flag_hp,save_flag, filename):


    write('../test_audio/fut.wav', sr, y)      #write file under test
    if flag_hp:
        y_harm, y_perc = librosa.effects.hpss(y)
        write('../test_audio/fut__hamonic_comp.wav', sr, y_harm)
        write('../test_audio/fut_percussive_comp.wav', sr, y_perc)

        D_harm = librosa.stft(y_harm, hop_length=hop_length)
        D_perc = librosa.stft(y_perc, hop_length=hop_length)

    
        plt.subplot(211)    
        librosa.display.specshow(librosa.amplitude_to_db(D_harm,
                                                       ref=np.max),
                               y_axis='log', x_axis='time')
        plt.title('Harmonic')    
        #plt.title('Turkish March:Power spectrogram of harmonic component: First ' + str(len(y)) + ' iterations' + ' with hopsize = ' + str(hop_length))
        plt.colorbar(format='%+2.0f dB')
        plt.tight_layout()            

        plt.subplot(212)
        librosa.display.specshow(librosa.amplitude_to_db(D_perc,
                                                       ref=np.max),
                               y_axis='log', x_axis='time')
        plt.title('Percussion')
        #plt.title('Turkish March:Power spectrogram of percussive component: First ' + str(len(y)) + ' iterations' + ' with hopsize = ' + str(hop_length))
        plt.colorbar(format='%+2.0f dB')
        plt.tight_layout()
        if save_flag:
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'harm_perc_spectogram.png')
        if plotFlag:
            plt.show()

    else:        
        D = librosa.stft(y, hop_length=hop_length)
        #D_left = librosa.stft(y, center=False)

        #D_short = librosa.stft(y, hop_length=64)

        librosa.display.specshow(librosa.amplitude_to_db(D,ref=np.max),y_axis='log', x_axis='time')
        plt.title(filename + ':Power spectrogram: First ' + str(len(y)) + ' iterations' + ' with hopsize = ' + str(hop_length))
        plt.colorbar(format='%+2.0f dB')
        if save_flag:
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'spectogram.png')
        plt.tight_layout()
        if plotFlag:             
            plt.show()

def getPitch(y,sr):
    sp = np.fft.fft(y)
    
    freq = np.fft.fftfreq(y.shape[-1])
    half = int(y.shape[-1]/2)
    freq = freq[0:half] 
    freqHz = freq * sr    
    pitch = 69 + 12*np.log2(freqHz/440.0) 
    print("Using the MIDI standard to map frequency to pitch")
    # plt.plot(freqHz, pitch)
    # plt.show()
    return pitch

def getFreq(y,sr):
    sp = np.fft.fft(y)
    freq = np.fft.fftfreq(y.shape[-1])
    half = int(y.shape[-1]/2)
    freq = freq[0:half] 
    freqHz = freq * sr    
    return freqHz, np.max(freqHz), np.min(freqHz)


def rmsEnergy(y):
    y = np.square(y)
    E = np.sum(y)
    rms_E = np.sqrt(E)
    rms_E = float(rms_E)/float(len(y))
    return rms_E 

def spectral_centroid(y,sr):
    sp = np.fft.fft(y)
    
    freq = np.fft.fftfreq(y.shape[-1])
    mag = np.abs(sp)
    half = int(y.shape[-1]/2)
    mag = mag[0:half]
    freq = freq[0:half]     
    
    freqHz = freq * sr

    centroid = float(np.sum(np.multiply(mag,freqHz)))/float(np.sum(mag))
    return centroid


def zero_crossing(y,sr):
    l = []
    for i in range(len(y)-1):
        if y[i]*y[i+1] < 0:
            l.append(i)
    zero_crossing_rate = float(len(l))/float(len(y))
    return zero_crossing_rate, l         

def plotTimeSeries(y,sr, downsampleF, flag_hp, plotFlag, save_flag, filename):
    # y_8k = librosa.resample(y, sr, sr/downsampleF)
    if flag_hp:
        y_harm, y_perc = librosa.effects.hpss(y)
        write('../test_audio/fut__hamonic_comp.wav', sr, y_harm)
        write('../test_audio/fut_percussive_comp.wav', sr, y_perc)
        librosa.display.waveplot(y_harm, sr=sr, alpha=0.25)
        librosa.display.waveplot(y_perc, sr=sr, color='r', alpha=0.5)
        plt.title('Harmonic + Percussive')
        plt.tight_layout()
        if save_flag:
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'HPtimeseries.png')
        if plotFlag:
            plt.show()

    else:    
        fig = figure()
        ax = fig.add_subplot(111, autoscale_on=True)
        write('../test_audio/fut.wav', sr, y)
        ax.set_title('Time Series plot of music data')
        ax.set_xlabel('Amplitude')
        ax.set_ylabel('time')
        ax.plot(y)
        scale = 1.1
        zp = ZoomPan()
        figZoom = zp.zoom_factory(ax, base_scale = scale)
        figPan = zp.pan_factory(ax)
        ax.legend()
        if save_flag:
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'timeseries.png')
        if plotFlag:
            plt.show()



def plotSpectrum(y,sr,flag_hp, plotFlag, save_flag, filename):

    if flag_hp:
        y_harm, y_perc = librosa.effects.hpss(y)
        write('../test_audio/fut__hamonic_comp.wav', sr, y_harm)
        write('../test_audio/fut_percussive_comp.wav', sr, y_perc)

        sp = np.fft.fft(y_harm)
        
        freq = np.fft.fftfreq(y_harm.shape[-1])
        mag = np.abs(sp)
        half = int(y.shape[-1]/2)
        mag = mag[0:half]
        freq = freq[0:half] 
        freqHz = freq * sr

        fig = figure()
        ax = fig.add_subplot(111, autoscale_on=True)

        ax.set_title('Harmony Spectrum of ' + filename )
        ax.set_xlabel('Maginitude')
        ax.set_ylabel('Frequency [in hertz]')
        ax.plot(freqHz, mag)
        scale = 1.1
        zp = ZoomPan()
        figZoom = zp.zoom_factory(ax, base_scale = scale)
        figPan = zp.pan_factory(ax)
        ax.legend()
        if save_flag:
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'Hspectrum.png')

        sp = np.fft.fft(y_perc)
        
        freq = np.fft.fftfreq(y_perc.shape[-1])
        mag = np.abs(sp)
        half = int(y.shape[-1]/2)
        mag = mag[0:half ]
        freq = freq[0:half] 
        freqHz = freq * sr

        fig = figure()
        ax = fig.add_subplot(111, autoscale_on=True)

        ax.set_title('Percussion Spectrum of ' + filename)
        ax.set_xlabel('Maginitude')
        ax.set_ylabel('Frequency [in hertz]')
        ax.plot(freqHz, mag)
        scale = 1.1
        zp = ZoomPan()
        figZoom = zp.zoom_factory(ax, base_scale = scale)
        figPan = zp.pan_factory(ax)
        ax.legend()
        if save_flag:
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'Pspectrum.png')
        if plotFlag:
            plt.show()        

    else: 
        sp = np.fft.fft(y)

        freq = np.fft.fftfreq(y.shape[-1])
        mag = np.abs(sp)
        half = int(y.shape[-1]/2)
        mag = mag[0:half ]
        freq = freq[0:half] 
        freqHz = freq * sr

        fig = figure()
        ax = fig.add_subplot(111, autoscale_on=True)

        ax.set_title('Spectrum of ' + filename)
        ax.set_ylabel('Magnitude')
        ax.set_xlabel('Frequency [in hertz]')
        ax.plot(freqHz, mag)
        scale = 1.1
        zp = ZoomPan()
        figZoom = zp.zoom_factory(ax, base_scale = scale)
        figPan = zp.pan_factory(ax)
        ax.legend()
        if save_flag:
            pylab.savefig('../results/' + filename + '_' + str(len(y)) + 'i_' + 'spectrum.png')
        if plotFlag:
            plt.show()



def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)

    return y

'''
Useful comments: 

-The Nyquist frequency is half the sampling rate.

-You are working with regularly sampled data, so you want a digital filter, not an analog filter. 
This means you should not use analog=True in the call to butter, and you should use scipy.signal.freqz (not freqs) to generate the frequency response.

-One goal of those short utility functions is to allow you to leave all your frequencies expressed in Hz.
As long as you express your frequencies with consistent units, the scaling in the utility functions takes care of the normalization for you.

'''



def lpf(y, sr, order, fs, cutoff, freq_resp_plot, plotFlag):

    if freq_resp_plot:    
        # Get the filter coefficients so we can check its frequency response.
        b, a = butter_lowpass(cutoff, fs, order)
        # Plot the frequency response.
        w, h = freqz(b, a, worN=8000)
        # plt.subplot(2, 1, 1)
        plt.plot(0.5*fs*w/np.pi, np.abs(h), 'b')
        plt.plot(cutoff, 0.5*np.sqrt(2), 'ko')
        plt.axvline(cutoff, color='k')
        plt.xlim(0, 0.5*fs)
        plt.title("Lowpass Filter Frequency Response")
        plt.xlabel('Frequency [Hz]')
        plt.grid()
        pylab.savefig('freq_response.png')



    y_filtered = butter_lowpass_filter(y, cutoff, fs, order)
    figure()
    # plt.subplot(2, 1, 2)
    plt.plot(y, 'b-', label='data')
    figure()
    plt.plot(y_filtered, 'g-', linewidth=2, label='filtered data')
    plt.xlabel('Time [sec]')
    plt.grid()
    plt.legend()
    pylab.savefig('fitered.png')
    if plotFlag:
        plt.show()

    return y_filtered    



def cepstral_analysis(y, sr, plotFlag):

    logfft = np.log(fft(y))
    freq = np.fft.fftfreq(y.shape[-1])

    ceps = ifft(logfft)
    if plotFlag:
        figure()
        plt.plot(freq*sr, np.abs(logfft))
        pylab.savefig('logfft.png')
        figure()
        plt.plot(ceps)
        pylab.savefig('ceps.png')
    
    return ceps
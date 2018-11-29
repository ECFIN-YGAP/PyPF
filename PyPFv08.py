# -*- coding: utf-8 -*-
"""
                                        #---------------#
                                        #     PyPF      #
                                        #---------------#


Created on Fri Oct 26 18:34:27 2018
@author: François Blondeau (European Commisssion, Directorate-General for Economic and Financial Affairs)

Reference :
    - Similar code in RATS and MATLAB (Valerie Vandermeulen)
    - OGWG commonly agreed production function (PF) methodology :
        "The Production Function Methodology
for Calculating Potential Growth Rates & Output Gaps", Havik et al. (2014)
European Commission Economic Paper 535 | November 2014

This program is a PILOT project.
It is a trial of the Python programming language possibilities in the framework of a move towards open source.
It could be used instead of the presently used RATS program to compute indicators needed for assessing both the productive capacity
(i.e. potential output) and cyclical position (i.e. output gaps) of EU economies.

Python is open source and royalty-free.
-> https://www.python.org/
-> https://wiki.python.org/moin/BeginnersGuide


"""
#-------------------
# TODO : handel exceptions in data types
#
#-------------------
# TODO : IMPORTANT
# ------------------
# In this program only the AR part of ARIMA as been implemented to use Least Squares estimations.
# The Moving Average part is estimated using Maximum Likelyhood, the method available in the existing Python ARIMA libraries
# The original RATS program uses Box-Jenkins LS method for ARIMA
# Results estimated via OLS are indentical to the original RATS results
#------------------
# TODO : ESTIMATION OF TREND GDP (GDP HP)
#------------------
#
#timer to evaluate speed of processing
import datetime
import sys
import numpy as np
current1 = np.datetime64(datetime.datetime.now())
import pandas as pd
from pandas import ExcelWriter
import statsmodels.api as sm
#from statsmodels.tsa.api import ExponentialSmoothing
from statsmodels.tsa.arima_model import ARIMA
#import matplotlib.pylab as plt
from scipy.optimize import fsolve

# Function created to estimate AR using OLS instead of the default Python ML

def ols_ar(series, nblag, const, ar_start, changey, nb_fcst, time=False):   
    endog = series.loc[ar_start:changey]
    if nblag > 0:
        serieslagged = series.shift(1) 
        exog = pd.DataFrame(serieslagged.loc[ar_start:changey], columns=['lag1']) 
        for lag in range (2, nblag+1): 
            serieslagged=series.shift(lag) 
            exog['lag'+str(lag)] = serieslagged.loc[ar_start:changey] 
        if const: 
            exog = sm.add_constant(exog) 
        if time:
            exog['time'] = pd.Series(series.index[ar_start-1960:changey-1959], index=exog.index)
    else:
 #       n = len(series.loc[ar_start:changey])
        exog=pd.DataFrame(index=range(ar_start,changey+1))
        exog['const'] = np.ones(changey+1-ar_start)
    model = sm.OLS(endog, exog, missing='drop') 
    res = model.fit() 
    print(res.summary()) 
    for i in range(1, nb_fcst + 1): 
        if const: 
            newexog = pd.DataFrame([1.], columns=['const'])
            for lag in range (1, nblag+1): 
                newexog['lag'+str(lag)] = series[changey-lag+i] 
        else:
            newexog = pd.DataFrame([series[changey-1+i]], columns=['lag1']) 
            for lag in range (2, nblag+1): 
                newexog['lag'+str(lag)] = series[changey-lag+i] 
        if time:
            newexog['time'] = pd.Series(series.index[changey-1960+i], index=newexog.index)
            print(newexog)
        series[changey+i] = res.predict(newexog) 
    return series.loc[:changey+nb_fcst]

# The next function implements a mechanical closure.
    # Meaning that after n years the gap should be zero

def closure(series,clos_nb_y,changey):
    for i in range (1, clos_nb_y+1):
        series[changey+i] = (clos_nb_y - i)  / clos_nb_y * series[changey]
    series.loc[changey+clos_nb_y+1:series.size+1959] = 0.
    return series

# This function is the model of equations to solve
    
def modeltosolve(guesses, params):
    ypot, k, iq, y, sr = guesses #unpacking tuple with initial guesses
    totalhs, srkf, dep, klag, iypot, ygap, totalh_mt = params  # unpacking tuple with parameters
    alpha2 = .65
    eq1 = totalhs**alpha2 * k**(1-alpha2) * np.exp(srkf) - ypot #1st equation of the model
    eq2 = iq + (1-dep) * klag - k # 2d equation
    eq3 = iypot / 100 * ypot - iq # 3d equation
    eq4 = ypot * (1 + ygap / 100) - y # 4th equation
    eq5 = np.log( y / (totalh_mt**alpha2 * k**(1 - alpha2))) - sr # 5th and last equation
    return [eq1, eq2, eq3, eq4, eq5]

# PARAMETERS READING (CSV is used, XLSX could be as well)
# the files parameters are designed to be edited by a user interface    
try:
    #params = pd.read_excel('PyPF.parameters.xlsx', sheet_name='cross country params', header=0, index_col=1)
    PrgParams = pd.read_csv('PyPF.general.parameters.csv', header=0, index_col=1)
    #CountryParams = pd.read_excel('PyPF.parameters.xlsx', sheet_name='country specific params', header=0, index_col=2)
    CountryParams = pd.read_csv('PyPF.country.parameters.csv', header=0, index_col=2)
except:
    print('\n----------------------------------------------------\nThe parameter file is missing, the program will stop...\n----------------------------------------------------\n')
    sys.exit(78)

changey = int(PrgParams.loc['changey', 'value'])  # last year of the short term forecast
yf = int(PrgParams.loc['yf','value'])
OutStartYear = int(PrgParams.loc['OutputStartingYear', 'value'])
clos_nb_y = int(PrgParams.loc['clos_nb_y','value'])


endy = changey + yf
beginfy = changey + 1
dendy = changey + yf - 3
endt5 = changey + 3 + 3
t6 = changey + 4
endmt = changey + 3

seriesofOnes = pd.Series(1., index=range(1960, endy+1))

# Pandas is used to read excel file using dataframe with years -
# - as index + column names for easiness of usage

ameco = pd.read_excel(PrgParams.loc['amecoFile','value'], header=0, index_col=0)
ameco = ameco.T
tfpKF = pd.read_excel(PrgParams.loc['tfpKFFile','value'], header=0, index_col=0)
nawrudf = pd.read_excel(PrgParams.loc['nawruFile','value'], header=0, index_col=0)

europop = pd.read_excel(PrgParams.loc['popFile','value'], sheet_name="to rats", header=0, index_col=0)
europop = europop.T

#NOTE : the europop file as years as string (excel formula) -> convert index to integer on the fly
europop.index = europop.index.astype('int64')

outputfile = ExcelWriter(PrgParams.loc['outFile','value'])
seriesofOnes.loc[OutStartYear:changey+yf].to_excel(outputfile, sheet_name='PyPF Output',startcol=0, index=True, index_label='YEAR')
excelcolumn = 1

#DEBUG 
#countrylist = ['at', 'be','de','dk','el','es','fr','ie','it','lu','nl','pt','fi','se','uk','cz','ee','hu','lv','lt','pl','sk','si','cy','mt','bg','ro','hr']
#countrylist = ['de','it','cy','mt']
#countrylist = ['at']

#for country in countrylist:
#DEBUG END

for country in CountryParams.columns[2:]:
    print('\n\n - -  - - - -  - - - - - -   - - -  - -- -')
    print(country,' - ',country,' - ',country,' - ',country,' - ',country,' - ',country)
    print(' - -  - - - -  - - - - - -   - - -  - -- -')
  
# the needed data is then put in arrays (Pandas series) or computed if needed
#
# CALCULATE ACTUAL VARIABLES

#    GDP (y)
# -----------

    y = ameco[country+'_gdpq'] * seriesofOnes

#wy = growthrates(y)
    wy = y.pct_change() * 100


# LABOUR (totalh)
# -----------

# unemployment

    lurharm = ameco[country+'_lur']
    dlur = lurharm.diff()
    nawru = nawrudf[country+'_nawru']


# wages
    w = ameco[country + '_hwcdw']
    gw = w.pct_change() * 100
    winf = gw.diff()

#employment
    l = ameco[country+'_sled'] * seriesofOnes
    
    lf = l / (1 - lurharm / 100)
    
    if country == 'lu':
        l_lux = ameco[country+'_sle1'] * seriesofOnes  	         # employment series. NB: National accounts national concept for all countries
        l_cb = l - l_lux
        ratio_cb = l_cb / l                                   # ratio of cross-border workers
        lf = l_lux/(1-lurharm/100)
        
    lu = lurharm * lf

# for full prog conditions to be added for SLE=1
    sle = ameco[country+'_sle']

#hours worked
    hpere = ameco[country+'_hpere'] * seriesofOnes
    
    totalh = hpere * l
    totalh.name = country+'_totalh'
    
    wtotalh = totalh.pct_change()

#population of working age
    popw = ameco[country+'_popa1']
    popt = ameco[country+'_popt']

#participation rate
    part = 100 * lf / popw

# CAPITAL (k)
# -----------
# some country specificities here
    k = ameco[country+'_kt'] * seriesofOnes
    
    iq = ameco[country+'_iq'] * seriesofOnes
    
    iy = iq / y
    
    inv = ameco[country+'_in'] * seriesofOnes

#*I* for Ireland there has been a re-valuation of the capital stock to include aircraft leasing.
#*I* this is not yet visible in the ameco capital stock series, and therefore we make an adjustment here.
#*I* on 29/9/2016 it is believed that capital stock goes up by 53.7% in 2015 and remains at this higher level from then on.
#*I* as on Autumn 2018 another modification to this procedure was made, based on country specificity for Ireland

    if country == 'ie':

        # calculate some additional variables
        k_ori = k.copy()
        k_difference = k.diff()    		# = iq - cfc
        dep_ori  = (iq-(k-k.shift(1)))/k.shift(1)
        dep_difference = dep_ori - dep_ori.shift(1)
        outturny = abs(dep_difference.where(abs(dep_difference) < 0.00000001))
        outturnyear = outturny.idxmin()

#*** remark: outturn year is most of the time equal to t-1

#* actual adjustment:
#* cso estimate of the increase in the K stock for 2015
        k[2015] = 1.532*k[2014]
#♦* after 2015, until the outturn year, the iq and cfc series are correct, they relate to the new capital stock
        for i in range(2016,outturnyear+1):
            k[i] = k[i-1] + k_difference[i]
#* when there is no info on cfc, a constant dep rate is assumed for these years
        dep = (iq-(k-k.shift(1)))/k.shift(1)
        for i in range(outturnyear,changey+1):
            dep[i]     = dep[i-1]
        for i in range(outturnyear,changey+1):
            k[i] = iq[i] + (1-dep[i])*k[i-1]


    if country == 'lv':
#
#	*I* depreciation rate is calculated based on investment and capital information
#	*I* and then kept constant from the forecast starting
#
        ee_iq = ameco['ee_iq'] * seriesofOnes
        ee_kt = ameco['ee_kt'] * seriesofOnes
        dep_ee = (ee_iq-(ee_kt-ee_kt.shift(1)))/ee_kt.shift(1)
        dep_ee[changey:endy]     = dep_ee[changey-1]
        
        lt_iq = ameco['lt_iq'] * seriesofOnes
        lt_kt = ameco['lt_kt'] * seriesofOnes
        dep_lt = (lt_iq-(lt_kt-lt_kt.shift(1)))/lt_kt.shift(1)       
        dep_lt[changey:endy] = dep_lt[changey-1]

        dep = (dep_ee + dep_lt)/2  # average dep of LT and EE

        k_ori = k.copy()
        for i in range(1996, endy+1):
            k[i] = k[i-1] * (1-dep[i]) + iq[i]

# PRODUCTIVITY (solow residual)
# -----------

    alpha = .65
    sr = np.log ( y / (totalh ** alpha * k ** ( 1 - alpha)))

# FORECAST EXOGENEOUS
# Trend TFP (srkf)
# -----------
    wsr = sr.diff()

    print('\nExtending WSR :\n---------------')    

# for the moment (AF2018) ARIMA estimation is used for 6 countries
#TODO : ARIMA is estimated with Python MLE instead of RATS LS Gauss-Newton
    if int(CountryParams.loc['tfp_ma_order', country]) > 0:        
        p = int(CountryParams.loc['tfp_nblag', country])
        d = 0
        q = int(CountryParams.loc['tfp_ma_order', country])
        if bool(int(CountryParams.loc['tfp_const', country])):
            const = 'c'
        else:
            const = 'nc'
        
        ar_start = int(CountryParams.loc['tfp_ar_start', country]) 
# ARIMA requests that index is "datetime tagded"
        wsr.index = pd.to_datetime(wsr.index, format='%Y', exact=True)
        model = ARIMA(wsr.loc[str(ar_start):str(changey)], order=(p,d,q), freq='AS-JAN')
        model_fit = model.fit(trend=const)
        print(model_fit.summary())
        forecast = model_fit.predict(start=str(changey+1), end=str(endy))
        wsr.loc[str(changey+1):str(endy)] = forecast.loc[str(changey+1):str(endy)]
        wsr=wsr.values * seriesofOnes
    else:   
        nblag = int(CountryParams.loc['tfp_nblag', country])
        const = bool(int(CountryParams.loc['tfp_const', country]))
        ar_start = int(CountryParams.loc['tfp_ar_start', country])   
        wsr = ols_ar(wsr, nblag, const, ar_start, changey, yf)

    for i in range(sr.first_valid_index(), changey+yf):
        sr[i+1] = sr[i] + wsr[i+1]

        
# filter the forecasted series

# extended series on actual TFP (old method) 
# = tfp_forecast(sr,index of last year of forecast,number of forecast years)
#use of the ARMA function defined (series, nblag, const, ar_start, changey, nb_fcst)
#
# NOTE THAT IN FULL PROG, WSR is extended and then SR is rebuild from it
# for this exercise we use the KF SR directly

    starthp = int(CountryParams.loc['starthp', country])

# filter the forecasted series
    
    cycle, srhp = sm.tsa.filters.hpfilter(sr.loc[starthp:endy], int(CountryParams.loc['tfp_lambda', country]))
    srhp = srhp * seriesofOnes
    wsrhp =srhp.diff()
    srkf = tfpKF[country.upper()+'_SRKF'] * seriesofOnes
    

# connect the hp and k filtered series to make it start in 1960
# because SRKF starts in 1980
       
    for i in range(1,21):
        srkf[1980-i] = srkf[1980-i+1]-wsrhp[1980-i+1]
        
    wsrkf = srkf.diff()

# Extended population at working age (popw)
# -----------
    popwf = europop[country.upper()+'_POPAF']
    poptf = europop[country.upper()+'_POPTF']

    mpopf = (popwf.shift(-1) + popwf) / (popwf + popwf.shift(1))
    mpoptf = (poptf.shift(-1) + poptf) / (poptf + poptf.shift(1))


    for i in range(1,7):
        popw[changey+i] = popw[changey+i-1] * mpopf[changey+i]
        popt[changey+i] = popt[changey+i-1] * mpoptf[changey+i]

    wpopw = popw.pct_change()
    wpopt = popt.pct_change()

# Trend Participation Rate (parts)
# -----------

# extended series on part 




    if country == 'de':
#	*I* participation rates of migrants and non-migrants
        MigrationDE = pd.read_excel(PrgParams.loc['MigrationFile','value'], header=0, index_col=0)
        partM = MigrationDE['DE_PARTM'] * 100 * seriesofOnes
        for i in range (changey+4, changey+yf+1):
            partM[i] = partM[i-1] + 0.5*(partM[i-1]-partM[i-2]) + 0.5*(partM[i-2]-partM[i-3])
        
        partsM = partM.copy()				#µ trend migrant participation rate = actual rate

#	*I* population at working age for migrants and non-migrants

        popwM = MigrationDE['DE_POPWM'] /1000 * seriesofOnes			# migrant population at working age
#* I assume that after 2021 no new migrants arrive (!) and that all of them stay in the 'migrant' group for several years
        popwM.loc[changey+4:] = popwM[changey+3]

#	*I* labour force of migrants and non-migrants

        lfM = pd.Series(np.zeros(changey+yf-1959), index=range(1960,changey+yf+1))			# migrant labour force
        lfM.loc[2015:] = popwM.loc[2015:] * partM.loc[2015:] / 100
        LFnonM = lf - lfM				# non-migrant labour force

        partnonM = part.copy()				# non-migrant participation rate
        popwnonM = popw - popwM	  # non-migrant population at working age
        partnonM.loc[2015:changey] = LFnonM.loc[2015:changey] / popwnonM.loc[2015:changey] * 100 #???

# = ar (series, nblag, const, ar_start, changey, nb_fcst)
    nblag=int(CountryParams.loc['part_nblag', country])
    const=bool(int(CountryParams.loc['part_const', country]))
    ar_start = int(CountryParams.loc['part_ar_start', country])
    
# TODO : HP SHOULD DEAL WITH SHORTER SERIES (CY)    
    if country == 'cy':
        starthp = 1997
    elif country == 'hr':
        starthp = 2001
        
    print('\nExtending PART :\n----------------')
    time = bool(int(CountryParams.loc['part_timexog', country]))
    part = ols_ar(part, nblag, const, ar_start, changey, yf, time)
# filter the forecasted series
    if country == 'de':
        	#*I* calculate the non migrant participation rate as a part of total actual participation rate
        partnonM.loc[2015:] = part.loc[2015:]*popw.loc[2015:]/(popw.loc[2015:]-popwM.loc[2015:]) - partM.loc[2015:]*popwM.loc[2015:]/(popw.loc[2015:]-popwM.loc[2015:])
        cycle, partsnonM = sm.tsa.filters.hpfilter(partnonM.loc[starthp:changey+yf], int(CountryParams.loc['part_lambda',country]))
        partsnonM = partsnonM  * seriesofOnes
        parts = partsnonM.copy()
        parts.loc[2015:] = partsnonM.loc[2015:]*(popwnonM.loc[2015:]/popw.loc[2015:]) + partsM.loc[2015:]*(popwM.loc[2015:]/popw.loc[2015:])
    else:
        #ISSUE WITH CY HP FILTER START IN 1997 and do not provide values for 1995 ->

        cycle, parts = sm.tsa.filters.hpfilter(part.loc[starthp:changey+yf], int(CountryParams.loc['part_lambda',country]))
        parts = parts * seriesofOnes


# Extended NAWRU (nawru)
# -----------

# NAWRU: **** NEW end rule Spring 2014:
#----------
	#*I* in the t+5 framework (yf<4) we use an extension rule; "end rule"
	#*I* in t+10 the nawru series is complete and long in the dataset

#===========
#* Autumn Final 2018
#* since the wage indicator gives the wrong signal for IE nawru, replace the nawru by a simple HP (lurharm)
#*===========

    if country == 'ie':
        
        lurori = lurharm.copy()
        lurharm = lurharm * seriesofOnes
        nblag=2
        const=True
        ar_start = 1965
        lurharm = ols_ar(lurharm, nblag, const, ar_start, changey, yf)
        cycle, lurharms = sm.tsa.filters.hpfilter(lurharm.loc[starthp:changey+yf], 10)

        lurharms[beginfy] = lurharms[beginfy-1]+.5*(lurharms[beginfy-1]-lurharms[beginfy-2])
        lurharms.loc[beginfy+1:] = lurharms[beginfy]

        nawru = lurharms
    else:
        nawru[beginfy] = nawru[beginfy-1] + 0.5 * (nawru[beginfy-1] - nawru[beginfy-2])

        for i in range(1,yf):
            nawru[beginfy+i] = nawru[beginfy]
            
    dnawru = nawru.diff()

# Trend Hours worked per Employee (hperehp)
# -----------
# extended series on hours worked 
# = ar(series, nblag, const, ar_start, changey, nb_fcst)
    nblag=int(CountryParams.loc['hpere_nblag', country])
    const=bool(int(CountryParams.loc['hpere_const', country]))
    ar_start = int(CountryParams.loc['hpere_ar_start', country])

    print('\nExtending HPERE :\n-----------------')
    hpere = ols_ar(hpere, nblag, const, ar_start, changey, yf)

# TODO : HP SHOULD DEAL WITH SHORTER SERIES (CY, HR)    
    if country == 'cy':
        starthp = 1995
    elif country =='hr':
        starthp = 1995

# filter the forecasted series
    cycle, hperehp = sm.tsa.filters.hpfilter(hpere.loc[starthp:endy], int(CountryParams.loc['hpere_lambda',country]))
    hperehp = hperehp * seriesofOnes

    dhpere = hpere.diff()
    whperehp = hperehp.pct_change()

# CROSS-BORDER WORKERS
#------------
# in the case of LU we need to add cross-border workers

    if country == 'lu':
#find the best ARIMA proces to explain the cross border worker ratio in the past
# use this best proces to forecast the series
# filter this long series to get the trend
        nblag=2
        const=False
        ar_start = 1978
        ratio_cb = ols_ar(ratio_cb, nblag, const, ar_start, changey, yf)
        cycle, ratio_cb_hp = sm.tsa.filters.hpfilter(ratio_cb.loc[starthp:endy], 10)

# Trend labour (totalhs)
# -----------
    if country == 'lu':
	#extend the seperate series

        l_lux      = part/100*popw*(1-lurharm/100)
        l_cb       = l_lux*ratio_cb/(1-ratio_cb)
        l          = l_lux+l_cb
        totalh     = l*hpere
	#          create related trend series

        l_luxs     = parts/100*popw*(1-nawru/100)
        l_cb_hp    = l_luxs*ratio_cb_hp/(1-ratio_cb_hp)
        lfss       = parts/100 *popw			#trend labour force, only includes luxembourgish!
        lp2        = l_luxs+l_cb_hp     #trend employment
        totalhs    = lp2*hperehp        #trend total hours worked
    else:
        lfss = parts / 100 * popw
        lp2 = lfss * (1 - nawru / 100)
    
    wlp2 = lp2.pct_change()

    totalhs = lp2 * hperehp
    wtotalhs = totalhs.pct_change()

    #create a totalhs specific for the t+10
    



# Investment rule (IYPOT)
# -----------

    srkf_level = np.exp(srkf)
    ypot = totalhs ** alpha * k ** (1-alpha) * srkf_level
# ypot = ypot * seriesofOnes

    iypot = 100 * (iq / ypot)
    iypot = iypot * seriesofOnes


# NOTE : THERE IS A COUNTRY SPECIFICITY FOR DE FRO T+10

    nblag=int(CountryParams.loc['iypot_nblag', country])
    const=bool(int(CountryParams.loc['iypot_const', country]))
    ar_start = int(CountryParams.loc['iypot_ar_start', country])
    
    print('\nExtending IYPOT :\n-----------------')
    iypot = ols_ar(iypot, nblag, const, ar_start, changey, yf)

# Depreciation rate (dep)
# -----------

    dep = (iq-(k-k.shift(1)))/k.shift(1)

    for i in range (1,yf+1):
        dep[changey+i] = dep[changey-1]

# GAP closure rule (ygap)
# -----------
    ygap = 100 * (y / ypot-1)



#TODO
    ygap = closure(ygap, clos_nb_y, changey)


# other GAP closure rules (totalh_mt)
# -----------

# create the medium term actual series
    part_mt = part.copy()
    hpere_mt = hpere.copy()
    l_mt = l.copy()
       
    totalh_mt = totalh.copy()
    lurharm_mt = lurharm * seriesofOnes
# create the gap series
    partgap = part - parts
    hperegap = hpere - hperehp
    lurgap = lurharm - nawru

# close each gap (by the end of the period = 6)

    partgap = closure(partgap, clos_nb_y, changey)
    hperegap = closure(hperegap, clos_nb_y, changey)
    lurgap = closure(lurgap, clos_nb_y, changey)

# fill in the medium term actual series
#TODO define a function to do so ?
    part_mt.loc[beginfy:endy] = parts.loc[beginfy:endy] + partgap.loc[beginfy:endy]
    hpere_mt.loc[beginfy:endy] = hperehp.loc[beginfy:endy] + hperegap.loc[beginfy:endy]
    lurharm_mt.loc[beginfy:endy] = nawru.loc[beginfy:endy] + lurgap.loc[beginfy:endy]
    

    if country == 'lu':
        lcbgap = seriesofOnes * 0.
        for i in range(1, clos_nb_y+1):
            lcbgap[changey+i] = (clos_nb_y - i) / clos_nb_y * (l_cb[changey]-l_cb_hp[changey])
        lcbgap.loc[changey+clos_nb_y+1:lcbgap.size+1959] = 0.

        l_lux_mt = l_lux
        l_lux_mt.loc[beginfy:endy] = popw.loc[beginfy:endy] * part_mt.loc[beginfy:endy] / 100 * (1-lurharm_mt.loc[beginfy:endy]/100)
        l_cb_mt = l_cb
        l_cb_mt.loc[beginfy:endy]     =  l_cb_hp.loc[beginfy:endy] - lcbgap.loc[beginfy:endy]
        l_mt.loc[beginfy:endy]      = l_lux_mt.loc[beginfy:endy] + l_cb_mt.loc[beginfy:endy]
    else:
        l_mt.loc[beginfy:endy] = popw.loc[beginfy:endy] * part_mt.loc[beginfy:endy] / 100 * (1-lurharm_mt.loc[beginfy:endy]/100)
    
    totalh_mt.loc[beginfy:endy] = l_mt.loc[beginfy:endy]*hpere_mt.loc[beginfy:endy]



    ypot0, k0, iq0, y0, sr0 =  ypot[changey], k[changey], iq[changey], y[changey], sr[changey]     # initial guesses
    x0 = [ypot0, k0, iq0, y0, sr0]

#    print('\n\nMODEL SOLVING :\n_______________\n')

    for i in range (1, 7):
        params = [totalhs[changey+i], srkf[changey+i], dep[changey+i], k[changey+i-1], iypot[changey+i], ygap[changey+i], totalh_mt[changey+i]]
        x0 = fsolve(modeltosolve, x0, params)
        ypot[changey+i], k[changey+i], iq[changey+i], y[changey+i], sr[changey+i] = x0
        print("Computed values for year ", changey+i, "(ypot, k, iq, y, sr) :\n", x0)

    wsr = sr.diff()


    output = pd.concat([y,
#                        yhp,
                        ygap,
                        ypot,
                        part_mt,
                        parts,
                        wsr*100,
                        wsrkf*100,
                        nawru,
                        lurharm_mt,
                        hpere_mt,
                        iq,
                        lfss,
                        lp2,
                        totalhs,
                        l_mt,
                        totalh_mt,
                        k,
                        winf,
#                        sle,
                        popw,
                        popt,
                        sr,
                        srhp,
                        srkf,
                        dep], axis=1)
#                        iypot

    output.columns = [country+'_GDP',
#                      country+'_Trend_GDP',
                      country+'_Y_GAP(PF)',
                      country+'_Y_Pot',
                      country+'_part',
                      country+'_Part_S',
                      country+'_wSR',
                      country+'_wSR_KF',
                      country+'_NAWRU',
                      country+'_UnEmpl_Rate',
                      country+'_HperE',
                      country+'_Investment',
                      country+'_Pot_LF',
                      country+'_Pot_Empl',
                      country+'_Pot_Tot_Hrs',
                      country+'_Empl',
                      country+'_Tot_Hrs',
                      country+'_Capital',
                      country+'_Wage_Infl',
#                      country+'_Civ_empl',
                      country+'_Pop_WA',
                      country+'_Tot_Pop',
                      country+'_SR',
                      country+'_SR_HP',
                      country+'_SR_Kf',
                      country+'_Depreciation']
#                      country+'_iypot']
          
    output.loc[OutStartYear:changey+yf].to_excel(outputfile, sheet_name='PyPF Output',startcol=excelcolumn, index=False)
#Results can be writen in a CSV file
#    output.loc[OutStartYear:changey+yf].to_csv(outputfile, startcol=excelcolumn, index=False)

    excelcolumn += 24
#    output.loc[1965:2025].to_csv('PyPF_Output.csv')

outputfile.save()
print("\nTime spend for the computations : ", np.datetime64(datetime.datetime.now())-current1)

#############################
# DEBUG
# THIS code prints the roots of the equations to check the computing precision
#for i in range (2020, 2026):
#    print('\nYear',i,' :\n-------------')
#    print('eq1 : ', totalhs[i]**alpha * k[i]**(1-alpha) * np.exp(srkf[i]) - ypot[i])
#    print('eq2 : ', iq[i] + (1-dep[i]) * k[i-1] - k[i])
#    print('eq3 : ', iypot[i] / 100 * ypot[i] - iq[i])
#    print('eq4 : ', ypot[i] * (1 + ygap[i] / 100) - y[i])
#    print('eq5 : ', np.log( y[i] / (totalh_mt[i]**alpha * k[i]**(1 - alpha))) - sr[i])
    

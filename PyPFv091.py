# -*- coding: utf-8 -*-
"""
                         #---------------------#
                         #     PyPFOG v0.9     #
                         #---------------------#

NOTE : The program itself begins at line 166, after some introduction, libraries import,
                                                                        parameters + data reading and file creations!

@author: François Blondeau (European Commisssion, Directorate-General for Economic and Financial Affairs)

References :
    - Similar code in WinRATS (Cécile Denis, Werner Röger and Valerie Vandermeulen)
        and MATLAB (Valerie Vandermeulen)
    - OGWG commonly agreed production function (PF) methodology :
        "The Production Function Methodology
for Calculating Potential Growth Rates & Output Gaps", Havik et al. (2014)
European Commission Economic Paper 535 | November 2014

This program is a PILOT project.
It is a trial of the Python programming language possibilities in the framework of a move towards open source.
It could be used instead of the presently used WinRATS program to compute indicators needed for assessing both
the productive capacity (i.e. potential output) and cyclical position (i.e. output gaps) of EU economies.

Python is open source and royalty-free.
-> https://www.python.org/
-> https://wiki.python.org/moin/BeginnersGuide

"""
# ---------------------
#    IMPORTANT NOTE
# ---------------------
# The original WinRATS program uses Box-Jenkins Least Squares method for ARIMA
#
# In this program only the AR part of ARIMA as been implemented to use LS estimations.
# Results estimated via ols_ar function are identical to the original WinRATS results
#
# The Moving Average part is estimated using Maximum Likelihood, which is the method available
# in the existing Python ARIMA libraries
# ---------------------------------------------------------
#          IMPORT of needed libraries and functions
# ---------------------------------------------------------
#
# timer to evaluate speed of processing
import datetime
import numpy as np
current1 = np.datetime64(datetime.datetime.now())
import os, sys, inspect
from scipy.optimize import fsolve
import pandas as pd
from pandas import ExcelWriter
gap_path = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
projpath = gap_path + '/'
sys.path.insert(0, projpath + 'lib/')
import jrc_tools
import sr_prep
import nawru_prep
import pf_prep
import modeltosolve


# ----------------------------------------------------
#            PARAMETERS READING and SETTING
# ----------------------------------------------------
# NOTE : this program can be launched via a button within the "start.xlsm" file 
prgversion='PyPFOGv09'

logfile=projpath+"log/"+prgversion+"_MAINlog_"+str(current1).replace(':', '-')+".log"
pypfoglog=open(logfile,'w+')
pypfoglog.close()

olslog=projpath+"log/"+prgversion+"_OLSlog_"+str(current1).replace(':', '-')+".log"
pypfoglog=open(olslog,'w+')
pypfoglog.close()

try:
    prg_params = pd.read_excel(projpath+'start.xlsm', sheet_name='general', header=0, index_col=1)
except:
    with open(logfile, 'a') as f:
        f.write('\n----------------------------------------------------\nThe general parameters could not be read, '
                'the program will stop...\n----------------------------------------------------\n')
    sys.exit(78)

# Set the list of country for which we want Trend TFP estimation
try:
    tfp_params = pd.read_excel(projpath+'start.xlsm', sheet_name='trend_tfp', header=0, index_col=0)
except:
    print('\n----------------------------------------------------\nThe trend TFP parameters could not be read, '
          'the program will stop...\n----------------------------------------------------\n')
    sys.exit(79)

tfp_countrylist=list(tfp_params.loc[tfp_params['DO_TrendTFP_ESTIMATES?']==True].index)

# Read NAWRU adjustment factors from excel file and set the list of country for which we want NAWRU estimation
try:
    nawru_params = pd.read_excel(projpath+'start.xlsm', sheet_name='nawru', header=0, index_col=0)
except:
    print('\n----------------------------------------------------\nThe NAWRU parameter could not be read, '
          'the program will stop...\n----------------------------------------------------\n')
    sys.exit(80)
nawru_countrylist=list(nawru_params.loc[nawru_params['DO_NAWRU_ESTIMATES ?']==True].index)

# Set the list of country for which we want YGAP estimation
try:
    country_params = pd.read_excel(projpath+'start.xlsm', sheet_name='main', header=0, index_col=2)
except:
    with open(logfile, 'a') as f:
        f.write('\n\nThe main parameters could not be read, the program will stop...')
    sys.exit(81)

country_params = country_params.T
pf_countrylist = list(country_params.loc[country_params['compute']=='True'].index)
country_params = country_params.T
countrylist = list(country_params.columns)
countrylist = countrylist[2:]

# the settings are read from parameter file values.
# the description of each parameter is detailed in the Excel file
changey = int(prg_params.loc['changey', 'value'])  # last year of the short term forecast
yf = int(prg_params.loc['yf','value'])
alpha = float(prg_params.loc['alpha', 'value'])
# clos_nb_year (number of year to close the YGAP) is normally 3 years and correspond to the mid term "horizon"
# the variable is used as well to set the end year for output writing (short term + mid term = t+5)
clos_nb_y = int(prg_params.loc['clos_nb_y', 'value'])
OutStartYear = int(prg_params.loc['OutputStartingYear', 'value'])
vintage_name = prg_params.loc['vintage_name','value']
ones = pd.Series(1., index=range(1960, changey + yf + 1))
ygap_passed = 0

# -------------------------------------------------
#               MAIN DATA FILES READING
# -------------------------------------------------

ameco = pd.read_excel(projpath+prg_params.loc['amecoFile','value'], header=0, index_col=0)
ameco = ameco.T
cubs = pd.read_excel(projpath + prg_params.loc['cubsFile', 'value'], index_col=0, header=0)

try:
    srkf_exog = pd.read_excel(projpath+'datafiles/tfp_'+vintage_name+'.xls', header=0, index_col=0)
except:
    pass
try:
    nawru_exog = pd.read_excel(projpath+'datafiles/nawru_'+vintage_name+'.xls', header=0, index_col=0)
except:
    pass

# -------------------------------------------------
#               OUTPUT INITIALISATION
# -------------------------------------------------

outputfile = ExcelWriter(projpath+'output/PyPFOG_output_'+vintage_name+'.xlsx')
ones.loc[OutStartYear:changey+clos_nb_y].to_excel(outputfile, sheet_name=prgversion+'_'+vintage_name,startcol=0,
                                                  index=True, index_label='YEAR')
excelcolumn = 1
srkf_output = pd.DataFrame(index=range(OutStartYear,changey + 21))
srkf_file = ExcelWriter(projpath+'datafiles/tfp_'+vintage_name+'.xls')

nawru_output = pd.DataFrame(index=range(OutStartYear,changey + 11))
nawru_file = ExcelWriter(projpath+'datafiles/nawru_'+vintage_name+'.xls')

#
# ----------------------------------------------------------------------------------------
#
#                            LET'S START NOW!
#
# ----------------------------------------------------------------------------------------
for country in countrylist:
    with open(logfile, 'a') as f:
        f.write('\nRUNNING ESTIMATIONS FOR ' + country.upper())
    with open(olslog, 'a') as f:
        f.write(
            '\n\n\n - - - - - - - - - - - - - - - - - - -\n        ' + country.upper() + ' - ' + country.upper() +
            ' - ' + country.upper() + '\n - - - - - - - - - - - - - - - - - - -\n')

    pf_data = pd.DataFrame()
# 
# ----------------------------------------------------------------------------------------
#
#               TREND TFP (SRKF) ESTIMATIONS VIA GAP50.DLL
#
# ----------------------------------------------------------------------------------------
    srkf_exists = True
    try:
        srkf_output[country.upper() + '_SRKF'] = srkf_exog[country.upper() + '_SRKF']
    except:
        srkf_exists = False

    if country in tfp_countrylist or country in pf_countrylist:
        pf_data = pd.concat([pf_data, sr_prep.sr_prep(country, ameco, cubs, country_params, tfp_params, changey,
                                                      changey + yf, olslog)], axis=1)
    if country in tfp_countrylist:
        est_type = 'tfp'
        adjfact = []
        gaptimer = np.datetime64(datetime.datetime.now())
        pf_data = pd.concat([pf_data,
                             jrc_tools.rungap50(country, pf_data, adjfact, vintage_name, changey,
                                                gap_path, est_type, logfile)], axis=1)
        with open(logfile, 'a') as f:
            f.write(' Time spend for computations : '+str(np.datetime64(datetime.datetime.now())-gaptimer))
        srkf_output[country.upper() + '_SRKF'] = pf_data['SRKF']
        srkf_exists = True
    else:
        with open(logfile, 'a') as f:
            f.write('\n---NO Trend TFP estimations requested in parameter file')
        if srkf_exists:
            with open(logfile, 'a') as f:
                f.write(', found existing Trend TFP estimations in data file, will use it.')
            pf_data['SRKF'] = srkf_exog[country.upper() + '_SRKF']
        else:
            with open(logfile, 'a') as f:
                f.write(', no existing Trend TFP estimations found in data file.')
# 
# 
# ----------------------------------------------------------------------------------------
#
#                   NAWRU ESTIMATIONS VIA GAP50.DLL
#
# ----------------------------------------------------------------------------------------
    nawru_exists = True
    try:
        nawru_output[country.upper() + '_NAWRU'] = nawru_exog[country.upper() + '_NAWRU']
    except:
        nawru_exists = False

    if country in nawru_countrylist:
        if 'LUR' in pf_data.columns:
            lur_ok = True
        else:
            lur_ok = False
        pf_data = pd.concat([pf_data, nawru_prep.nawru_prep(country, ameco, nawru_params, changey, lur_ok)], axis=1)
        est_type = 'nawru'
        adjfact = nawru_params['Adjustment Factor']
        gaptimer = np.datetime64(datetime.datetime.now())
        pf_data = pd.concat([pf_data, jrc_tools.rungap50(country, pf_data, adjfact, vintage_name, changey,
                                                         gap_path, est_type, logfile)], axis=1)
        with open(logfile, 'a') as f:
            f.write(' Time spend for computations : '+str(np.datetime64(datetime.datetime.now())-gaptimer))
        nawru_output[country.upper() + '_NAWRU'] = pf_data['NAWRU']
        nawru_exists = True
    else:
        with open(logfile, 'a') as f:
            f.write('\n---NO NAWRU estimations requested in parameter file')
        if nawru_exists:
            with open(logfile, 'a') as f:
                f.write(', found previous NAWRU estimations in data file, will use it.')
            pf_data['NAWRU'] = nawru_exog[country.upper() + '_NAWRU']

    # ols function needs NaN instead of -99999.0 to work (-99999.0 are requested by GAP.DLL)
    pf_data = pf_data.replace(-99999.0, np.nan)

# ----------------------------------------------------------------------------------------
#
#                       YGAP ESTIMATIONS
#
# ----------------------------------------------------------------------------------------

    if country in pf_countrylist:
        do_pf_estimations = True
        with open(logfile, 'a') as f:
            f.write('\n---Computing YGAP estimations')
        if not srkf_exists:
            with open(logfile, 'a') as f:
                f.write('\n-----SRKF is missing, YGAP estimation is not possible')
            do_pf_estimations = False
        if not nawru_exists:
            with open(logfile, 'a') as f:
                f.write('\n-----NAWRU is missing, YGAP estimation is not possible')
            do_pf_estimations = False
        if not do_pf_estimations:
            with open(logfile, 'a') as f:
                f.write('\n-----NO YGAP estimation possible')
            continue

        pf_data = pf_prep.pf_prep(country, ameco, pf_data, prg_params, country_params, changey, yf, projpath, olslog)

# Some data is extracted from the main DataFrame for ease of code reading
        ypot = pf_data['ypot']
        dep = pf_data['dep']
        k = pf_data['k']
        iypot = pf_data['iypot']
        ygap = pf_data['ygap']
        totalh_mt = pf_data['totalh_mt']
        iq = pf_data['iq']
        y = pf_data['y']
        sr = pf_data['SR']
        srkf = pf_data['SRKF']
        totalhs = pf_data['totalhs']

        x0= [ypot[changey], k[changey], iq[changey], y[changey], sr[changey]]     # initial guesses

        for t in range (changey + 1, changey + clos_nb_y + 1):
            params = [totalhs[t], srkf[t], dep[t], k[t - 1], iypot[t],
                      ygap[t], totalh_mt[t], alpha]
            x0 = fsolve(modeltosolve.modeltosolve, x0, params)
            ypot[t], k[t], iq[t], y[t], sr[t] = x0

        wsr = sr.diff()

        output = pd.concat([y,
                            ygap,
                            ypot,
                            pf_data['part_mt'],
                            pf_data['parts'],
                            pf_data['wsr']*100,
                            pf_data['wsrkf']*100,
                            pf_data['NAWRU'],
                            pf_data['lurharm_mt'],
                            pf_data['hpere_mt'],
                            iq,
                            pf_data['lfss'],
                            pf_data['lp2'],
                            totalhs,
                            pf_data['l_mt'],
                            totalh_mt,
                            k,
                            pf_data['nwinf'],
                            pf_data['popw'],
                            pf_data['popt'],
                            sr,
                            pf_data['srhp'],
                            srkf,
                            iypot,
                            dep], axis=1)

        output.columns = [country + '_GDP', country + '_Y_GAP(PF)', country + '_Y_Pot', country + '_part',
                          country + '_Part_S', country + '_wSR', country + '_wSR_KF', country + '_NAWRU',
                          country + '_UnEmpl_Rate', country + '_HperE', country + '_Investment', country + '_Pot_LF',
                          country + '_Pot_Empl', country+'_Pot_Tot_Hrs', country+'_Empl', country+'_Tot_Hrs',
                          country+'_Capital', country+'_Wage_Infl', country+'_Pop_WA', country+'_Tot_Pop',
                          country+'_SR', country+'_SR_HP', country+'_SR_Kf', country+'_iypot', country+'_Depreciation']

        output.loc[OutStartYear:changey + clos_nb_y].to_excel(outputfile, sheet_name=prgversion + '_' + vintage_name,
                                                              startcol=excelcolumn, index=False)
        excelcolumn += 24
        ygap_passed += 1
        with open(logfile, 'a') as f:
            f.write(' ->PASSED')

    else:
        with open(logfile, 'a') as f:
            f.write('\n---NO YGAP estimation requested')

    outputfile.close()

srkf_output.to_excel(srkf_file, sheet_name=prgversion+'_'+vintage_name)
srkf_file.close()
# TODO : DEBUG changed output of nawru... should be up to changey
nawru_output.loc[OutStartYear:].to_excel(nawru_file, sheet_name=prgversion+'_'+vintage_name)
nawru_file.close()

with open(logfile, 'a') as f:
    f.write("\n\nYGAP ESTIMATIONS ->PASSED for " + str(ygap_passed) +
            " countries.\nTime spend for the total program run : "
            + str(np.datetime64(datetime.datetime.now()) - current1))

# ------------------------------------------------------------
#                    THIS IS THE END
# ------------------------------------------------------------

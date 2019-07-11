"""
# --------------------------------------------------------------------------------------------------------
# 
# Modified version of code written by C.Planas and A.Rossi at 
# the Joint Research Centre (JRC) of the European Commission
#
# The original code was modified to work with Excel data files using Pandas library instead 
# of using a tree structure (Anytree library).
#
#
# GAP50.DLL is developped at the JRC computes Trend TFP and NAWRU estimation 
# as discussed in  K. Havik, K. Mc Morrow, F. Orlandi, C. Planas, R. Raciborski,
# W. Röger, A. Rossi, A. Thum-Thysen, V. Vandermeulen, (2014), "The Production Function
# Methodology for Calculating Potential Growth Rates & Output Gaps", Economic Papers 535,
# Economic and Financial Affairs.
#
# --------------------------------------------------------------------------------------------------------
"""
# Run gap50.dll


def rungap50(country, data, adjfact, vintage_name, changey, path, tipo, logfile):
    import ctypes as ct
    import numpy as np
    import pandas as pd
    from _ctypes import FreeLibrary
    import f90nml

    projpath = path+'/'
    path = path + '$'                                # add to find end of dtring
    dllversion="GAP50DLL20190503.dll"

    with open(logfile, 'a') as f:
        f.write('\n---computing ' + tipo.upper() + ' for '+ country.upper() + ' via GAP50.DLL v.' + dllversion)
    lib = ct.CDLL(projpath+"lib/"+dllversion)

    gap50 = getattr(lib, "pytogap")

    # Read Namelist
    nml    = f90nml.read(projpath + 'priors/' + tipo.upper() + '_DLL_' + country.upper() + '_'
                         + vintage_name.replace('final','') + '.nml')
    nmlstr = str(nml)
    nt   = len(nml['prior']['lab'])       # number of parameters
    ny   = len(nml['ssm']['endogenous'])  # number of endogenous series
    inter = nml['GAP']['Inter']           # INTER: 1=(Back,PC),2=(Back,Cycle),3=(Forw,PC),4=(Forw,Cycle)
    hor  = max(0,nml['GAP']['Anchor'][1]) # horizon for anchored estimates
    starty = nml['GAP']['Startyear']
    stri = str(nml['ssm']['exogenous'])
    pos  = list(find_all(stri, ','))
    nz =  len(pos) + 1                   # number of exogenous series
    name_vars = list()

    if tipo == 'nawru':
        name_vars.append('LUR')
        nf = hor
    else:
        name_vars.append('SR')
        nf = 10
    if tipo == 'nawru':
        if inter < 3:
            name_vars.append('DWINF')
        else:
            name_vars.append('DRULC')
    else:
        name_vars.append('CU')

    if nz == 1:
        name_vars.append(stri.strip())
    if nz > 1:
        name_vars.append(stri[0:pos[0]].strip())
        for i in range(0,len(pos)-1):
            name_vars.append(stri[pos[i]+1:pos[i+1]].strip())
        name_vars.append( stri[pos[len(pos)-1]+1:].strip() )

    nmax = changey - starty + 1
# Select variables
    (inds,indn,xn) = selectdata(data, changey, name_vars[0:ny], nmax)
    ismax1 = np.amax(inds)    # maximum missing position
    ismax2 = 0
    if nz > 1:  #number of exog series
        (indse, indne, xne) = selectdata(data, changey, name_vars[ny+1:], nmax)
        ismax2 = np.amax(indse)   # maximum missing position
    ismax = max(ismax1,ismax2)
    nobs  = nmax-ismax             # number of in-sample observations
    yk = np.arange(0, ny+nz, dtype=float)*0  # setup the nobs+nf - long
    for i in range(0, nobs+max(nf,hor)-1):            # concatenate columns until it is nrow x ncol
        yk = np.c_[yk, np.arange(0, ny+nz, dtype=float) * 0]
    yk[0:ny,0:nobs] = xn[0:ny,ismax:nobs+ismax]
    yk[0:ny,nobs:]  = -99999.0
    if nz > 0:
        yk[ny,:] = 1.0   # set the constant series
    if nz > 1:
        yk[ny+1:,0:nobs] = xne[0:,ismax:nobs+ismax]

        for j in range(nobs,nobs+max(nf,hor)):

            yk[ny+1:,j]  = 0
#                    yk[ny+1:,j]  = xne[0:,nobs+ismax-1]

# Set other dll Input
    b_string0 = nmlstr.encode('utf-8')
    b_string1 = path.encode('utf-8')
    arr = (ct.c_char * 5000 * 2)()
    arr[0].value = b_string0
    arr[1].value = b_string1
    nstring = ct.pointer(ct.c_int(2))
    nobsp = ct.pointer(ct.c_int(nobs))   # setup the pointer
    nyp   = ct.pointer(ct.c_int(ny))
    nzp   = ct.pointer(ct.c_int(nz))
    nfp   = ct.pointer(ct.c_int(nf))
    horp  = ct.pointer(ct.c_int(hor))
    ntp   = ct.pointer(ct.c_int(nt))

# Set dll Output
# Both ML and Bayes
    unobs = np.arange(0, 26, dtype=float) * 0  # setup the nobs+nf - long
    for i in range(1, nobs+max(nf, hor)):      # concatenate columns until it is nrow x ncol
            unobs = np.c_[unobs, np.arange(0, 26, dtype=float) * 0]
# Bayes
    ac = np.arange(0, 4*ny, dtype=float)*0  # setup the nobs+nf - long
    for i in range(1, 5):                   # concatenate columns until it is nrow x ncol
            ac = np.c_[ac, np.arange(0, 4*ny, dtype=float) * 0]
    param = np.arange(0, nt, dtype=float)*0  # setup the nobs+nf - long
    for i in range(1, 409):                   # concatenate columns until it is nrow x ncol
        param = np.c_[param, np.arange(0, nt, dtype=float) * 0]
    marginal = np.arange(0, nobs+nf, dtype=float)*0  # setup the nobs+nf - long
    for i in range(1, 1200):                   # concatenate columns until it is nrow x ncol
        marginal = np.c_[marginal, np.arange(0, nobs+nf, dtype=float) * 0]
    margl = np.arange(0, 13, dtype=float)*0  # setup the nobs+nf - long
    for i in range(1, 2):                   # concatenate columns until it is nrow x ncol
        margl = np.c_[margl, np.arange(0, 13, dtype=float) * 0]

    with open(logfile, 'a') as f:
        f.write('\n-----Variable list : ' + str(name_vars))

    gap50(nstring, arr, nobsp, nyp, nzp, nfp, horp, ntp, np.ctypeslib.as_ctypes(yk), np.ctypeslib.as_ctypes(unobs),
          np.ctypeslib.as_ctypes(ac), np.ctypeslib.as_ctypes(param), np.ctypeslib.as_ctypes(marginal),
          np.ctypeslib.as_ctypes(margl))

    handle = lib._handle
    FreeLibrary(handle)

# --------------------------------------------------------
# UNOBSERVABLES (nob+nf,26)  Maximum Likelihood estimates
# 1 series + forecasts, 2 rmse, 3 akrmse,
# 4 smoothed trend + forecast, 5 rmse, 6 akrmse
# 7 smoothed cycle + forecast, 8 rmse, 9 akrmse
# 10 filtered trend, 11 filtered cycle, 12 rmse
# 13 1st series innovations
# 14 PC  series + forecast
# 15 rmse
# 16 akrmse
# 17 PC innovations
# 18 PC idiosync smoothed - empty!
# 19 PC idiosync filtered - empty!
# 20 PC Smoothed component  - mu + beta'*c(t|T)
# 21 PC filtered component  - mu + beta'*c(t|t)"
# 22 PC fitted values - mu + beta'*c(t|T)+gam'*z
# 23 Anchored trend
# 24 Anchored cycle
# ---------------------------------------------------------

    if tipo=='nawru':

        if nml['GAP']['Anchor'][1] < 0:
            nawru_series = pd.Series(unobs[3,0:nmax-ismax+nf]+adjfact[country.lower()],
                                     index=range(changey+1-nmax+ismax, changey+nf+1)).rename('NAWRU')
        else:
            nawru_series = pd.Series(unobs[22,0:nmax-ismax+nf]+adjfact[country.lower()],
                                     index=range(changey+1-nmax+ismax, changey+nf+1)).rename('NAWRU')

        with open(logfile, 'a') as f:
            f.write('->PASSED')
        return nawru_series


    else:
        # ------------------------------------------------------------------------
        # UNOBSERVABLES, Bayesian estimates
        # by cols: ser1,  p2.5, p5, p95, p97.5, trend, p2.5, p5, p95, p97.5,
        #          cycle, p2.5, p5, p95, p97.5, ser2,  p2.5, p5, p95, p97.5, inn
        #          slope, p2.5, p5, p95, p97.5
        # ------------------------------------------------------------------------

        with open(logfile, 'a') as f:
            f.write('->PASSED')
        return pd.Series(unobs[5,0:nmax+nf], index=range(changey+1-nmax+ismax, changey+ismax+nf+1)).rename('SRKF')


def find_all(a_str, sub):
    # Finds all occurrences of a sub string inside a string
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches

# -----------------------------------------------------------
# SELECTDATA
#
# INPUT
#  data: Pandas DataFrame that contains all needed series
#  changey : last year of short term forecast
#  varnames: a list of variables to be selected from "data"
#  nmax: the length of the time series (including missings)
# OUTPUT
#  inds: array containing number of missings
#  indn: array containing number of obs
#  xn: array containing the series by row
# -----------------------------------------------------------


def selectdata(data, changey, varnames, nmax):
    import numpy as np
    nvar = len(varnames)
    indstart = list()
    indnobs = list()
    xn = np.zeros((nvar,nmax))

    for i in range(0,nvar):
        xn[i,:] = data.loc[changey-nmax+1:changey, varnames[i]].values
        start = data[varnames[i]].loc[changey-nmax+1:changey].first_valid_index()-(changey-nmax+1)
        nobs = len(data[varnames[i]].loc[changey-nmax+1:changey])-start
        indstart.append(start)
        indnobs.append(nobs)

    inds = np.asarray(indstart)
    indn = np.asarray(indnobs)

    return inds,indn,xn

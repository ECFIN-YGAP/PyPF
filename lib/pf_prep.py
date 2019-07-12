

def pf_prep(country, ameco, data, prg_params, country_params, changey, yf, projpath, olslog_path):
    import pandas as pd
    import numpy as np
    import ols_ar
    import closure
    import statsmodels.api as sm
    europop = pd.read_excel(projpath + prg_params.loc['popFile', 'value'], sheet_name="to rats", header=0, index_col=0)
    europop = europop.T
    # NOTE : the europop file as years as string (excel formula) -> convert index to integer on the fly
    europop.index = europop.index.astype('int64')
    ones = pd.Series(1., index=range(1960, changey + 11))
    ratio_cb = pd.Series(np.nan, index=range(1960, changey + 11))
    alpha = float(prg_params.loc['alpha', 'value'])
    clos_nb_y = int(prg_params.loc['clos_nb_y', 'value'])
    starthp = int(country_params.loc['starthp', country])
    # CALCULATE ACTUAL VARIABLES

    # LABOUR (totalh)
    # -----------
    # unemployment
    # create alias of LUR and NAWRU to ease the use of indices
    lurharm = data['LUR']
    dlur = lurharm.diff()
    nawru = data['NAWRU']

    # wages
    w = ameco[country + '_hwcdw']
    gw = w.pct_change() * 100
    data['nwinf'] = gw.diff()

    if country == 'lu':
        l_lux = ameco[
                    country + '_sle1'] * ones  # employment series. NB: National accounts national concept for all countries
        l_cb = data['l'] - l_lux
        ratio_cb = l_cb / data['l']  # ratio of cross-border workers
        lf = l_lux / (1 - lurharm / 100)
    else:
        lf = data['l'] / (1 - lurharm / 100)

    lu = lurharm * lf
    # for full prog conditions to be added for SLE=1
    sle = ameco[country + '_sle']


    # population of working age
    popw = ameco[country + '_popa1']
    popt = ameco[country + '_popt']

    # participation rate
    part = 100 * lf / popw

    # Extended population at working age (popw) using projections from Eurostat
    # -----------
    popwf = europop[country.upper() + '_POPAF']
    poptf = europop[country.upper() + '_POPTF']

    mpopf = (popwf.shift(-1) + popwf) / (popwf + popwf.shift(1))
    mpoptf = (poptf.shift(-1) + poptf) / (poptf + poptf.shift(1))

    for i in range(1, 7):
        popw[changey + i] = popw[changey + i - 1] * mpopf[changey + i]
        popt[changey + i] = popt[changey + i - 1] * mpoptf[changey + i]

    wpopw = popw.pct_change()
    wpopt = popt.pct_change()

    # Trend Participation Rate (parts)
    # -----------

    # extended series on part

    if country == 'de':
        #	 participation rates of migrants and non-migrants
        MigrationDE = pd.read_excel(projpath + prg_params.loc['MigrationFile', 'value'], header=0, index_col=0)
        partM = MigrationDE['DE_PARTM'] * 100 * ones
        for i in range(changey + 4, changey + yf + 1):
            partM[i] = partM[i - 1] + 0.5 * (partM[i - 1] - partM[i - 2]) + 0.5 * (partM[i - 2] - partM[i - 3])

        partsM = partM.copy()  # trend migrant participation rate = actual rate

        #	 population at working age for migrants and non-migrants

        popwM = MigrationDE['DE_POPWM'] / 1000 * ones  # migrant population at working age
        # assume that after 2023 no new migrants arrive (!) and that all of them stay in the 'migrant' group for several years
        popwM.loc[changey + 4:] = popwM[changey + 3]

        #	 labour force of migrants and non-migrants

        lfM = pd.Series(np.zeros(changey + yf - 1959), index=range(1960, changey + yf + 1))  # migrant labour force
        lfM.loc[2015:] = popwM.loc[2015:] * partM.loc[2015:] / 100
        LFnonM = lf - lfM  # non-migrant labour force

        partnonM = part.copy()  # non-migrant participation rate
        popwnonM = popw - popwM  # non-migrant population at working age
        partnonM.loc[2015:changey] = LFnonM.loc[2015:changey] / popwnonM.loc[2015:changey] * 100  # ???

    nblag = int(country_params.loc['part_nblag', country])
    const = bool(int(country_params.loc['part_const', country]))
    ar_start = int(country_params.loc['part_ar_start', country])

# We have to deal with shorter series for PART for CY 1997 and HR 2001
    if part.first_valid_index() > starthp:
        starthp = part.first_valid_index()

    time = bool(int(country_params.loc['part_timexog', country]))
    with open(olslog_path, 'a') as f:
        f.write('\n\n\n - - -PART OLS_AR\n')
    part = ols_ar.ols_ar(part, nblag, const, ar_start, changey, yf, olslog_path, time)

    # filter the forecasted series
    if country == 'de':
        # calculate the non migrant participation rate as a part of total actual participation rate
        partnonM.loc[2015:] = part.loc[2015:] * popw.loc[2015:] / (popw.loc[2015:] - popwM.loc[2015:]) - partM.loc[
                                                                                                         2015:] * popwM.loc[
                                                                                                                  2015:] / (
                                          popw.loc[2015:] - popwM.loc[2015:])
        cycle, partsnonM = sm.tsa.filters.hpfilter(partnonM.loc[starthp:changey + yf],
                                                   int(country_params.loc['part_lambda', country]))
        partsnonM = partsnonM * ones
        parts = partsnonM.copy()
        parts.loc[2015:] = partsnonM.loc[2015:] * (popwnonM.loc[2015:] / popw.loc[2015:]) + partsM.loc[2015:] * (
                    popwM.loc[2015:] / popw.loc[2015:])
    else:
        # ISSUE WITH CY HP FILTER START IN 1997 and do not provide values for 1995 ->

        cycle, parts = sm.tsa.filters.hpfilter(part.loc[starthp:changey + yf],
                                               int(country_params.loc['part_lambda', country]))
        parts = parts * ones

    # connect the hp and k filtered series to make it start in 1960
    # because SRKF starts in 1980

    for i in range(1, 21):
        data.loc[1980 - i, 'SRKF'] = data.loc[1980 - i + 1, 'SRKF'] - data.loc[1980 - i + 1, 'wsrhp']

    data['wsrkf'] = data['SRKF'].diff()

    # Extended NAWRU (nawru)
    # -----------

    # NAWRU: **** NEW end rule Spring 2014:
    # ----------
    # *I* in the t+5 framework (yf<4) we use an extension rule; "end rule"
    # *I* in t+10 the nawru series is complete and long in the dataset

    # ===========
    # * Autumn Final 2018
    # * since the wage indicator gives the wrong signal for IE nawru, replace the nawru by a simple HP (lurharm)
    # *===========

    if country == 'ie':
        lurori = lurharm.copy()
        lurharm = lurharm * ones
        nblag = 2
        const = True
        ar_start = 1965
        with open(olslog_path, 'a') as f:
            f.write('\n\n\n - - -LURHARM OLS_AR\n')
        lurharm = ols_ar.ols_ar(lurharm, nblag, const, ar_start, changey, yf, olslog_path)
        cycle, lurharms = sm.tsa.filters.hpfilter(lurharm.loc[starthp:changey + yf], 10)

        lurharms[changey + 1] = lurharms[changey] + .5 * (lurharms[changey] - lurharms[changey - 1])
        lurharms.loc[changey + 2:] = lurharms[changey + 1]

        nawru = lurharms
    else:
        nawru.loc[changey + 1:changey + yf] = nawru[changey] + 0.5 * (nawru[changey] - nawru[changey - 1])

    dnawru = nawru.diff()

    # Trend Hours worked per Employee (hperehp)
    # -----------
    # extended series on hours worked
    # = ar(series, nblag, const, ar_start, changey, nb_fcst)
    nblag = int(country_params.loc['hpere_nblag', country])
    const = bool(int(country_params.loc['hpere_const', country]))
    ar_start = int(country_params.loc['hpere_ar_start', country])

    # print('\nExtending HPERE :\n-----------------')
    with open(olslog_path, 'a') as f:
        f.write('\n\n\n - - -HPERE OLS_AR\n')
    data['hpere'] = ols_ar.ols_ar(data['hpere'], nblag, const, ar_start, changey, yf, olslog_path)

    starthp = int(country_params.loc['starthp', country])
    # filter the forecasted series
    cycle, hperehp = sm.tsa.filters.hpfilter(data.loc[starthp:changey + yf, 'hpere'], int(country_params.loc['hpere_lambda', country]))
    hperehp = hperehp * ones

    dhpere = data['hpere'].diff()
    whperehp = hperehp.pct_change()
    lfss = parts / 100 * popw
    # CROSS-BORDER WORKERS
    # ------------
    # in the case of LU we need to add cross-border workers
    if country == 'lu':
        # find the best ARIMA proces to explain the cross border worker ratio in the past
        # use this best proces to forecast the series
        # filter this long series to get the trend
        nblag = 2
        const = False
        ar_start = 1978
        with open(olslog_path, 'a') as f:
            f.write('\n\n\n - - -RATIO CB OLS_AR\n')
        ratio_cb = ols_ar.ols_ar(ratio_cb, nblag, const, ar_start, changey, yf, olslog_path)
        cycle, ratio_cb_hp = sm.tsa.filters.hpfilter(ratio_cb.loc[starthp:changey + yf], 10)
        # extend the related series
        l_lux = part / 100 * popw * (1 - lurharm / 100)
        l_cb = l_lux * ratio_cb / (1 - ratio_cb)
        data['l'] = l_lux + l_cb
        data['totalh'] = data['hpere'] * data['l']
    # Trend labour (totalhs)
    # -----------
        l_luxs = parts / 100 * popw * (1 - nawru / 100)
        l_cb_hp = l_luxs * ratio_cb_hp / (1 - ratio_cb_hp)
#        lfss = parts / 100 * popw  # trend labour force, only includes luxembourgish!
        lp2 = l_luxs + l_cb_hp  # trend employment
    else:
        data['lf'] = data['l'] / (1 - lurharm / 100)
        lp2 = lfss * (1 - nawru / 100)

    wlp2 = lp2.pct_change()
    # trend total hours worked
    totalhs = lp2 * hperehp
    wtotalhs = totalhs.pct_change()

    # create a totalhs specific for the t+10


    # Investment rule (IYPOT)
    # -----------

    srkf_level = np.exp(data['SRKF'])
    ypot = totalhs ** alpha * data['k'] ** (1 - alpha) * srkf_level
    # ypot = ypot * ones
    iypot = 100 * (data['iq'] / ypot)
    iypot = iypot * ones

    # NOTE : THERE IS A COUNTRY SPECIFICITY FOR DE FOR T+10

    nblag = int(country_params.loc['iypot_nblag', country])
    const = bool(int(country_params.loc['iypot_const', country]))
    ar_start = int(country_params.loc['iypot_ar_start', country])

    # print('\nExtending IYPOT :\n-----------------')
    with open(olslog_path, 'a') as f:
        f.write('\n\n\n - - -IYPOT OLS_AR\n')
    iypot = ols_ar.ols_ar(iypot, nblag, const, ar_start, changey, yf, olslog_path)



    # GAP closure rule (ygap)
    # -----------
    ygap = 100 * (data['y'] / ypot - 1)

    # TODO
    ygap = closure.closure(ygap, clos_nb_y, changey)

    # other GAP closure rules (totalh_mt)
    # -----------

    # create the medium term actual series
    part_mt = part.copy()
    hpere_mt = data['hpere'].copy()
    l_mt = data['l'].copy()

    totalh_mt = data['totalh'].copy()
    lurharm_mt = lurharm * ones
    # create the gap series
    partgap = part - parts
    hperegap = data['hpere'] - hperehp
    lurgap = lurharm - nawru

    # close each gap (by the end of the period = 6)

    partgap = closure.closure(partgap, clos_nb_y, changey)
    hperegap = closure.closure(hperegap, clos_nb_y, changey)
    lurgap = closure.closure(lurgap, clos_nb_y, changey)

    # fill in the medium term actual series
    # TODO define a function to do so ?
    part_mt.loc[changey + 1:changey + yf] = parts.loc[changey + 1:changey + yf] + partgap.loc[changey + 1:changey + yf]
    hpere_mt.loc[changey + 1:changey + yf] = hperehp.loc[changey + 1:changey + yf] + hperegap.loc[changey + 1:changey + yf]
    lurharm_mt.loc[changey + 1:changey + yf] = nawru.loc[changey + 1:changey + yf] + lurgap.loc[changey + 1:changey + yf]

    if country == 'lu':
        lcbgap = ones * 0.
        for i in range(1, clos_nb_y + 1):
            lcbgap[changey + i] = (clos_nb_y - i) / clos_nb_y * (l_cb[changey] - l_cb_hp[changey])
        lcbgap.loc[changey + clos_nb_y + 1:lcbgap.size + 1959] = 0.

        l_lux_mt = l_lux
        l_lux_mt.loc[changey + 1:changey + yf] = popw.loc[changey + 1:changey + yf] * part_mt.loc[changey + 1:changey + yf] / 100 * (
                    1 - lurharm_mt.loc[changey + 1:changey + yf] / 100)
        l_cb_mt = l_cb
        l_cb_mt.loc[changey + 1:changey + yf] = l_cb_hp.loc[changey + 1:changey + yf] - lcbgap.loc[changey + 1:changey + yf]
        l_mt.loc[changey + 1:changey + yf] = l_lux_mt.loc[changey + 1:changey + yf] + l_cb_mt.loc[changey + 1:changey + yf]
    else:
        l_mt.loc[changey + 1:changey + yf] = popw.loc[changey + 1:changey + yf] * part_mt.loc[changey + 1:changey + yf] / 100 * (
                    1 - lurharm_mt.loc[changey + 1:changey + yf] / 100)

    totalh_mt.loc[changey + 1:changey + yf] = l_mt.loc[changey + 1:changey + yf] * hpere_mt.loc[changey + 1:changey + yf]

    data = pd.concat([data, ygap.rename('ygap'), ypot.rename('ypot'), part_mt.rename('part_mt'), parts.rename('parts'), lurharm_mt.rename('lurharm_mt'), hpere_mt.rename('hpere_mt'), lfss.rename('lfss'), lp2.rename('lp2'), totalhs.rename('totalhs'), l_mt.rename('l_mt'), totalh_mt.rename('totalh_mt'), popw.rename('popw'), popt.rename('popt'), iypot.rename('iypot')], axis=1)
    return data
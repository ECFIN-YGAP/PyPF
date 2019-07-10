

def sr_prep(country, ameco, cubs, country_params, changey, endy, olslog):
    import numpy as np
    import pandas as pd
    import statsmodels.api as sm
    import ols_ar
    from statsmodels.tsa.arima_model import ARIMA
    alpha = .65
    data = pd.DataFrame(index=range(1960, changey + 11))
    ones = pd.Series(1., index=range(1960, changey + 11))
    #    GDP (y)
    # -----------
    data['y'] = ameco[country + '_gdpq']
    wy = data['y'].pct_change() * 100

    # LABOUR (totalh)
    # -----------
    # hours worked
    data['hpere'] = ameco[country + '_hpere']
    data['l'] = ameco[country + '_sled']
    data['totalh'] = data['hpere'] * data['l']
    data['wtotalh'] = data['totalh'].pct_change()
    # LUR is needed even if NAWRU is provided exogenously so they are defined here
    data['LUR'] = ameco[country + '_lur']

    # CAPITAL (k)
    # -----------
    # some country specificities here
    data['k'] = ameco[country + '_kt']
    data['iq'] = ameco[country + '_iq']
    data['iy'] = data['iq'] / data['y']

    
    # *I* for Ireland there has been a re-valuation of the capital stock to include aircraft leasing.
    # *I* this is not yet visible in the ameco capital stock series, and therefore we make an adjustment here.
    # *I* on 29/9/2016 it is believed that capital stock goes up by 53.7% in 2015 and remains at this higher level from then on.
    # *I* as on Autumn 2018 another modification to this procedure was made, based on country specificity for Ireland

    # DEP is needed for IE and LV to compute K (needed for TFP calculation)

    if country == 'ie':
        # calculate some additional variables
        k_ori = data['k'].copy()
        k_difference = data['k'].diff()  # = iq - cfc
        dep_ori = (data['iq'] - (data['k'] - data['k'].shift(1))) / data['k'].shift(1)
        dep_difference = dep_ori - dep_ori.shift(1)
        outturny = abs(dep_difference.where(abs(dep_difference) < 0.00000001))
        outturnyear = outturny.idxmin()
    
        # *** remark: outturn year is most of the time equal to t-1
    
        # * actual adjustment:
        # * cso estimate of the increase in the K stock for 2015
        data.loc[2015, 'k'] = 1.532 * data.loc[2014, 'k']
        # * after 2015, until the outturn year, the iq and cfc series are correct, they relate to the new capital stock
        for i in range(2016, outturnyear + 1):
            data.loc[i, 'k'] = data.loc[i - 1, 'k'] + k_difference[i]
        # * when there is no info on cfc, a constant dep rate is assumed for these years
        data['dep'] = (data['iq'] - (data['k'] - data['k'].shift(1))) / data['k'].shift(1)
        for i in range(outturnyear, changey + 1):
            data.loc[i, 'dep'] = data.loc[i - 1, 'dep']
        for i in range(outturnyear, changey + 1):
            data.loc[i, 'k'] = data.loc[i, 'iq'] + (1 - data.loc[i, 'dep']) * data.loc[i - 1, 'k']
    
    elif country == 'lv':
        #
        #	*I* depreciation rate is calculated based on investment and capital information
        #	*I* and then kept constant from the forecast starting
        #
            ee_iq = ameco['ee_iq'] * ones
            ee_kt = ameco['ee_kt'] * ones
            dep_ee = (ee_iq - (ee_kt - ee_kt.shift(1))) / ee_kt.shift(1)
            dep_ee.loc[changey:endy] = dep_ee[changey - 1]
    
            lt_iq = ameco['lt_iq'] * ones
            lt_kt = ameco['lt_kt'] * ones
            dep_lt = (lt_iq - (lt_kt - lt_kt.shift(1))) / lt_kt.shift(1)
            dep_lt.loc[changey:endy] = dep_lt[changey - 1]

            data['dep'] = (dep_ee + dep_lt) / 2  # average dep of LT and EE
    
            k_ori = data['k'].copy()
            for i in range(1996, endy + 1):
                data.loc[i, 'k'] = data.loc[i - 1, 'k'] * (1 - data.loc[i, 'dep']) + data.loc[i, 'iq']

    else:
        data['dep'] = (data['iq'] - (data['k'] - data['k'].shift(1))) / data['k'].shift(1)
        data.loc[changey:endy, 'dep'] = data.loc[changey - 1, 'dep']

    # PRODUCTIVITY (solow residual)
    # -----------

    data['SR'] = np.log(data['y'] / (data['totalh'] ** alpha * data['k'] ** (1 - alpha)))
    
    # FORECAST EXOGENEOUS
    # Trend TFP (srkf)
    # -----------
    wsr = data['SR'].diff()
    
    # for the moment (SF2019) ARIMA estimation is used for 6 countries
    # TODO : ARIMA is estimated with Python MLE instead of LS Gauss-Newton
    
    
    if int(country_params.loc['tfp_ma_order', country]) > 0:
        p = int(country_params.loc['tfp_nblag', country])
        d = 0
        q = int(country_params.loc['tfp_ma_order', country])
        if bool(int(country_params.loc['tfp_const', country])):
            const = 'c'
        else:
            const = 'nc'
    
        ar_start = int(country_params.loc['tfp_ar_start', country])
        # ARIMA requests that index is "datetime taged"
        wsr.index = pd.to_datetime(wsr.index, format='%Y', exact=True)
        model = ARIMA(wsr.loc[str(ar_start):str(changey)], order=(p, d, q), freq='AS-JAN')
        model_fit = model.fit(trend=const, disp=False)
        with open(olslog, 'a') as f:
            f.write('\n\n\n - - -TFP ARIMA\n' + str(model_fit.summary()))
        forecast = model_fit.predict(start=str(changey + 1), end=str(endy))
        wsr.loc[str(changey + 1):str(endy)] = forecast.loc[str(changey + 1):str(endy)]
        data['wsr'] = wsr.values * ones
    else:
        nblag = int(country_params.loc['tfp_nblag', country])
        const = bool(int(country_params.loc['tfp_const', country]))
        ar_start = int(country_params.loc['tfp_ar_start', country])
        with open(olslog, 'a') as f:
            f.write('\n\n\n - - -TFP OLS_AR\n')
        data['wsr'] = ols_ar.ols_ar(wsr, nblag, const, ar_start, changey, endy-changey, olslog)

    for i in range(data['SR'].first_valid_index(), endy):
        data.loc[i + 1, 'SR'] = data.loc[i, 'SR'] + data.loc[i + 1, 'wsr']
    
    # filter the forecasted series
    
    # extended series on actual TFP (old method)
    # = tfp_forecast(sr,index of last year of forecast,number of forecast years)
    # use of the ARMA function defined (series, nblag, const, ar_start, changey, nb_fcst)
    #
    # NOTE THAT IN RATS PROG, WSR is extended and then SR is rebuild from it
    # for this exercise we use the KF SR directly
    
    starthp = int(country_params.loc['starthp', country])
    
    # filter the forecasted series
    cycle, data['srhp'] = sm.tsa.filters.hpfilter(data.loc[starthp:endy,'SR'], int(country_params.loc['tfp_lambda', country]))
    data['wsrhp'] = data['srhp'].diff()

    data['CU'] = cubs['CUBS_ST_' + country.upper()]
    data = data.fillna(-99999.0)

    return data



def nawru_prep(country, ameco, params, changey, lur_ok):
    import pandas as pd
    data = pd.DataFrame(index=range(1960, changey + 11))
    #        Correspondence between nawrudata Excel file and ameco file
    #
    #        B: at_lur (=LUR)
    #        C: DWINF = 0.01*(O10-O9)
    #        D: DDTOT = (P10-Q10)-(P9-Q9)
    #        E: DDPROD  = H10-H9
    #        F: DDTOT1 = D9
    #        G: DDPROD1 = E9
    #        H: at_dlprod (=DPROD)
    #        I: DPROD1 = H9
    #        J: at_ws (=WS)
    #        K: WS1 = J9
    #        L: WS2 = K9
    #        M: terms of trade =P10-Q10
    #        N: terms of trade lag =M9
    #        O: at_winf (=WINF)
    #        P: at_pce (=DPCE)
    #        Q: at_dgdpdefl
    #        R: at_dpcegdp
    data.head()
    if not lur_ok:
        data['LUR'] = ameco[country + '_lur'] # B
    data['DPROD'] = ameco[country + '_dlprod'] # H
    data['WINF'] = ameco[country + '_winf'] # O
    data['DPCE'] = ameco[country + '_pce']  # P
    data['WS'] = ameco[country + '_ws']  # J
    data['DWINF'] = 0.01 * (data['WINF'] - data['WINF'].shift(1))   # C
    data['DDTOT'] = (data['DPCE'] - ameco[country + '_dgdpdefl']) - (data['DPCE'].shift(1) -  ameco[country + '_dgdpdefl'].shift(1)) # D
    data['DDTOT1'] = data['DDTOT'].shift(1) # F
    data['DDPROD'] = data['DPROD'] - data['DPROD'].shift(1)     # E
    data['DDPROD1'] = data['DDPROD'].shift(1)  # G
    data['DPROD1'] = data['DPROD'].shift(1) # I
    data['WS1'] = data['WS'].shift(1) # K
    data['WS2'] = data['WS'].shift(2) # L
    data['DTOT'] = data['DPCE'] - ameco[country + '_dgdpdefl'] # M
    data['DTOT1'] = data['DTOT'].shift(1) # N
    data['DDWS'] = (data['WS'] - data['WS1']) - (data['WS1'] - data['WS2'])
    data['DRULC'] = data['WINF'] / 100 - data['DPROD'] - (data['DPCE'] - 1)

    for i in range(1,6):
        if isinstance(params.loc[country, 'Dummy ' + str(i)], str):
            dummy = params.loc[country, 'Dummy ' + str(i)].split(':')
            dummy_years = dummy[0].split(',')
            dummy_value = dummy[1]
            data['dum' + str(i)] = 0.
            for year in dummy_years:
                data.loc[int(year), 'dum' + str(i)] = dummy_value
        else:
            continue
    return data

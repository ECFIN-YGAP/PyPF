# This function is the model of equations to solve


def modeltosolve(guesses, params):
    import numpy as np
    ypot, k, iq, y, sr = guesses #unpacking tuple with initial guesses
    totalhs, srkf, dep, klag, iypot, ygap, totalh_mt, alpha = params  # unpacking tuple with parameters
    eq1 = totalhs**alpha * k**(1-alpha) * np.exp(srkf) - ypot #1st equation of the model
    eq2 = iq + (1-dep) * klag - k # 2d equation
    eq3 = iypot / 100 * ypot - iq # 3d equation
    eq4 = ypot * (1 + ygap / 100) - y # 4th equation
    eq5 = np.log( y / (totalh_mt**alpha * k**(1 - alpha))) - sr # 5th and last equation
    return [eq1, eq2, eq3, eq4, eq5]
# The next function implements a mechanical closure.
# Meaning that after n years the gap should be zero


def closure(series, clos_nb_y, changey):
    for i in range (1, clos_nb_y + 1):
        series[changey+i] = (clos_nb_y - i) / clos_nb_y * series[changey]
    series.loc[changey + clos_nb_y + 1:] = 0.

    return series

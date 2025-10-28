

def get_beta(fc):
    if fc <= 280:
        beta = 0.85
    elif fc > 280 and fc < 550:
        beta = 0.85 - 0.005 * (fc - 280)/70
    else:
        beta = 0.65
    return beta


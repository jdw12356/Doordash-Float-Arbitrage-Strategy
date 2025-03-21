import numpy as np

def get_macro_profile(year, days):
    if year == 2020:
        # COVID dip + rebound
        cpi = [0.0003 + 0.0001 * np.sin(i/30) for i in range(days)]
        vol_mult = [0.015 + 0.01 * np.sin(i/20) for i in range(days)]
    elif year == 2022:
        # High inflation regime
        cpi = [0.0008 + 0.0002 * np.sin(i/45) for i in range(days)]
        vol_mult = [0.012 + 0.008 * np.sin(i/25) for i in range(days)]
    elif year == 2023:
        # Disinflation & low vol
        cpi = [0.0004 + 0.00005 * np.sin(i/50) for i in range(days)]
        vol_mult = [0.008 + 0.004 * np.sin(i/35) for i in range(days)]
    else:
        # Baseline
        cpi = [0.0005 for _ in range(days)]
        vol_mult = [0.01 for _ in range(days)]
    return cpi[:days], vol_mult[:days]
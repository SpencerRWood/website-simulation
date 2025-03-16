import numpy as np

def configure_gamma(seasonal_distribution):
    def parse_gamma_params(gamma_params):
        return np.random.uniform(gamma_params["low"], gamma_params["high"], size=gamma_params["size"])

    gamma_1 = parse_gamma_params(seasonal_distribution["gamma_1"])
    gamma_2 = parse_gamma_params(seasonal_distribution["gamma_2"])
    return (gamma_1, gamma_2)
         
def generate_fourier_multiplier(date, gamma_tuple, harmonics=2):
    """Computes seasonal adjustment using a Fourier series approximation.
    Parameters:
    t (int or array): Time index (e.g., week number).
    gamma_1 (array): Coefficients for cosine terms.
    gamma_2 (array): Coefficients for sine terms.
    harmonics (int): Number of harmonics to include in the sum.

    Returns:
    float or array: Seasonality adjustment factor.
    """
    gamma_1, gamma_2 = gamma_tuple
    t = date.isocalendar()[1]
    fourier_multiplier = np.zeros_like(t, dtype=float)
    for d in range(1, harmonics + 1):
        fourier_multiplier += gamma_1[d-1] * np.cos((2 * np.pi * d / 52) * t) \
                       + gamma_2[d-1] * np.sin((2 * np.pi * d / 52) * t)
    
    return fourier_multiplier

def min_max_scaling(val_list, floor_val, ceiling_val):
    min_val, max_val = min(val_list), max(val_list)
    return [((val-min_val) / (max_val - min_val)) * (ceiling_val - floor_val) + floor_val for val in val_list]

def seasonal_multiplier(date_range, seasonal_distribution):
    gamma_tuple = configure_gamma(seasonal_distribution)
    fourier_multiplier = [generate_fourier_multiplier(date,gamma_tuple) for date in date_range]

    min_val, max_val = min(fourier_multiplier), max(fourier_multiplier)
    floor_val, ceiling_val = seasonal_distribution["scaling"]["min_factor_val"], seasonal_distribution["scaling"]["max_factor_val"]

    return [((val - min_val) / (max_val - min_val)) * (ceiling_val - floor_val) + floor_val for val in fourier_multiplier]

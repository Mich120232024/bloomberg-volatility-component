#!/usr/bin/env python3
"""
Professional Garman-Kohlhagen FX Option Pricing Model
Backend implementation for centralized option pricing service
"""

import math
from typing import Dict, Union

def norm_cdf(x: float) -> float:
    """Accurate normal cumulative distribution function approximation"""
    # Abramowitz and Stegun approximation
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911
    
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    
    return 0.5 * (1.0 + sign * y)

def norm_pdf(x: float) -> float:
    """Normal probability density function"""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

def price_fx_option(
    spot: float,
    strike: float, 
    time_to_expiry: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    option_type: str,
    notional: float = 1.0
) -> Dict[str, Union[float, str]]:
    """
    Price FX option using Garman-Kohlhagen model
    
    Args:
        spot: Current spot rate (e.g., 1.1742 for EURUSD)
        strike: Strike price
        time_to_expiry: Time to expiry in years (e.g., 0.0833 for 1 month)
        domestic_rate: Quote currency interest rate in % (e.g., 4.96 for USD)
        foreign_rate: Base currency interest rate in % (e.g., 1.90 for EUR)
        volatility: Implied volatility in % (e.g., 7.34)
        option_type: 'call' or 'put'
        notional: Notional amount in base currency
    
    Returns:
        Dictionary with pricing results and Greeks
    """
    try:
        # Convert percentages to decimals
        r_d = domestic_rate / 100
        r_f = foreign_rate / 100
        sigma = volatility / 100
        
        # Calculate d1 and d2
        d1 = (math.log(spot / strike) + (r_d - r_f + 0.5 * sigma * sigma) * time_to_expiry) / (sigma * math.sqrt(time_to_expiry))
        d2 = d1 - sigma * math.sqrt(time_to_expiry)
        
        # CDFs and PDFs
        nd1 = norm_cdf(d1)
        nd2 = norm_cdf(d2)
        pdf_d1 = norm_pdf(d1)
        
        # Option value calculation
        if option_type.lower() == 'call':
            premium = spot * math.exp(-r_f * time_to_expiry) * nd1 - strike * math.exp(-r_d * time_to_expiry) * nd2
            delta = math.exp(-r_f * time_to_expiry) * nd1
        else:  # put
            premium = strike * math.exp(-r_d * time_to_expiry) * (1 - nd2) - spot * math.exp(-r_f * time_to_expiry) * (1 - nd1)
            delta = math.exp(-r_f * time_to_expiry) * (nd1 - 1)
        
        # Greeks calculation
        gamma = math.exp(-r_f * time_to_expiry) * pdf_d1 / (spot * sigma * math.sqrt(time_to_expiry))
        vega = spot * math.exp(-r_f * time_to_expiry) * pdf_d1 * math.sqrt(time_to_expiry) / 100  # Per 1% vol
        
        # Theta (per day)
        if option_type.lower() == 'call':
            theta = (-spot * pdf_d1 * sigma * math.exp(-r_f * time_to_expiry) / (2 * math.sqrt(time_to_expiry))
                    - r_d * strike * math.exp(-r_d * time_to_expiry) * nd2
                    + r_f * spot * math.exp(-r_f * time_to_expiry) * nd1) / 365
        else:
            theta = (-spot * pdf_d1 * sigma * math.exp(-r_f * time_to_expiry) / (2 * math.sqrt(time_to_expiry))
                    + r_d * strike * math.exp(-r_d * time_to_expiry) * (1 - nd2)
                    - r_f * spot * math.exp(-r_f * time_to_expiry) * (1 - nd1)) / 365
        
        # Rho (per 1% rate move)
        if option_type.lower() == 'call':
            rho = strike * time_to_expiry * math.exp(-r_d * time_to_expiry) * nd2 / 100
        else:
            rho = -strike * time_to_expiry * math.exp(-r_d * time_to_expiry) * (1 - nd2) / 100
        
        # Calculate forward rate
        forward = spot * math.exp((r_d - r_f) * time_to_expiry)
        
        return {
            "premium": premium * notional,
            "premium_percent": (premium / spot) * 100,
            "delta": delta * 100,  # As percentage
            "delta_notional": delta * notional,
            "gamma": gamma * 100,  # Per 1% spot move
            "gamma_notional": gamma * notional,
            "vega": vega,  # Per 1% vol move
            "vega_notional": vega * notional,
            "theta": theta,  # Per day
            "theta_notional": theta * notional,
            "rho": rho,  # Per 1% rate move
            "rho_notional": rho * notional,
            "forward": forward,
            "intrinsic_value": max(0, (spot - strike if option_type.lower() == 'call' else strike - spot)) * notional,
            "time_value": (premium - max(0, (spot - strike if option_type.lower() == 'call' else strike - spot))) * notional,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "premium": 0,
            "premium_percent": 0
        }

def calculate_forward(spot: float, time_to_expiry: float, domestic_rate: float, foreign_rate: float) -> float:
    """Calculate forward rate using interest rate parity"""
    r_d = domestic_rate / 100
    r_f = foreign_rate / 100
    return spot * math.exp((r_d - r_f) * time_to_expiry)
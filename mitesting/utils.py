from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division


def create_greek_dict():
    from sympy.abc import (alpha, beta,  delta, epsilon, eta,
                           theta, iota, kappa, mu, nu, xi, omicron, pi,
                           rho, sigma, tau, upsilon, phi, chi, psi, omega)
    from sympy import Symbol
    lambda_symbol = Symbol('lambda')
    gamma_symbol = Symbol('gamma')
    zeta_symbol = Symbol('zeta')
    greek_dict = {'alpha': alpha, 'alpha_symbol': alpha, 
                  'beta': beta,'beta_symbol': beta, 
                  'gamma_symbol': gamma_symbol, 
                  'delta': delta, 'delta_symbol': delta, 
                  'epsilon': epsilon, 'epsilon_symbol': epsilon,
                  'zeta_symbol': zeta_symbol, 
                  'eta': eta, 'eta_symbol': eta, 
                  'theta': theta, 'theta_symbol': theta, 
                  'iota': iota, 'iota_symbol': iota, 
                  'kappa': kappa, 'kappa_symbol': kappa, 
                  'lambda_symbol': lambda_symbol, 
                  'mu': mu, 'mu_symbol': mu,
                  'nu': nu, 'nu_symbol': nu,
                  'xi': xi,'xi_symbol': xi, 
                  'omicron': omicron,'omicron_symbol': omicron, 
                  'rho': rho, 'rho_symbol': rho, 
                  'sigma': sigma, 'sigma_symbol': sigma, 
                  'tau': tau, 'tau_symbol': tau, 
                  'upsilon': upsilon,'upsilon_symbol': upsilon,
                  'phi': phi, 'phi_symbol': phi, 
                  'chi': chi, 'chi_symbol': chi, 
                  'psi': psi, 'psi_symbol': psi, 
                  'omega': omega, 'omega_symbol': omega }

    return greek_dict
    

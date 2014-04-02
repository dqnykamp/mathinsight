from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from mitesting.customized_commands import *

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
    

def return_sympy_global_dict(allowed_sympy_commands=[]):
    """
    Make a whitelist of allowed commands sympy and customized commands.
    Argument allowed_sympy_commands is an iterable containing
    strings of comma separated commands names.
    Returns a dictionary where keys are the command names and 
    values are the corresponding function or sympy expression.
    The local dictionary contains
    1.  all greek symbols from create_greek_dict()
    2.  the allowed sympy_commands that match localized commands
    3.  the allowed sympy_commands that match standard sympy commands.
    Command names that don't match either customized or sympy commands
    are ignored.
    """

    # create a dictionary containing all sympy commands
    all_sympy_commands = {}
    exec "from sympy import *" in all_sympy_commands

    # create a dictionary containing the localized commands
    localized_commands = {'roots_tuple': roots_tuple, 
                          'real_roots_tuple': real_roots_tuple, 
                          'round': round_expression,
                          'smallest_factor': smallest_factor,
                          'e': all_sympy_commands['E'], 
                          'max': max_including_tuples,
                          'Max': max_including_tuples,
                          'min': min_including_tuples,
                          'Min': min_including_tuples,
                          'abs': Abs,
                          'evalf': evalf_expression,
                          'index': index,
                          'sum': sum,
                          'iif': iif,
                          'len': len,
                          }
    
    # create a set of allowed commands containing all comma-separated
    # strings from allowed_sympy_commands
    allowed_commands = set()
    for commandstring in allowed_sympy_commands:
        allowed_commands=allowed_commands.union(
            [item.strip() for item in commandstring.split(",")])

    # create the dictionary
    # First add the greek symbols
    global_dict = create_greek_dict()

    for command in allowed_commands:
        try:
            # attempt to match command with localized command
            global_dict[str(command)]=localized_commands[command]
        except KeyError:
            try:
                # if command isn't found in localized command
                # then attempt to match with standard sympy command
                global_dict[str(command)]=all_sympy_commands[command]
            except KeyError:
                pass

    return global_dict

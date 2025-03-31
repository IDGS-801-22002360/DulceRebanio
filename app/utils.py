from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def role_required(roles):
    """
    * Decorador para restringir el acceso a usuarios con roles específicos.
    * :param roles: Lista de roles permitidos.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.rol not in roles:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                
                #* Redirigir según el rol del usuario
                if current_user.is_authenticated:
                    if current_user.rol == 'Admin':
                        return redirect(url_for('usuarios.index'))
                    elif current_user.rol == 'Ventas':
                        return redirect(url_for('ventas.puntoVenta'))
                    elif current_user.rol == 'Produccion':
                        return redirect(url_for('produccion.galletas'))
                    elif current_user.rol == 'Cliente':
                        return redirect(url_for('clientes.index'))
                return redirect(url_for('auth.login'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

def is_password_insecure(contrasena):
    with open('insecure_passwords.txt', 'r') as file:
        insecure_passwords = [line.strip() for line in file]
    return contrasena in insecure_passwords
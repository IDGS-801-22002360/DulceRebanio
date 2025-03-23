from logger import error_logger, action_logger

#!  esta mdre solo es de prueba para ver que si genera los logs, se va 
#!  a cambiar mas adelante por uno que guarde bien los datos y las acciones
#!  de la aplicacion

def test_logging():
    # Generar un log de acción
    action_logger.info('This is a test action log')

    # Generar un log de error
    try:
        1 / 0  # Genera un error
    except ZeroDivisionError as e:
        error_logger.error('This is a test error log: %s', e)

if __name__ == '__main__':
    test_logging()
    print("Logs generated. Check the 'logs' directory.")
import logging
import os

#! esto va a crear directorio para los logs si no existe en la carpeta de logs
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

#! esta seria la configuracion de los logs para los errores que pasen
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler(os.path.join(log_directory, 'error.log'))
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

#! y este para las acciones que se generen en la aplicacion
action_logger = logging.getLogger('action_logger')
action_logger.setLevel(logging.INFO)
action_handler = logging.FileHandler(os.path.join(log_directory, 'action.log'))
action_handler.setLevel(logging.INFO)
action_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
action_handler.setFormatter(action_formatter)
action_logger.addHandler(action_handler)
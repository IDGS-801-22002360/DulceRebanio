import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey

import urllib

MAIL_SERVER = 'smtp.gmail.com' 
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'tu_correo@gmail.com'
MAIL_PASSWORD = 'tu_contraseña'
MAIL_DEFAULT_SENDER = 'tu_correo@gmail.com'

class Config(object):
    SECRET_KEY="Clave nueva"
    SESSION_COOKIE_SECRET=False
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@127.0.0.1/dongalleto2'

import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey

import urllib

class Config(object):
    SECRET_KEY="Clave nueva"
    SESSION_COOKIE_SECRET=False
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@127.0.0.1/dongalleto2'
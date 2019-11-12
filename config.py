import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    # SECRET KEY
    SECRET_KEY = os.environ.get('SECRET_KEY') or '1S1SLJJMTDSX**'
    #RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY') or 'SHIHIDI-JIJISPPP'
    #RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY') or 'SHIHIDI-JIJISPPjjjP'
    # Database configuration
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:ece1779pass@ece1779db.cxadwgdqjmo8.us-east-1.rds.amazonaws.com:3306/ece1779'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 15*1024*1024
    # Flask Gmail config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'lxh56b@gmail.com'
    MAIL_PASSWORD = 'qiyztgtxpjackfon'
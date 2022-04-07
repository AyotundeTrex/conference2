class Config(object):
    ADMIN_EMAIL="some random parameters"
    USERNAME="SAMPLE"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI="mysql+mysqlconnector://root@127.0.0.1/confdb2"
    SQLALCHEMY_TRACK_MODIFICATIONS=True
    MERCHANT_ID="t98765@0"

class TestConfig(Config):
    DATABASE_URI="Test Connection parameters"
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail,Message

#Instantiate an object of flask and making it global for other modules to see
app = Flask(__name__, instance_relative_config=True)

csrf = CSRFProtect(app)

#Load the config and local imports
#Load the routes,forms,models here
from conferenceapp2 import config
app.config.from_object(config.ProductionConfig)
app.config.from_pyfile('config.py',silent=False) #From instance folder


db = SQLAlchemy(app)
mail=Mail(app)
migrate=Migrate(app,db)

from conferenceapp2.myroutes import adminroutes, userroutes
from conferenceapp2 import forms, mymodels
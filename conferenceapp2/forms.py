from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length

#This class generates fields for contact form
class LoginForm(FlaskForm):
    username = StringField("Your email:", validators=[DataRequired(), Email()])
    pwd = PasswordField("Enter Password:")
    loginbtn = SubmitField("Login")

class Contact(FlaskForm):
    fullname = StringField("Full name:", validators=[DataRequired()])
    email = StringField("Email:", validators=[Email()])
    msg = TextAreaField("Message", validators=[DataRequired()])
    sendbtn = SubmitField("Send Message")

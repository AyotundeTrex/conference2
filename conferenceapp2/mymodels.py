import datetime
from conferenceapp2 import db

#A helpr table to handle the relationship between user and breakout
user_sessions = db.Table('user_breakout',
db.Column('user_id', db.Integer(), db.ForeignKey('user.user_id')),
db.Column('breakout_id', db.Integer(), db.ForeignKey('breakout.break_id'))
)

class Myorder(db.Model):
    order_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    order_userid = db.Column(db.Integer(), db.ForeignKey("user.user_id"))
    order_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow())
   
    #set up relationship with user
    user = db.relationship('User', backref='myorders')#use backref so that we dont have to explicitly set relationship on user table

class OrderDetails(db.Model):
    __tablename__="order_details"
    det_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    det_orderid = db.Column(db.Integer(), db.ForeignKey("myorder.order_id"))
    det_breakid = db.Column(db.Integer(), db.ForeignKey("breakout.break_id"))
    det_breakamt = db.Column(db.Float())
    det_qty = db.Column(db.Integer())
    #set up relationship with myorder table
    d_order = db.relationship('Myorder', backref='order_deets')#use backref 

class Payment(db.Model):
    pay_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    pay_userid = db.Column(db.Integer(), db.ForeignKey("user.user_id"))
    pay_orderid = db.Column(db.Integer(), db.ForeignKey("myorder.order_id"))
    pay_ref = db.Column(db.String(255), nullable=False)
    pay_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow())
    pay_status=db.Column(db.Enum("pending","paid","failed"), default="pending")
    pay_amt=db.Column(db.Float())
    pay_response=db.Column(db.Text(), nullable=True)
    #set up relationship with myorder
    order_paid4 = db.relationship('Myorder', backref='pay_deets')#use backref so that we dont have to explicitly set relationship on myorder table
    user_who_paid = db.relationship('User', backref='user_payments')#available as user_payments on User table



class User(db.Model): 
    user_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    user_email = db.Column(db.String(255), nullable=False)
    user_pass = db.Column(db.String(255), nullable=False)
    user_fname = db.Column(db.String(255), nullable=False)
    user_lname = db.Column(db.String(255), nullable=False)
    user_address = db.Column(db.Text(), nullable=True)
    user_phone = db.Column(db.String(255), nullable=True)
    user_reg = db.Column(db.DateTime(), default=datetime.datetime.utcnow())

    #create the foreign keys
    user_skillid = db.Column(db.Integer(), db.ForeignKey("skill.skill_id")) 
    user_stateid = db.Column(db.Integer(), db.ForeignKey("state.state_id")) 

    #setup the relationships         
    myskillobj = db.relationship('Skill', back_populates ='users')
    mystateobj = db.relationship('State', back_populates='stateusers')
    userposts = db.relationship('Posts', back_populates='duser')
    user_comments = db.relationship('Comments', back_populates ='userdeets')

    #setup relationship between User and Breakout, then specify that we are using an association table
    mybreakouts = db.relationship('Breakout', secondary=user_sessions, back_populates='regusers')


class Skill(db.Model): 
    skill_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    skill_name = db.Column(db.String(255), nullable=False)
    #set up the relationship
    users = db.relationship('User', back_populates ='myskillobj')
    breakouts = db.relationship('Breakout', back_populates ='skillobj')

class State(db.Model): 
    state_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    state_name = db.Column(db.String(255), nullable=False)
    #set up the relationship
    stateusers = db.relationship('User', back_populates ='mystateobj')

class Breakout(db.Model): 
    break_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    break_title = db.Column(db.String(255), nullable=False)
    break_picture = db.Column(db.String(255), nullable=True)
    break_amt = db.Column(db.Float(), nullable=True)
    #create the foreign key
    break_skillid = db.Column(db.Integer(), db.ForeignKey("skill.skill_id"))
    
    #set up the relationship
    skillobj = db.relationship('Skill', back_populates ='breakouts')

    #setup relationship between User and Breakout, then specify that we are using an association table
    regusers = db.relationship('User', secondary=user_sessions, back_populates='mybreakouts')

class Admin(db.Model): 
    admin_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    admin_username = db.Column(db.String(255), nullable=False)
    admin_password = db.Column(db.String(255), nullable=False)
    admin_lastlogin = db.Column(db.DateTime(), onupdate=datetime.datetime.utcnow())
    
class Contactus(db.Model):
    contact_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    contact_name = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_message = db.Column(db.String(255), nullable=True)

class Posts(db.Model):
    p_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    p_title = db.Column(db.String(255), nullable=False)
    p_desc = db.Column(db.Text(), nullable=False)
    p_userid = db.Column(db.Integer(), db.ForeignKey("user.user_id"))
    p_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow())

    #Create the relationship
    duser = db.relationship('User', back_populates ='userposts')
    post_comments = db.relationship('Comments', back_populates ='postdeets')


class Comments(db.Model):
    __tablename__ = 'comments'
    c_id = db.Column(db.Integer(), primary_key=True,autoincrement=True)
    c_userid = db.Column(db.Integer(), db.ForeignKey("user.user_id"))
    c_postid = db.Column(db.Integer(), db.ForeignKey("posts.p_id"))
    c_comment = db.Column(db.Text(255))
    c_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow())
    
    #Create the relationship
    userdeets = db.relationship('User', back_populates ='user_comments')
    postdeets = db.relationship('Posts', back_populates ='post_comments')

class Tracks(db.Model):
    track_id= db.Column(db.Integer(), primary_key=True,autoincrement=True)
    track_image = db.Column(db.String(255), nullable=False)
    track_title = db.Column(db.String(255), nullable=False)
    track_artist_name = db.Column(db.String(255), nullable=False)
    track_mp3= db.Column(db.String(255), nullable=False)
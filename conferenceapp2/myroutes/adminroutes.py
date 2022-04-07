"""This file contains all the routes, it is like a controller that determines what happens when a user visits our app"""
import math, random, os

from flask import render_template, request, redirect, url_for, flash, make_response, session 

from werkzeug.security import generate_password_hash, check_password_hash

from conferenceapp2 import app,db
from conferenceapp2.mymodels import User, State, Skill, Breakout, Admin
#from conferenceapp2.forms import LoginForm

@app.route("/admin/login")
def adminlogin():
    return render_template("admin/login.html")

@app.route("/admin/signup", methods=['GET','POST'])
def admin_signup():
    if request.method == 'GET':
        return render_template("admin/signup.html")
    else:
        #Retrieve form data
        username = request.form.get('username')
        pwd1 = request.form.get('password')
        pwd2 = request.form.get('password2')

        if pwd1 == pwd2:
            formated = generate_password_hash(pwd1)
            ad = Admin(admin_username=username,admin_password=formated)
            db.session.add(ad)
            db.session.commit()
            flash("New admin signed up")
            return redirect("/admin/login")
        else:
            flash("The two passwords do not match")
            return redirect("/admin/signup")

@app.route("/admin/reg")
def registrations():
    #Method 1
    users = db.session.query(User,State,Skill).join(State).join(Skill).filter(Skill.skill_id==1).all()
    #Explicitly setting the join clause
    #users = User.query.join(State,User.user_stateid==State.state_id).add_columns(State).all()
    #Outer join
    #users = User.query.outerjoin(State,User.user_stateid==State.state_id).add_columns(State).all()
    #Order by
    #users = User.query.outerjoin(State,User.user_stateid==State.state_id).add_columns(State).order_by(User.user_fname).all()
    #filter and 
    #users = User.query.outerjoin(State,User.user_stateid==State.state_id).add_columns(State).filter(User.user_fname.like(%a%)).order_by(User.user_fname).all()
    #Method 2
    #users = User.query.join(State).join(Skill).add_columns(State,Skill).all()
    return render_template("admin/allusers.html", users=users)

# @app.route("/admin/submit/login", methods=['POST'])
# def submit_adminlogin():
#     username = request.form.get('username')
#     pwd = request.form.get('password')

#     if '' not in request.form.values():
#         deets = Admin.query.filter(Admin.admin_username ==username, Admin.admin_password ==pwd).first()
     
#         if deets:
#             id = deets.admin_id
#             session['admin'] = id
#             return redirect('/admin/home')

#         else:
#             #Keep a failed message in flash, then redirect to login page
#             flash('Invalid Credentials')
#             return redirect('/admin/login')
#     else:
#         flash("Fields must be completed")
#         return redirect("/admin/login")

@app.route("/admin/submit/login", methods=['POST'])
def submit_adminlogin():
    username = request.form.get('username')
    pwd = request.form.get('password')

    if '' not in request.form.values():
        #Query the admin with only the username
        deets = Admin.query.filter(Admin.admin_username ==username).first()
        #get the password hash
        formated_pwd = deets.admin_password
        #Check the password hash from db with password from frontend
        check = check_password_hash(formated_pwd, pwd)
        #if the check is true then the passwords match
        if check:
            id = deets.admin_id
            session['admin'] = id
            return redirect('/admin/home')
        else:
            #Keep a failed message in flash, then redirect to login page
            flash('Invalid Credentials')
            return redirect(url_for('adminlogin'))
    else:
        flash("Fields must be completed")
        return redirect("/admin/login")

@app.route('/admin/logout')
def admin_logout():
    #Remove the admin from the session dictionary
    session.pop('admin')
    #redirect them to the login page
    return redirect('/admin/login')

@app.route("/admin/breakout")
def breakout():
    admin = session.get('admin')
    if admin == None:
        return render_template('admin/login.html')
    else:
        break_deets = Breakout.query.all()
        return render_template('admin/breakout.html', break_deets=break_deets)

@app.route('/admin/addbreakout', methods=['GET','POST'])
def addbreakout():
    admin = session.get('admin')
    if admin == None:
        return render_template('admin/login.html')
    else:
        if request.method =='GET':
            skills = Skill.query.all()
            return render_template('admin/addbreakout.html', skills=skills)
        else:
            #Retrieve form data (request.form....)
            title = request.form.get('title')
            level = request.form.get('skill')
            #request file which is an object
            pic_object = request.files.get('image')
            original_file =  pic_object.filename

            if title =='' or level =='':
                flash("Title and Level cannot be empty")
                return redirect('/admin/addbreakout')

            if original_file !='': #check if file is not empty
                extension = os.path.splitext(original_file)
                if extension[1].lower() in ['.jpg','.png']:
                    fn = math.ceil(random.random() * 100000000)  
                    save_as = str(fn) + extension[1] 
                    pic_object.save(f"conferenceapp/static/assets/img/{save_as}")
                    #insert other details into db
                    b = Breakout(break_title=title,break_picture=save_as,break_skillid=level)
                    db.session.add(b)
                    db.session.commit()            
                    return redirect("/admin/breakout")
                else:
                    flash('File Not Allowed')
                    return redirect("/admin/addbreakout")

            else:
                save_as =""
                b = Breakout(break_title=title,break_picture=save_as,break_skillid=level)
                db.session.add(b)
                db.session.commit() 
                return redirect("/admin/breakout")  

@app.route("/admin/breakout/delete/<id>")
def breakout_delete(id):
    admin = session.get('admin')
    if admin == None:
        return render_template('admin/login.html')
    else:
        x = db.session.query(Breakout).get(id)
        db.session.delete(x)
        db.session.commit()
        flash(f"Breakout Session {id} deleted")
        return redirect("/admin/breakout")

@app.route("/admin/home")
def admin_home():
    admin = session.get('admin')
    if admin == None:
        return render_template('admin/login.html')
    else:
        return render_template("admin/index.html")

@app.route("/admin/upload", methods=['POST','GET'])
def admin_upload():
    admin = session.get('admin')
    if admin == None:
        return render_template('admin/login.html')
    else:
        if request.method == 'GET':
            return render_template("admin/test.html")
        else:
            file = request.files.get('image')
            original_name = file.filename
            #generate a random number for the filename
            fn = math.ceil(random.random() * 10000000)
            #Get the extension
            #ext = original_name.split(".")
            #save_as = str(fn) + "." + ext[-1]

            #A better way to get file extension
            ext = os.path.splitext(original_name)
            save_as = str(fn) + ext[1]

            allowed = ['.jpg','.png','.gif']
            if ext[1].lower() in allowed:
                file.save(f"conferenceapp/static/assets/img/{save_as}")
                return f"Submitted and saved as {save_as}"
            else:
                return "File type not allowed"

"""This file contains all the routes, it is like a controller that determines what happens when a user visits our app"""
import json
import os, math
from random import random
import requests
from flask import render_template, request, redirect, url_for, flash, make_response, session
from sqlalchemy import desc
from conferenceapp2 import app,db
from conferenceapp2.mymodels import Payment, Posts, Tracks, User, State, Skill, Breakout,user_sessions, Contactus, Comments, Myorder, OrderDetails
from conferenceapp2.forms import LoginForm,Contact
from conferenceapp2 import Message,mail



@app.route("/")
def home():
    login=LoginForm()
    user_msg = Contact()
    id = session.get('loggedin')
    userdeets = User.query.get(id)
    break_deets = Breakout.query.all()

    try:
        #Connect to API
        response = requests.get('http://127.0.0.1:8080/api/v1.0/listall')
        #retrieve the json in the request
        hostel_json = response.json() #json.loads(response.text)
        status = hostel_json.get('status') #To pick the status
    except:
        hostel_json = {}

    #Connect if there is authentication
    #response = requests.get('http://127.0.0.1:8080/api/v1.0/listall', auth=('admin','1234'))

    #Pass it to the template as hostel_json=hostel_json
    return render_template("user/index.html", login=login, user_msg=user_msg, userdeets=userdeets, break_deets=break_deets, hostel_json=hostel_json)

@app.route("/user/breakout")
def all_breakout():
    
    #get the user id to 
    loggedin = session.get('loggedin')
    if loggedin == None:
        return redirect("/")
    else:
        #use the id to query the user table
        userdeets = db.session.query(User).get(loggedin)
        user_skill = userdeets.user_skillid
        #Query the breakout table filter it by providing the user with sessions for their skill
        user_sessions = Breakout.query.filter(Breakout.break_skillid ==user_skill).all()
        user_msg = Contact()
        return render_template("user/paybreakout.html", user_sessions=user_sessions, userdeets=userdeets, user_msg=user_msg)

@app.route("/user/pay/breakout", methods=['POST','GET'])
def pay_breakout():
    #retrieve the form data
    user_id = session.get('loggedin')
    if user_id == None:
        return redirect("/")
    if request.method == 'POST':
        #retrieve form data, breakout ids
        bid = request.form.getlist('bid')
        #insert new recd into myorder,
        user_order = Myorder(order_userid=user_id)
        db.session.add(user_order)
        db.session.commit()
        orderid = user_order.order_id
        #Generate a random number as transaction ref
        ref = int(random() * 10000000)
        session['refno'] = ref
         #loop over the selected breakout ids and insert into
        #order_details, 
        totalamt = 0
        #Loop through the breakout id and insert into the order_details
        for i in bid:
            breakdeets = Breakout.query.get(i)
            break_amt = breakdeets.break_amt
            totalamt = totalamt + break_amt
            order_deets = OrderDetails(det_orderid=orderid, det_breakid = i)
            db.session.add(order_deets)
        db.session.commit()
        user_pay = Payment(pay_userid=user_id, pay_orderid=orderid, pay_ref=ref, pay_amt=totalamt)
        db.session.add(user_pay)
        db.session.commit()
        return redirect("/user/confirm_breakout")
    else:
        return redirect("/userhome")

@app.route("/user/confirm_breakout", methods=['POST','GET'])
def confirm_break():
    loggedin = session.get('loggedin')
    ref = session.get('refno')
    if loggedin == None or ref == None:
        return redirect("/")
    userdeets = User.query.get(loggedin) 
    deets = Payment.query.filter(Payment.pay_ref==ref).first()
    if request.method == 'GET':
        contactform = Contact()
        return render_template("user/show_breakout_html.html", deets = deets,userdeets=userdeets,contactform=contactform)
    else:
        url = "https://api.paystack.co/transaction/initialize"   
        data = {"email":userdeets.user_email,"amount":deets.pay_amt*100, "reference":deets.pay_ref}
        headers = {"Content-Type": "application/json", "Authorization":"Bearer sk_test_9d303419a00f4f7bc2e0f192c3271ad8b1c38462"}

        response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=json.dumps(data))
        rspjson = json.loads(response.text) 
        if rspjson.get('status') == True:
            authurl = rspjson['data']['authorization_url']
            return redirect(authurl)
        else:
            return "Please try again"
        #return render_template("user/demo.html",response=rspjson)
        #return render_template("user/show_breakout_html.html", deets=deets)

#This  is the landing page for paystack, you are to connect to paystack and check the actual details of the transaction, then update yopur database
@app.route("/user/payverify")
def paystack():
    reference = request.args.get('reference')
    ref = session.get('refno')
    #update our database 
    headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_here"}

    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    rsp =response.json()#in json format
    if rsp['data']['status'] =='success':
        amt = rsp['data']['amount']
        ipaddress = rsp['data']['ip_address']
        p = Payment.query.filter(Payment.pay_ref==ref).first()
        p.pay_status = 'paid'
        db.session.add(p)
        db.session.commit()
        return "Payment Was Successful"  #update database and redirect them to the feedback page
    else:
        p = Payment.query.filter(Payment.pay_ref==ref).first()
        p.pay_status = 'failed'
        db.session.add(p)
        db.session.commit()
        return "Payment Failed"  
    #return render_template("user/demo.html", response=rsp)


@app.route("/donate", methods=['GET','POST'])
def donation():
    if request.method == 'GET':
        return render_template('user/donate.html')
    else:
        #Retrieve the form data
        fname = request.form.get('fname')
        email =request.form.get('email')
        amt = request.form.get('amt')
        #Generate a random number as transaction ref
        ref = int(random() * 1000000)
        #keep ref in session
        session['refno'] = ref
        #Insert into the database
        db.session.execute(f"INSERT INTO donation SET fullname='{fname}', email='{email}', amt='{amt}', status='pending', ref='{ref}'")
        db.session.commit()
        return redirect("/confirmpay")

@app.route('/confirmpay')
def confirmpay():
    ref = session.get('refno')
    #Run query to retrieve details of this donation
    qry = db.session.execute(f"SELECT * FROM donation WHERE ref={ref}")
    data = qry.fetchone()
    return render_template("user/payconfirm.html", data=data)

@app.route("/user/message", methods=['POST','GET'])
def submit_msg():
    user_msg = Contact()
    # fname = user_msg.fullname.data
    # email = user_msg.email.data
    # msg = user_msg.msg.data
    fname = request.args.get('fullname')
    email = request.args.get('email')
    msg = request.args.get('msg')

    #if user_msg.validate_on_submit():
    cm = Contactus(contact_name=fname, contact_email=email, contact_message=msg)
    db.session.add(cm)
    db.session.commit()
    cid = cm.contact_id
    if cid:
        return json.dumps({"id":cid, "msg":"Message Sent"})
    else:
        return "Sorry, please try again"
    # else:
    #     return "Please complete all fields"


@app.route("/user/login", methods=['POST'])
def submit_login():
    login = LoginForm()
    #retrieve form data
    username = request.form.get('username')
    pwd = login.pwd.data
    #validate
    if login.validate_on_submit():
        #deets = User.query.filter(User.user_email ==username).filter(User.user_pass ==pwd).all()
        deets = User.query.filter(User.user_email ==username, User.user_pass ==pwd).first()
     
        if deets:
            #Retrieve the user_id and then keep in session
            id = deets.user_id
            session['loggedin'] = id
            #redirect him/her to userhome
            return redirect('/userhome')
        else:
            #Keep a failed message in flash, then redirect to login page
            flash('Invalid Credentials')
            return redirect('/')
    else:
        return render_template("user/index.html", login=login)

@app.route("/user/editprofile")
def edit_profile():
    user_msg = Contact()
    loggedin = session.get('loggedin')
    if loggedin == None:
        return redirect("/")
    else:
        userdeets = db.session.query(User).get(loggedin)
        all_levels = Skill.query.all()
        all_states = State.query.all()
        return render_template("user/profile.html", userdeets=userdeets, all_levels=all_levels, all_states=all_states, user_msg=user_msg)

# @app.route("/user/update/<id>", methods=['POST','GET'])
# def user_update(id):
#     loggedin = session.get("loggedin")
#     if loggedin == None:
#         return redirect("/")
#     if request.method == "GET":
#         return redirect(url_for('userhome'))

#     #Retrieve the form data
#     fname = request.form.get('fname')
#     lname = request.form.get('lname')
#     skill_level = request.form.get('skill')
#     phone = request.form.get('phone')
#     address = request.form.get('address')
#     state = request.form.get('state')

#     if int(loggedin) == int(id):
#         user = User.query.get(id)
#         #Change the fields
#         user.user_fname = fname
#         user.user_lname = lname
#         user.user_phone= phone
#         user.user_address = address
#         user.user_skillid = skill_level
#         user.user_stateid = state
#         db.session.commit()
#         flash("Your profile has been updated")
#     return redirect('/userhome')

@app.route("/user/update", methods=['POST','GET'])
def user_update():
    loggedin = session.get("loggedin")
    if loggedin == None:
        return redirect("/")
    if request.method == "GET":
        return redirect(url_for('userhome'))

    user = User.query.get(loggedin)
    #Change the fields
    user.user_fname = request.form.get('fname')
    user.user_lname = request.form.get('lname')
    user.user_phone= request.form.get('phone')
    user.user_address = request.form.get('address')
    user.user_skillid = request.form.get('skill')
    user.user_stateid = request.form.get('state')
    db.session.commit()
    flash("Your profile has been updated")
    return redirect('/userhome')


@app.route("/user/regbreakout", methods=["POST"])
def reg_breakout():
    #getlist() to retrieve multiple form elements with same name
    bid = request.form.getlist('bid')
    #Get the user id from the logged in session
    loggedin = session.get("loggedin")
    #ORM method we instantied an user object by querying the user table with the loged in ID
    user = User.query.get(loggedin)
    #Delete all registered sessions before inserting and signing up
    db.session.execute(f"DELETE FROM user_breakout WHERE user_id='{loggedin}'")
    db.session.commit()
    #Loop through the form data list and insert into the association table
    for i in bid:
        #METHOD 1 - SQL Alcheny Core
        # statement = user_sessions.insert().values(user_id=loggedin, breakout_id=i)
        # db.session.execute(statement)
        # db.session.commit()
        #METHOD 2 - Using SQLAlchemy ORM
        #We instantiated a Breakout object with the form data bid(i)
        item = Breakout.query.get(i)
        #Then used the association relationship in the User table and appended it to the table
        user.mybreakouts.append(item)
        db.session.commit()
    return redirect("/user/breakout")

@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == 'GET':
        user_msg = Contact()
        login=LoginForm()
        skills = Skill.query.all()
        states = State.query.all()
        return render_template("user/register.html", skills=skills, states=states, user_msg=user_msg, login=login)
    else:
        email = request.form.get('email')
        pwd1 = request.form.get('pwd1')
        pwd2 = request.form.get('pwd2')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        state = request.form.get('state')
        skill = request.form.get('skill')

        if '' in request.form.values():
            flash('Fields must be completed')
            return redirect('/register')
        elif pwd1 != pwd2:
            flash('Passwords must match')
            return redirect('/register')
        else:
            #Instantiante an object and give it parameters with values of the form in the table columns
            u = User(user_email=email, user_pass=pwd1, user_fname=fname, user_lname=lname, user_stateid=state, user_skillid=skill)
            #Insert into the database
            db.session.add(u)
            db.session.commit()
            id = u.user_id
            #If successfully registered create a session with their id and redirect them to their dashboard
            session['loggedin'] = id
            return redirect('/userhome')

@app.route('/userhome')
def userhome():
    user_msg = Contact()
    #Get the userid
    loggedin = session.get('loggedin')
    if loggedin == None:
        return redirect('/')
    else:
        # Use the id to get the user on the database
        userdeets = db.session.query(User).get(loggedin)
        #This returns an object which we pass into the template to get the user details
        return render_template('user/userhome.html', loggedin=loggedin, userdeets=userdeets, user_msg=user_msg)

@app.route('/logout')
def logout():
    #Remove the logged id from the session dictionary
    session.pop('loggedin')
    #redirect them tothe home page
    return redirect('/')

@app.route("/user/breakout")
def user_breakout():
    user_msg = Contact()
    #get the user id to 
    loggedin = session.get('loggedin')
    if loggedin == None:
        return redirect("/")
    else:
        #use the id to query the user table
        userdeets = db.session.query(User).get(loggedin)
        user_skill = userdeets.user_skillid
        #Query the breakout table filter it by providing the user with sessions for their skill
        user_sessions = Breakout.query.filter(Breakout.break_skillid ==user_skill).all()
        return render_template("user/breakout.html", user_sessions=user_sessions, userdeets=userdeets, user_msg=user_msg)

@app.route("/user/breakout/<id>")
def break_details(id):
    deets = db.session.query(Breakout).get(id)
    return render_template("user/demo.html", demo=deets)

@app.route("/demo/available")
def available():
    return render_template("user/username.html")

@app.route("/check/result")
def check_username():
    user = request.args.get("username")
    #query the user table
    deets = User.query.filter(User.user_email==user).first()
    if deets:
        return "Username is taken"
    else:
        return "Username is available"

@app.route("/check/lga")
def check_lga():
    #Fetch all the states to pass into the template
    states = State.query.all()
    return render_template("user/load_lga.html", states=states)

@app.route('/demo/lga', methods=['POST'])
def show_lga():
    state = request.form.get('stateid')
    #TO DO: write a query that wll fetch from LGA table where state_id =state
    res = db.session.execute(f"SELECT * FROM lga WHERE state_id={state}")
    results = res.fetchmany(20)

    select_html = "<select>"
    for x,y,z in results:
        select_html = select_html + f"<option value='{x}'>{z}</option>"
    
    select_html = select_html + "</select>"

    return select_html


@app.route("/user/discussion")
def discussion():
    contactform = Contactus()
    user_msg = Contact()
    loggedin = session.get('loggedin')
    if loggedin == None:
        return redirect("/")
    else:
        userdeets = User.query.get(loggedin)
        #retrieve all the posts and display it in the temlplate
        posts = Posts.query.all()
        return render_template("user/discussions.html", contactform=contactform, userdeets=userdeets, user_msg=user_msg, posts=posts)

@app.route("/posts/details/<id>")
def post_details(id):
    loggedin = session.get('loggedin')
    if loggedin == None:
        return redirect("/")
    else:
        #use this form
        postdeets = Posts.query.get_or_404(id)
        #Retrieve the comments on the order of latest
        commentdeets = db.session.query(Comments).filter(Comments.c_postid==id).order_by(desc(Comments.c_date)).all()
        return render_template("user/comments.html", posts=postdeets, commentdeets=commentdeets)

@app.route("/post/comment", methods=["POST"])
def post_comment():
    #Retrieve the data
    loggedin = session.get("loggedin", 0)
    postid = request.form.get('postid')
    comment = request.form.get("comment")
    #Insert into the association table
    #METHOD 1
    # c = Comments()
    # db.session.add(c)
    # c.c_userid = loggedin
    # c.c_postid = postid
    # c.c_comment = comment
    # db.session.commit()
    #METHOD 2
    # c = Comments(c_userid=loggedin, c_postid=postid, c_comment=comment)
    # db.session.add(c)
    # db.session.commit()
    #METHOD 3
    user = User.query.get(loggedin)
    dpost = Posts.query.get(postid)
    c = Comments()
    db.session.add(c)
    user.user_comments.append(c)
    dpost.post_comments.append(c)
    c.c_comment = comment
    db.session.commit()
    return comment
@app.route("/showmusicform")
def show_form():
    return render_template("user/music.html")

@app.route('/submittrack',methods=['POST'])
def submit_track():
    trackartistname=request.form.get('trackartistname')
    tracktitle=request.form.get('tracktitle')
    trackimg_object = request.files.get('trackimage')
    track_object = request.files.get('track')
    originalimg_file =  trackimg_object.filename
    originaltrack_file = track_object.filename
    ext_trackimg = os.path.splitext(originalimg_file)
    ext_track = os.path.splitext(originaltrack_file)
    if ext_trackimg[1].lower() in ['.jpg','.png'] and ext_track[1].lower() in ['.mp3']:
        trackfn = math.ceil(random() * 100000000)  
        trackimgfn = math.ceil(random() * 100000000)
        savetrack_as = str(trackfn) + ext_track[1] 
        savetrkimg_as = str(trackimgfn) + ext_trackimg[1]
        trackimg_object.save(f"conferenceapp2/static/assets/trackimg/{savetrkimg_as}")
        track_object.save(f"conferenceapp2/static/assets/tracks/{savetrack_as}")
        #insert other details into db
        b = Tracks(track_image=savetrkimg_as, track_title=tracktitle, track_artist_name=trackartistname, track_mp3=savetrack_as)
        db.session.add(b)
        db.session.commit()            
        return "Added"
    else:
        flash('File Not Allowed')
        return "Failed"

@app.route("/allmusic")
def show_allmusic():
    allmusic = Tracks.query.all()
    return render_template("user/allmusic.html", allmusic=allmusic)



@app.route("/sendemail")
def sendmail():
    subject = "Automated Email"
    sender=["elizzalexa442@gmail.com"]
    recipient = ["deanaosendorfzbi52@gmail.com"]
    # try:
        # msg=Message(subject=subject,sender=sender,recipients=recipient,body="<b>This is a sample email sent from Python App</>")
        #method2
    msg= Message()
    msg.subject = subject
    msg.sender=sender
    msg.body="Test Message Again"
    msg.recipients=recipient
    #sending html
    htmlstr = "<div><h1 style='color:red'> Thank you for signing up</h1><p>You have subscribed...<br>Signed by Admin</p><img src='https://thumbs.dreamstime.com/z/cup-cofee-top-heart-117247683.jpg' width='100px'></div>"
    msg.html = htmlstr
    with app.open_resource("mywebpage.pdf") as fp:
        #what you wan to save it as when it gets there
        msg.attach('dash.pdf','application/pdf',fp.read())

    mail.send(msg)
    return "mail sent"
    # except:
    #     return "Connection refused" 
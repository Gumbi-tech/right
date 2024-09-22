from flask import Flask, url_for, redirect, render_template, request, session, flash, Response, jsonify
from datetime import timedelta
import pandas as pd
import pandasql as ps
from geopy.distance import great_circle as GRC
from sqlalchemy import func, text
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = "Dalubuhle"
app.permanent_session_lifetime = timedelta(hours=1)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rapidrescuew.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

db = SQLAlchemy(app)

# user class


class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(255), nullable=False, default='Patient')
    address = db.Column(db.String(255))

    def __repr__(self):
        return f'<Users: username={self.username}, email={self.email}, acctype={self.acctype}>'


class RequestedAmbulance(db.Model):
    request_id = db.Column(db.Integer, primary_key=True)
    pickup_location = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    emergency_type = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False, default='Pending')
    request_time = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    ambulance_id = db.Column(
        db.Integer, db.ForeignKey('ambulance.ambulance_id'))

    def __repr__(self):
        return f'<Users: requests_id={self.request_id}, location={self.pickup_location}>'


class Ambulance(db.Model):
    ambulance_id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(255), nullable=False)
    equipment_level = db.Column(db.String(255), nullable=False)
    hospital = db.Column(db.String(255), nullable=False)
    current_status = db.Column(db.String(255), nullable=False)




class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    sent_at = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __repr__(self):
        return f'<Users: username={self.username}, subject={self.subject}, sent={self.sent_at}>'


#------------------dao
def addRow(row):
    """
        =================================
        =================================
        name of file -- dao
        add Row method created by use
        --you add the row as argument(object/table as class)
    """  
    db.session.add(row)
    db.session.commit()
    
    
def FilterRow(tableName , locatingColumn, filterValue):
    """
        =================================
        =================================
        name of file -- dao
        -get A Row the data from the table method created by use
        -this method will filter the tables
    """       
    #changing the string to a class
    opp = eval(tableName)
     
    f = '{} = {}'.format(locatingColumn, filterValue)
  
    obj = opp.query.filter(text(f))
    return obj    
    
    
    
 
   
def deleteRow(tableName , locatingColumn, id):
    """
        =================================
        =================================
        name of file -- dao
        delete method created by use
    """    
    #changing the string to a class
    opp = eval(tableName)
     
    f = '{} = {}'.format(locatingColumn, id)
  
    obj = opp.query.filter(text(f)).one()
    if obj:
        db.session.delete(obj)
        db.session.commit() 
 
 
 
 
    
    
    
    
    
#-------------------end dao








@app.route("/")
def home():
    if "patient" in session:
        name = session["patient"]
        return render_template("index.html")
    return render_template("index.html")


@app.route("/request")
def rider():
    if "patient" in session:
        name = session["patient"]
        return render_template("request.html", name=name)
    else:
        return redirect("/")

# register


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["firstname"]
        lastname = request.form["lastname"]
        number = request.form["number"]
        email = request.form["email"]
        password = request.form["password"]
        acctype = request.form["acctypes"]
        location = request.form["address"]

        #  check if email exists
        isEmail = Users.query.filter_by(email=email).first()
        #  if email exists

        if isEmail:
            flash("Account already exists!", category='error')
            return redirect(url_for('login'))
        else:
            user = Users(username=name, lastname=lastname, phone_number=number, email=email,
                         password=password, account_type=acctype, address=location)
            db.session.add(user)
            db.session.commit()
            if acctype == 'Patient':
                session["patient"] = name
                return redirect(url_for("requestA"))
            elif acctype == 'Admin':
                session["admin"] = name
                return redirect(url_for("admin"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    mssg=None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('type')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', 'success')
                login_user(user, remember=True)
                if user_type=="User":
                    return redirect(url_for('views.makeRequest'))
                elif user_type=="Admin":
                    return redirect(url_for('views.admin'))
                elif user_type=="Driver":
                    return redirect(url_for('views.driver'))
                else:
                    return redirect(url_for('views.emt'))
            else:
                mssg = 'error'
        else:
            pass

    # return render_template("login.html",mssg=mssg, user=current_user)
    return render_template("login.html",mssg=mssg)
@app.route('/logout')
def logout():
    # logout_user()
    return redirect(url_for('auth.login'))

@app.route('/sign-up', methods=["GET","POST"])
def sign_up():
  if request.method == 'POST':
      email = request.form.get('email')
      name = request.form.get('username')
      phone= request.form.get('number')
      password1 = request.form.get('password')
      password2 = request.form.get('cpassword')
      email = request.form.get('email')
      dob = request.form.get('dob')
      address = request.form.get('address')
      user_type = request.form.get('type')

      user = User.query.filter_by(email=email).first()
      if user:
          flash('Email already exists.', 'error')
          return redirect(url_for('auth.sign-up'))
      elif len(email) < 4:
          flash('Email must be greater than 3 characters.', 'error')
      elif len(name) < 2:
          flash('First name must be greater than 1 character.', 'error')
      elif password1 != password2:
          flash('Passwords don\'t match.', 'error')
      elif len(password1) < 7:
          flash('Password must be at least 7 characters.', 'error')
      else:
          new_user = User(email=email, user_name=name, phone=phone, address=address, dob=dob, userType=user_type, password=generate_password_hash(
              password1, method='sha256'))
          db.session.add(new_user)
          db.session.commit()
          login_user(new_user, remember=True)
          flash('Account created successfully!', 'success')
          return redirect(url_for('auth.login'))

  return render_template("register.html")
  return render_template("register.html", user=current_user)


# request ambulance
@app.route("/request")
def requestA():
    if "patient" in session:
        name = session["patient"]
        return render_template("request.html", name=name)
    else:
        return redirect("/")

# request ambulance


@app.route("/request-ambulance", methods=["GET", "POST"])
def requestAmbulance():
    if request.method == "POST":
        # Reading map CSV and getting locations
        df = pd.read_csv('sz.csv')
        City = request.form["pickup"]
        Hospital = request.form["hospital"]
        emergency_type = request.form["type"]
        locationPoints = ps.sqldf(
            f'select * from df where Hospital=="{Hospital}"')
        lat = locationPoints['Latitude'].iloc[0]
        lng = locationPoints['Longitude'].iloc[0]
        latCity = request.form["latitude"]
        lngCity = request.form["longitude"]

        location = (latCity, lngCity)
        destination = (lat, lng)

        km = round(GRC(location, destination).km, 1)
        time = round(km/50, 1)
        time2 = time * 60
        atime = f'{int(time2 / 60)}hrs {round(time2 % 60)} mins'

        session['arrivalTime'] = atime
        session['hospital'] = Hospital
        session['emergency_type'] = emergency_type
        name = session["patient"]
        user_id = Users.query.filter_by(username=name).first()

        # Create new ambulance request
        new_request = RequestedAmbulance(
            pickup_location=City,
            destination=Hospital,
            emergency_type=emergency_type,
            user_id=user_id.user_id,
            status="Pending"
        )
        db.session.add(new_request)
        db.session.commit()

        # Store the request ID in session
        session['request_id'] = new_request.request_id
        return redirect(url_for("loading_screen"))

    return render_template("request.html")


@app.route("/loading")
def loading_screen():
    if 'request_id' in session:
        request_id = session['request_id']
        return render_template("loading.html", request_id=request_id)
    else:
        return redirect(url_for("requestAmbulance"))


@app.route("/check-status")
def check_status():
    if 'request_id' in session:
        request_id = session['request_id']
        ambulance_request = RequestedAmbulance.query.get(request_id)


        if ambulance_request:
            return jsonify(status=ambulance_request.status)
        return jsonify(status="not found"), 404
    else:
        return jsonify(status="no request found"), 404


@app.route("/dispatch", methods=["POST"])
def dispatch_ambulance():
    if 'request_id' in session:
        request_id = session['request_id']
        ambulance_request = RequestedAmbulance.query.get(request_id)

        if ambulance_request:
            available_ambulance = Ambulance.query.filter_by(
                current_status="Available").first()

            if available_ambulance:
                # Assign the ambulance and update statuses
                ambulance_request.ambulance_id = available_ambulance.ambulance_id
                ambulance_request.status = "On Call"
                available_ambulance.current_status = "On Call"

                db.session.commit()

                return jsonify({'message': 'Ambulance dispatched successfully!'})
            else:
                return jsonify({'message': 'No available ambulance.'}), 404
        else:
            return jsonify({'message': 'Request not found.'}), 404
    return jsonify({'message': 'No request ID in session.'}), 400

# confirm ambulance details


@app.route("/assign-ambulance/<int:request_id>/<int:ambulance_id>", methods=["POST"])
def assign_ambulance(request_id, ambulance_id):
    # Find the ambulance and request in the database
    ambulance = Ambulance.query.get(ambulance_id)
    request = RequestedAmbulance.query.get(request_id)

    if ambulance and request:
        # Update the ambulance and request statuses
        ambulance.current_status = "On Call"
        request.status = "On Call"
        request.ambulance_id = ambulance_id

        db.session.commit()

        return jsonify({"success": True, "message": "Ambulance assigned successfully"})

    return jsonify({"success": False, "message": "Ambulance or Request not found"})


@app.route("/confirm")
def confirm():
    if 'request_id' in session:
        request_id = session['request_id']
        ambulance_request = RequestedAmbulance.query.get(request_id)

        if ambulance_request and ambulance_request.status == "On Call":
            ambulance = Ambulance.query.get(ambulance_request.ambulance_id)
            return render_template(
                "confirm.html",
                arrival_time=session['arrivalTime'],
                ambulance=ambulance,
                request=ambulance_request
            )
    return redirect(url_for("loading_screen"))


# complete ambulance duty
@app.route("/complete-request/<int:request_id>", methods=["POST"])
def complete_request(request_id):
    request = RequestedAmbulance.query.get(request_id)

    if request:
        # Set request and ambulance to completed
        request.status = "Completed"
        ambulance = Ambulance.query.get(request.ambulance_id)
        if ambulance:
            ambulance.current_status = "Available"

        db.session.commit()

        return jsonify({"success": True, "message": "Request marked as completed"})

    return jsonify({"success": False, "message": "Request not found"})


@app.route("/notify-user", methods=["POST"])
def notify_user():
    if request.methods == "POST":
        message = request.form['message']
        session['notification'] = message

        redirect(url_for("dispatch_dashboard"))
    redirect(url_for("dispatch_dashboard"))

@app.route("/dispatch-dashboard", methods=["GET", "POST"])
def dispatch_dashboard():
    # Fetch pending ambulance requests
    pending_requests = RequestedAmbulance.query.filter_by(
        status="Pending").all()

    ambulances = Ambulance.query.all()

    # Fetch available ambulances
    available_ambulances = Ambulance.query.filter_by(
        current_status="Available").all()

    # Fetch available for user
    available_ambulances_for_user = Ambulance.query.filter_by(
        hospital=session['hospital']).all()

    # Fetch dispatched ambulances (On Call)
    dispatched_ambulances = RequestedAmbulance.query.filter_by(
        status="On Call").all()

    return render_template(
        "Admin/dispatch-control.html",
        ambulances = ambulances,
        pending_requests=pending_requests,
        available_ambulances=available_ambulances,
        dispatched_ambulances=dispatched_ambulances,
        available_ambulances_for_user=available_ambulances_for_user,
        username=session['patient']
    )


@app.route("/admin-dashboard", methods=["GET", "POST"])
def adminDashboard():
           
    addRow(Ambulance(vehicle_number='34d', equipment_level="advanced", hospital='mbabane', current_status='waiting'))
    ambulances = Ambulance.query.all()
    #getting drivers
    drivers = Users.query.all()
    return render_template(
        "Admin/ambulance_table.html",
        ambulances = ambulances,
        drivers = drivers)

#adding to database users
@app.route("/addNewRecord", methods=["GET", "POST"])
def adminDashboard_AddNewRecord():
     if request.method == "POST":
       # getting input with name = fname in HTML form
       username = request.form.get("username")
       lastname = request.form.get("lastname")
       phone_number = request.form.get("phone_number")
       password = request.form.get("password")
       email = request.form.get("email")
       account_type = request.form.get("account_type")
       address = request.form.get("address")
       
     
       addRow(Users(username=username, lastname=lastname, phone_number=phone_number, password=password,
                    email=email, account_type=account_type,address=address))
       return "", 201
      
#deleting to database users
@app.route("/deleteDriver", methods=["GET", "POST"])
def adminDashboard_deleteRecord():
    
    id = request.args.get('id')
    deleteRow("Users", "user_id", id)
    
    return "", 201
      

@app.route("/add-ambulance", methods=["GET", "POST"])
def addAmbulance():
    ambulances = Ambulance.query.all()
    return render_template(
        "Admin/ambulance_management.html",
        ambulances = ambulances)


# track ambulance details
@app.route("/track")
def track():
    return render_template("tracking.html")


@app.route("/first-aid")
def firstAid():
    return render_template("firstAid.html")


@app.errorhandler(400)
def bad_upload(e):
    return render_template('Other/400.html'), 400


@app.errorhandler(404)
def page_not_found(e):
    return render_template('Other/404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('Other/500.html'), 500


# running app
if __name__ == "__main__":
    app.app_context().push()
    db.create_all()
    app.run(debug=False)

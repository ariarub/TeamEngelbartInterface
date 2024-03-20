from contextlib import nullcontext
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from datetime import datetime
from config import DB_CONFIG
import pyodbc
import os
import json
import boto3
import calendar

application = Flask(__name__)

application.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db = SQLAlchemy(application) 
bcrypt = Bcrypt(application)
application.config['SECRET_KEY'] = 'secretkey'
application.config['STATIC_FOLDER'] = 'static'

login_manager = LoginManager()
login_manager.init_app(application)
#login_manager.login_view = "login"


s3 = boto3.client('s3')

connection_string = f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"

application.config['STATIC_FOLDER'] = 'static'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), nullable=False, unique=True) 
    password = db.Column(db.String(80), nullable=False)

    def __init__(self, first_name, last_name, username, password):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password

class RegisterForm(FlaskForm):
    first_name = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder":"First name"})
    last_name = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder":"Last name"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder":"Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_name = User.query.filter_by(username=username.data).first()

        if existing_user_name:
            raise ValidationError("Username already exists.")
        
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder":"Password"})
    submit = SubmitField("Login")

def create_db():
    with application.app_context():
        db.create_all()
        print('Created database!')

@application.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
    return render_template('login.html', form=form)

@application.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@application.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)  

def test_db_connection():
    try:
        conn = pyodbc.connect(connection_string)
        conn.close()
        return True
    except Exception as e:
        print("Error connecting to database:", e)
        return False

def get_call_records():
    rows = []
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_query = 'SELECT * FROM Calls'
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        for row in rows:
            print(row) 
        cursor.close()
        conn.close()
        
    except pyodbc.Error as e:
        print("Error:", e)
    return rows

def get_calls_for(month):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_query = f"""
            SELECT * 
            FROM Calls 
            WHERE MONTH(CallStartTimestamp) = ?
        """
        cursor.execute(sql_query, (month,))
        calls = cursor.fetchall()
        cursor.close()
        conn.close()
        return calls
    except pyodbc.Error as e:
        print("Error:", e)
        return []

def get_call_details(callid):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_query = f"""
            SELECT * 
            FROM Calls 
            WHERE CallID = ?
        """
        cursor.execute(sql_query, (callid))
        calls = cursor.fetchone()
        if calls is not None:
            cursor.close()
            conn.close()
            return calls
    except pyodbc.Error as e:
        print("Error:", e)
        return [] 

def format_transcript(transcript):
    formatted_transcript = ""
    current_speaker = None

    for entry in transcript:
        speaker = entry['role']
        content = entry['content']
        if speaker != current_speaker:
            if current_speaker is not None:
                formatted_transcript += "</p>"
            formatted_transcript += f"<p><strong>{speaker.capitalize()}:</strong> {content}"
            current_speaker = speaker
        else:
            formatted_transcript += f"<br/>{content}"
    formatted_transcript += "</p>"

    return formatted_transcript


def get_transcript_data(CallID):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_query = """
            SELECT LogFileName 
            FROM Calls 
            WHERE CallID = ?
        """
        cursor.execute(sql_query, (CallID,))
        calls = cursor.fetchone()
        cursor.close()
        conn.close()
    except pyodbc.Error as e:
        print("Error:", e)
        return None
    
    if calls:
        transcript_filename = calls[0] 
        bucket_name = 'engelbartchatlogs1'
        transcript_key = transcript_filename
        
        try:
            response = s3.get_object(Bucket=bucket_name, Key=transcript_key)
            transcript_data = json.loads(response['Body'].read().decode('utf-8'))
            return transcript_data
        except Exception as e:
            print(f"Error retrieving transcript for call {CallID}: {e}")
            return None
    else:
        print(f"No transcript found for call {CallID}")
        return None

def count_calls_for():
    month = datetime.now().month
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_query = f"""
            SELECT COUNT(*) AS call_count
            FROM Calls 
            WHERE MONTH(CallStartTimestamp) = ?
        """
        cursor.execute(sql_query, (month,))
        calls = cursor.fetchone()
        if calls is not None:
            cursor.close()
            conn.close()
            print(calls[0])
            return calls[0]
        else:
            return -1
    except pyodbc.Error as e:
        print("Error:", e)
        return -1  

def count_issues_for():
    # Get the current month
    current_month = datetime.now().month

    # Establish a connection to the database
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    # Query the database to count the number of issues generated this month
    sql_query = """
        SELECT COUNT(*) AS issue_count
        FROM Issues
        JOIN ConnectCallIssue ON Issues.IssueID = ConnectCallIssue.IssueID
        JOIN Calls ON ConnectCallIssue.CallID = Calls.CallID
        WHERE MONTH(Calls.CallStartTimeStamp) = ?
    """
    cursor.execute(sql_query, (current_month,))
    issue_count = cursor.fetchone()
    if issue_count is not None:
        # Close the cursor and connection
        cursor.close()
        conn.close()
        return issue_count[0]
    else:
        return -1

def minutes_saved():
    current_month = datetime.now().month
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    # sql_issue_count = """
    #     SELECT COUNT(*) AS issue_count
    #     FROM Issues
    #     JOIN ConnectCallIssue ON Issues.IssueID = ConnectCallIssue.IssueID
    #     JOIN Calls ON ConnectCallIssue.CallID = Calls.CallID
    #     WHERE MONTH(Calls.CallStartTimeStamp) = ?
    # """
    # cursor.execute(sql_issue_count, (current_month,))
    # issue_count = cursor.fetchone()[0]
    sql_total_duration = """
        SELECT SUM(DurationSeconds) AS total_duration
        FROM Calls
        WHERE MONTH(CallStartTimeStamp) = ?
    """
    cursor.execute(sql_total_duration, (current_month,))
    total_duration = cursor.fetchone()
    if total_duration is not None:
        # Close the cursor and connection
        cursor.close()
        conn.close()
        return round(total_duration[0]/60,1)
    else:
        return -1

def report_records(selected_month):
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    sql_query = """
        SELECT Calls.CallerNumber, Calls.CallStartTimeStamp, Calls.DurationSeconds, Issues.TypeName
        FROM Calls
        LEFT JOIN ConnectCallIssue ON Calls.CallID = ConnectCallIssue.CallID
        LEFT JOIN Issues ON ConnectCallIssue.IssueID = Issues.IssueID
        WHERE MONTH(Calls.CallStartTimeStamp) = ?
    """
    cursor.execute(sql_query, (selected_month,))
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    return calls 

def count_issue_types():
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_query = """
            SELECT TypeName 
            FROM IssueTypes
        """
        cursor.execute(sql_query)
        issue_types = cursor.fetchall()
        cursor.close()
        conn.close()
        return [issue_type[0] for issue_type in issue_types]
    except pyodbc.Error as e:
        print("Error:", e)
        return []

def count_issues_for_type(issue_type):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_query = """
            SELECT COUNT(*) 
            FROM Issues
            WHERE TypeName = ?
        """
        cursor.execute(sql_query, (issue_type,))
        count = cursor.fetchone()
        if count is not None:
            cursor.close()
            conn.close()
            return count[0]
        else:
            return -1
    except pyodbc.Error as e:
        print("Error:", e)
        return 0

@application.route('/')
@login_required
def index():
    current_user_name = f"{current_user.first_name} {current_user.last_name}" if current_user.is_authenticated else None
    issues = count_issues_for()
    duration = minutes_saved()
    issueTypes = count_issue_types()
    issueCounts = [count_issues_for_type(issue_type) for issue_type in issueTypes]
    data = {
        "labels": issueTypes,
        "data": issueCounts 
    }
    calls_this_month = count_calls_for()
    if test_db_connection():
        return render_template('index.html', current_user_name = current_user_name, duration = duration, issues = issues, calls_this_month = calls_this_month, data = data, connected=True, page = 'index')
    else:
        return render_template('logRubbishReport.html', connected=False)

@application.route('/logReport')
def logAReport():
    return render_template('logRubbishReport.html', page = 'logAReport')

@application.route('/viewReport', methods = ['GET', 'POST'])
def viewReports():
    if request.method == 'POST':
        selected_month = int(request.form['month'])
        reports = report_records(selected_month)

    else:
        selected_month = datetime.now().month
        reports = report_records(selected_month)
    current_month_name = calendar.month_name[selected_month]
    return render_template('viewReport.html',reports = reports, current_month_name = current_month_name, page = 'viewReports')

@application.route('/history', methods = ['GET', 'POST'])
def history():
    if request.method == 'POST':
        selected_month = int(request.form['month'])
        calls = get_calls_for(selected_month)
    else:
        selected_month = datetime.now().month
        calls = get_calls_for(selected_month)
    chosen_month = calendar.month_name[selected_month]
    return render_template('history.html', chosen_month = chosen_month, selected_month=selected_month, calls=calls, page = 'history')

@application.route('/call/<string:CallID>', methods=['GET', 'POST'])
def call_details(CallID):
    call = get_call_details(CallID)
    transcript = get_transcript_data(CallID)
    formatted_transcript = ""

    if transcript:
        if isinstance(transcript, list):
            formatted_transcript = format_transcript(transcript)
        else:
            formatted_transcript = format_transcript(transcript.get('entries', []))
    
    return render_template('callDetails.html', call=call, formatted_transcript=formatted_transcript)

if __name__ == '__main__':
    with application.app_context():
        db.create_all()
        application.run(debug=True)

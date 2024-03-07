from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pyodbc
import os

application = Flask(__name__)

# db_server = os.environ.get('lexdb-dev.cwxwqmt5bnip.eu-west-2.rds.amazonaws.com')
# db_username = os.environ.get('hilladmin')
# db_password = os.environ.get('Fg8peHWvpTZeTxuXHagi')
# db_port = os.environ.get('1433')
# db_name = os.environ.get('LexIssueData')

# db_uri = f'mssql+pymssql://{db_username}:{db_password}@{db_server}:{db_port}/{db_name}'

# application.config['SQLALCHEMY_DATABASE_URI'] = db_uri

# db = SQLAlchemy(application)

server = 'lexdb-dev.cwxwqmt5bnip.eu-west-2.rds.amazonaws.com'
database = 'LexIssueData'
username = 'hilladmin'
password = 'Fg8peHWvpTZeTxuXHagi'
driver = '{ODBC Driver 17 for SQL Server}'

connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

application.config['STATIC_FOLDER'] = 'static'

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
        sql_query = 'SELECT * FROM callRecords'
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        for row in rows:
            print(row)  # Assuming you want to print each row
            
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
            FROM callRecords 
            WHERE MONTH(callStartTimestamp) = ?
        """
        cursor.execute(sql_query, (month,))
        calls = cursor.fetchall()
        cursor.close()
        conn.close()
        return calls
    except pyodbc.Error as e:
        print("Error:", e)
        return []

@application.route('/')
def index():
    # return render_template('index.html')
    # Test database connection
    if test_db_connection():
        return render_template('index.html', connected=True)
    else:
        return render_template('logRubbishReport.html', connected=False)

@application.route('/logReport')
def logAReport():
    return render_template('logRubbishReport.html')

@application.route('/viewReport')
def viewReports():
    return render_template('viewReport.html')

@application.route('/history', methods = ['GET', 'POST'])
def history():
    if request.method == 'POST':
        selected_month = int(request.form['month'])
        calls = get_calls_for(selected_month)
    else:
        selected_month = datetime.now().month
        calls = get_calls_for(selected_month)
    return render_template('history.html', selected_month=selected_month, calls=calls)


if __name__ == '__main__':
    # Run the Flask app
    application.run(debug=True)

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import DB_CONFIG
import pyodbc
import os
import json
import boto3
import calendar

application = Flask(__name__)

s3 = boto3.client('s3')

connection_string = f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"

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

def get_call_details(callid):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_query = f"""
            SELECT * 
            FROM callRecords 
            WHERE CallID = ?
        """
        cursor.execute(sql_query, (callid))
        calls = cursor.fetchone()
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
            SELECT logFileName 
            FROM callRecords 
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
            FROM callRecords 
            WHERE MONTH(callStartTimestamp) = ?
        """
        cursor.execute(sql_query, (month,))
        calls = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(calls)
        return calls
    except pyodbc.Error as e:
        print("Error:", e)
        return -1  

@application.route('/')
def index():
     # Dummy data for demonstration
    data = {
        "labels": ["Request a bin bag", "Report a pothole", "Report graffiti"],
        "data": [30, 40, 30]  # Percentages of each type
    }
    calls_this_month = count_calls_for()
    if test_db_connection():
        return render_template('index.html', calls_this_month = calls_this_month, data = data, connected=True, page = 'index')
    else:
        return render_template('logRubbishReport.html', connected=False)

@application.route('/logReport')
def logAReport():
    return render_template('logRubbishReport.html', page = 'logAReport')

@application.route('/viewReport', methods = ['GET', 'POST'])
def viewReports():
    if request.method == 'POST':
        selected_month = int(request.form['month'])
        #calls = get_calls_for(selected_month)
    else:
        selected_month = datetime.now().month
        #calls = get_calls_for(selected_month)
    current_month_name = calendar.month_name[selected_month]
    return render_template('viewReport.html',current_month_name = current_month_name, page = 'viewReports')

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

@application.route('/call/<int:CallID>', methods=['GET', 'POST'])
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
    # Run the Flask app
    application.run(debug=True)

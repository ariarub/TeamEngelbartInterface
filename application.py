from flask import Flask, render_template

application = Flask(__name__)

application.config['STATIC_FOLDER'] = 'static'

@application.route('/')
def index():
    return render_template('index.html')

@application.route('/logReport')
def logAReport():
    return render_template('logRubbishReport.html')

@application.route('/viewReport')
def viewReports():
    return render_template('viewReport.html')

@application.route('/history')
def history():
    return render_template('history.html')
import unittest
from flask import Flask, render_template, url_for, request, redirect
from config import DB_CONFIG
from flask_sqlalchemy import SQLAlchemy
from unittest.mock import patch, MagicMock
from datetime import datetime
import pyodbc
from application import application, test_db_connection, count_calls_for, get_call_records, get_calls_for, get_call_details, count_issues_for, minutes_saved, report_records, count_issue_types, count_issues_for_type

class TestFlask(unittest.TestCase):

    #set up tests and test page generation 
    def setUp(self):
        self.app = application.test_client()
        self.connection_string = f"DRIVER={DB_CONFIG['pyodbcDriver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['callDatabase']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_log_report_page(self):
        response = self.app.get('/logReport')
        self.assertEqual(response.status_code, 200)

    def test_view_report_page(self):
        response = self.app.get('/viewReport')
        self.assertEqual(response.status_code, 200)

    def test_history_page(self):
        response = self.app.get('/history')
        self.assertEqual(response.status_code, 200)

    def test_call_details_page(self):
        response = self.app.get('/call/1')
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)

    #test DB connection and methods reading from the DB 
    def test_DB_Conn(self):
        self.assertTrue(test_db_connection())

    def test_database_connection(self):
        try:
            connection = pyodbc.connect(self.connection_string)
            print("Connected to the database successfully!")
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM Calls")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
            cursor.close()
            connection.close()
        except pyodbc.Error as e:
            print("Error connecting to the database:", e)

    def test_count_calls_for(self):
        self.assertIsInstance(count_calls_for(), int)

    def test_get_call_records(self):
        with patch('pyodbc.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [(1, 'Some Call'), (2, 'Another Call')]
            records = get_call_records()
            self.assertEqual(len(records), 2)

    def test_get_calls_for(self):
        with patch('pyodbc.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [(1, 'Some Call'), (2, 'Another Call')]
            calls = get_calls_for(1)
            self.assertEqual(len(calls), 2)

    def test_get_call_details(self):
        with patch('pyodbc.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (1, 'Some Call Details')
            details = get_call_details(1)
            self.assertIsNotNone(details)

    def test_count_issues_for(self):
        with patch('pyodbc.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (5,)
            issue_count = count_issues_for()
            self.assertEqual(issue_count, 5)

    def test_minutes_saved(self):
        with patch('pyodbc.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (600,)  
            minutes = minutes_saved()
            self.assertEqual(minutes, 10.0)

    def test_report_records(self):
        with patch('pyodbc.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [(1234567890, datetime(2022, 1, 1), 600, 'Some Type')]
            records = report_records(1)
            self.assertEqual(len(records), 1)

    def test_count_issue_types(self):
        with patch('pyodbc.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [('Issue Type 1',), ('Issue Type 2',)]
            issue_types = count_issue_types()
            self.assertEqual(len(issue_types), 2)

    def test_count_issues_for_type(self):
        with patch('pyodbc.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (10,)
            count = count_issues_for_type('Issue Type')
            self.assertEqual(count, 10)

    #test forms and buttons 
    def test_valid_form_submission_history(self):
        valid_form_data = {
            'month': '1' 
        }
        response = self.app.post('/history', data=valid_form_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_valid_form_submission_view_report(self):
        valid_form_data = {
            'month': '1' 
        }
        response = self.app.post('/viewReport', data=valid_form_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_view_details_button(self):
        response = self.app.post("/call/1", data={"some_key": "some_value"})
        self.assertEqual(response.status_code, 200)

    
    #test 
    
    #test login and authentication 


if __name__ == '__main__':
    unittest.main()


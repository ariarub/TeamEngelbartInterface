import unittest
from unittest.mock import patch, MagicMock
from application import application, test_db_connection, count_calls_for, get_call_records, get_calls_for, get_call_details, get_transcript_data

class TestFlask(unittest.TestCase):

    #set up tests and test page generation 
    def setUp(self):
        self.app = application.test_client()
        self.app.testing = True

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

    #test DB connection and methods reading from the DB 
    def test_DB_Conn(self):
        self.assertTrue(test_db_connection())

    def test_count_calls_for(self):
        self.assertIsInstance(count_calls_for(), int)

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


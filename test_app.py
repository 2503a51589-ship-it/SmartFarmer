import os
import unittest
from datetime import date
from app import app
from database import query_db, init_db
from smart_queue import SmartQueueEngine

class SmartFarmerTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-key'
        self.client = app.test_client()
        init_db()

    def test_01_public_routes(self):
        """Test public landing page, about, and contact pages"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Smart Farmer Procurement', res.data)
        
        res = self.client.get('/about')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SIH26032', res.data)

        res = self.client.get('/contact')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Kisan Call Center', res.data)

    def test_02_smart_queue_engine(self):
        """Test smart queue mathematical estimations and congestion classification"""
        # Wait time: 4 people ahead, 2 counters, 15 min avg = ceil(4/2) * 15 = 30 mins
        wait = SmartQueueEngine.calculate_estimated_wait_time(4, 2, 15)
        self.assertEqual(wait, 30)

        # Congestion levels
        cong_low = SmartQueueEngine.get_congestion_level(15)
        self.assertEqual(cong_low['level'], 'LOW CONGESTION')

        cong_med = SmartQueueEngine.get_congestion_level(35)
        self.assertEqual(cong_med['level'], 'MEDIUM CONGESTION')

        cong_high = SmartQueueEngine.get_congestion_level(50)
        self.assertEqual(cong_high['level'], 'HIGH CONGESTION')

    def test_03_farmer_login_and_dashboard(self):
        """Test farmer authentication and dashboard access"""
        with self.client:
            # Login as farmer1
            res = self.client.post('/login', data={
                'username': 'farmer1',
                'password': 'farmer123',
                'role': 'farmer'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Farmer Portal Overview', res.data)

            # Access booking history
            res = self.client.get('/farmer/booking_history')
            self.assertEqual(res.status_code, 200)

            # Access queue status
            res = self.client.get('/farmer/queue_status')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Live Visual Queue Tracking', res.data)

    def test_04_operator_console_and_actions(self):
        """Test operator login and queue processing"""
        with self.client:
            res = self.client.post('/login', data={
                'username': 'operator1',
                'password': 'operator123',
                'role': 'operator'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Procurement Counter Console', res.data)

            # Call next farmer
            res = self.client.post('/operator/call_next', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

    def test_05_admin_dashboard_and_analytics(self):
        """Test admin dashboard and reports"""
        with self.client:
            res = self.client.post('/login', data={
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Agricultural Procurement Command Center', res.data)

            # Reports
            res = self.client.get('/admin/reports')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'State Procurement Analytical Reports', res.data)

    def test_06_live_api_endpoint(self):
        """Test JSON live queue API"""
        res = self.client.get('/api/queue_status?center_id=1&token=A104')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('estimated_wait_mins', data)
        self.assertIn('people_ahead', data)

if __name__ == '__main__':
    unittest.main()

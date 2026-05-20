#!/usr/bin/env python3
"""
API Testing Script for Native Language Service Assistant
Tests all POST endpoints with comprehensive test cases
"""

import requests
import json
import time
import sys
from datetime import datetime

class APITester:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.otp_code = None
        self.user_id = None
        
        # Test data
        self.test_phone = "9876543210"
        self.test_language = "English"
        
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        # Print colored output
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        print(f"      {message}")
        if response_data and not success:
            print(f"      Response: {response_data}")
        print()
        
    def check_backend_connection(self):
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Health Check", True, 
                            f"Backend is running. Status: {data.get('status', 'unknown')}")
                return True
            else:
                self.log_test("Backend Health Check", False, 
                            f"Backend returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("Backend Health Check", False, 
                        "Cannot connect to backend. Make sure Flask server is running at http://localhost:5000")
            return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_send_otp(self):
        """Test POST /api/send-otp endpoint"""
        print("🔸 Testing Send OTP endpoint...")
        
        # Test Case 1: Valid phone number (English)
        try:
            payload = {
                "phone_number": self.test_phone,
                "language": "English"
            }
            response = self.session.post(f"{self.base_url}/send-otp", 
                                       json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.otp_code = data.get('otp')  # Store OTP for next test
                self.log_test("Send OTP - Valid Phone (English)", True, 
                            f"OTP sent successfully. Message: {data.get('message', 'N/A')}", data)
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Send OTP - Valid Phone (English)", False, 
                            f"Status: {response.status_code}, Error: {error_data.get('error', 'Unknown error')}", 
                            error_data)
        except Exception as e:
            self.log_test("Send OTP - Valid Phone (English)", False, f"Exception: {str(e)}")
        
        # Test Case 2: Valid phone number (Hindi)
        try:
            payload = {
                "phone_number": self.test_phone,
                "language": "Hindi"
            }
            response = self.session.post(f"{self.base_url}/send-otp", 
                                       json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Send OTP - Valid Phone (Hindi)", True, 
                            f"OTP sent in Hindi. Message: {data.get('message', 'N/A')}", data)
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Send OTP - Valid Phone (Hindi)", False, 
                            f"Status: {response.status_code}", error_data)
        except Exception as e:
            self.log_test("Send OTP - Valid Phone (Hindi)", False, f"Exception: {str(e)}")
        
        # Test Case 3: Invalid phone number
        try:
            payload = {
                "phone_number": "123",
                "language": "English"
            }
            response = self.session.post(f"{self.base_url}/send-otp", 
                                       json=payload, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Send OTP - Invalid Phone", True, 
                            "Correctly rejected invalid phone number")
            else:
                self.log_test("Send OTP - Invalid Phone", False, 
                            f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Send OTP - Invalid Phone", False, f"Exception: {str(e)}")
        
        # Test Case 4: Missing phone number
        try:
            payload = {
                "language": "English"
            }
            response = self.session.post(f"{self.base_url}/send-otp", 
                                       json=payload, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Send OTP - Missing Phone", True, 
                            "Correctly rejected missing phone number")
            else:
                self.log_test("Send OTP - Missing Phone", False, 
                            f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Send OTP - Missing Phone", False, f"Exception: {str(e)}")
    
    def test_verify_otp(self):
        """Test POST /api/verify-otp endpoint"""
        print("🔸 Testing Verify OTP endpoint...")
        
        if not self.otp_code:
            self.log_test("Verify OTP - Valid OTP", False, 
                        "No OTP code available. Send OTP test might have failed.")
            return
        
        # Test Case 1: Valid OTP
        try:
            payload = {
                "phone_number": self.test_phone,
                "otp_code": self.otp_code,
                "language": "English"
            }
            response = self.session.post(f"{self.base_url}/verify-otp", 
                                       json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get('user_id')
                self.log_test("Verify OTP - Valid OTP", True, 
                            f"Login successful. User ID: {self.user_id}", data)
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Verify OTP - Valid OTP", False, 
                            f"Status: {response.status_code}, Error: {error_data.get('error', 'Unknown')}", 
                            error_data)
        except Exception as e:
            self.log_test("Verify OTP - Valid OTP", False, f"Exception: {str(e)}")
        
        # Test Case 2: Invalid OTP
        try:
            payload = {
                "phone_number": self.test_phone,
                "otp_code": "000000",
                "language": "English"
            }
            # Use new session to avoid session conflicts
            temp_session = requests.Session()
            response = temp_session.post(f"{self.base_url}/verify-otp", 
                                       json=payload, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Verify OTP - Invalid OTP", True, 
                            "Correctly rejected invalid OTP")
            else:
                self.log_test("Verify OTP - Invalid OTP", False, 
                            f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Verify OTP - Invalid OTP", False, f"Exception: {str(e)}")
        
        # Test Case 3: Missing fields
        try:
            payload = {
                "phone_number": self.test_phone
                # Missing otp_code
            }
            temp_session = requests.Session()
            response = temp_session.post(f"{self.base_url}/verify-otp", 
                                       json=payload, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Verify OTP - Missing OTP Code", True, 
                            "Correctly rejected missing OTP code")
            else:
                self.log_test("Verify OTP - Missing OTP Code", False, 
                            f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Verify OTP - Missing OTP Code", False, f"Exception: {str(e)}")
    
    def test_bills_fetch(self):
        """Test POST /api/bills/fetch endpoint"""
        print("🔸 Testing Bills Fetch endpoint...")
        
        # Test Case 1: Valid request (authenticated)
        try:
            payload = {
                "customer_id": "CUST001",
                "bill_type": "electricity"
            }
            response = self.session.post(f"{self.base_url}/bills/fetch", 
                                       json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                bill_details = data.get('bill_details', {})
                self.log_test("Bills Fetch - Valid Request", True, 
                            f"Bill fetched. Amount: ₹{bill_details.get('amount', 'N/A')}", data)
            elif response.status_code == 401:
                self.log_test("Bills Fetch - Valid Request", False, 
                            "Authentication failed. User might not be logged in.")
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Bills Fetch - Valid Request", False, 
                            f"Status: {response.status_code}", error_data)
        except Exception as e:
            self.log_test("Bills Fetch - Valid Request", False, f"Exception: {str(e)}")
        
        # Test Case 2: Missing customer ID
        try:
            payload = {
                "bill_type": "electricity"
                # Missing customer_id
            }
            response = self.session.post(f"{self.base_url}/bills/fetch", 
                                       json=payload, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Bills Fetch - Missing Customer ID", True, 
                            "Correctly rejected missing customer ID")
            else:
                self.log_test("Bills Fetch - Missing Customer ID", False, 
                            f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Bills Fetch - Missing Customer ID", False, f"Exception: {str(e)}")
        
        # Test Case 3: Unauthenticated request
        try:
            payload = {
                "customer_id": "CUST001",
                "bill_type": "electricity"
            }
            # Use new session (not authenticated)
            temp_session = requests.Session()
            response = temp_session.post(f"{self.base_url}/bills/fetch", 
                                       json=payload, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Bills Fetch - Unauthenticated", True, 
                            "Correctly rejected unauthenticated request")
            else:
                self.log_test("Bills Fetch - Unauthenticated", False, 
                            f"Should have returned 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Bills Fetch - Unauthenticated", False, f"Exception: {str(e)}")
    
    def test_bills_pay(self):
        """Test POST /api/bills/pay endpoint"""
        print("🔸 Testing Bills Pay endpoint...")
        
        # Test Case 1: Valid payment (authenticated)
        try:
            payload = {
                "customer_id": "CUST001",
                "amount": 1250.50,
                "payment_method": "UPI"
            }
            response = self.session.post(f"{self.base_url}/bills/pay", 
                                       json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Bills Pay - Valid Payment", True, 
                            f"Payment successful. Transaction ID: {data.get('transaction_id', 'N/A')}", data)
            elif response.status_code == 401:
                self.log_test("Bills Pay - Valid Payment", False, 
                            "Authentication failed. User might not be logged in.")
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Bills Pay - Valid Payment", False, 
                            f"Status: {response.status_code}", error_data)
        except Exception as e:
            self.log_test("Bills Pay - Valid Payment", False, f"Exception: {str(e)}")
        
        # Test Case 2: Different payment methods
        payment_methods = ["Credit Card", "Debit Card", "Net Banking"]
        for method in payment_methods:
            try:
                payload = {
                    "customer_id": f"CUST00{payment_methods.index(method) + 2}",
                    "amount": 800.00,
                    "payment_method": method
                }
                response = self.session.post(f"{self.base_url}/bills/pay", 
                                           json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Bills Pay - {method}", True, 
                                f"Payment via {method} successful. Transaction ID: {data.get('transaction_id', 'N/A')}")
                elif response.status_code == 401:
                    self.log_test(f"Bills Pay - {method}", False, "Authentication required")
                else:
                    self.log_test(f"Bills Pay - {method}", False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Bills Pay - {method}", False, f"Exception: {str(e)}")
        
        # Test Case 3: Missing required fields
        try:
            payload = {
                "customer_id": "CUST001",
                # Missing amount and payment_method
            }
            response = self.session.post(f"{self.base_url}/bills/pay", 
                                       json=payload, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Bills Pay - Missing Fields", True, 
                            "Correctly rejected incomplete payment data")
            else:
                self.log_test("Bills Pay - Missing Fields", False, 
                            f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Bills Pay - Missing Fields", False, f"Exception: {str(e)}")
        
        # Test Case 4: Unauthenticated request
        try:
            payload = {
                "customer_id": "CUST001",
                "amount": 1000.00,
                "payment_method": "UPI"
            }
            temp_session = requests.Session()
            response = temp_session.post(f"{self.base_url}/bills/pay", 
                                       json=payload, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Bills Pay - Unauthenticated", True, 
                            "Correctly rejected unauthenticated payment")
            else:
                self.log_test("Bills Pay - Unauthenticated", False, 
                            f"Should have returned 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Bills Pay - Unauthenticated", False, f"Exception: {str(e)}")
    
    def test_rides_book(self):
        """Test POST /api/rides/book endpoint"""
        print("🔸 Testing Rides Book endpoint...")
        
        # Test Case 1: Valid ride booking (Auto)
        try:
            payload = {
                "pickup_location": "Airport",
                "drop_location": "City Center",
                "ride_type": "auto"
            }
            response = self.session.post(f"{self.base_url}/rides/book", 
                                       json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                ride_details = data.get('ride_details', {})
                self.log_test("Rides Book - Auto Rickshaw", True, 
                            f"Booking successful. ID: {ride_details.get('booking_id', 'N/A')}, "
                            f"Fare: ₹{ride_details.get('estimated_fare', 'N/A')}", data)
            elif response.status_code == 401:
                self.log_test("Rides Book - Auto Rickshaw", False, 
                            "Authentication failed. User might not be logged in.")
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Rides Book - Auto Rickshaw", False, 
                            f"Status: {response.status_code}", error_data)
        except Exception as e:
            self.log_test("Rides Book - Auto Rickshaw", False, f"Exception: {str(e)}")
        
        # Test Case 2: Different ride types
        ride_types = [
            {"type": "mini", "name": "Mini Car"},
            {"type": "sedan", "name": "Sedan"}
        ]
        
        for ride in ride_types:
            try:
                payload = {
                    "pickup_location": "Railway Station",
                    "drop_location": "Mall",
                    "ride_type": ride["type"]
                }
                response = self.session.post(f"{self.base_url}/rides/book", 
                                           json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    ride_details = data.get('ride_details', {})
                    self.log_test(f"Rides Book - {ride['name']}", True, 
                                f"Booking successful. Fare: ₹{ride_details.get('estimated_fare', 'N/A')}")
                elif response.status_code == 401:
                    self.log_test(f"Rides Book - {ride['name']}", False, "Authentication required")
                else:
                    self.log_test(f"Rides Book - {ride['name']}", False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Rides Book - {ride['name']}", False, f"Exception: {str(e)}")
        
        # Test Case 3: Missing pickup location
        try:
            payload = {
                "drop_location": "City Center",
                "ride_type": "auto"
                # Missing pickup_location
            }
            response = self.session.post(f"{self.base_url}/rides/book", 
                                       json=payload, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Rides Book - Missing Pickup", True, 
                            "Correctly rejected missing pickup location")
            else:
                self.log_test("Rides Book - Missing Pickup", False, 
                            f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Rides Book - Missing Pickup", False, f"Exception: {str(e)}")
        
        # Test Case 4: Missing drop location
        try:
            payload = {
                "pickup_location": "Airport",
                "ride_type": "auto"
                # Missing drop_location
            }
            response = self.session.post(f"{self.base_url}/rides/book", 
                                       json=payload, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Rides Book - Missing Drop", True, 
                            "Correctly rejected missing drop location")
            else:
                self.log_test("Rides Book - Missing Drop", False, 
                            f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Rides Book - Missing Drop", False, f"Exception: {str(e)}")
        
        # Test Case 5: Unauthenticated request
        try:
            payload = {
                "pickup_location": "Airport",
                "drop_location": "City Center",
                "ride_type": "auto"
            }
            temp_session = requests.Session()
            response = temp_session.post(f"{self.base_url}/rides/book", 
                                       json=payload, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Rides Book - Unauthenticated", True, 
                            "Correctly rejected unauthenticated booking")
            else:
                self.log_test("Rides Book - Unauthenticated", False, 
                            f"Should have returned 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Rides Book - Unauthenticated", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Native Language Service Assistant API Tests")
        print("=" * 60)
        print()
        
        # Check backend connection first
        if not self.check_backend_connection():
            print("❌ Backend is not accessible. Please start the Flask server first:")
            print("   python app.py")
            return
        
        print("✅ Backend is accessible. Starting API tests...")
        print()
        
        # Run all tests in sequence
        self.test_send_otp()
        time.sleep(1)  # Brief pause between tests
        
        self.test_verify_otp()
        time.sleep(1)
        
        self.test_bills_fetch()
        time.sleep(1)
        
        self.test_bills_pay()
        time.sleep(1)
        
        self.test_rides_book()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print()
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "0%")
        print()
        
        if failed > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
            print()
        
        print("🔍 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}")
        
        print()
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Your API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the error messages above.")
        
        print()
        print("💡 To run individual endpoint tests:")
        print("   • Send OTP: tester.test_send_otp()")
        print("   • Verify OTP: tester.test_verify_otp()")
        print("   • Bills Fetch: tester.test_bills_fetch()")
        print("   • Bills Pay: tester.test_bills_pay()")
        print("   • Rides Book: tester.test_rides_book()")

def main():
    """Main function to run tests"""
    print("🌐 Native Language Service Assistant API Tester")
    print("=" * 60)
    print()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python test_apis.py [base_url]")
        print()
        print("Options:")
        print("  base_url    Backend URL (default: http://localhost:5000/api)")
        print("  --help      Show this help message")
        print()
        print("Examples:")
        print("  python test_apis.py")
        print("  python test_apis.py http://192.168.1.100:5000/api")
        return
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000/api"
    
    print(f"🔗 Backend URL: {base_url}")
    print()
    
    # Create tester and run tests
    tester = APITester(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()

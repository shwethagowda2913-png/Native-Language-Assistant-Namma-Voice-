from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import hashlib
import random
import string
from datetime import datetime, timedelta
import requests
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
CORS(app, supports_credentials=True)

# Database setup
def init_db():
    conn = sqlite3.connect('NammaVoice.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            preferred_language TEXT DEFAULT 'English',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_used BOOLEAN DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            transaction_type TEXT NOT NULL,
            amount DECIMAL(10,2),
            status TEXT DEFAULT 'pending',
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pickup_location TEXT,
            drop_location TEXT,
            ride_type TEXT,
            status TEXT DEFAULT 'confirmed',
            booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estimated_fare DECIMAL(10,2),
            driver_name TEXT,
            vehicle_number TEXT,
            driver_phone TEXT,
            estimated_arrival TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Enhanced translations with more languages
TRANSLATIONS = {
    'English': {
        'welcome': 'Welcome to NammaVoice',
        'enter_phone': 'Enter your phone number',
        'enter_otp': 'Enter OTP',
        'login_success': 'Login successful',
        'invalid_otp': 'Invalid OTP',
        'bill_payment': 'Bill Payment',
        'book_ride': 'Book Ride',
        'payment_success': 'Payment successful',
        'booking_confirmed': 'Booking confirmed',
        'otp_sent': 'OTP sent successfully',
        'phone_required': 'Phone number required',
        'not_authenticated': 'Not authenticated',
        'bill_fetched': 'Bill fetched successfully',
        'payment_failed': 'Payment failed',
        'booking_failed': 'Booking failed',
        'language_updated': 'Language updated successfully'
    },
    'Hindi': {
        'welcome': 'सेवा सहायक में आपका स्वागत है',
        'enter_phone': 'अपना फोन नंबर दर्ज करें',
        'enter_otp': 'OTP दर्ज करें',
        'login_success': 'लॉगिन सफल',
        'invalid_otp': 'गलत OTP',
        'bill_payment': 'बिल भुगतान',
        'book_ride': 'सवारी बुक करें',
        'payment_success': 'भुगतान सफल',
        'booking_confirmed': 'बुकिंग की पुष्टि',
        'otp_sent': 'OTP सफलतापूर्वक भेजा गया',
        'phone_required': 'फोन नंबर आवश्यक',
        'not_authenticated': 'प्रामाणित नहीं',
        'bill_fetched': 'बिल सफलतापूर्वक लाया गया',
        'payment_failed': 'भुगतान असफल',
        'booking_failed': 'बुकिंग असफल',
        'language_updated': 'भाषा सफलतापूर्वक अपडेट की गई'
    },
    'Kannada': {
        'welcome': 'ಸೇವಾ ಸಹಾಯಕಕ್ಕೆ ಸ್ವಾಗತ',
        'enter_phone': 'ನಿಮ್ಮ ಫೋನ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ',
        'enter_otp': 'OTP ನಮೂದಿಸಿ',
        'login_success': 'ಲಾಗಿನ್ ಯಶಸ್ವಿ',
        'invalid_otp': 'ಅಮಾನ್ಯ OTP',
        'bill_payment': 'ಬಿಲ್ ಪಾವತಿ',
        'book_ride': 'ಸವಾರಿ ಬುಕ್ ಮಾಡಿ',
        'payment_success': 'ಪಾವತಿ ಯಶಸ್ವಿ',
        'booking_confirmed': 'ಬುಕಿಂಗ್ ದೃಢೀಕರಿಸಲಾಗಿದೆ',
        'otp_sent': 'OTP ಯಶಸ್ವಿಯಾಗಿ ಕಳುಹಿಸಲಾಗಿದೆ',
        'phone_required': 'ಫೋನ್ ಸಂಖ್ಯೆ ಅಗತ್ಯವಿದೆ',
        'not_authenticated': 'ದೃಢೀಕರಿಸಲಾಗಿಲ್ಲ',
        'bill_fetched': 'ಬಿಲ್ ಯಶಸ್ವಿಯಾಗಿ ತರಲಾಗಿದೆ',
        'payment_failed': 'ಪಾವತಿ ವಿಫಲ',
        'booking_failed': 'ಬುಕಿಂಗ್ ವಿಫಲ',
        'language_updated': 'ಭಾಷೆ ಯಶಸ್ವಿಯಾಗಿ ಅಪ್‌ಡೇಟ್ ಮಾಡಲಾಗಿದೆ'
    },
    'Tamil': {
        'welcome': 'சேவை உதவியாளருக்கு வரவேற்கிறோம்',
        'enter_phone': 'உங்கள் தொலைபேசி எண்ணை உள்ளிடவும்',
        'enter_otp': 'OTP உள்ளிடவும்',
        'login_success': 'உள்நுழைவு வெற்றி',
        'invalid_otp': 'தவறான OTP',
        'bill_payment': 'பில் செலுத்துதல்',
        'book_ride': 'சவாரி பதிவு செய்யுங்கள்',
        'payment_success': 'பணம் செலுத்துதல் வெற்றி',
        'booking_confirmed': 'பதிவு உறுதி செய்யப்பட்டது',
        'otp_sent': 'OTP வெற்றிகரமாக அனுப்பப்பட்டது',
        'phone_required': 'தொலைபேசி எண் தேவை',
        'not_authenticated': 'அங்கீகரிக்கப்படவில்லை',
        'bill_fetched': 'பில் வெற்றிகரமாக பெறப்பட்டது',
        'payment_failed': 'பணம் செலுத்துதல் தோல்வி',
        'booking_failed': 'பதிவு தோல்வி',
        'language_updated': 'மொழி வெற்றிகரமாக புதுப்பிக்கப்பட்டது'
    },
    'Telugu': {
        'welcome': 'సేవా సహాయకుడికి స్వాగతం',
        'enter_phone': 'మీ ఫోన్ నంబర్‌ను నమోదు చేయండి',
        'enter_otp': 'OTP నమోదు చేయండి',
        'login_success': 'లాగిన్ విజయవంతమైంది',
        'invalid_otp': 'చెల్లని OTP',
        'bill_payment': 'బిల్లు చెల్లింపు',
        'book_ride': 'రైడ్ బుక్ చేయండి',
        'payment_success': 'చెల్లింపు విజయవంతమైంది',
        'booking_confirmed': 'బుకింగ్ నిర్ధారించబడింది',
        'otp_sent': 'OTP విజయవంతంగా పంపబడింది',
        'phone_required': 'ఫోన్ నంబర్ అవసరం',
        'not_authenticated': 'ప్రామాణీకరించబడలేదు',
        'bill_fetched': 'బిల్లు విజయవంతంగా పొందబడింది',
        'payment_failed': 'చెల్లింపు విఫలమైంది',
        'booking_failed': 'బుకింగ్ విఫలమైంది',
        'language_updated': 'భాష విజయవంతంగా అప్‌డేట్ చేయబడింది'
    },
    'Bengali': {
        'welcome': 'সেবা সহায়কে স্বাগতম',
        'enter_phone': 'আপনার ফোন নম্বর লিখুন',
        'enter_otp': 'OTP লিখুন',
        'login_success': 'লগইন সফল',
        'invalid_otp': 'ভুল OTP',
        'bill_payment': 'বিল পেমেন্ট',
        'book_ride': 'রাইড বুক করুন',
        'payment_success': 'পেমেন্ট সফল',
        'booking_confirmed': 'বুকিং নিশ্চিত',
        'otp_sent': 'OTP সফলভাবে পাঠানো হয়েছে',
        'phone_required': 'ফোন নম্বর প্রয়োজন',
        'not_authenticated': 'প্রমাণীকৃত নয়',
        'bill_fetched': 'বিল সফলভাবে আনা হয়েছে',
        'payment_failed': 'পেমেন্ট ব্যর্থ',
        'booking_failed': 'বুকিং ব্যর্থ',
        'language_updated': 'ভাষা সফলভাবে আপডেট করা হয়েছে'
    }
}

def get_translation(language, key):
    return TRANSLATIONS.get(language, TRANSLATIONS['English']).get(key, key)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        phone_number = data.get('phone_number')
        language = data.get('language', 'English')
        
        if not phone_number:
            return jsonify({'error': get_translation(language, 'phone_required')}), 400
        
        phone_number = phone_number.strip().replace(' ', '').replace('-', '')
        otp_code = generate_otp()
        
        conn = sqlite3.connect('service_assistant.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE otps SET is_used = 1 WHERE phone_number = ?', (phone_number,))
        cursor.execute('INSERT INTO otps (phone_number, otp_code) VALUES (?, ?)', 
                       (phone_number, otp_code))
        conn.commit()
        conn.close()
        
        print(f"OTP for {phone_number}: {otp_code}")
        
        return jsonify({
            'message': get_translation(language, 'otp_sent'),
            'otp': otp_code
        })
        
    except Exception as e:
        print(f"Error in send_otp: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        phone_number = data.get('phone_number')
        otp_code = data.get('otp_code')
        language = data.get('language', 'English')
        
        if not phone_number or not otp_code:
            return jsonify({'error': 'Phone number and OTP required'}), 400
        
        phone_number = phone_number.strip().replace(' ', '').replace('-', '')
        
        conn = sqlite3.connect('service_assistant.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM otps 
            WHERE phone_number = ? AND otp_code = ? AND is_used = 0 
            AND created_at > datetime('now', '-10 minutes')
        ''', (phone_number, otp_code))
        
        otp_record = cursor.fetchone()
        
        if not otp_record:
            conn.close()
            return jsonify({'error': get_translation(language, 'invalid_otp')}), 400
        
        cursor.execute('UPDATE otps SET is_used = 1 WHERE id = ?', (otp_record[0],))
        cursor.execute('SELECT id FROM users WHERE phone_number = ?', (phone_number,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute('INSERT INTO users (phone_number, preferred_language) VALUES (?, ?)',
                          (phone_number, language))
            user_id = cursor.lastrowid
        else:
            user_id = user[0]
            cursor.execute('UPDATE users SET preferred_language = ? WHERE id = ?', 
                          (language, user_id))
        
        conn.commit()
        conn.close()
        
        session['user_id'] = user_id
        session['phone_number'] = phone_number
        session['language'] = language
        
        return jsonify({
            'message': get_translation(language, 'login_success'),
            'user_id': user_id,
            'language': language
        })
        
    except Exception as e:
        print(f"Error in verify_otp: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/language', methods=['POST'])
def update_language():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        language = data.get('language')
        
        if not language:
            return jsonify({'error': 'Language required'}), 400
        
        conn = sqlite3.connect('service_assistant.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET preferred_language = ? WHERE id = ?',
                       (language, session['user_id']))
        conn.commit()
        conn.close()
        
        session['language'] = language
        
        return jsonify({'message': get_translation(language, 'language_updated')})
        
    except Exception as e:
        print(f"Error in update_language: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/bills/fetch', methods=['POST'])
def fetch_bill():
    if 'user_id' not in session:
        return jsonify({'error': get_translation('English', 'not_authenticated')}), 401
    
    try:
        data = request.json
        customer_id = data.get('customer_id')
        bill_type = data.get('bill_type', 'electricity')
        
        if not customer_id:
            return jsonify({'error': 'Customer ID required'}), 400
        
        mock_bill = {
            'customer_id': customer_id,
            'amount': round(random.uniform(500, 3000), 2),
            'due_date': '2025-10-15',
            'bill_type': bill_type,
            'units_consumed': random.randint(100, 300),
            'previous_reading': random.randint(1000, 1200),
            'current_reading': random.randint(1300, 1500)
        }
        
        language = session.get('language', 'English')
        
        return jsonify({
            'bill_details': mock_bill,
            'message': get_translation(language, 'bill_fetched')
        })
        
    except Exception as e:
        print(f"Error in fetch_bill: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/bills/pay', methods=['POST'])
def pay_bill():
    if 'user_id' not in session:
        return jsonify({'error': get_translation('English', 'not_authenticated')}), 401
    
    try:
        data = request.json
        customer_id = data.get('customer_id')
        amount = data.get('amount')
        payment_method = data.get('payment_method')
        
        if not all([customer_id, amount, payment_method]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = sqlite3.connect('service_assistant.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (user_id, transaction_type, amount, status, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], 'bill_payment', amount, 'completed', 
              json.dumps({'customer_id': customer_id, 'payment_method': payment_method})))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        language = session.get('language', 'English')
        
        return jsonify({
            'message': get_translation(language, 'payment_success'),
            'transaction_id': transaction_id,
            'amount': amount,
            'status': 'completed'
        })
        
    except Exception as e:
        print(f"Error in pay_bill: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/rides/book', methods=['POST'])
def book_ride():
    if 'user_id' not in session:
        return jsonify({'error': get_translation('English', 'not_authenticated')}), 401
    
    try:
        data = request.json
        pickup_location = data.get('pickup_location')
        drop_location = data.get('drop_location')
        ride_type = data.get('ride_type', 'auto')
        
        if not all([pickup_location, drop_location]):
            return jsonify({'error': 'Pickup and drop locations required'}), 400
        
        fare_rates = {'auto': 25, 'mini': 50, 'sedan': 80}
        base_fare = fare_rates.get(ride_type, 25)
        distance_fare = random.uniform(50, 200)
        estimated_fare = round(base_fare + distance_fare, 2)
        
        drivers = [
            {'name': 'Rajesh Kumar', 'phone': '+91-9876543210'},
            {'name': 'Suresh Patil', 'phone': '+91-9123456780'},
            {'name': 'Mahesh Singh', 'phone': '+91-9234567890'},
            {'name': 'Ramesh Reddy', 'phone': '+91-9345678901'}
        ]
        
        vehicles = ['KA-01-AB-1234', 'KA-05-CD-5678', 'TN-09-EF-9012', 'AP-12-GH-3456']
        
        driver = random.choice(drivers)
        vehicle_number = random.choice(vehicles)
        estimated_arrival = f"{random.randint(5, 15)} minutes"
        
        conn = sqlite3.connect('service_assistant.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bookings (user_id, pickup_location, drop_location, ride_type, 
                                status, estimated_fare, driver_name, vehicle_number, 
                                driver_phone, estimated_arrival)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], pickup_location, drop_location, ride_type, 'confirmed', 
              estimated_fare, driver['name'], vehicle_number, driver['phone'], estimated_arrival))
        
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        language = session.get('language', 'English')
        
        ride_details = {
            'booking_id': booking_id,
            'pickup_location': pickup_location,
            'drop_location': drop_location,
            'ride_type': ride_type,
            'estimated_fare': estimated_fare,
            'estimated_arrival': estimated_arrival,
            'driver_name': driver['name'],
            'driver_phone': driver['phone'],
            'vehicle_number': vehicle_number,
            'status': 'confirmed'
        }
        
        return jsonify({
            'message': get_translation(language, 'booking_confirmed'),
            'ride_details': ride_details
        })
        
    except Exception as e:
        print(f"Error in book_ride: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/rides/available', methods=['GET'])
def get_available_rides():
    try:
        rides = [
            {'type': 'auto', 'name': 'Auto Rickshaw', 'base_fare': 25, 'per_km': 12},
            {'type': 'mini', 'name': 'Mini Car', 'base_fare': 50, 'per_km': 15},
            {'type': 'sedan', 'name': 'Sedan', 'base_fare': 80, 'per_km': 20}
        ]
        return jsonify({'available_rides': rides})
    except Exception as e:
        print(f"Error in get_available_rides: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    try:
        conn = sqlite3.connect('service_assistant.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT preferred_language, COUNT(*) FROM users GROUP BY preferred_language')
        language_stats = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "completed"')
        completed_transactions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "failed"')
        failed_transactions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM bookings WHERE status = "confirmed"')
        confirmed_bookings = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM bookings WHERE status = "cancelled"')
        cancelled_bookings = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'language_stats': language_stats,
            'completed_transactions': completed_transactions,
            'failed_transactions': failed_transactions,
            'confirmed_bookings': confirmed_bookings,
            'cancelled_bookings': cancelled_bookings
        })
    except Exception as e:
        print(f"Error in get_admin_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/translations/<language>')
def get_translations(language):
    try:
        return jsonify(TRANSLATIONS.get(language, TRANSLATIONS['English']))
    except Exception as e:
        print(f"Error in get_translations: {str(e)}")
        return jsonify(TRANSLATIONS['English'])

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

if __name__ == '__main__':
    init_db()
    print("✅ Database initialized successfully!")
    print("🚀 Starting Flask server...")
    print("🌐 Backend available at: http://localhost:5000")
    print("\n📋 API Endpoints:")
    print("   - POST /api/send-otp")
    print("   - POST /api/verify-otp")
    print("   - POST /api/bills/fetch")
    print("   - POST /api/bills/pay")
    print("   - POST /api/rides/book")
    print("   - GET /api/rides/available")
    print("   - GET /api/admin/stats")
    print("   - GET /api/translations/<language>")
    print("\n🗣️  Supported Languages: English, Hindi, Kannada, Tamil, Telugu, Bengali")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
import os
import random
import string
from functools import wraps
from datetime import datetime, date, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database import init_db, query_db
from smart_queue import SmartQueueEngine

app = Flask(__name__)
app.config.from_object(Config)

# ----------------- Database Initialization -----------------
with app.app_context():
    init_db()

# ----------------- Authentication Helpers -----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            user_role = session.get('role')
            if user_role not in roles:
                flash(f'Access restricted. Required role: {", ".join(roles)}', 'danger')
                if user_role == 'farmer':
                    return redirect(url_for('farmer_dashboard'))
                elif user_role == 'operator':
                    return redirect(url_for('operator_dashboard'))
                elif user_role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ----------------- Helper Functions -----------------
def generate_token_number(center_id, queue_date):
    """Generates unique token number like A101, A102, etc."""
    center = query_db("SELECT center_code FROM procurement_centers WHERE id = %s", (center_id,), one=True)
    code_letter = 'A'
    if center and center.get('center_code'):
        # Extract letter from code e.g. CTR-AND-01 -> A, CTR-NAV-02 -> N
        parts = center['center_code'].split('-')
        if len(parts) >= 2 and parts[1]:
            code_letter = parts[1][0].upper()
            
    # Count existing tokens for this center today
    cnt = query_db("SELECT COUNT(*) as c FROM queue WHERE center_id = %s AND queue_date = %s", (center_id, queue_date), one=True)
    count = (cnt['c'] if cnt else 0) + 101
    return f"{code_letter}{count}"

def generate_booking_ref():
    chars = ''.join(random.choices(string.digits, k=6))
    return f"BK-2026-{chars}"

def generate_dbt_txn_id():
    chars = ''.join(random.choices(string.digits, k=8))
    return f"DBT-2026-TXN-{chars}"

def get_smart_recommendations_for_centers():
    """Computes real-time smart queue prediction across all centers."""
    today = date.today()
    centers = query_db("SELECT * FROM procurement_centers WHERE is_active = 1") or []
    analyses = []
    for c in centers:
        cid = c['id']
        active_queue = query_db(
            "SELECT q.*, b.crop_quantity FROM queue q JOIN bookings b ON q.booking_id = b.id WHERE q.center_id = %s AND q.queue_date = %s",
            (cid, today)
        ) or []
        analysis = SmartQueueEngine.analyze_center_queue(
            cid, c['center_name'], active_queue, c.get('total_counters', 3), c.get('avg_processing_time_mins', 15)
        )
        analysis['district'] = c.get('district', 'Gujarat')
        analyses.append(analysis)
    return SmartQueueEngine.get_smart_recommendation(analyses)

# =========================================================================
# PUBLIC ROUTES
# =========================================================================

@app.route('/')
def index():
    centers = query_db("SELECT * FROM procurement_centers WHERE is_active = 1 LIMIT 6") or []
    smart_rec = get_smart_recommendations_for_centers()
    return render_template('index.html', centers=centers, smart_rec=smart_rec)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        category = request.form.get('category')
        message = request.form.get('message')
        flash(f"Thank you {name}! Your query regarding '{category}' has been logged. Our helpline officer will contact +91 {phone} shortly.", 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        role = session.get('role')
        if role == 'farmer':
            return redirect(url_for('farmer_dashboard'))
        elif role == 'operator':
            return redirect(url_for('operator_dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))
            
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'farmer').strip()

        user = query_db("SELECT * FROM users WHERE username = %s AND role = %s", (username, role), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['phone'] = user['phone']
            
            flash(f"Welcome back, {user['username']}! Signed in as {user['role'].upper()}.", 'success')
            if role == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            elif role == 'operator':
                return redirect(url_for('operator_dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username, password, or role selection. Please verify test credentials.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        village = request.form.get('village', '').strip()
        district = request.form.get('district', '').strip()
        land_size_acres = float(request.form.get('land_size_acres', 0.0) or 0.0)
        bank_account_no = request.form.get('bank_account_no', '').strip()
        ifsc_code = request.form.get('ifsc_code', '').strip().upper()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Check existing username
        existing_user = query_db("SELECT id FROM users WHERE username = %s", (username,), one=True)
        if existing_user:
            flash('Username is already registered. Please choose another username or log in.', 'warning')
            return render_template('register.html')

        try:
            # Create user
            pass_hash = generate_password_hash(password)
            user_id = query_db(
                "INSERT INTO users (username, password_hash, role, email, phone) VALUES (%s, %s, %s, %s, %s)",
                (username, pass_hash, 'farmer', f"{username}@kisanmail.in", mobile_number),
                commit=True
            )
            # Create farmer record
            rand_code = ''.join(random.choices(string.digits, k=4))
            farmer_uid = f"FMR-GJ-2026-{rand_code}"
            query_db(
                "INSERT INTO farmers (user_id, farmer_uid, full_name, mobile_number, village, district, state, land_size_acres, bank_account_no, ifsc_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (user_id, farmer_uid, full_name, mobile_number, village, district, 'Gujarat', land_size_acres, bank_account_no, ifsc_code),
                commit=True
            )
            flash(f"Registration successful! Your Farmer ID is {farmer_uid}. You may now log in.", 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", 'danger')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# =========================================================================
# FARMER PORTAL ROUTES
# =========================================================================

@app.route('/farmer/dashboard')
@role_required('farmer')
def farmer_dashboard():
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)
    if not farmer:
        flash('Farmer profile not found.', 'danger')
        return redirect(url_for('logout'))

    farmer_id = farmer['id']
    today = date.today()

    # Total lifetime bookings count
    tot = query_db("SELECT COUNT(*) as c FROM bookings WHERE farmer_id = %s", (farmer_id,), one=True)
    total_bookings = tot['c'] if tot else 0

    # Today's active booking
    active_booking = query_db(
        """SELECT b.*, c.center_name, c.district as center_district, cr.crop_name, s.slot_date, s.start_time, s.end_time
           FROM bookings b
           JOIN procurement_centers c ON b.center_id = c.id
           JOIN crops cr ON b.crop_id = cr.id
           JOIN slots s ON b.slot_id = s.id
           WHERE b.farmer_id = %s AND s.slot_date >= %s AND b.status NOT IN ('Procurement Completed', 'Cancelled')
           ORDER BY s.slot_date ASC, s.start_time ASC LIMIT 1""",
        (farmer_id, today),
        one=True
    )

    # Active queue & waiting calculation
    active_queue = None
    people_ahead = 0
    estimated_wait_mins = 0
    expected_time = "--:--"
    
    if active_booking:
        active_queue = query_db("SELECT * FROM queue WHERE booking_id = %s", (active_booking['id'],), one=True)
        if active_queue:
            # Count people ahead in same center today
            ahead = query_db(
                """SELECT COUNT(*) as c FROM queue 
                   WHERE center_id = %s AND queue_date = %s AND id < %s AND status IN ('Waiting', 'Calling', 'In-Process')""",
                (active_booking['center_id'], today, active_queue['id']),
                one=True
            )
            people_ahead = ahead['c'] if ahead else 0
            
            center_info = query_db("SELECT total_counters, avg_processing_time_mins FROM procurement_centers WHERE id = %s", (active_booking['center_id'],), one=True)
            counters = center_info.get('total_counters', 3) if center_info else 3
            avg_time = center_info.get('avg_processing_time_mins', 15) if center_info else 15
            
            estimated_wait_mins = SmartQueueEngine.calculate_estimated_wait_time(people_ahead, counters, avg_time)
            expected_time = SmartQueueEngine.calculate_expected_completion_time(estimated_wait_mins)

    # Latest payment record
    active_payment = query_db(
        "SELECT * FROM payments WHERE farmer_id = %s ORDER BY id DESC LIMIT 1",
        (farmer_id,),
        one=True
    )

    # Recent bookings list
    recent_bookings = query_db(
        """SELECT b.*, c.center_name, cr.crop_name, s.slot_date, s.start_time
           FROM bookings b
           JOIN procurement_centers c ON b.center_id = c.id
           JOIN crops cr ON b.crop_id = cr.id
           JOIN slots s ON b.slot_id = s.id
           WHERE b.farmer_id = %s
           ORDER BY b.id DESC LIMIT 5""",
        (farmer_id,)
    ) or []

    # Smart Recommendation (SIH Innovation)
    smart_rec = get_smart_recommendations_for_centers()

    return render_template(
        'farmer_dashboard.html',
        farmer=farmer,
        total_bookings=total_bookings,
        active_booking=active_booking,
        active_queue=active_queue,
        people_ahead=people_ahead,
        estimated_wait_mins=estimated_wait_mins,
        expected_time=expected_time,
        active_payment=active_payment,
        recent_bookings=recent_bookings,
        smart_rec=smart_rec
    )

@app.route('/farmer/book_slot', methods=['GET', 'POST'])
@role_required('farmer')
def book_slot():
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)
    today = date.today()

    if request.method == 'POST':
        crop_id = request.form.get('crop_id')
        crop_quantity = float(request.form.get('crop_quantity', 0.0) or 0.0)
        harvest_date = request.form.get('harvest_date')
        center_id = request.form.get('center_id')
        slot_id = request.form.get('slot_id')
        notes = request.form.get('notes', '')

        # Validate slot capacity
        slot = query_db("SELECT * FROM slots WHERE id = %s AND is_active = 1", (slot_id,), one=True)
        if not slot:
            flash('Selected time slot is invalid or no longer available.', 'danger')
            return redirect(url_for('book_slot'))

        if slot['booked_count'] >= slot['max_capacity']:
            flash('Selected time slot is full. Please choose another slot or center.', 'warning')
            return redirect(url_for('book_slot'))

        # Generate unique references & token number
        booking_ref = generate_booking_ref()
        token_number = generate_token_number(center_id, slot['slot_date'])
        
        # Position in queue for this center today
        existing_q_count = query_db(
            "SELECT COUNT(*) as c FROM queue WHERE center_id = %s AND queue_date = %s",
            (center_id, slot['slot_date']),
            one=True
        )
        queue_pos = (existing_q_count['c'] if existing_q_count else 0) + 1

        # Create Booking
        booking_id = query_db(
            """INSERT INTO bookings (booking_ref, farmer_id, center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_number, status, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Booked', %s)""",
            (booking_ref, farmer['id'], center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_pos, notes),
            commit=True
        )

        # Create Queue entry
        query_db(
            """INSERT INTO queue (center_id, booking_id, queue_date, token_number, position, status, counter_assigned)
               VALUES (%s, %s, %s, %s, %s, 'Waiting', 1)""",
            (center_id, booking_id, slot['slot_date'], token_number, queue_pos),
            commit=True
        )

        # Increment booked count on slot
        query_db("UPDATE slots SET booked_count = booked_count + 1 WHERE id = %s", (slot_id,), commit=True)

        flash(f"Slot booked successfully! Your Token Number is {token_number} (Ref: {booking_ref}).", 'success')
        return redirect(url_for('my_token', booking_id=booking_id))

    # GET Request
    selected_center_id = request.args.get('center_id')
    crops = query_db("SELECT * FROM crops ORDER BY crop_name ASC") or []
    centers = query_db("SELECT * FROM procurement_centers WHERE is_active = 1 ORDER BY center_name ASC") or []
    slots = query_db(
        "SELECT * FROM slots WHERE slot_date >= %s AND is_active = 1 ORDER BY slot_date ASC, start_time ASC",
        (today,)
    ) or []

    return render_template(
        'book_slot.html',
        crops=crops,
        centers=centers,
        slots=slots,
        selected_center_id=selected_center_id,
        today_date=today.strftime('%Y-%m-%d')
    )

@app.route('/farmer/my_token')
@app.route('/farmer/my_token/<int:booking_id>')
@role_required('farmer')
def my_token(booking_id=None):
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)
    today = date.today()

    if booking_id:
        booking = query_db(
            """SELECT b.*, f.full_name, f.farmer_uid, f.mobile_number, c.center_name, c.address as center_address, c.district, cr.crop_name, cr.msp_per_quintal, s.slot_date, s.start_time, s.end_time
               FROM bookings b
               JOIN farmers f ON b.farmer_id = f.id
               JOIN procurement_centers c ON b.center_id = c.id
               JOIN crops cr ON b.crop_id = cr.id
               JOIN slots s ON b.slot_id = s.id
               WHERE b.id = %s AND b.farmer_id = %s""",
            (booking_id, farmer['id']),
            one=True
        )
    else:
        # Get latest active booking
        booking = query_db(
            """SELECT b.*, f.full_name, f.farmer_uid, f.mobile_number, c.center_name, c.address as center_address, c.district, cr.crop_name, cr.msp_per_quintal, s.slot_date, s.start_time, s.end_time
               FROM bookings b
               JOIN farmers f ON b.farmer_id = f.id
               JOIN procurement_centers c ON b.center_id = c.id
               JOIN crops cr ON b.crop_id = cr.id
               JOIN slots s ON b.slot_id = s.id
               WHERE b.farmer_id = %s AND s.slot_date >= %s
               ORDER BY b.id DESC LIMIT 1""",
            (farmer['id'], today),
            one=True
        )

    return render_template('my_token.html', booking=booking)

@app.route('/farmer/queue_status')
@role_required('farmer')
def queue_status():
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)
    today = date.today()

    # Find today's active booking for this farmer
    active_booking = query_db(
        """SELECT b.*, c.center_name, s.slot_date FROM bookings b 
           JOIN procurement_centers c ON b.center_id = c.id
           JOIN slots s ON b.slot_id = s.id
           WHERE b.farmer_id = %s AND s.slot_date = %s AND b.status != 'Cancelled'
           ORDER BY b.id DESC LIMIT 1""",
        (farmer['id'], today),
        one=True
    )

    center_id = active_booking['center_id'] if active_booking else 1
    user_token = active_booking['token_number'] if active_booking else None

    center = query_db("SELECT * FROM procurement_centers WHERE id = %s", (center_id,), one=True)
    
    # Retrieve all queue records for this center today
    queue_records = query_db(
        """SELECT q.*, b.crop_quantity, f.full_name, cr.crop_name 
           FROM queue q
           JOIN bookings b ON q.booking_id = b.id
           JOIN farmers f ON b.farmer_id = f.id
           JOIN crops cr ON b.crop_id = cr.id
           WHERE q.center_id = %s AND q.queue_date = %s
           ORDER BY q.position ASC""",
        (center_id, today)
    ) or []

    # Build visual pipeline representation
    visual_data = SmartQueueEngine.build_visual_queue(queue_records, user_token)

    # Current calling token
    calling = query_db(
        "SELECT token_number FROM queue WHERE center_id = %s AND queue_date = %s AND status IN ('Calling', 'In-Process') LIMIT 1",
        (center_id, today),
        one=True
    )
    calling_token = calling['token_number'] if calling else None

    counters = center.get('total_counters', 3) if center else 3
    avg_proc = center.get('avg_processing_time_mins', 15) if center else 15
    est_wait = SmartQueueEngine.calculate_estimated_wait_time(visual_data['people_ahead'], counters, avg_proc)
    expected_clock = SmartQueueEngine.calculate_expected_completion_time(est_wait)

    return render_template(
        'queue_status.html',
        center=center,
        user_token=user_token,
        today_date=today.strftime('%d %B %Y'),
        people_ahead=visual_data['people_ahead'],
        estimated_wait_mins=est_wait,
        expected_time=expected_clock,
        calling_token=calling_token,
        visual_items=visual_data['visual_items'],
        queue_list=queue_records,
        active_counter=1
    )

@app.route('/farmer/procurement_status')
@role_required('farmer')
def procurement_status():
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)

    booking = query_db(
        """SELECT b.*, c.center_name, cr.crop_name 
           FROM bookings b
           JOIN procurement_centers c ON b.center_id = c.id
           JOIN crops cr ON b.crop_id = cr.id
           WHERE b.farmer_id = %s
           ORDER BY b.id DESC LIMIT 1""",
        (farmer['id'],),
        one=True
    )

    record = None
    if booking:
        record = query_db("SELECT * FROM procurement_records WHERE booking_id = %s", (booking['id'],), one=True)

    return render_template('procurement_status.html', booking=booking, record=record)

@app.route('/farmer/payment_status')
@role_required('farmer')
def payment_status():
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)

    payments = query_db(
        """SELECT p.*, b.booking_ref, b.token_number, b.crop_quantity, cr.crop_name, pr.final_accepted_quantity
           FROM payments p
           JOIN bookings b ON p.booking_id = b.id
           JOIN crops cr ON b.crop_id = cr.id
           LEFT JOIN procurement_records pr ON p.procurement_id = pr.id
           WHERE p.farmer_id = %s
           ORDER BY p.id DESC""",
        (farmer['id'],)
    ) or []

    return render_template('payment_status.html', farmer=farmer, payments=payments)

@app.route('/farmer/booking_history')
@role_required('farmer')
def booking_history():
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)

    bookings = query_db(
        """SELECT b.*, c.center_name, c.district, cr.crop_name, s.slot_date, s.start_time, s.end_time
           FROM bookings b
           JOIN procurement_centers c ON b.center_id = c.id
           JOIN crops cr ON b.crop_id = cr.id
           JOIN slots s ON b.slot_id = s.id
           WHERE b.farmer_id = %s
           ORDER BY s.slot_date DESC, b.id DESC""",
        (farmer['id'],)
    ) or []

    return render_template('booking_history.html', bookings=bookings)

@app.route('/farmer/cancel_booking/<int:booking_id>', methods=['POST'])
@role_required('farmer')
def cancel_booking(booking_id):
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)

    booking = query_db("SELECT * FROM bookings WHERE id = %s AND farmer_id = %s", (booking_id, farmer['id']), one=True)
    if booking:
        if booking['status'] in ['Booked', 'Waiting']:
            query_db("UPDATE bookings SET status = 'Cancelled' WHERE id = %s", (booking_id,), commit=True)
            query_db("UPDATE queue SET status = 'Cancelled' WHERE booking_id = %s", (booking_id,), commit=True)
            query_db("UPDATE slots SET booked_count = GREATEST(0, booked_count - 1) WHERE id = %s", (booking['slot_id'],), commit=True)
            flash(f"Booking {booking['booking_ref']} (Token {booking['token_number']}) has been cancelled.", 'info')
        else:
            flash("Cannot cancel a booking that is already in-process or completed.", 'warning')

    return redirect(url_for('booking_history'))

@app.route('/farmer/profile', methods=['GET', 'POST'])
@role_required('farmer')
def farmer_profile():
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        village = request.form.get('village', '').strip()
        district = request.form.get('district', '').strip()
        land_size_acres = float(request.form.get('land_size_acres', 0.0) or 0.0)
        bank_account_no = request.form.get('bank_account_no', '').strip()
        ifsc_code = request.form.get('ifsc_code', '').strip().upper()

        query_db(
            """UPDATE farmers SET full_name = %s, mobile_number = %s, village = %s, district = %s, land_size_acres = %s, bank_account_no = %s, ifsc_code = %s
               WHERE id = %s""",
            (full_name, mobile_number, village, district, land_size_acres, bank_account_no, ifsc_code, farmer['id']),
            commit=True
        )
        flash('Profile and DBT bank details updated successfully.', 'success')
        return redirect(url_for('farmer_profile'))

    return render_template('profile.html', farmer=farmer)

# =========================================================================
# PROCUREMENT CENTER OPERATOR ROUTES
# =========================================================================

@app.route('/operator/dashboard')
@role_required('operator')
def operator_dashboard():
    user_id = session.get('user_id')
    operator = query_db("SELECT * FROM operators WHERE user_id = %s", (user_id,), one=True)
    if not operator:
        flash('Operator record not found.', 'danger')
        return redirect(url_for('logout'))

    center_id = operator['center_id']
    center = query_db("SELECT * FROM procurement_centers WHERE id = %s", (center_id,), one=True)
    today = date.today()

    # Total appointments today
    tot = query_db(
        "SELECT COUNT(*) as c FROM queue WHERE center_id = %s AND queue_date = %s",
        (center_id, today),
        one=True
    )
    total_today = tot['c'] if tot else 0

    # Waiting count
    wait_cnt = query_db(
        "SELECT COUNT(*) as c FROM queue WHERE center_id = %s AND queue_date = %s AND status = 'Waiting'",
        (center_id, today),
        one=True
    )
    waiting_count = wait_cnt['c'] if wait_cnt else 0

    # Completed count
    comp_cnt = query_db(
        "SELECT COUNT(*) as c FROM queue WHERE center_id = %s AND queue_date = %s AND status = 'Completed'",
        (center_id, today),
        one=True
    )
    completed_count = comp_cnt['c'] if comp_cnt else 0

    # Active token in process
    current_q = query_db(
        "SELECT * FROM queue WHERE center_id = %s AND queue_date = %s AND status IN ('Calling', 'In-Process') LIMIT 1",
        (center_id, today),
        one=True
    )
    current_token = current_q['token_number'] if current_q else None

    current_booking = None
    if current_q:
        current_booking = query_db(
            """SELECT b.*, f.full_name, f.farmer_uid, f.mobile_number, cr.crop_name, cr.msp_per_quintal
               FROM bookings b
               JOIN farmers f ON b.farmer_id = f.id
               JOIN crops cr ON b.crop_id = cr.id
               WHERE b.id = %s""",
            (current_q['booking_id'],),
            one=True
        )

    # All queue items for today
    queue_items = query_db(
        """SELECT b.*, f.full_name, f.farmer_uid, f.mobile_number, f.village, cr.crop_name, s.start_time, s.end_time, q.status as q_status
           FROM queue q
           JOIN bookings b ON q.booking_id = b.id
           JOIN farmers f ON b.farmer_id = f.id
           JOIN crops cr ON b.crop_id = cr.id
           JOIN slots s ON b.slot_id = s.id
           WHERE q.center_id = %s AND q.queue_date = %s
           ORDER BY q.position ASC""",
        (center_id, today)
    ) or []

    return render_template(
        'operator_dashboard.html',
        operator=operator,
        center=center,
        total_today=total_today,
        waiting_count=waiting_count,
        completed_count=completed_count,
        current_token=current_token,
        current_booking=current_booking,
        queue_items=queue_items,
        today_date=today.strftime('%d %B %Y')
    )

@app.route('/operator/call_next', methods=['POST'])
@role_required('operator')
def call_next_farmer():
    user_id = session.get('user_id')
    operator = query_db("SELECT * FROM operators WHERE user_id = %s", (user_id,), one=True)
    center_id = operator['center_id']
    today = date.today()

    # Find the first 'Waiting' token
    next_item = query_db(
        "SELECT * FROM queue WHERE center_id = %s AND queue_date = %s AND status = 'Waiting' ORDER BY position ASC LIMIT 1",
        (center_id, today),
        one=True
    )

    if next_item:
        query_db(
            "UPDATE queue SET status = 'In-Process', called_time = %s, counter_assigned = %s WHERE id = %s",
            (datetime.now(), operator.get('assigned_counter', 1), next_item['id']),
            commit=True
        )
        query_db(
            "UPDATE bookings SET status = 'Weighing' WHERE id = %s",
            (next_item['booking_id'],),
            commit=True
        )
        flash(f"Calling Token {next_item['token_number']} to Counter #{operator.get('assigned_counter', 1)}.", 'success')
    else:
        flash("No more farmers waiting in line today.", 'info')

    return redirect(url_for('operator_dashboard'))

@app.route('/operator/todays_queue')
@role_required('operator')
def todays_queue():
    user_id = session.get('user_id')
    operator = query_db("SELECT * FROM operators WHERE user_id = %s", (user_id,), one=True)
    center_id = operator['center_id']
    center = query_db("SELECT * FROM procurement_centers WHERE id = %s", (center_id,), one=True)
    today = date.today()

    queue_items = query_db(
        """SELECT b.*, f.full_name, f.farmer_uid, f.mobile_number, cr.crop_name, s.start_time, s.end_time
           FROM queue q
           JOIN bookings b ON q.booking_id = b.id
           JOIN farmers f ON b.farmer_id = f.id
           JOIN crops cr ON b.crop_id = cr.id
           JOIN slots s ON b.slot_id = s.id
           WHERE q.center_id = %s AND q.queue_date = %s
           ORDER BY q.position ASC""",
        (center_id, today)
    ) or []

    return render_template('todays_queue.html', center=center, queue_items=queue_items, today_date=today.strftime('%d %B %Y'))

@app.route('/operator/farmer/<int:farmer_id>')
@role_required('operator', 'admin')
def farmer_details(farmer_id):
    farmer = query_db("SELECT * FROM farmers WHERE id = %s", (farmer_id,), one=True)
    bookings = query_db(
        """SELECT b.*, cr.crop_name, s.slot_date 
           FROM bookings b
           JOIN crops cr ON b.crop_id = cr.id
           JOIN slots s ON b.slot_id = s.id
           WHERE b.farmer_id = %s ORDER BY b.id DESC""",
        (farmer_id,)
    ) or []
    return render_template('farmer_details.html', farmer=farmer, bookings=bookings)

@app.route('/operator/update_status/<int:booking_id>', methods=['GET', 'POST'])
@role_required('operator')
def update_procurement_status(booking_id):
    user_id = session.get('user_id')
    operator = query_db("SELECT * FROM operators WHERE user_id = %s", (user_id,), one=True)

    booking = query_db(
        """SELECT b.*, f.full_name, f.farmer_uid, f.bank_account_no, f.ifsc_code, cr.crop_name, cr.msp_per_quintal, cr.id as crop_id
           FROM bookings b
           JOIN farmers f ON b.farmer_id = f.id
           JOIN crops cr ON b.crop_id = cr.id
           WHERE b.id = %s""",
        (booking_id,),
        one=True
    )

    record = query_db("SELECT * FROM procurement_records WHERE booking_id = %s", (booking_id,), one=True)

    if request.method == 'POST':
        new_status = request.form.get('status')
        actual_qty = float(request.form.get('actual_quantity', 0.0) or 0.0)
        quality_grade = request.form.get('quality_grade', 'Grade A')
        moisture = float(request.form.get('moisture_content', 12.0) or 12.0)
        deduction_pct = float(request.form.get('deduction_percentage', 0.0) or 0.0)
        remarks = request.form.get('remarks', '')

        # Calculate final accepted weight
        deduction_qty = actual_qty * (deduction_pct / 100.0)
        final_qty = max(0.0, actual_qty - deduction_qty)

        # Update Booking Status
        query_db("UPDATE bookings SET status = %s WHERE id = %s", (new_status, booking_id), commit=True)

        # Upsert Procurement Record
        if record:
            query_db(
                """UPDATE procurement_records SET actual_quantity = %s, moisture_content = %s, quality_grade = %s, deduction_percentage = %s, final_accepted_quantity = %s, remarks = %s, status = 'Verified'
                   WHERE id = %s""",
                (actual_qty, moisture, quality_grade, deduction_pct, final_qty, remarks, record['id']),
                commit=True
            )
            proc_id = record['id']
        else:
            proc_id = query_db(
                """INSERT INTO procurement_records (booking_id, operator_id, center_id, actual_quantity, moisture_content, quality_grade, deduction_percentage, final_accepted_quantity, remarks, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Verified')""",
                (booking_id, operator['id'], booking['center_id'], actual_qty, moisture, quality_grade, deduction_pct, final_qty, remarks),
                commit=True
            )

        # If Completed or Accepted -> Generate Payment DBT Record
        if new_status in ['Accepted', 'Procurement Completed']:
            query_db("UPDATE queue SET status = 'Completed', completed_time = %s WHERE booking_id = %s", (datetime.now(), booking_id), commit=True)
            
            msp_rate = float(booking['msp_per_quintal'])
            total_amount = final_qty * msp_rate
            txn_ref = generate_dbt_txn_id()

            existing_pmt = query_db("SELECT id FROM payments WHERE booking_id = %s", (booking_id,), one=True)
            if existing_pmt:
                query_db(
                    "UPDATE payments SET total_amount = %s, msp_rate = %s, payment_status = 'Credited' WHERE id = %s",
                    (total_amount, msp_rate, existing_pmt['id']),
                    commit=True
                )
            else:
                query_db(
                    """INSERT INTO payments (procurement_id, booking_id, farmer_id, msp_rate, total_amount, payment_status, transaction_ref, payment_date, bank_status)
                       VALUES (%s, %s, %s, %s, %s, 'Credited', %s, %s, 'DBT Disbursed directly to farmer registered Bank A/C')""",
                    (proc_id, booking_id, booking['farmer_id'], msp_rate, total_amount, txn_ref, datetime.now()),
                    commit=True
                )

        flash(f"Procurement record for Token {booking['token_number']} updated to '{new_status}'.", 'success')
        return redirect(url_for('operator_dashboard'))

    return render_template('update_status.html', booking=booking, record=record)

# =========================================================================
# ADMIN PORTAL ROUTES
# =========================================================================

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    user_id = session.get('user_id')
    admin = query_db("SELECT * FROM admins WHERE user_id = %s", (user_id,), one=True)
    today = date.today()

    # Top KPI Metrics
    tf = query_db("SELECT COUNT(*) as c FROM farmers", one=True)
    total_farmers = tf['c'] if tf else 0

    tc = query_db("SELECT COUNT(*) as c FROM procurement_centers WHERE is_active = 1", one=True)
    total_centers = tc['c'] if tc else 0

    tb = query_db("SELECT COUNT(*) as c FROM queue WHERE queue_date = %s", (today,), one=True)
    today_bookings_count = tb['c'] if tb else 0

    wf = query_db("SELECT COUNT(*) as c FROM queue WHERE queue_date = %s AND status = 'Waiting'", (today,), one=True)
    waiting_farmers_count = wf['c'] if wf else 0

    cp = query_db("SELECT COUNT(*) as c FROM bookings WHERE status = 'Procurement Completed'", one=True)
    completed_procurements_count = cp['c'] if cp else 0

    # Chart.js Analytics Data
    # 1. Daily Bookings Trend (Past 7 Days)
    daily_labels = []
    daily_counts = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        daily_labels.append(d.strftime('%d %b'))
        cnt = query_db("SELECT COUNT(*) as c FROM bookings b JOIN slots s ON b.slot_id = s.id WHERE s.slot_date = %s", (d,), one=True)
        daily_counts.append(cnt['c'] if cnt else 0)

    # 2. Crop-wise Procurement Distribution
    crop_rows = query_db(
        """SELECT cr.crop_name, COALESCE(SUM(pr.final_accepted_quantity), 0) as total_qty 
           FROM crops cr
           LEFT JOIN bookings b ON b.crop_id = cr.id
           LEFT JOIN procurement_records pr ON pr.booking_id = b.id
           GROUP BY cr.id, cr.crop_name LIMIT 6"""
    ) or []
    crop_labels = [r['crop_name'].split('(')[0].strip() for r in crop_rows]
    crop_quantities = [float(r['total_qty']) for r in crop_rows]

    # 3. Center Queue Comparison & Congestion AI
    centers = query_db("SELECT * FROM procurement_centers WHERE is_active = 1") or []
    center_analyses = []
    center_names = []
    center_queues = []

    for c in centers:
        active_q = query_db(
            "SELECT * FROM queue WHERE center_id = %s AND queue_date = %s",
            (c['id'], today)
        ) or []
        analysis = SmartQueueEngine.analyze_center_queue(
            c['id'], c['center_name'], active_q, c.get('total_counters', 3), c.get('avg_processing_time_mins', 15)
        )
        analysis['district'] = c.get('district', 'Gujarat')
        center_analyses.append(analysis)
        center_names.append(c['center_name'].split(' ')[0] + ' Center')
        center_queues.append(analysis['waiting_farmers'])

    # 4. Payment Stats
    p_credited = query_db("SELECT COUNT(*) as c FROM payments WHERE payment_status = 'Credited'", one=True)
    p_processing = query_db("SELECT COUNT(*) as c FROM payments WHERE payment_status = 'Processing'", one=True)
    p_pending = query_db("SELECT COUNT(*) as c FROM payments WHERE payment_status = 'Pending'", one=True)
    payment_stats = [
        p_credited['c'] if p_credited else 1,
        p_processing['c'] if p_processing else 0,
        p_pending['c'] if p_pending else 0
    ]

    analytics_data = {
        'daily_labels': daily_labels,
        'daily_counts': daily_counts,
        'crop_labels': crop_labels if crop_labels else ['Wheat', 'Paddy', 'Groundnut', 'Gram', 'Mustard'],
        'crop_quantities': crop_quantities if any(crop_quantities) else [450, 320, 210, 180, 95],
        'center_names': center_names,
        'center_queues': center_queues,
        'payment_stats': payment_stats
    }

    return render_template(
        'admin_dashboard.html',
        admin=admin,
        total_farmers=total_farmers,
        total_centers=total_centers,
        today_bookings_count=today_bookings_count,
        waiting_farmers_count=waiting_farmers_count,
        completed_procurements_count=completed_procurements_count,
        center_analyses=center_analyses,
        analytics_data=analytics_data
    )

@app.route('/admin/manage_farmers')
@role_required('admin')
def manage_farmers():
    farmers = query_db("SELECT * FROM farmers ORDER BY id DESC") or []
    return render_template('manage_farmers.html', farmers=farmers)

@app.route('/admin/manage_centers', methods=['GET', 'POST'])
@role_required('admin')
def manage_centers():
    if request.method == 'POST':
        center_name = request.form.get('center_name')
        center_code = request.form.get('center_code')
        district = request.form.get('district')
        total_counters = int(request.form.get('total_counters', 3) or 3)
        address = request.form.get('address')
        contact_phone = request.form.get('contact_phone', '')

        query_db(
            """INSERT INTO procurement_centers (center_name, center_code, district, state, address, contact_phone, total_counters, avg_processing_time_mins, is_active)
               VALUES (%s, %s, %s, 'Gujarat', %s, %s, %s, 15, 1)""",
            (center_name, center_code, district, address, contact_phone, total_counters),
            commit=True
        )
        flash(f"Procurement Center '{center_name}' created successfully.", 'success')
        return redirect(url_for('manage_centers'))

    centers = query_db("SELECT * FROM procurement_centers ORDER BY id DESC") or []
    return render_template('manage_centers.html', centers=centers)

@app.route('/admin/manage_slots', methods=['GET', 'POST'])
@role_required('admin')
def manage_slots():
    today = date.today()
    if request.method == 'POST':
        center_id = request.form.get('center_id')
        slot_date = request.form.get('slot_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        max_capacity = int(request.form.get('max_capacity', 20) or 20)

        query_db(
            """INSERT INTO slots (center_id, slot_date, start_time, end_time, max_capacity, booked_count, is_active)
               VALUES (%s, %s, %s, %s, %s, 0, 1)""",
            (center_id, slot_date, start_time, end_time, max_capacity),
            commit=True
        )
        flash('Time slot created successfully.', 'success')
        return redirect(url_for('manage_slots'))

    centers = query_db("SELECT * FROM procurement_centers WHERE is_active = 1") or []
    slots = query_db(
        """SELECT s.*, c.center_name 
           FROM slots s
           JOIN procurement_centers c ON s.center_id = c.id
           WHERE s.slot_date >= %s
           ORDER BY s.slot_date ASC, s.start_time ASC""",
        (today,)
    ) or []

    return render_template('manage_slots.html', centers=centers, slots=slots, today_date=today.strftime('%Y-%m-%d'))

@app.route('/admin/delete_slot/<int:slot_id>', methods=['POST'])
@role_required('admin')
def delete_slot(slot_id):
    query_db("DELETE FROM slots WHERE id = %s", (slot_id,), commit=True)
    flash('Time slot removed.', 'info')
    return redirect(url_for('manage_slots'))

@app.route('/admin/procurement_records')
@role_required('admin', 'operator')
def admin_procurement_records():
    records = query_db(
        """SELECT pr.*, b.token_number, b.booking_ref, f.full_name, f.farmer_uid, c.center_name, cr.crop_name
           FROM procurement_records pr
           JOIN bookings b ON pr.booking_id = b.id
           JOIN farmers f ON b.farmer_id = f.id
           JOIN procurement_centers c ON pr.center_id = c.id
           JOIN crops cr ON b.crop_id = cr.id
           ORDER BY pr.id DESC"""
    ) or []
    return render_template('procurement_records.html', records=records)

@app.route('/admin/payments')
@role_required('admin')
def admin_payments():
    payments = query_db(
        """SELECT p.*, f.full_name, f.bank_account_no, f.ifsc_code, b.token_number, cr.crop_name, pr.final_accepted_quantity
           FROM payments p
           JOIN farmers f ON p.farmer_id = f.id
           JOIN bookings b ON p.booking_id = b.id
           JOIN crops cr ON b.crop_id = cr.id
           LEFT JOIN procurement_records pr ON p.procurement_id = pr.id
           ORDER BY p.id DESC"""
    ) or []
    return render_template('payments.html', payments=payments)

@app.route('/admin/update_payment/<int:payment_id>', methods=['POST'])
@role_required('admin')
def admin_update_payment(payment_id):
    txn = generate_dbt_txn_id()
    query_db(
        "UPDATE payments SET payment_status = 'Credited', transaction_ref = %s, payment_date = %s, bank_status = 'DBT Successfully Credited to Farmer Account' WHERE id = %s",
        (txn, datetime.now(), payment_id),
        commit=True
    )
    flash(f"DBT Payment #{payment_id} successfully credited (Txn: {txn}).", 'success')
    return redirect(url_for('admin_payments'))

@app.route('/admin/reports')
@role_required('admin')
def reports():
    tot_ton = query_db("SELECT COALESCE(SUM(final_accepted_quantity), 0) as s FROM procurement_records", one=True)
    total_tonnage = float(tot_ton['s']) if tot_ton else 0.0

    tot_pay = query_db("SELECT COALESCE(SUM(total_amount), 0) as s FROM payments WHERE payment_status = 'Credited'", one=True)
    total_disbursed = float(tot_pay['s']) if tot_pay else 0.0

    crop_stats = query_db(
        """SELECT cr.crop_name, cr.msp_per_quintal, 
                  COALESCE(SUM(pr.final_accepted_quantity), 0) as total_qty,
                  COALESCE(SUM(p.total_amount), 0) as total_amount
           FROM crops cr
           LEFT JOIN bookings b ON b.crop_id = cr.id
           LEFT JOIN procurement_records pr ON pr.booking_id = b.id
           LEFT JOIN payments p ON p.booking_id = b.id
           GROUP BY cr.id, cr.crop_name, cr.msp_per_quintal"""
    ) or []

    center_stats = query_db(
        """SELECT c.center_name, c.district, c.total_counters, COUNT(b.id) as total_bookings
           FROM procurement_centers c
           LEFT JOIN bookings b ON b.center_id = c.id
           GROUP BY c.id, c.center_name, c.district, c.total_counters"""
    ) or []

    return render_template(
        'reports.html',
        total_tonnage=total_tonnage,
        total_disbursed=total_disbursed,
        crop_stats=crop_stats,
        center_stats=center_stats
    )

# =========================================================================
# LIVE API ENDPOINTS
# =========================================================================

@app.route('/api/queue_status')
def api_queue_status():
    center_id = request.args.get('center_id', 1)
    user_token = request.args.get('token', '')
    today = date.today()

    center = query_db("SELECT * FROM procurement_centers WHERE id = %s", (center_id,), one=True)
    if not center:
        return jsonify({'success': False, 'message': 'Center not found'}), 404

    active_queue = query_db(
        """SELECT q.*, b.crop_quantity, f.full_name, cr.crop_name 
           FROM queue q
           JOIN bookings b ON q.booking_id = b.id
           JOIN farmers f ON b.farmer_id = f.id
           JOIN crops cr ON b.crop_id = cr.id
           WHERE q.center_id = %s AND q.queue_date = %s
           ORDER BY q.position ASC""",
        (center_id, today)
    ) or []

    visual_data = SmartQueueEngine.build_visual_queue(active_queue, user_token)
    
    calling = query_db(
        "SELECT token_number FROM queue WHERE center_id = %s AND queue_date = %s AND status IN ('Calling', 'In-Process') LIMIT 1",
        (center_id, today),
        one=True
    )
    calling_token = calling['token_number'] if calling else None

    counters = center.get('total_counters', 3)
    avg_proc = center.get('avg_processing_time_mins', 15)
    est_wait = SmartQueueEngine.calculate_estimated_wait_time(visual_data['people_ahead'], counters, avg_proc)

    return jsonify({
        'success': True,
        'center_name': center['center_name'],
        'people_ahead': visual_data['people_ahead'],
        'estimated_wait_mins': est_wait,
        'expected_time': SmartQueueEngine.calculate_expected_completion_time(est_wait),
        'calling_token': calling_token,
        'visual_items': visual_data['visual_items']
    })

# ----------------- Runner -----------------
if __name__ == '__main__':
    print("=================================================================")
    print(" Smart Farmer Procurement & Queue System (SIH26032)")
    print(" Running locally at: http://127.0.0.1:5000")
    print(" Test Logins:")
    print("   Farmer:    username = farmer1   | password = farmer123")
    print("   Operator:  username = operator1 | password = operator123")
    print("   Admin:     username = admin     | password = admin123")
    print("=================================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)

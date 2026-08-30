import os
import sys
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

# Ensure root dir is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, query_db, DB_MODE

def seed_database():
    print("[Database Seed] Initializing tables if needed...")
    init_db()
    
    # Check if already seeded
    existing_admin = query_db("SELECT id FROM users WHERE username = %s", ('admin',), one=True)
    if existing_admin:
        print("[Database Seed] Database already contains seed records. Re-verifying key accounts...")
        return
        
    print("[Database Seed] Seeding Users, Farmers, Operators, Admins, Crops, Centers, Slots, Bookings, Queue...")

    # 1. Seed Users & Admins
    admin_pass = generate_password_hash('admin123')
    admin_user_id = query_db(
        "INSERT INTO users (username, password_hash, role, email, phone) VALUES (%s, %s, %s, %s, %s)",
        ('admin', admin_pass, 'admin', 'admin.procurement@gov.in', '9876543210'),
        commit=True
    )
    query_db(
        "INSERT INTO admins (user_id, full_name, department, designation) VALUES (%s, %s, %s, %s)",
        (admin_user_id, 'Dr. Rajesh Sharma', 'Dept of Agriculture & Cooperation', 'State Procurement Director'),
        commit=True
    )

    # 2. Seed Procurement Centers
    centers_data = [
        ('Anand Central Mandi Procurement Hub', 'CTR-AND-01', 'Anand', 'Gujarat', 'Near APMC Yard, Borsad Road, Anand - 388001', '02692-245110', 4, 12),
        ('Navsari Kisan Samiti Procurement Center', 'CTR-NAV-02', 'Navsari', 'Gujarat', 'National Highway 48, Eru Char Rasta, Navsari - 396450', '02637-284920', 3, 15),
        ('Patan Krishi Upaj Mandi Center', 'CTR-PAT-03', 'Patan', 'Gujarat', 'State Highway 7, Near Sardar Patel Chowk, Patan - 384265', '02766-221045', 2, 18),
        ('Vadodara PACS Regional Procurement Point', 'CTR-VAD-04', 'Vadodara', 'Gujarat', 'Vemali Road, Sama-Savli Highway, Vadodara - 390024', '0265-2789123', 3, 14),
        ('Rajkot Grain Mandi Direct Counter', 'CTR-RJK-05', 'Rajkot', 'Gujarat', 'Bedi Marketing Yard, Morbi Bypass Road, Rajkot - 360003', '0281-2704112', 4, 10)
    ]
    
    center_ids = []
    for c in centers_data:
        cid = query_db(
            "INSERT INTO procurement_centers (center_name, center_code, district, state, address, contact_phone, total_counters, avg_processing_time_mins, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], 1),
            commit=True
        )
        center_ids.append(cid)

    # 3. Seed Operators
    op_pass = generate_password_hash('operator123')
    
    # Operator 1 for Anand Center
    op1_user_id = query_db(
        "INSERT INTO users (username, password_hash, role, email, phone) VALUES (%s, %s, %s, %s, %s)",
        ('operator1', op_pass, 'operator', 'operator.anand@gov.in', '9825102030'),
        commit=True
    )
    query_db(
        "INSERT INTO operators (user_id, center_id, full_name, badge_id, assigned_counter) VALUES (%s, %s, %s, %s, %s)",
        (op1_user_id, center_ids[0], 'Maheshbhai Patel', 'OP-AND-101', 1),
        commit=True
    )

    # Operator 2 for Navsari Center
    op2_user_id = query_db(
        "INSERT INTO users (username, password_hash, role, email, phone) VALUES (%s, %s, %s, %s, %s)",
        ('operator2', op_pass, 'operator', 'operator.navsari@gov.in', '9825104050'),
        commit=True
    )
    query_db(
        "INSERT INTO operators (user_id, center_id, full_name, badge_id, assigned_counter) VALUES (%s, %s, %s, %s, %s)",
        (op2_user_id, center_ids[1], 'Sureshbhai Desai', 'OP-NAV-102', 1),
        commit=True
    )

    # 4. Seed Farmers
    farmer_pass = generate_password_hash('farmer123')
    
    farmers_data = [
        ('farmer1', 'Ramesh Kumar Solanki', 'FMR-GJ-2026-001', '9876500001', 'Boriavi', 'Anand', 6.50, 'SBIN0004128911', 'SBIN0001234'),
        ('farmer2', 'Jayantilal Prajapati', 'FMR-GJ-2026-002', '9876500002', 'Vansda', 'Navsari', 8.20, 'BKID0007812903', 'BKID0005678'),
        ('farmer3', 'Govindbhai Chaudhary', 'FMR-GJ-2026-003', '9876500003', 'Chanasma', 'Patan', 12.00, 'BARB0PATANX1', 'BARB0PATANX'),
        ('farmer4', 'Dineshbhai Vaghela', 'FMR-GJ-2026-004', '9876500004', 'Karjan', 'Vadodara', 5.00, 'PUNB018274612', 'PUNB0182746'),
        ('farmer5', 'Bhupatbhai Ahir', 'FMR-GJ-2026-005', '9876500005', 'Gondal', 'Rajkot', 15.50, 'HDFC000192837', 'HDFC0001928')
    ]
    
    farmer_ids = []
    for f in farmers_data:
        f_user_id = query_db(
            "INSERT INTO users (username, password_hash, role, email, phone) VALUES (%s, %s, %s, %s, %s)",
            (f[0], farmer_pass, 'farmer', f'{f[0]}@kisanmail.in', f[3]),
            commit=True
        )
        fid = query_db(
            "INSERT INTO farmers (user_id, farmer_uid, full_name, mobile_number, village, district, state, land_size_acres, bank_account_no, ifsc_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (f_user_id, f[2], f[1], f[3], f[4], f[5], 'Gujarat', f[6], f[7], f[8]),
            commit=True
        )
        farmer_ids.append(fid)

    # 5. Seed Crops with Govt MSP 2026 Rates (INR per Quintal)
    crops_data = [
        ('Wheat (Sharbati / Mill Quality)', 'Cereal', 2425.00, 'Quintal', 'Govt MSP approved fair average quality grain with moisture <= 12%'),
        ('Paddy (Common / Grade-A)', 'Cereal', 2300.00, 'Quintal', 'Clean matured paddy grains, sound quality and moisture <= 17%'),
        ('Groundnut (Pod)', 'Oilseed', 6783.00, 'Quintal', 'Properly dried pods with high oil recovery percentage'),
        ('Gram / Chana', 'Pulses', 5650.00, 'Quintal', 'Clean whole chana grains without infestation'),
        ('Mustard / Rapeseed', 'Oilseed', 5950.00, 'Quintal', 'High oil content seeds with minimal foreign matter'),
        ('Cotton (Medium Staple)', 'Commercial', 7121.00, 'Quintal', 'Clean lint cotton without yellowing or trash'),
        ('Soybean (Yellow)', 'Oilseed', 4892.00, 'Quintal', 'Sound yellow soybean grain for direct processing'),
        ('Bajra (Pearl Millet)', 'Millet / Nutri-Cereal', 2625.00, 'Quintal', 'Nutri-cereal procurement under National Food Security Mission')
    ]
    
    crop_ids = []
    for cr in crops_data:
        crid = query_db(
            "INSERT INTO crops (crop_name, category, msp_per_quintal, unit, description) VALUES (%s, %s, %s, %s, %s)",
            (cr[0], cr[1], cr[2], cr[3], cr[4]),
            commit=True
        )
        crop_ids.append(crid)

    # 6. Seed Time Slots (Today, Tomorrow, and Next 5 Days)
    today = date.today()
    slot_ids = []
    
    time_windows = [
        ('09:00:00', '11:00:00', 15),
        ('11:00:00', '13:00:00', 15),
        ('14:00:00', '16:00:00', 15),
        ('16:00:00', '18:00:00', 15)
    ]
    
    for c_id in center_ids:
        for day_offset in range(0, 7):
            cur_date = today + timedelta(days=day_offset)
            for tw in time_windows:
                sid = query_db(
                    "INSERT INTO slots (center_id, slot_date, start_time, end_time, max_capacity, booked_count, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (c_id, cur_date, tw[0], tw[1], tw[2], 0, 1),
                    commit=True
                )
                slot_ids.append(sid)

    # 7. Seed Active Bookings & Live Queue for Today
    today_slot_center1 = slot_ids[0] # Anand center slot 1
    
    # Booking 1 (Completed earlier today)
    b1_id = query_db(
        "INSERT INTO bookings (booking_ref, farmer_id, center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_number, status, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ('BK-2026-9001', farmer_ids[4], center_ids[0], today_slot_center1, crop_ids[0], 45.00, today - timedelta(days=3), 'A101', 1, 'Procurement Completed', 'Verified Grade A'),
        commit=True
    )
    query_db(
        "INSERT INTO queue (center_id, booking_id, queue_date, token_number, position, status, counter_assigned, arrival_time, called_time, completed_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (center_ids[0], b1_id, today, 'A101', 1, 'Completed', 1, datetime.now() - timedelta(minutes=90), datetime.now() - timedelta(minutes=75), datetime.now() - timedelta(minutes=60)),
        commit=True
    )
    p1_id = query_db(
        "INSERT INTO procurement_records (booking_id, operator_id, center_id, actual_quantity, moisture_content, quality_grade, deduction_percentage, final_accepted_quantity, remarks, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (b1_id, 1, center_ids[0], 45.00, 11.20, 'Grade A', 0.00, 45.00, 'Excellent quality wheat grain delivered in standard bags', 'Accepted'),
        commit=True
    )
    query_db(
        "INSERT INTO payments (procurement_id, booking_id, farmer_id, msp_rate, total_amount, payment_status, transaction_ref, payment_date, bank_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (p1_id, b1_id, farmer_ids[4], 2425.00, 109125.00, 'Credited', 'DBT-2026-TXN-884910', datetime.now() - timedelta(minutes=30), 'Transferred successfully via NPCI-DBT to Bank of Baroda'),
        commit=True
    )

    # Booking 2 (Currently in process at Counter 1)
    b2_id = query_db(
        "INSERT INTO bookings (booking_ref, farmer_id, center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_number, status, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ('BK-2026-9002', farmer_ids[1], center_ids[0], today_slot_center1, crop_ids[2], 30.00, today - timedelta(days=2), 'A102', 2, 'Weighing', 'Weighbridge check active'),
        commit=True
    )
    query_db(
        "INSERT INTO queue (center_id, booking_id, queue_date, token_number, position, status, counter_assigned, arrival_time, called_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (center_ids[0], b2_id, today, 'A102', 2, 'In-Process', 1, datetime.now() - timedelta(minutes=40), datetime.now() - timedelta(minutes=10)),
        commit=True
    )

    # Booking 3 (Waiting in line - Farmer 3)
    b3_id = query_db(
        "INSERT INTO bookings (booking_ref, farmer_id, center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_number, status, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ('BK-2026-9003', farmer_ids[2], center_ids[0], today_slot_center1, crop_ids[3], 50.00, today - timedelta(days=1), 'A103', 3, 'Arrived', 'Vehicle waiting in holding bay'),
        commit=True
    )
    query_db(
        "INSERT INTO queue (center_id, booking_id, queue_date, token_number, position, status, counter_assigned, arrival_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (center_ids[0], b3_id, today, 'A103', 3, 'Waiting', 1, datetime.now() - timedelta(minutes=25)),
        commit=True
    )

    # Booking 4 (Primary Test Farmer 1 - Token A104 - Waiting)
    b4_id = query_db(
        "INSERT INTO bookings (booking_ref, farmer_id, center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_number, status, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ('BK-2026-9004', farmer_ids[0], center_ids[0], today_slot_center1, crop_ids[0], 60.00, today - timedelta(days=2), 'A104', 4, 'Booked', 'Appointment confirmed for morning slot'),
        commit=True
    )
    query_db(
        "INSERT INTO queue (center_id, booking_id, queue_date, token_number, position, status, counter_assigned) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (center_ids[0], b4_id, today, 'A104', 4, 'Waiting', 1),
        commit=True
    )

    # Booking 5 (Waiting after Farmer 1 - Token A105)
    b5_id = query_db(
        "INSERT INTO bookings (booking_ref, farmer_id, center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_number, status, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ('BK-2026-9005', farmer_ids[3], center_ids[0], today_slot_center1, crop_ids[1], 40.00, today - timedelta(days=1), 'A105', 5, 'Waiting', 'Slot booked'),
        commit=True
    )
    query_db(
        "INSERT INTO queue (center_id, booking_id, queue_date, token_number, position, status, counter_assigned) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (center_ids[0], b5_id, today, 'A105', 5, 'Waiting', 1),
        commit=True
    )

    # Update booked count on the slot
    query_db("UPDATE slots SET booked_count = 5 WHERE id = %s", (today_slot_center1,), commit=True)

    print("[Database Seed] Seed data successfully populated.")
    print("--------------------------------------------------")
    print("Test Login Credentials:")
    print("1. Admin:    username = admin      | password = admin123")
    print("2. Operator: username = operator1  | password = operator123")
    print("3. Farmer:   username = farmer1    | password = farmer123")
    print("--------------------------------------------------")

if __name__ == '__main__':
    seed_database()

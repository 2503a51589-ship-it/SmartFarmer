import os
import sqlite3
import mysql.connector
from config import Config

DB_MODE = 'mysql'
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'smart_farmer.db')

def try_mysql_connection():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.close()
        conn.close()
        
        db_conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            autocommit=True
        )
        return db_conn
    except Exception as e:
        # If MySQL connection fails (e.g. custom root password or not running), we safely log and fallback
        return None

def get_db():
    global DB_MODE
    mysql_conn = try_mysql_connection()
    if mysql_conn is not None:
        DB_MODE = 'mysql'
        return mysql_conn
    else:
        DB_MODE = 'sqlite'
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def query_db(query, args=(), one=False, commit=False):
    global DB_MODE
    conn = get_db()
    
    if DB_MODE == 'mysql':
        cursor = conn.cursor(dictionary=True)
        try:
            formatted_query = query.replace('?', '%s')
            cursor.execute(formatted_query, args)
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
                cursor.close()
                conn.close()
                return last_id if last_id else rowcount
            else:
                rv = cursor.fetchall()
                cursor.close()
                conn.close()
                return (rv[0] if rv else None) if one else rv
        except Exception as err:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
            raise err
    else:
        cursor = conn.cursor()
        try:
            formatted_query = query.replace('%s', '?')
            cursor.execute(formatted_query, args)
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
                conn.close()
                return last_id if last_id else rowcount
            else:
                rows = cursor.fetchall()
                dict_rows = [dict(r) for r in rows]
                conn.close()
                return (dict_rows[0] if dict_rows else None) if one else dict_rows
        except Exception as err:
            try:
                conn.close()
            except Exception:
                pass
            raise err

def init_db():
    conn = get_db()
    global DB_MODE
    
    if DB_MODE == 'mysql':
        sql_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'smart_farmer.sql')
        if os.path.exists(sql_file_path):
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            cursor = conn.cursor()
            for statement in sql_script.split(';'):
                stmt = statement.strip()
                if stmt and not stmt.lower().startswith('create database') and not stmt.lower().startswith('use '):
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        pass
            cursor.close()
            conn.close()
    else:
        cursor = conn.cursor()
        sqlite_schema = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'farmer',
            email TEXT,
            phone TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS procurement_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT NOT NULL,
            center_code TEXT NOT NULL UNIQUE,
            district TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'Gujarat',
            address TEXT NOT NULL,
            contact_phone TEXT,
            total_counters INTEGER NOT NULL DEFAULT 3,
            avg_processing_time_mins INTEGER NOT NULL DEFAULT 15,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            farmer_uid TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            mobile_number TEXT NOT NULL,
            village TEXT NOT NULL,
            district TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'Gujarat',
            land_size_acres REAL DEFAULT 0.00,
            bank_account_no TEXT,
            ifsc_code TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            department TEXT NOT NULL DEFAULT 'Agriculture & Food Procurement Dept',
            designation TEXT DEFAULT 'District Procurement Officer',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            center_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            badge_id TEXT NOT NULL UNIQUE,
            assigned_counter INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (center_id) REFERENCES procurement_centers(id)
        );
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT 'Cereal',
            msp_per_quintal REAL NOT NULL,
            unit TEXT NOT NULL DEFAULT 'Quintal',
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_id INTEGER NOT NULL,
            slot_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            max_capacity INTEGER NOT NULL DEFAULT 20,
            booked_count INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (center_id) REFERENCES procurement_centers(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_ref TEXT NOT NULL UNIQUE,
            farmer_id INTEGER NOT NULL,
            center_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            crop_id INTEGER NOT NULL,
            crop_quantity REAL NOT NULL,
            harvest_date DATE NOT NULL,
            token_number TEXT NOT NULL,
            queue_number INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'Booked',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
            FOREIGN KEY (center_id) REFERENCES procurement_centers(id),
            FOREIGN KEY (slot_id) REFERENCES slots(id),
            FOREIGN KEY (crop_id) REFERENCES crops(id)
        );
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_id INTEGER NOT NULL,
            booking_id INTEGER NOT NULL UNIQUE,
            queue_date DATE NOT NULL,
            token_number TEXT NOT NULL,
            position INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Waiting',
            counter_assigned INTEGER DEFAULT 1,
            arrival_time DATETIME NULL,
            called_time DATETIME NULL,
            completed_time DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (center_id) REFERENCES procurement_centers(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS procurement_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL UNIQUE,
            operator_id INTEGER NOT NULL,
            center_id INTEGER NOT NULL,
            actual_quantity REAL NOT NULL,
            moisture_content REAL DEFAULT 12.00,
            quality_grade TEXT NOT NULL DEFAULT 'Grade A',
            deduction_percentage REAL DEFAULT 0.00,
            final_accepted_quantity REAL NOT NULL,
            rejection_reason TEXT NULL,
            remarks TEXT,
            status TEXT NOT NULL DEFAULT 'Verified',
            verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
            FOREIGN KEY (operator_id) REFERENCES operators(id),
            FOREIGN KEY (center_id) REFERENCES procurement_centers(id)
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            procurement_id INTEGER NOT NULL UNIQUE,
            booking_id INTEGER NOT NULL UNIQUE,
            farmer_id INTEGER NOT NULL,
            msp_rate REAL NOT NULL,
            total_amount REAL NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Pending',
            transaction_ref TEXT NULL UNIQUE,
            payment_date DATETIME NULL,
            bank_status TEXT DEFAULT 'Payment Initiated under Govt DBT Scheme',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (procurement_id) REFERENCES procurement_records(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (farmer_id) REFERENCES farmers(id)
        );
        '''
        cursor.executescript(sqlite_schema)
        conn.commit()
        conn.close()


# Smart Farmer Procurement & Queue System (SIH26032)

A modern full-stack web application designed for the Smart India Hackathon problem statement **SIH26032**.

---

## Key Features & Highlights

1. **Farmer Portal**:
   - Crop harvest details registration (Wheat, Paddy, Groundnut, Gram, Mustard, Cotton, etc.)
   - Instant MSP estimation & procurement center selection.
   - Dynamic time slot booking with auto-generated digital token slip (e.g. `A104`).
   - Live visual queue tracking with countdown timer (`A100 Completed -> A101 Completed -> A102 Processing -> A103 Waiting -> A104 Your Token`).
   - Multi-step procurement stage progress bar (`Booked -> Arrived -> Weighing -> Quality Checking -> Accepted -> Completed`).
   - Direct Benefit Transfer (DBT) payment ledger and transaction reference tracking.
   - Booking history with one-click cancellation.

2. **Procurement Center Operator Portal**:
   - Operator live console with active counter caller.
   - "Call Next Farmer" instant queue transition.
   - Electronic weighbridge & quality verification grading (Gross weight, Grade A/B/C, moisture %, deduction %).
   - Auto-calculation of net payout and trigger of DBT settlement.

3. **Admin Command Center**:
   - State-level dashboard with 5 real-time KPI metrics.
   - 4 interactive Chart.js visualizations (Daily Bookings Trend, Crop-wise Procurement, Center-wise Congestion Comparison, DBT Payment Status).
   - Time slot scheduling and capacity management.
   - Complete audit trail of farmers, centers, procurement records, and financial payments.

4. **SIH Innovation: Smart Queue Prediction & Congestion AI**:
   - Calculates waiting time dynamically:
     $$\text{Estimated Waiting Time} = \left\lceil \frac{\text{People Ahead}}{\text{Active Counters}} \right\rceil \times \text{Avg Processing Time}$$
   - Congestion classification: **LOW CONGESTION**, **MEDIUM CONGESTION**, **HIGH CONGESTION**.
   - Smart Recommendation Card recommending least crowded centers to save time for farmers.

---

## Test Login Credentials

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Farmer** | `farmer1` | `farmer123` | Book slot, track live queue, view DBT payments |
| **Center Operator** | `operator1` | `operator123` | Call next token, record weighing & quality grade |
| **Admin** | `admin` | `admin123` | Manage centers, slots, view Chart.js analytics |

---

## Quick Start Guide

### 1. Requirements
- Python 3.10+
- MySQL Server (optional; works with native MySQL or automatic demo fallback)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```bash
python database/seed_data.py
```

### 4. Run Application
```bash
python run.py
```
Open **`http://127.0.0.1:5000`** in your browser.

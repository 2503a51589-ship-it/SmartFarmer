with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''@app.route('/farmer/book_slot', methods=['GET', 'POST'])
@role_required('farmer')
def book_slot():
    return "STEP 2 - with role_required decorator only"'''

new = '''@app.route('/farmer/book_slot', methods=['GET', 'POST'])
@role_required('farmer')
def book_slot():
    user_id = session.get('user_id')
    farmer = query_db("SELECT * FROM farmers WHERE user_id = %s", (user_id,), one=True)
    today = date.today()
    selected_center_id = request.args.get('center_id')
    crops = query_db("SELECT * FROM crops ORDER BY crop_name ASC") or []
    centers = query_db("SELECT * FROM procurement_centers WHERE is_active = 1 ORDER BY center_name ASC") or []
    slots = query_db(
        "SELECT * FROM slots WHERE slot_date >= %s AND is_active = 1 ORDER BY slot_date ASC, start_time ASC",
        (today,)
    ) or []
    return f"STEP 3 - queries done. crops={len(crops)} centers={len(centers)} slots={len(slots)} farmer={farmer}"'''

if old not in content:
    print("ERROR: could not find the step-2 test function. No changes made.")
    exit(1)

content = content.replace(old, new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: added database queries back.")
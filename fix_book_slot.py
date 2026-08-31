import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "@app.route('/farmer/book_slot'"
end_marker = "@app.route('/farmer/my_token')"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1:
    print("ERROR: Could not find the book_slot route start. No changes made.")
    exit(1)
if end_idx == -1:
    print("ERROR: Could not find the my_token route (used as the end marker). No changes made.")
    exit(1)
if end_idx < start_idx:
    print("ERROR: my_token route appears before book_slot route - unexpected file structure. No changes made.")
    exit(1)

new_function = '''@app.route('/farmer/book_slot', methods=['GET', 'POST'])
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

        slot = query_db("SELECT * FROM slots WHERE id = %s AND is_active = 1", (slot_id,), one=True)
        if not slot:
            flash('Selected time slot is invalid or no longer available.', 'danger')
            return redirect(url_for('book_slot'))

        if slot['booked_count'] >= slot['max_capacity']:
            flash('Selected time slot is full. Please choose another slot or center.', 'warning')
            return redirect(url_for('book_slot'))

        booking_ref = generate_booking_ref()
        token_number = generate_token_number(center_id, slot['slot_date'])

        existing_q_count = query_db(
            "SELECT COUNT(*) as c FROM queue WHERE center_id = %s AND queue_date = %s",
            (center_id, slot['slot_date']),
            one=True
        )
        queue_pos = (existing_q_count['c'] if existing_q_count else 0) + 1

        booking_id = query_db(
            """INSERT INTO bookings (booking_ref, farmer_id, center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_number, status, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Booked', %s)""",
            (booking_ref, farmer['id'], center_id, slot_id, crop_id, crop_quantity, harvest_date, token_number, queue_pos, notes),
            commit=True
        )

        query_db(
            """INSERT INTO queue (center_id, booking_id, queue_date, token_number, position, status, counter_assigned)
               VALUES (%s, %s, %s, %s, %s, 'Waiting', 1)""",
            (center_id, booking_id, slot['slot_date'], token_number, queue_pos),
            commit=True
        )

        query_db("UPDATE slots SET booked_count = booked_count + 1 WHERE id = %s", (slot_id,), commit=True)

        flash(f"Slot booked successfully! Your Token Number is {token_number} (Ref: {booking_ref}).", 'success')
        return redirect(url_for('my_token', booking_id=booking_id))

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

'''

new_content = content[:start_idx] + new_function + content[end_idx:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: book_slot route replaced cleanly.")
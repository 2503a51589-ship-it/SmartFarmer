with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''@app.route('/farmer/book_slot', methods=['GET', 'POST'])
def book_slot():
    return "HELLO WORLD - SIMPLEST POSSIBLE TEST, NO DECORATOR, NO LOGIC"'''

new = '''@app.route('/farmer/book_slot', methods=['GET', 'POST'])
@role_required('farmer')
def book_slot():
    return "STEP 2 - with role_required decorator only"'''

if old not in content:
    print("ERROR: could not find the step-1 test function. No changes made.")
    exit(1)

content = content.replace(old, new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: added role_required decorator back.")
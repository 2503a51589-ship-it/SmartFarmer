with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "@app.route('/farmer/book_slot'"
end_marker = "@app.route('/farmer/my_token')"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
    print("ERROR: markers not found correctly. No changes made.")
    exit(1)

new_function = '''@app.route('/farmer/book_slot', methods=['GET', 'POST'])
def book_slot():
    return "HELLO WORLD - SIMPLEST POSSIBLE TEST, NO DECORATOR, NO LOGIC"

'''

new_content = content[:start_idx] + new_function + content[end_idx:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: book_slot simplified to bare minimum.")
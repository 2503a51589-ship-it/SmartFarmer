with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    return f"STEP 3 - queries done. crops={len(crops)} centers={len(centers)} slots={len(slots)} farmer={farmer}"'''

new = '''    from flask import render_template_string
    return render_template_string("<h1>STEP 4 - fake template works. Crops: {{ crops|length }}</h1>", crops=crops, centers=centers, slots=slots)'''

if old not in content:
    print("ERROR: could not find the step-3 test line. No changes made.")
    exit(1)

content = content.replace(old, new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: testing with fake inline template.")
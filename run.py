from app import app

if __name__ == '__main__':
    print("=================================================================")
    print(" Smart Farmer Procurement & Queue System (SIH26032)")
    print(" Server started at http://127.0.0.1:5000")
    print("=================================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)

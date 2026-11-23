from db import test_connection

success, result = test_connection()

if success:
    print("Database connected successfully!")
    print("Database:", result)
else:
    print("Connection failed:")
    print(result)
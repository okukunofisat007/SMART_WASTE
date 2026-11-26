
from auth import create_admin
from getpass import getpass


print("CREATE ILORIN SMART WASTE ADMIN ACCOUNT")

full_name = input("Enter your full name: ")
email = input("Enter your email: ")
phone = input("Enter your phone number: ")

password = getpass("Create your password: ")
confirm_password = getpass("Confirm your password: ")


if password != confirm_password:
    print("Passwords do not match.")

elif len(password) < 8:
    print("Password must contain at least 8 characters.")

else:

    try:

        user_id = create_admin(
            full_name=full_name,
            email=email,
            password=password,
            phone=phone
        )

        print("Administrator account created successfully!")
        print("Admin ID:", user_id)

    except Exception as e:
        print("Account creation failed:", e)

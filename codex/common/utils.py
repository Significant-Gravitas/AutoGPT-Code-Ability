import string
import random


def generate_db_credentials(username_prefix="user", password_length=16):
    username = f"{username_prefix}{random.randint(1000, 9999)}"
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    password = "".join(random.choice(characters) for i in range(password_length))
    return username, password

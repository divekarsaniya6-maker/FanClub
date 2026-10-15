"""
FanClub Platform - Administrator CLI Provisioning Utility
Creates or promotes an administrator securely via CLI arguments or interactive prompts.
"""
import os
import sys
import getpass
import argparse

# Ensure project root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from models import db, User
from werkzeug.security import generate_password_hash

def create_or_promote_admin(name, email, phone, password):
    email = email.strip().lower()
    name = name.strip()
    phone = phone.strip()

    if not name or not email or not phone or not password:
        print("[!] Error: All fields (name, email, phone, password) are required.")
        return False

    if len(password) < 8:
        print("[!] Error: Administrator password must be at least 8 characters long.")
        return False

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        hashed = generate_password_hash(password)

        if user:
            print(f"[*] Account '{email}' exists. Promoting to Administrator...")
            user.role = 'admin'
            user.name = name
            user.phone = phone
            user.password_hash = hashed
            db.session.commit()
            print(f"[+] User '{email}' promoted to Administrator successfully!")
        else:
            new_admin = User(
                name=name,
                email=email,
                phone=phone,
                password_hash=hashed,
                role='admin'
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"[+] Administrator '{name}' ({email}) created successfully!")

    return True

def main():
    parser = argparse.ArgumentParser(description="Create or promote an administrator for FanClub")
    parser.add_argument("--name", help="Full name of administrator")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--phone", help="Administrator contact phone number")
    parser.add_argument("--password", help="Administrator password (min 8 characters)")

    args = parser.parse_args()

    name = args.name
    email = args.email
    phone = args.phone
    password = args.password

    if not name or not email or not phone or not password:
        print("=" * 60)
        print("⚽ FANCLUB - SECURE ADMINISTRATOR PROVISIONING")
        print("=" * 60)
        if not name:
            name = input("Enter Administrator Full Name: ").strip()
        if not email:
            email = input("Enter Administrator Email: ").strip()
        if not phone:
            phone = input("Enter Administrator Phone: ").strip()
        if not password:
            password = getpass.getpass("Enter Administrator Password (min 8 chars): ").strip()
            confirm = getpass.getpass("Confirm Administrator Password: ").strip()
            if password != confirm:
                print("[!] Error: Passwords do not match.")
                sys.exit(1)

    success = create_or_promote_admin(name, email, phone, password)
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()

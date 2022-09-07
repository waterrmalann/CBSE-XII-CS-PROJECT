## Import Necessary Modules.
import os
import mysql.connector
import time
import random
import pyperclip

## Hashing, Encoding, & Encryption.
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import bcrypt
import base64

# Connect to local database and retrieve cursor.
DATABASE = mysql.connector.connect(
    host="localhost",
    user="user",
    password="password"
)
DB_CURSOR = DATABASE.cursor()

DB_CURSOR.execute("CREATE DATABASE IF NOT EXISTS userpasswds")
DB_CURSOR.execute("USE userpasswds")

# Check if entries table is already defined.
query = DB_CURSOR.execute("SHOW TABLES LIKE 'entries'")
result = DB_CURSOR.fetchone()
if not result:
    # If not, create the table.
    DB_CURSOR.execute("CREATE TABLE entries(id VARCHAR(4), title VARCHAR(32), profile VARCHAR(32), password VARCHAR(512), notes VARCHAR(512), timestamp VARCHAR(18))")

# Check if config table is already defined.
query = DB_CURSOR.execute("SHOW TABLES LIKE 'config'")
result = DB_CURSOR.fetchone()
if not result:
    # If not, create the table.
    DB_CURSOR.execute("CREATE TABLE config(keyName VARCHAR(128), keyValue VARCHAR(512))")
    DB_CURSOR.execute("INSERT INTO config VALUES(%s, %s)", ('masterPassword', ''))
    DATABASE.commit()

# Global Variables          
MASTER_PASS = ''

# Utility functions to hash, encrypt, and decrypt passwords.
def hash_SHA256(text):
    """Hash an input string using the SHA-256 hashing algorithm."""
    return SHA256.new(text.encode()).hexdigest()

def derive_key(password):
    """Derive a fixed length key from a password string."""
    b64pwd = base64.b64encode(SHA256.new(password.encode()).digest())
    bcrypt_hash = bcrypt(b64pwd, 12, b'salt for bcrypt1')
    return bcrypt_hash[:32]

def encrypt_AES(text, key):
    """Encrypt a string using the AES-256 encryption algorithm."""
    cipher = AES.new(key, AES.MODE_CFB, key[::-1][:16])
    return base64.b64encode(cipher.encrypt(text.encode())).decode()

def decrypt_AES(text, key):
    """Decrypt an AES-256 encrypted string from key."""
    cipher = AES.new(key, AES.MODE_CFB, key[::-1][:16])
    return cipher.decrypt(base64.b64decode(text)).decode()

# Utility functions to manage the windows console.
def cls():
    """Clear the console screen."""
    os.system('cls')

def color(clr):
    """Set the console text color."""
    os.system(f'color {clr}')

def title(text):
    """Set the console window title."""
    os.system(f'title {text}')

def pause(message):
    """Pause the console window and await keyboard input."""
    print(message)
    os.system('pause>nul')

def print_header():
    """Print a large fancy heading text."""
    print()
    print(r"  ██████╗ ██╗   ██╗██████╗  █████╗ ███████╗███████╗")
    print(r"  ██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔════╝██╔════╝")
    print(r"  ██████╔╝ ╚████╔╝ ██████╔╝███████║███████╗███████╗")
    print(r"  ██╔═══╝   ╚██╔╝  ██╔═══╝ ██╔══██║╚════██║╚════██║")
    print(r"  ██║        ██║   ██║     ██║  ██║███████║███████║")
    print(r"  ╚═╝        ╚═╝   ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝")

def main():
    """Driver function to enter the application."""
    cls()
    color('a')
    title("Password Manager - Authorization")
    print("=====================================================")
    print("=====================================================")
    print_header()
    print("  A password manager written in pure Python.")
    print("=====================================================")
    print("=====================================================")
    print()
    
    # Get master password from database.
    query = DB_CURSOR.execute("SELECT keyValue FROM config WHERE keyName = 'masterPassword'")
    master_password = DB_CURSOR.fetchone()[0]
    
    # If no master password is found. Make user generate one.
    if not master_password:
        entry_password = ''
        while True:
            entry_password = input("  Create Master Password: ")
            entry_passconfirm = input("  Re-Enter New Master Password (Confirmation): ")
            if entry_password == entry_passconfirm:
                break
            else:
                print("{ERROR} Password Mismatch. Enter Again.\n")

        master_password = hash_SHA256(entry_password)
        DB_CURSOR.execute("UPDATE config SET keyValue=%s WHERE keyName='masterPassword'", (master_password, ))
        DATABASE.commit()
        print("New Master Password Set.\n")
        
    mpass = input("  Enter Master Password: ")
    
    # Verify master password.
    mpass_hashed = hash_SHA256(mpass)
    if mpass_hashed != master_password:  # check against password hash
        print("Access Denied. Incorrect Master Password.")
        if DATABASE.is_connected():
            DB_CURSOR.close()
            DATABASE.close()
        exit()  # --> kick the user out of the application
    else:
        MASTER_PASS = master_password
        menu_showMain()  # --> allow the user into the application

def menu_showMain():
    cls()
    color('a')
    title("Password Manager - Main")
    print_header()
    print()
    print("  1] List Accounts")
    print("  2] Add Account")
    print("  3] Edit Account")
    print("  4] Delete Account")
    print("  5] Exit")
    print()
    while True:
        ch = input(">> ").strip().lower()
        
        if ch in ('1', 'list', 'l'):
            return menu_showList()
        elif ch in ('2', 'add', 'a'):
            return menu_showAdd()
        elif ch in ('3', 'edit', 'e'):
            return menu_showEdit()
        elif ch in ('4', 'delete', 'd', 'del'):
            return menu_showDelete()
        elif ch in ('5', 'exit', 'quit', 'q'):
            print("Exiting...")
            if DATABASE.is_connected():
                DB_CURSOR.close()
                DATABASE.close()  # safely close connection with database
            return exit()
        else:
            print("{ERROR} Invalid Option. Try Again. [1/2/3/4/5]\n")
            
def menu_showList():
    cls()
    color('a')
    title("Password Manager - List Accounts")
    print()
    print(r"  ╦  ╦╔═╗╔╦╗")
    print(r"  ║  ║╚═╗ ║ ")
    print(r"  ╩═╝╩╚═╝ ╩ ")
    print(r"  ──────────")
    print()
    
    query = DB_CURSOR.execute("SELECT * FROM entries")
    results = DB_CURSOR.fetchall()
    if len(results) == 0:
        print("  No profiles are saved yet.")
        pause("\n  << Back [press any key]")
        return menu_showMain()
        
    for c, entry in enumerate(results, 1):
        print(F"[ID #{c}] {entry[1]}")
        print("Profile: ", entry[2])
        print("Password: ", '[Hidden]')
        print("Notes: ", entry[4])
        print(". . . . . ")
    print()
    while True:
        print("Enter ID to copy password to clipboard.")
        print("'back' to go back.")

        inp = input(">> ").strip().lower()
        if inp == 'back':
            return menu_showMain()
        elif inp.isdigit():
            intinp = int(inp) - 1
            if intinp < len(results) and intinp > -1:
                encrypted_passwd = results[intinp][3]
                # Decrypt the encrypted password using key from master password.
                passwd = decrypt_AES(encrypted_passwd, derive_key(MASTER_PASS))
                # Copy the password to user clipboard.
                pyperclip.copy(passwd)
                print(f"Password for {results[intinp][2]} ({results[intinp][1]}) copied to clipboard.\n")

def menu_showAdd():
    cls()
    color('a')
    title("Password Manager - Add Account")
    print()
    print(r"  ╔═╗╔╦╗╔╦╗")
    print(r"  ╠═╣ ║║ ║║")
    print(r"  ╩ ╩═╩╝═╩╝")
    print(r"  ─────────")
    print()
    
    entry_title = input("Enter Title: ")
    entry_profile = input("Enter Username/Profile: ")
    entry_password = ''
    while True:
        entry_password = input("Enter Password: ")
        entry_passconfirm = input("Enter Password (Confirmation): ")
        if entry_password == entry_passconfirm:
            break
        else:
            print("{ERROR} Password Mismatch. Enter Again.\n")
    entry_notes = input("Additional Notes: ")
    last_modified = str(time.time())
    
    # Encrypt the password for secure storage.
    password_encrypted = encrypt_AES(entry_password, derive_key(MASTER_PASS))
    
    id = entry_title[0] + str(random.randint(100, 999))
    data = (id, entry_title, entry_profile, password_encrypted, entry_notes, last_modified)
    DB_CURSOR.execute("INSERT INTO entries VALUES(%s, %s, %s, %s, %s, %s)", data)
    DATABASE.commit()
    print("Successfully added entry.")

    pause("\n  << Back [press any key]")
    menu_showMain()
    
def menu_showEdit():
    cls()
    color('a')
    title("Password Manager - Edit Account")
    print()
    print(r"  ╔═╗╔╦╗╦╔╦╗")
    print(r"  ║╣  ║║║ ║ ")
    print(r"  ╚═╝═╩╝╩ ╩ ")
    print(r"  ──────────")
    print()
    
    query = DB_CURSOR.execute("SELECT * FROM entries")
    results = DB_CURSOR.fetchall()
    if len(results) == 0:
        print("  No profiles are saved yet.")
        pause("\n  << Back [press any key]")
        return menu_showMain()
        
    for c, entry in enumerate(results, 1):
        print(f"[ID #{c}] {entry[1]} | {entry[2]}")
    print()
    
    while True:
        inp = input("Enter ID (to Edit): ").strip()
        if inp.isdigit():
            intinp = int(inp) - 1
            if intinp < len(results) and intinp > -1:
                entry_data = list(results[intinp])
                uid = entry_data[0]
                
                print(f"Editing Entry {intinp} [#{uid}] (Leave blank on fields you do not wish to edit.)")
                print("\nTitle: ", entry_data[1])
                new_title = input("Title (New): ").strip()
                print("\nUsername/Profile:", entry_data[2])
                new_profile = input("Username/Profile (New): ").strip()
                print("\nPassword:", '[hidden]')
                new_password = ''
                while True:
                    new_password = input("Password (New): ")
                    if not new_password:
                        break
                    new_passconfirm = input("Password (Confirmation): ")
                    if new_password == new_passconfirm:
                        break
                    else:
                        print("{ERROR} Password Mismatch. Enter Again.\n")
                print("\nNotes:", entry_data[4])
                new_notes = input("Notes (New):").strip()
                
                if new_title:
                    entry_data[1] = new_title
                if new_profile:
                    entry_data[2] = new_profile
                if new_password:
                    encrypted_password = encrypt_AES(new_password, derive_key(MASTER_PASS))
                    entry_data[3] = encrypted_password
                if new_notes:
                    entry_data[4] = new_notes
                entry_data[5] = str(time.time())
                data = tuple(entry_data)
                
                DB_CURSOR.execute("DELETE FROM entries WHERE id=%s", (uid, ))
                DB_CURSOR.execute("INSERT INTO entries VALUES(%s, %s, %s, %s, %s, %s)", data)
                DATABASE.commit()
                
                print("Successfully edited entry.")
                break
            else:
                break
        else:
            print("{ERROR} Invalid ID: Not an integer.\n")
            
    pause("\n  << Back [press any key]")
    menu_showMain()

def menu_showDelete():
    cls()
    color('a')
    title("Password Manager - Delete Account")
    print()
    print(r"  ╔╦╗╔═╗╦  ╔═╗╔╦╗╔═╗")
    print(r"   ║║║╣ ║  ║╣  ║ ║╣ ")
    print(r"  ═╩╝╚═╝╩═╝╚═╝ ╩ ╚═╝")
    print(r"  ──────────────────")
    print()
    
    query = DB_CURSOR.execute("SELECT * FROM entries")
    results = DB_CURSOR.fetchall()
    if len(results) == 0:
        print("  No profiles are saved yet.")
        pause("\n  << Back [press any key]")
        return menu_showMain()
        
    for c, entry in enumerate(results, 1):
        print(f"[ID #{c}] {entry[1]} | {entry[2]}")
    print()
    
    while True:
        inp = input("Enter ID (to Delete): ").strip()
        if inp.isdigit():
            intinp = int(inp) - 1
            if intinp < len(results) and intinp > -1:
                uid = results[intinp][0]
                DB_CURSOR.execute("DELETE FROM entries WHERE id=%s", (uid, ))
                DATABASE.commit()
                print("Successfully deleted entry.")
                break
            else:
                print("Invalid ID: Out of range.\n")
        else:
            break

    pause("\n  << Back [press any key]")
    menu_showMain()

# Call the main() function to enter the application.
main()
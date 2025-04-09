from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import qrcode

app = Flask(__name__)
app.secret_key = "your_secret_key"

DB_FILE = "devices.db"
EMAIL = "ssapoorva3@gmail.com"
PASSWORD = "Apoorva123"


def initialize_database():
    """
    Initializes the SQLite database and creates the required table if it doesn't exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Device_Component TEXT NOT NULL,
            Department TEXT NOT NULL,
            serial_number TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            price REAL NOT NULL,
            warranty TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def remove_device_data_column():
    """
    Modifies the database schema by removing the 'device_data' column if it exists.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if the `devices` table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='devices'")
    if not cursor.fetchone():
        print("The table 'devices' does not exist. Initializing database.")
        initialize_database()
        return

    # Check if the column `device_data` exists
    cursor.execute("PRAGMA table_info(devices)")
    columns = [info[1] for info in cursor.fetchall()]
    if "device_data" not in columns:
        print("The column 'device_data' does not exist. No action needed.")
        return

    # Rename the old table
    cursor.execute("ALTER TABLE devices RENAME TO devices_old")

    # Create a new table without the `device_data` column
    cursor.execute("""
        CREATE TABLE devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Device_Component TEXT NOT NULL,
            Department TEXT NOT NULL,
            serial_number TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            price REAL NOT NULL,
            warranty TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

    # Copy the data from the old table to the new table
    cursor.execute("""
        INSERT INTO devices (id, Device_Component, Department, serial_number, purchase_date, price, warranty, location)
        SELECT id, Device_Component, Department, serial_number, purchase_date, price, warranty, location
        FROM devices_old
    """)

    # Drop the old table
    cursor.execute("DROP TABLE devices_old")

    conn.commit()
    conn.close()


# Run the script to ensure the database is initialized and update the schema if necessary
initialize_database()
remove_device_data_column()


def get_all_devices():
    """
    Retrieves all devices from the database.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, Device_Component, Department, serial_number, purchase_date, price, warranty, location 
        FROM devices
    """)
    devices = cursor.fetchall()
    conn.close()
    return devices


def get_device_by_id(device_id):
    """
    Retrieves a single device by ID from the database.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, Device_Component, Department, serial_number, purchase_date, price, warranty, location 
        FROM devices WHERE id = ?
    """, (device_id,))
    device = cursor.fetchone()
    conn.close()
    return device


def add_device_to_db(Device_Component, Department, serial_number, purchase_date, price, warranty, location):
    """
    Adds a new device to the database.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO devices (Device_Component, Department, serial_number, purchase_date, price, warranty, location) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (Device_Component, Department, serial_number, purchase_date, price, warranty, location))
    conn.commit()
    conn.close()


def delete_device_from_db(device_id):
    """
    Deletes a device from the database by ID.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()


def update_device_in_db(device_id, Device_Component, Department, serial_number, purchase_date, price, warranty, location):
    """
    Updates a device in the database.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE devices 
        SET Device_Component = ?, Department = ?, serial_number = ?, purchase_date = ?, price = ?, warranty = ?, location = ?
        WHERE id = ?
    """, (Device_Component, Department, serial_number, purchase_date, price, warranty, location, device_id))
    conn.commit()
    conn.close()


def create_qr_code(Device_Component, Department, serial_number, purchase_date, price, warranty, location, file_name):
    """
    Generates a QR code with device information and saves it to a file.
    """
    qr_data = f"Device_Component: {Device_Component}\nDepartment: {Department}\nSerial Number: {serial_number}\nPurchase Date: {purchase_date}\nPrice: {price}\nWarranty: {warranty}\nLocation: {location}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img.save(file_name)


@app.route("/", methods=["GET", "POST"])
def login():
    """
    Handles login for the application.
    """
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email == EMAIL and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            return "Invalid email or password!"

    return render_template("login.html")


@app.route("/index")
def index():
    """
    Displays all devices with options to add, edit, or delete devices.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    devices = get_all_devices()
    return render_template("index.html", devices=devices)


@app.route("/add", methods=["GET", "POST"])
def add_device():
    """
    Handles adding a new device.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        Device_Component = request.form["Device_Component"]
        Department = request.form["Department"]
        serial_number = request.form["serial_number"]
        purchase_date = request.form["purchase_date"]
        price = float(request.form["price"])
        warranty = request.form["warranty"]
        location = request.form["location"]
        add_device_to_db(Device_Component, Department, serial_number, purchase_date, price, warranty, location)
        return redirect(url_for("index"))
    return render_template("add_device.html")


@app.route("/edit/<int:device_id>", methods=["GET", "POST"])
def edit_device(device_id):
    """
    Handles editing an existing device.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        Device_Component = request.form["Device_Component"]
        Department = request.form["Department"]
        serial_number = request.form["serial_number"]
        purchase_date = request.form["purchase_date"]
        price = float(request.form["price"])
        warranty = request.form["warranty"]
        location = request.form["location"]
        update_device_in_db(device_id, Device_Component, Department, serial_number, purchase_date, price, warranty, location)
        return redirect(url_for("index"))

    device = get_device_by_id(device_id)
    return render_template("edit_device.html", device=device)


@app.route("/delete/<int:device_id>", methods=["POST"])
def delete_device(device_id):
    """
    Deletes a device by its ID.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()
    
    # Use flash to notify the user
    flash("Device deleted successfully!", "success")
    return redirect(url_for("index"))


@app.route("/generate_qr_code/<int:device_id>")
def generate_qr_code(device_id):
    """
    Generates a QR code for a specific device by ID.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    device = get_device_by_id(device_id)
    if not device:
        return f"Device with ID {device_id} not found."

    device_id, Device_Component, Department, serial_number, purchase_date, price, warranty, location = device
    output_folder = "generated_QR_code"
    os.makedirs(output_folder, exist_ok=True)

    file_name = os.path.join(output_folder, f"{Device_Component.replace(' ', '_')}_qr_code.png")
    create_qr_code(Device_Component, Department, serial_number, purchase_date, price, warranty, location, file_name)

    return f"QR Code for device '{Device_Component}' generated successfully. Check the 'generated_QR_code' folder."


if __name__ == "__main__":
    app.run(debug=True)

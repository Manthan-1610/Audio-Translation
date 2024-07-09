import mysql.connector
from datetime import datetime, timedelta

# Connect to MySQL server
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root"
)
cursor = db_connection.cursor()

# Create database
cursor.execute("CREATE DATABASE IF NOT EXISTS Education_system")

# Connect to the newly created database
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="Education_system"
)
cursor = db_connection.cursor()

# Create Classes table
cursor.execute("CREATE TABLE IF NOT EXISTS Classes (id INT AUTO_INCREMENT PRIMARY KEY, class_name VARCHAR(255))")

# Create Lecture_data table
cursor.execute("CREATE TABLE IF NOT EXISTS Lecture_data (id INT AUTO_INCREMENT PRIMARY KEY, class_id INT, lecture_name VARCHAR(255), date DATE, audio LONGBLOB, english_transcript TEXT, hindi_translation TEXT, gujarati_translation TEXT, FOREIGN KEY (class_id) REFERENCES Classes(id))")

# Create Class_lectures table
cursor.execute("CREATE TABLE IF NOT EXISTS Class_lectures (class_id INT, lecture_name VARCHAR(255), day VARCHAR(10), FOREIGN KEY (class_id) REFERENCES Classes(id))")

# Predefine class names
class_names = ["6IT-A", "6CE-A", "6IOT-A"]  # Add more if needed

# Insert class names into Classes table
for class_name in class_names:
    cursor.execute("INSERT INTO Classes (class_name) VALUES (%s)", (class_name,))
    db_connection.commit()

# Predefine lecture names for each class from Monday to Friday
class_lectures = {
    "6IT-A": {
        "Monday": ["DSML", "AI", "TOC", "CC"],
        "Tuesday": ["AI", "ASB"],
        "Wednesday": ["EH", "CC"],
        "Thursday": ["CC", "DSML", "EH", "TOC"],
        "Friday": ["EH", "AI", "TOC", "DSML"],
        # Add more lectures for each day if needed
    },
    "6CE-A": {
        "Monday": ["DSML", "AI", "TOC", "CC"],
        "Tuesday": ["AI", "ASB"],
        "Wednesday": ["EH", "CC"],
        "Thursday": ["CC", "DSML", "EH", "TOC"],
        "Friday": ["EH", "AI", "TOC", "DSML"],
    },
    "6IOT-A": {
        "Monday": ["DSML", "AI", "TOC", "CC"],
        "Tuesday": ["AI", "ASB"],
        "Wednesday": ["EH", "CC"],
        "Thursday": ["CC", "DSML", "EH", "TOC"],
        "Friday": ["EH", "AI", "TOC", "DSML"],
        # Add more lectures for each day if needed
    }
    # Add more classes and lectures if needed
}

# Map lecture names to lecture IDs
for class_name, daily_lectures in class_lectures.items():
    for day_of_week, lectures in daily_lectures.items():
        for lecture_name in lectures:
            cursor.execute("INSERT INTO Class_lectures (class_id, lecture_name, day) VALUES ((SELECT id FROM Classes WHERE class_name = %s), %s, %s)", (class_name, lecture_name, day_of_week))
            db_connection.commit()

print("Database setup and initial data insertion completed.")

# Close database connection
cursor.close()
db_connection.close()

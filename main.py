import face_recognition
import cv2
import numpy as np
import os
import pickle
import sqlite3
from datetime import datetime
import pandas as pd

def train_face_recognition(training_images_path, encoding_file="face_encodings.pkl"):
    # Get absolute paths and ensure training directory exists
    training_images_path = os.path.abspath(training_images_path)
    if not os.path.exists(training_images_path):
        os.makedirs(training_images_path)
        print(f"Created training directory at: {training_images_path}")
    
    # Make sure encoding_file has the correct directory path
    encoding_file = os.path.join(os.path.dirname(training_images_path), encoding_file)
    print(f"Looking for saved encodings at: {encoding_file}")
    
    # Check if we have saved encodings
    if os.path.exists(encoding_file):
        try:
            print("Loading saved encodings...")
            with open(encoding_file, 'rb') as f:
                data = pickle.load(f)
                print("Successfully loaded saved encodings!")
                return data['encodings'], data['names']
        except Exception as e:
            print(f"Error loading saved encodings: {str(e)}")
            # If there's an error loading, we'll recreate the encodings
            if os.path.exists(encoding_file):
                os.remove(encoding_file)
    else:
        print("No saved encodings found. Will process images...")
    
    known_face_encodings = []
    known_face_names = []
    
    try:
        print("Loading training images...")
        for filename in os.listdir(training_images_path):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                try:
                    image_path = os.path.join(training_images_path, filename)
                    print(f"Processing image: {filename}")
                    image = face_recognition.load_image_file(image_path)
                    face_encoding = face_recognition.face_encodings(image)[0]
                    
                    name = ''.join([i for i in os.path.splitext(filename)[0] if not i.isdigit()])
                    
                    known_face_encodings.append(face_encoding)
                    known_face_names.append(name)
                except IndexError:
                    print(f"No face found in {filename}. Skipping...")
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
        
        print(f"Successfully processed {len(known_face_encodings)} images")
        
        # Save encodings to file
        print("Saving encodings for future use...")
        with open(encoding_file, 'wb') as f:
            pickle.dump({
                'encodings': known_face_encodings,
                'names': known_face_names
            }, f)
        
        return known_face_encodings, known_face_names
        
    except Exception as e:
        print(f"Error during training: {str(e)}")
        return [], []

def setup_database():
    """Create and populate the database with student information from CSV"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll_number TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT,
            login_time DATETIME,
            FOREIGN KEY (roll_number) REFERENCES students(roll_number)
        )
    ''')
    
    try:
        # Load student data from CSV
        df = pd.read_csv('students.csv')
        df.to_sql('students', conn, if_exists='replace', index=False)
        print("Database initialized with student data from CSV")
    except Exception as e:
        print(f"Error loading student data: {str(e)}")
    finally:
        conn.close()

def log_attendance(name):
    """Log attendance when a face is recognized"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        # Get roll number for the recognized name
        cursor.execute('SELECT roll_number FROM students WHERE name = ?', (name,))
        result = cursor.fetchone()
        
        if result:
            roll_number = result[0]
            current_time = datetime.now()
            
            # Log the attendance
            cursor.execute('''
                INSERT INTO attendance_logs (roll_number, login_time)
                VALUES (?, ?)
            ''', (roll_number, current_time))
            
            conn.commit()
            print(f"Logged attendance for {name} (Roll: {roll_number}) at {current_time}")
        else:
            print(f"No roll number found for {name}")
            
    finally:
        conn.close()

def recognize_faces():
    print("Starting face recognition...")
    # Specify full path and ensure it exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    training_path = os.path.join(base_dir, "training_images")
    if not os.path.exists(training_path):
        os.makedirs(training_path)
        print(f"Created training directory at: {training_path}")
    
    known_face_encodings, known_face_names = train_face_recognition(training_path)
    
    # Check if we have any encodings before proceeding
    if not known_face_encodings:
        print("No face encodings found. Please add images to the training_images directory.")
        return
    
    # Initialize database
    setup_database()
    
    # Initialize webcam
    video_capture = cv2.VideoCapture(0)
    
    last_logged_time = {}  # Dictionary to prevent duplicate entries
    
    while True:
        ret, frame = video_capture.read()
        
        # Find faces in current frame
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        
        # Loop through each face in current frame
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
            
            # Draw rectangle around face and label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.75, (0, 255, 0), 2)
        
        # Display result
        cv2.imshow('Video', frame)
        
        # Check for keypress
        key = cv2.waitKey(1) & 0xFF
        
        # Press 'q' to quit
        if key == ord('q'):
            break
        # Press 'c' to capture attendance
        elif key == ord('c'):
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]
                    
                    # Only log if name is known and hasn't been logged in the last 60 seconds
                    current_time = datetime.now()
                    if (name != "Unknown" and 
                        (name not in last_logged_time or 
                         (current_time - last_logged_time[name]).total_seconds() > 60)):
                        log_attendance(name)
                        last_logged_time[name] = current_time
                        print(f"Attendance captured for {name}")
    
    video_capture.release()
    cv2.destroyAllWindows()

def view_attendance_logs():
    print("Viewing attendance logs...")
    """View all attendance logs"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT s.name, s.roll_number, a.login_time 
            FROM attendance_logs a 
            JOIN students s ON a.roll_number = s.roll_number 
            ORDER BY a.login_time DESC
        ''')
        logs = cursor.fetchall()
        
        print("\nAttendance Logs:")
        print("Name | Roll Number | Login Time")
        print("-" * 50)
        for log in logs:
            print(f"{log[0]} | {log[1]} | {log[2]}")
            
    finally:
        conn.close()

def check_student_database():
    """Debug function to verify student data in database"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
        
        print("\nStudent Database Contents:")
        print("Roll Number | Name")
        print("-" * 30)
        for student in students:
            print(f"{student[0]} | {student[1]}")
            
    finally:
        conn.close()

if __name__ == '__main__':
    print("Main.py is being run directly")
else:
    print("Main.py is being imported as a module")

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                            QVBoxLayout, QWidget, QTableWidget, 
                            QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
import sys
import sqlite3
try:
    from main import recognize_faces, view_attendance_logs
    print("Successfully imported from main.py")
except ImportError as e:
    print(f"Error importing from main.py: {e}")

class AttendanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Set up the main window
        self.setWindowTitle("Face Recognition Attendance System")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create and style buttons
        self.login_button = QPushButton("Take Attendance")
        self.view_button = QPushButton("View Attendance")
        
        # Style buttons
        for button in [self.login_button, self.view_button]:
            button.setMinimumHeight(50)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        
        # Add buttons to layout
        layout.addWidget(self.login_button)
        layout.addWidget(self.view_button)
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border: 1px solid #ddd;
            }
        """)
        self.table.hide()
        layout.addWidget(self.table)
        
        # Connect buttons to functions
        self.login_button.clicked.connect(self.start_recognition)
        self.view_button.clicked.connect(self.show_attendance)
        
    def start_recognition(self):
        """Start the face recognition process"""
        self.hide()  # Hide the main window
        recognize_faces()  # Start face recognition
        self.show()  # Show the main window again when done
        
    def show_attendance(self):
        """Display attendance logs in a table"""
        self.table.show()
        
        # Connect to database
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Get attendance data
        cursor.execute('''
            SELECT s.name, s.roll_number, a.login_time 
            FROM attendance_logs a 
            JOIN students s ON a.roll_number = s.roll_number 
            ORDER BY a.login_time DESC
        ''')
        data = cursor.fetchall()
        
        # Set up table
        self.table.setRowCount(len(data))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Name', 'Roll Number', 'Login Time'])
        
        # Populate table
        for row, (name, roll, time) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(roll))
            self.table.setItem(row, 2, QTableWidgetItem(str(time)))
        
        # Adjust column widths
        header = self.table.horizontalHeader()
        for i in range(3):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        conn.close()

def main():
    print("Starting application...")
    try:
        app = QApplication(sys.argv)
        print("Created QApplication")
        
        window = AttendanceApp()
        print("Created main window")
        
        window.show()
        print("Showing window")
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error in main(): {str(e)}")

if __name__ == '__main__':
    print("Script is being run directly")
    main()
else:
    print("Script is being imported")
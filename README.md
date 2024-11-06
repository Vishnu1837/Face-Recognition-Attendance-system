# ML-Based Attendance System

This project uses machine learning to recognize faces and record attendance based on the identified faces. Follow the steps below to add new students, train the model, and run the attendance app.

## Instructions

### 1. Add a New Student
- Open `students.csv` and add the new student's details (name and roll number).
- Ensure the **name matches the format used for image naming** in the next step.

### 2. Prepare Training Images
- In the `training` folder, add at least 100 clear images of the person’s face.
- Name the images in this format: `Name001.jpg`, `Name002.jpg`, etc.
  - Example: For a student named Vishnu, images should be named `Vishnu001.jpg`, `Vishnu002.jpg`, and so on.
- **Important**: Ensure the name in the image filenames matches the name in `students.csv`.

### 3. Train the Model
- Run `main.py`. This will:
  - Create a trained model and save it as a `.pkl` file.
  - Generate the database and required tables if they don't already exist.
- **Note**: Training may take some time.

### 4. Test the Model
- After training is complete, a camera window will pop up for testing. Use this to verify the model's recognition performance.

### 5. Run the Attendance App
- To track attendance, open and run `attendance_app.py`.

---

Enjoy using the ML-based attendance system!

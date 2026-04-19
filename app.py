from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="student_project"
    )

# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template("login.html")
@app.route('/teacher_login', methods=['GET','POST'])
def teacher_login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            db = get_db()
            cursor = db.cursor(buffered=True)
            cursor.execute(
                "SELECT * FROM teachers WHERE email=%s AND password=%s",
                (email, password)
            )

            teacher = cursor.fetchone()
            cursor.close()
            db.close()

            if teacher:
                session['teacher_email'] = email
                return redirect('/teacher_dashboard')
            else:
                return "Invalid Email or Password ❌"

        except Exception as e:
            return f"Error: {e}"

    return render_template("teacher_login.html")


# ---------------- STUDENT SIGNUP ----------------
@app.route('/student_signup', methods=['GET','POST'])
def student_signup():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']

            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO students (name,email,password) VALUES (%s,%s,%s)",
                (name,email,password)
            )
            db.commit()
            cursor.close()
            db.close()

            return redirect('/student_login')

        except Exception as e:
            return f"Error: {e}"

    return render_template("student_signup.html")
# ---------------- TEACHER SIGNUP ----------------

@app.route('/teacher_signup', methods=['GET','POST'])
def teacher_signup():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO teachers (name,email,password) VALUES (%s,%s,%s)",
            (name,email,password)
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for('teacher_login'))

    return render_template("teacher_signup.html")

# ---------------- STUDENT LOGIN ----------------

@app.route('/student_login', methods=['GET','POST'])
def student_login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            db = get_db()
            cursor = db.cursor(buffered=True)
            cursor.execute(
                "SELECT * FROM students WHERE email=%s AND password=%s",
                (email,password)
            )

            student = cursor.fetchone()
            cursor.close()
            db.close()

            if student:
                session['student_email'] = email
                return redirect('/student_dashboard')
            else:
                return "Invalid Email or Password ❌"

        except Exception as e:
            return f"Error: {e}"

    return render_template("student_login.html")


# ---------------- STUDENT DASHBOARD ----------------

@app.route('/student_dashboard')
def student_dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    email = session.get('student_email')

    cursor.execute("""
        SELECT student_email, student_name, roll_no, marks, attendance, behaviour,
               maths, DBMS AS dbms, OS AS os, MDM AS mdm, CT AS ct
        FROM performance WHERE student_email=%s
    """, (email,))

    data = cursor.fetchone()
    cursor.close()
    db.close()

    if data:
        return render_template("student_dashboard.html", **data)

    return render_template("student_dashboard.html",
        marks=0, attendance=0, behaviour=0,
        maths=0, dbms=0, os=0, mdm=0, ct=0
    )


# ---------------- TEACHER DASHBOARD ----------------

@app.route('/teacher_dashboard')
def teacher_dashboard():
    return render_template("teacher_dashboard.html")





# ---------------- ADD / UPDATE ----------------

@app.route('/add_student_data', methods=['POST'])
def add_student_data():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    email = request.form['email']
    student_name = request.form.get('student_name', '')
    roll_no = request.form.get('roll_no', '')
    attendance = int(request.form['attendance'])

    maths = int(request.form['maths'] or 0)
    dbms = int(request.form['dbms'] or 0)
    os_mark = int(request.form['os'] or 0)
    mdm = int(request.form['mdm'] or 0)
    ct = int(request.form['ct'] or 0)

    # AUTO MARKS (average of all subjects)
    marks = round((maths + dbms + os_mark + mdm + ct) / 5)

    # AUTO BEHAVIOUR (attendance 60% + marks 40%)
    avg = attendance * 0.6 + marks * 0.4
    if avg > 75:
        behaviour = 90
    elif avg > 55:
        behaviour = 70
    elif avg > 35:
        behaviour = 50
    else:
        behaviour = 30

    cursor.execute("SELECT * FROM performance WHERE student_email=%s", (email,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE performance 
            SET student_name=%s, roll_no=%s, marks=%s, attendance=%s, behaviour=%s,
                maths=%s, DBMS=%s, OS=%s, MDM=%s, CT=%s
            WHERE student_email=%s
        """, (student_name, roll_no, marks, attendance, behaviour, maths, dbms, os_mark, mdm, ct, email))
    else:
        cursor.execute("""
            INSERT INTO performance 
            (student_email, student_name, roll_no, marks, attendance, behaviour, maths, DBMS, OS, MDM, CT)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (email, student_name, roll_no, marks, attendance, behaviour, maths, dbms, os_mark, mdm, ct))

    db.commit()
    cursor.close()
    db.close()

    return "OK"


# ---------------- LIVE DATA ----------------

@app.route('/get_students')
def get_students():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            id,
            student_email AS email,
            student_name,
            roll_no,
            marks,
            attendance,
            behaviour,
            maths,
            DBMS,
            OS,
            MDM,
            CT
        FROM performance
    """)

    data = cursor.fetchall()
    cursor.close()
    db.close()

    return jsonify(data)


# ---------------- DELETE ----------------

@app.route('/delete_student/<int:id>')
def delete_student(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM performance WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()

    return "OK"   # 🔥 IMPORTANT (NO REDIRECT)


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
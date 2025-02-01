from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

# HTML + CSS + JS Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Office Seating Planner</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 20px; }
        #controls { margin-bottom: 20px; }
        input { padding: 10px; margin: 5px; }
        button { padding: 10px; cursor: pointer; }
        #seating { display: flex; flex-wrap: wrap; justify-content: center; }
        .seat { width: 150px; height: 100px; border: 1px solid #333; margin: 5px; display: flex;
                align-items: center; justify-content: center; background-color: #f4f4f4; cursor: pointer; }
        .seat.assigned { background-color: #ff6961; cursor: not-allowed; }
    </style>
</head>
<body>
    <h1>Office Seating Planner</h1>
    <div id="controls">
        <input type="text" id="employeeName" placeholder="Employee Name">
        <input type="text" id="employeeId" placeholder="Employee ID">
        <input type="text" id="department" placeholder="Department">
        <input type="text" id="preference" placeholder="Seat Preference">
        <button onclick="addSeat()">Add Seat</button>
    </div>
    <div id="seating"></div>

    <script>
        document.addEventListener("DOMContentLoaded", () => { loadSeats(); });

        function loadSeats() {
            fetch("/seats")
                .then(response => response.json())
                .then(data => {
                    const seating = document.getElementById("seating");
                    seating.innerHTML = "";
                    data.forEach(seat => {
                        const seatDiv = document.createElement("div");
                        seatDiv.classList.add("seat");
                        if (seat.assigned) {
                            seatDiv.classList.add("assigned");
                            seatDiv.textContent = `${seat.name} (${seat.department}) - Assigned`;
                        } else {
                            seatDiv.textContent = `${seat.name} (${seat.department})`;
                            seatDiv.onclick = () => assignSeat(seat.id);
                        }
                        seating.appendChild(seatDiv);
                    });
                });
        }

        function assignSeat(id) {
            fetch("/assign", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id })
            }).then(() => loadSeats());
        }

        function addSeat() {
            const name = document.getElementById("employeeName").value.trim();
            const employeeId = document.getElementById("employeeId").value.trim();
            const department = document.getElementById("department").value.trim();
            const preference = document.getElementById("preference").value.trim();

            if (!name || !employeeId || !department || !preference) {
                alert("All fields are required!");
                return;
            }

            fetch("/add_seat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, employeeId, department, preference })
            }).then(() => {
                document.getElementById("employeeName").value = "";
                document.getElementById("employeeId").value = "";
                document.getElementById("department").value = "";
                document.getElementById("preference").value = "";
                loadSeats();
            });
        }
    </script>
</body>
</html>
"""

# Database Functions
def get_db_connection():
    conn = sqlite3.connect("seating.db")
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            employeeId TEXT NOT NULL,
            department TEXT NOT NULL,
            preference TEXT NOT NULL,
            assigned INTEGER DEFAULT 0
        )
    """)
    # Add default seats if none exist
    cursor.execute("SELECT COUNT(*) FROM seats")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO seats (name, employeeId, department, preference, assigned) VALUES (?, ?, ?, ?, 0)", 
            [(f"Seat {i}", f"EMP{i}", "Dept A", "Near Window") for i in range(1, 21)]
        )
    conn.commit()
    conn.close()

# Routes
@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/seats", methods=["GET"])
def get_seats():
    conn = get_db_connection()
    seats = conn.execute("SELECT * FROM seats").fetchall()
    conn.close()
    return jsonify([dict(row) for row in seats])

@app.route("/assign", methods=["POST"])
def assign_seat():
    data = request.json
    conn = get_db_connection()
    conn.execute("UPDATE seats SET assigned = 1 WHERE id = ?", (data["id"],))
    conn.commit()
    conn.close()
    return "", 204

@app.route("/add_seat", methods=["POST"])
def add_seat():
    data = request.json
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO seats (name, employeeId, department, preference, assigned) VALUES (?, ?, ?, ?, 0)", 
        (data["name"], data["employeeId"], data["department"], data["preference"])
    )
    conn.commit()
    conn.close()
    return "", 201

if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)

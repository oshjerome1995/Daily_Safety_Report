act as a pro stack developer in python, add functionality to my project
add "Sort by" and "Filter" at the right top of the table, once clicked it shows a dropdown windows that shows options of sort and filter respectively, 
and after clicking the export it will only export what you filter in the data, use optimal way such as sorting in database or any way possible as 
long as its bug free here is the complete structure and source code:
try
├── static
│   ├── css
│   │   └── style.css
│   └── uploads
├── templates
│   ├── index.html
│   └── record_form.html
├── app.py
├── config.py
├── database.py
├── models.py
├── readme.txt
├── records.json
└── requirements.txt

app.py:
from flask import Flask, render_template, request, redirect, url_for, send_file
import os, json
from datetime import datetime
from werkzeug.utils import secure_filename
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from PIL import Image as PILImage
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
RECORDS_FILE = 'records.json'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load records
def load_records():
    try:
        with open(RECORDS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save records
def save_records(records):
    with open(RECORDS_FILE, 'w') as f:
        json.dump(records, f, indent=4)

# Check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home page
@app.route('/')
def index():
    records = load_records()
    return render_template('index.html', records=records)

# Add record
@app.route('/add', methods=['GET', 'POST'])
def add_record():
    if request.method == 'POST':
        records = load_records()
        record_id = max([r['id'] for r in records], default=0) + 1

        # Main picture
        file = request.files.get('picture')
        picture_path = None
        if file and allowed_file(file.filename):
            filename = f"{record_id}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            picture_path = f'uploads/{filename}'

        # Additional picture
        add_file = request.files.get('additional_picture')
        additional_picture_path = None
        if add_file and allowed_file(add_file.filename):
            add_filename = f"{record_id}_add_{secure_filename(add_file.filename)}"
            add_file.save(os.path.join(app.config['UPLOAD_FOLDER'], add_filename))
            additional_picture_path = f'uploads/{add_filename}'

        category = request.form['category']
        status = "" if category == "Good Observation" else request.form['status']
        osh_rule = "" if category == "Good Observation" else request.form['osh_rule']

        record = {
            "id": record_id,
            "detailed_observation": request.form['detailed_observation'][:300],
            "picture_path": picture_path,
            "additional_picture_path": additional_picture_path,
            "area_department": request.form['area_department'][:300],
            "checked_by": request.form['checked_by'][:300],
            "action_done": request.form['action_done'][:300],
            "date": request.form['date'],
            "so_timestamp": datetime.now().strftime("%B %d %Y %H:%M:%S"),
            "area_in_charge": request.form['area_in_charge'][:300],
            "category": category,
            "status": status,
            "osh_rule": osh_rule,
            "safety_officer": request.form['safety_officer'][:300]
        }
        records.append(record)
        save_records(records)
        return redirect(url_for('index'))
    return render_template('record_form.html', record=None)

# Edit record
@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    records = load_records()
    record = next((r for r in records if r['id']==record_id), None)
    if not record:
        return "Record not found", 404

    if request.method == 'POST':
        file = request.files.get('picture')
        if file and allowed_file(file.filename):
            filename = f"{record_id}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            record['picture_path'] = f'uploads/{filename}'

        add_file = request.files.get('additional_picture')
        if add_file and allowed_file(add_file.filename):
            add_filename = f"{record_id}_add_{secure_filename(add_file.filename)}"
            add_file.save(os.path.join(app.config['UPLOAD_FOLDER'], add_filename))
            record['additional_picture_path'] = f'uploads/{add_filename}'

        record['detailed_observation'] = request.form['detailed_observation'][:300]
        record['area_department'] = request.form['area_department'][:300]
        record['checked_by'] = request.form['checked_by'][:300]
        record['action_done'] = request.form['action_done'][:300]
        record['date'] = request.form['date']
        record['area_in_charge'] = request.form['area_in_charge'][:300]
        record['category'] = request.form['category']
        record['status'] = "" if record['category']=="Good Observation" else request.form['status']
        record['osh_rule'] = "" if record['category']=="Good Observation" else request.form['osh_rule']
        record['safety_officer'] = request.form['safety_officer'][:300]

        save_records(records)
        return redirect(url_for('index'))

    return render_template('record_form.html', record=record)

# Delete record
@app.route('/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    records = load_records()
    records = [r for r in records if r['id'] != record_id]
    save_records(records)
    return redirect(url_for('index'))

# Export with centered image
@app.route('/export')
def export_excel():
    records = load_records()
    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Safety Report"

    headers = ["ID","Observation","Picture","Area/Dept","Checked By","Action Done",
               "Date","SO Timestamp","Area In-Charge","Category","Additional Picture",
               "Status","OSH Rule","Safety Officer"]
    ws.append(headers)

    alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    MAX_WIDTH, MAX_HEIGHT = 120, 80  # pixels
    img_cols = {"C": "picture_path", "K": "additional_picture_path"}

    # Fix column widths
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['K'].width = 18

    def insert_image(ws, col_letter, row_idx, img_path):
        if img_path and os.path.exists(img_path):
            img = PILImage.open(img_path)
            # Resize image to fit cell
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT))

            # Optional: add transparent padding to center
            final_img = PILImage.new("RGBA", (MAX_WIDTH, MAX_HEIGHT), (255, 255, 255, 0))
            paste_x = (MAX_WIDTH - img.width) // 2
            paste_y = (MAX_HEIGHT - img.height) // 2
            final_img.paste(img, (paste_x, paste_y))

            # Save to BytesIO for openpyxl
            temp = BytesIO()
            final_img.convert("RGB").save(temp, format="PNG")
            temp.seek(0)
            ws.add_image(XLImage(temp), f"{col_letter}{row_idx}")

    for row_idx, record in enumerate(records, start=2):
        ws.append([
            record['id'],
            record['detailed_observation'],
            "",
            record['area_department'],
            record['checked_by'],
            record['action_done'],
            record['date'],
            record['so_timestamp'],
            record['area_in_charge'],
            record['category'],
            "",
            record['status'],
            record['osh_rule'],
            record['safety_officer']
        ])

        # Apply alignment
        for col_idx in range(1, 15):
            ws.cell(row=row_idx, column=col_idx).alignment = alignment

        # Adjust row height to fit image
        ws.row_dimensions[row_idx].height = MAX_HEIGHT * 0.75

        # Insert images
        insert_image(ws, "C", row_idx, os.path.join(app.static_folder, record.get("picture_path") or ""))
        insert_image(ws, "K", row_idx, os.path.join(app.static_folder, record.get("additional_picture_path") or ""))

    # Adjust text columns width
    for col_idx in range(1, 15):
        col_letter = get_column_letter(col_idx)
        if col_letter not in ['C', 'K']:
            max_len = max((len(str(ws.cell(r, col_idx).value or "")) for r in range(1, ws.max_row+1)), default=0)
            ws.column_dimensions[col_letter].width = min(max_len + 5, 40)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"DailySafetyReport_{timestamp}.xlsx"
    wb.save(output_file)
    return send_file(output_file, as_attachment=True)

# Run app
if __name__ == '__main__':
    app.run(debug=True)

config.py:
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

MAX_CONTENT_LENGTH = 16 * 1024 * 1024

DATABASE = os.path.join(BASE_DIR, "database.db")

database.py:
import sqlite3
from config import DATABASE

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        detailed_observation TEXT,
        picture_path TEXT,
        area_department TEXT,
        checked_by TEXT,
        action_done TEXT,
        date TEXT,
        so_timestamp TEXT,
        area_in_charge TEXT,
        category TEXT,
        status TEXT,
        osh_rule TEXT,
        safety_officer TEXT
    )
    """)
    conn.commit()
    conn.close()

models.py:
from database import get_db


def get_all_records():
    conn = get_db()
    records = conn.execute(
        "SELECT * FROM records ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return records


def get_record(record_id):
    conn = get_db()
    record = conn.execute(
        "SELECT * FROM records WHERE id=?",
        (record_id,)
    ).fetchone()
    conn.close()
    return record


def delete_record(record_id):
    conn = get_db()
    conn.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()


requirements.txt:
Flask==2.3.4
Werkzeug==2.3.6
openpyxl==3.1.3
Pillow==10.1.0

index.html:
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Safety Report</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
  .table-img { width: 80px; height: auto; max-height: 60px; object-fit: cover; }
  .table-responsive { overflow-x: auto; }
</style>
</head>
<body class="bg-light">
<div class="container-fluid py-3">
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap">
        <h2 class="mb-2 mb-md-0">Daily Safety Report</h2>
        <div class="d-flex gap-2 flex-wrap">
            <a href="{{ url_for('add_record') }}" class="btn btn-primary mb-2">Add Record</a>
            <a href="{{ url_for('export_excel') }}" class="btn btn-success mb-2">Export Excel</a>
        </div>
    </div>

    <div class="table-responsive">
    <table class="table table-bordered table-striped table-hover align-middle">
        <thead class="table-dark">
            <tr>
                <th>ID</th><th>Observation</th><th>Picture</th><th>Area/Dept</th><th>Checked By</th>
                <th>Action Done</th><th>Date</th><th>SO Timestamp</th><th>Area In-Charge</th>
                <th>Category</th><th>Additional Picture</th><th>Status</th><th>OSH Rule</th><th>Safety Officer</th><th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for r in records %}
            <tr>
                <td>{{ r.id }}</td>
                <td>{{ r.detailed_observation }}</td>
                <td>
                    {% if r.picture_path %}
                    <img src="{{ url_for('static', filename=r.picture_path) }}" class="table-img">
                    {% endif %}
                </td>
                <td>{{ r.area_department }}</td>
                <td>{{ r.checked_by }}</td>
                <td>{{ r.action_done }}</td>
                <td>{{ r.date }}</td>
                <td>{{ r.so_timestamp }}</td>
                <td>{{ r.area_in_charge }}</td>
                <td>{{ r.category }}</td>
                <td>
                    {% if r.additional_picture_path %}
                    <img src="{{ url_for('static', filename=r.additional_picture_path) }}" class="table-img">
                    {% endif %}
                </td>
                <td>{{ r.status }}</td>
                <td>{{ r.osh_rule }}</td>
                <td>{{ r.safety_officer }}</td>
                <td class="d-flex flex-column flex-md-row gap-1">
                    <a href="{{ url_for('edit_record', record_id=r.id) }}" class="btn btn-sm btn-warning">Edit</a>
                    <form action="{{ url_for('delete_record', record_id=r.id) }}" method="POST" class="m-0 p-0">
                        <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('Delete this record?')">Delete</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </div>
</div>
</body>
</html>

record_form.html:

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ 'Edit Record' if record else 'Add Record' }}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
<script>
function toggleFields() {
    let category = document.getElementById('category').value;
    let status = document.getElementById('status');
    let osh_rule = document.getElementById('osh_rule');
    if(category == "Good Observation") {
        status.disabled = true;
        status.value = "";
        osh_rule.disabled = true;
        osh_rule.value = "";
    } else {
        status.disabled = false;
        osh_rule.disabled = false;
    }
}
</script>
</head>
<body class="bg-light">
<div class="container my-4">
<h2>{{ 'Edit Record' if record else 'Add Record' }}</h2>
<form method="POST" enctype="multipart/form-data">
  <div class="row g-3">
    <div class="col-12">
        <label class="form-label">Detailed Observation</label>
        <textarea name="detailed_observation" class="form-control" maxlength="300" required>{{ record.detailed_observation if record else '' }}</textarea>
    </div>

    <!-- Main Picture -->
    <div class="col-12 col-md-6">
        <label class="form-label">Picture Evidence</label>
        <input type="file" name="picture" class="form-control">
        {% if record and record.picture_path %}
            <img src="{{ url_for('static', filename=record.picture_path) }}" style="width:100%;max-width:200px;height:auto;margin-top:5px;">
        {% endif %}
    </div>

    <!-- Additional Picture -->
    <div class="col-12 col-md-6">
        <label class="form-label">Additional Picture</label>
        <input type="file" name="additional_picture" class="form-control">
        {% if record and record.additional_picture_path %}
            <img src="{{ url_for('static', filename=record.additional_picture_path) }}" style="width:100%;max-width:200px;height:auto;margin-top:5px;">
        {% endif %}
    </div>

    <div class="col-12 col-md-6">
        <label class="form-label">Area/Department</label>
        <input type="text" name="area_department" class="form-control" maxlength="300" value="{{ record.area_department if record else '' }}" required>
    </div>
    <div class="col-12 col-md-6">
        <label class="form-label">Checked By</label>
        <input type="text" name="checked_by" class="form-control" maxlength="300" value="{{ record.checked_by if record else '' }}" required>
    </div>
    <div class="col-12 col-md-6">
        <label class="form-label">Action Done</label>
        <input type="text" name="action_done" class="form-control" maxlength="300" value="{{ record.action_done if record else '' }}" required>
    </div>
    <div class="col-12 col-md-6">
        <label class="form-label">Date</label>
        <input type="date" name="date" class="form-control" value="{{ record.date if record else '' }}" required>
    </div>
    <div class="col-12 col-md-6">
        <label class="form-label">Area In-Charge</label>
        <input type="text" name="area_in_charge" class="form-control" maxlength="300" value="{{ record.area_in_charge if record else '' }}" required>
    </div>

    <!-- Category -->
    <div class="col-12 col-md-4">
        <label class="form-label">Category</label>
        <select name="category" id="category" class="form-select" onchange="toggleFields()">
            <option {{ 'selected' if record and record.category=='Good Observation' else '' }}>Good Observation</option>
            <option {{ 'selected' if record and record.category=='Findings' else '' }}>Findings</option>
        </select>
    </div>

    <!-- Status -->
    <div class="col-12 col-md-4">
        <label class="form-label">Status</label>
        <select name="status" id="status" class="form-select">
            <option {{ 'selected' if record and record.status=='Open' else '' }}>Open</option>
            <option {{ 'selected' if record and record.status=='Closed' else '' }}>Closed</option>
        </select>
    </div>

    <!-- OSH Rule -->
    <div class="col-12 col-md-4">
        <label class="form-label">OSH Rule</label>
        <select name="osh_rule" id="osh_rule" class="form-select">
            <option {{ 'selected' if record and record.osh_rule=='1060' else '' }}>1060</option>
            <option {{ 'selected' if record and record.osh_rule=='1200' else '' }}>1200</option>
            <option {{ 'selected' if record and record.osh_rule=='1210' else '' }}>1210</option>
        </select>
    </div>

    <div class="col-12">
        <label class="form-label">Safety Officer</label>
        <input type="text" name="safety_officer" class="form-control" maxlength="300" value="{{ record.safety_officer if record else '' }}" required>
    </div>
  </div>

  <div class="mt-3">
    <button type="submit" class="btn btn-success">Save</button>
    <a href="{{ url_for('index') }}" class="btn btn-secondary">Cancel</a>
  </div>
</form>
</div>
<script>toggleFields();</script>
</body>
</html>







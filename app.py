from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from PIL import Image as PILImage
from io import BytesIO
from database import init_db, get_db

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

init_db()


# ----------------------------
# Helpers
# ----------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def query_records(filters=None, sort_field=None, sort_order="ASC"):
    filters = filters or {}
    db = get_db()

    query = "SELECT * FROM records WHERE 1=1"
    params = []

    for key, val in filters.items():
        if val:
            query += f" AND {key} LIKE ?"
            params.append(f"%{val}%")

    VALID_SORT_FIELDS = {
        "id", "date", "category", "status",
        "area_department", "checked_by"
    }

    if sort_field in VALID_SORT_FIELDS:
        direction = "ASC" if sort_order.upper() == "ASC" else "DESC"
        query += f" ORDER BY {sort_field} {direction}, id DESC"
    else:
        query += " ORDER BY id DESC"

    records = db.execute(query, params).fetchall()
    db.close()
    return [dict(r) for r in records]


# ----------------------------
# Routes
# ----------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/records')
def fetch_records():
    filters = {
        "category": request.args.get("category"),
        "status": request.args.get("status"),
        "osh_rule": request.args.get("osh_rule"),
        "area_department": request.args.get("area_department")
    }

    sort_field = request.args.get("sort_field")
    sort_order = request.args.get("sort_order", "DESC")

    records = query_records(filters, sort_field, sort_order)
    return jsonify(records)


@app.route('/add', methods=['GET', 'POST'])
def add_record():
    if request.method == 'POST':
        db = get_db()

        file = request.files.get('picture')
        add_file = request.files.get('additional_picture')

        cursor = db.execute("""
            INSERT INTO records (
                detailed_observation, picture_path, additional_picture_path,
                area_department, checked_by, action_done, date,
                so_timestamp, area_in_charge, category, status,
                osh_rule, safety_officer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['detailed_observation'][:300],
            None,
            None,
            request.form['area_department'][:300],
            request.form['checked_by'][:300],
            request.form['action_done'][:300],
            request.form['date'],
            datetime.now().strftime("%B %d %Y %H:%M:%S"),
            request.form['area_in_charge'][:300],
            request.form['category'],
            "" if request.form['category']=="Good Observation" else request.form['status'],
            "" if request.form['category']=="Good Observation" else request.form['osh_rule'],
            request.form['safety_officer'][:300]
        ))

        record_id = cursor.lastrowid

        if file and allowed_file(file.filename):
            filename = f"{record_id}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            db.execute("UPDATE records SET picture_path=? WHERE id=?",
                       (f"uploads/{filename}", record_id))

        if add_file and allowed_file(add_file.filename):
            filename = f"{record_id}_add_{secure_filename(add_file.filename)}"
            add_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            db.execute("UPDATE records SET additional_picture_path=? WHERE id=?",
                       (f"uploads/{filename}", record_id))

        db.commit()
        db.close()
        return redirect(url_for('index'))

    return render_template('record_form.html', record=None)


@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    db = get_db()
    record = db.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()

    if not record:
        db.close()
        return "Record not found", 404

    if request.method == 'POST':
        file = request.files.get('picture')
        add_file = request.files.get('additional_picture')

        if file and allowed_file(file.filename):
            filename = f"{record_id}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            db.execute("UPDATE records SET picture_path=? WHERE id=?",
                       (f"uploads/{filename}", record_id))

        if add_file and allowed_file(add_file.filename):
            filename = f"{record_id}_add_{secure_filename(add_file.filename)}"
            add_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            db.execute("UPDATE records SET additional_picture_path=? WHERE id=?",
                       (f"uploads/{filename}", record_id))

        db.execute("""
            UPDATE records SET
                detailed_observation=?, area_department=?, checked_by=?,
                action_done=?, date=?, area_in_charge=?,
                category=?, status=?, osh_rule=?, safety_officer=?
            WHERE id=?
        """, (
            request.form['detailed_observation'][:300],
            request.form['area_department'][:300],
            request.form['checked_by'][:300],
            request.form['action_done'][:300],
            request.form['date'],
            request.form['area_in_charge'][:300],
            request.form['category'],
            "" if request.form['category']=="Good Observation" else request.form['status'],
            "" if request.form['category']=="Good Observation" else request.form['osh_rule'],
            request.form['safety_officer'][:300],
            record_id
        ))

        db.commit()
        db.close()
        return redirect(url_for('index'))

    db.close()
    return render_template('record_form.html', record=dict(record))


@app.route('/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    db = get_db()
    db.execute("DELETE FROM records WHERE id=?", (record_id,))
    db.commit()
    db.close()
    return redirect(url_for('index'))


@app.route('/export')
def export_excel():
    filters = {
        "category": request.args.get("category"),
        "status": request.args.get("status"),
        "osh_rule": request.args.get("osh_rule"),
        "area_department": request.args.get("area_department")
    }

    sort_field = request.args.get("sort_field")
    sort_order = request.args.get("sort_order", "DESC")

    records = query_records(filters, sort_field, sort_order)

    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Safety Report"

    headers = ["ID","Observation","Picture","Area/Dept","Checked By","Action Done",
               "Date","SO Timestamp","Area In-Charge","Category","Additional Picture",
               "Status","OSH Rule","Safety Officer"]

    ws.append(headers)

    alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for row_idx, r in enumerate(records, start=2):
        ws.append([
            r['id'], r['detailed_observation'], "", r['area_department'],
            r['checked_by'], r['action_done'], r['date'], r['so_timestamp'],
            r['area_in_charge'], r['category'], "",
            r['status'], r['osh_rule'], r['safety_officer']
        ])

        for col in range(1, 15):
            ws.cell(row=row_idx, column=col).alignment = alignment

    file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(file)
    return send_file(file, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)

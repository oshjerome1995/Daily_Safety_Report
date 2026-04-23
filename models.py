from database import get_db

def get_all_records(filters=None, sort_by=None, sort_dir='DESC'):
    conn = get_db()
    query = "SELECT * FROM records"
    params = []

    if filters:
        conditions = []
        for key, value in filters.items():
            if value:
                conditions.append(f"{key} LIKE ?")
                params.append(f"%{value}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

    allowed_sort_columns = ["id","date","category","status","area_department"]
    if sort_by in allowed_sort_columns:
        query += f" ORDER BY {sort_by} {sort_dir}"
    else:
        query += " ORDER BY id DESC"

    records = conn.execute(query, params).fetchall()
    conn.close()
    return records

def get_record(record_id):
    conn = get_db()
    record = conn.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
    conn.close()
    return record

def delete_record(record_id):
    conn = get_db()
    conn.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
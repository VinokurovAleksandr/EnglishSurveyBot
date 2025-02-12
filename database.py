import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Ініціалізація Google Sheets API
SHEET_ID = "1nm3YVan5Xv2k-tRu_DFl7fpqiIMHURv0cTlYiDO3OFA"  # Вставте ID Google-таблиці

def connect_google_sheets():
    """Підключення до Google Sheets API"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1  # Використовуємо перший лист
    return sheet

def create_db():
    """Створює локальну базу даних SQLite"""
    conn = sqlite3.connect("survey.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        reason TEXT,
        obstacle TEXT,
        future_use TEXT,
        interest TEXT,
        format TEXT,
        pace TEXT,
        hobbies TEXT,
        daily_use TEXT,
        favorites TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_response(user_id, column, answer):
    """Зберігає відповідь у локальну базу даних SQLite"""
    conn = sqlite3.connect("survey.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM responses WHERE user_id=?", (user_id,))
    existing_entry = cursor.fetchone()

    if existing_entry:
        cursor.execute(f"UPDATE responses SET {column} = ? WHERE user_id = ?", (answer, user_id))
    else:
        cursor.execute(f"INSERT INTO responses (user_id, {column}) VALUES (?, ?)", (user_id, answer))

    conn.commit()
    conn.close()

def save_to_google_sheets(user_id):
    """Зберігає всі відповіді користувача в Google Sheets"""
    conn = sqlite3.connect("survey.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM responses WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if data:
        sheet = connect_google_sheets()
        sheet.append_row(data)  # Додає рядок до таблиці

    conn.close()

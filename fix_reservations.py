from app import app, db

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS room_reservations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    room_id INT NOT NULL,
                    semester_id INT NOT NULL,
                    day ENUM('Monday','Tuesday','Wednesday','Thursday','Friday') NOT NULL,
                    time_start TIME NOT NULL,
                    time_end TIME NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                    FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
                )
            """))
            conn.commit()
            print('✅ room_reservations table created on Aiven!')
    except Exception as e:
        print(f'Note: {e}')
from app import app, db

with app.app_context():
    try:
        with db.engine.connect() as conn:
            # Create instructors table
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS instructors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    contact VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print('✅ Instructors table created!')

            # Add foreign key
            conn.execute(db.text("""
                ALTER TABLE schedules 
                ADD CONSTRAINT fk_instr 
                FOREIGN KEY (instructor_id) 
                REFERENCES instructors(id) 
                ON DELETE SET NULL
            """))
            conn.commit()
            print('✅ Foreign key added!')

    except Exception as e:
        print(f'Note: {e}')
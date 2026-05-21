from app import app, db

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS enrollment_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    school_email VARCHAR(100) DEFAULT 'acsicollegeiloilo31@gmail.com',
                    gcash_number VARCHAR(20) DEFAULT '09639859782',
                    gcash_name VARCHAR(100) DEFAULT 'Chewyll Simora',
                    palawan_number VARCHAR(20) DEFAULT '09639859782',
                    palawan_name VARCHAR(100) DEFAULT 'Chewyll Simora',
                    requirements TEXT,
                    courses TEXT,
                    payment_notes TEXT,
                    is_active TINYINT(1) DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """))
            conn.execute(db.text("""
                INSERT INTO enrollment_settings (requirements, courses, payment_notes) VALUES (
                    '["Photocopy of Birth Certificate (PSA)","Certificate of Good Moral Character","Form 138 / HS Card / Transcript of Records","2 pcs 2x2 ID Picture","2 pcs White Long Folder"]',
                    '["Bachelor of Science in Information Systems","Bachelor of Science in Computer Science","Associate in Computer Technology","Short-Term Courses"]',
                    'Payment can be made via GCash or Palawan Padala. Initial payment required upon enrollment.'
                )
            """))
            conn.commit()
            print('✅ Enrollment settings table created on Aiven!')
    except Exception as e:
        print(f'Note: {e}')
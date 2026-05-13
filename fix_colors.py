from app import app, db
from models import Subject

with app.app_context():
    # First add the column
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE subjects ADD COLUMN color VARCHAR(7) DEFAULT '#3498db'"))
            conn.commit()
            print('✅ Color column added!')
    except Exception as e:
        print(f'Note (column may already exist): {e}')

    # Then assign colors to all subjects
    color_palette = [
        '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#e67e22', '#e91e63', '#00bcd4', '#8bc34a',
        '#ff5722', '#607d8b', '#673ab7', '#009688', '#ff9800',
        '#c0392b', '#2980b9', '#27ae60', '#d35400', '#8e44ad',
        '#16a085', '#f1c40f', '#2c3e50', '#e056fd', '#badc58',
        '#f9ca24', '#6ab04c', '#eb4d4b', '#7ed6df', '#e55039'
    ]

    subjects = Subject.query.order_by(Subject.subject_code).all()
    for i, subject in enumerate(subjects):
        subject.color = color_palette[i % len(color_palette)]
    db.session.commit()
    print(f'✅ Colors assigned to {len(subjects)} subjects!')
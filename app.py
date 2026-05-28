from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Admin, Semester, Room, Subject, Schedule, Instructor, RoomReservation, EnrollmentSettings
import bcrypt
import qrcode
import io
import os
from datetime import datetime, time

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))

# ─────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────

@app.route('/')
def index():
    rooms = Room.query.order_by(Room.name).all()
    active_semester = Semester.query.filter_by(is_active=True).first()
    return render_template('index.html', rooms=rooms, active_semester=active_semester)

@app.route('/rooms')
def public_rooms():
    rooms = Room.query.order_by(Room.name).all()
    active_semester = Semester.query.filter_by(is_active=True).first()
    return render_template('rooms.html', rooms=rooms, active_semester=active_semester)

@app.route('/room/<int:room_id>')
def public_room(room_id):
    room = Room.query.get_or_404(room_id)
    active_semester = Semester.query.filter_by(is_active=True).first()

    schedules = []
    if active_semester:
        schedules = Schedule.query.filter_by(
            room_id=room_id,
            semester_id=active_semester.id
        ).all()

    # Build GLOBAL color map from subjects table
    subject_colors = {}
    all_subjects = Subject.query.all()
    for subj in all_subjects:
        subject_colors[subj.subject_code] = subj.color or '#3498db'

    # For subjects not in library, assign fallback colors
    color_palette = [
        '#e74c3c','#3498db','#2ecc71','#f39c12','#9b59b6',
        '#1abc9c','#e67e22','#e91e63','#00bcd4','#8bc34a',
        '#ff5722','#607d8b','#673ab7','#009688','#ff9800'
    ]
    color_index = 0
    for s in schedules:
        if s.subject_code not in subject_colors:
            subject_colors[s.subject_code] = color_palette[color_index % len(color_palette)]
            color_index += 1

    # Organize by day
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    schedule_by_day = {day: [] for day in days}
    for s in schedules:
        schedule_by_day[s.day].append(s)
    for day in days:
        schedule_by_day[day].sort(key=lambda x: x.time_start)

    # Build unique subjects and instructors
    seen_subjects = {}
    seen_instructors = {}
    for s in schedules:
        if s.subject_code not in seen_subjects:
            seen_subjects[s.subject_code] = s.subject_description
        if s.instructor_id and s.instructor_id not in seen_instructors:
            instr = db.session.get(Instructor, s.instructor_id)
            if instr:
                seen_instructors[instr.id] = instr
        elif not s.instructor_id and s.instructor not in seen_instructors:
            seen_instructors[s.instructor] = type('obj', (object,), {
                'name': s.instructor, 'email': None, 'contact': None
            })()

    # Build vacant slots
    time_slots = [
        ('09:00', '09:30'), ('09:30', '10:00'),
        ('10:00', '10:30'), ('10:30', '11:00'),
        ('11:00', '11:30'), ('11:30', '12:00'),
        ('12:00', '12:30'), ('12:30', '13:00'),
        ('13:00', '13:30'), ('13:30', '14:00'),
        ('14:00', '14:30'), ('14:30', '15:00'),
        ('15:00', '15:30'), ('15:30', '16:00'),
        ('16:00', '16:30'), ('16:30', '17:00'),
        ('17:00', '17:30'), ('17:30', '18:00'),
    ]

    # Get reservations
    reservations = []
    if active_semester:
        reservations = RoomReservation.query.filter_by(
            room_id=room_id,
            semester_id=active_semester.id
        ).all()

    vacant_by_day = {day: [] for day in days}
    for day in days:
        day_schedules = schedule_by_day[day]
        day_reservations = [r for r in reservations if r.day == day]

        # Merge scheduled and reserved slots
        busy_slots = []
        for s in day_schedules:
            busy_slots.append((s.time_start, s.time_end))
        for r in day_reservations:
            busy_slots.append((r.time_start, r.time_end))

        # Find vacant slots
        vacant_merged = []
        for slot_start, slot_end in time_slots:
            from datetime import datetime as dt
            ts = dt.strptime(slot_start, '%H:%M').time()
            te = dt.strptime(slot_end, '%H:%M').time()
            is_busy = False
            for busy_start, busy_end in busy_slots:
                if not (te <= busy_start or ts >= busy_end):
                    is_busy = True
                    break
            if not is_busy:
                vacant_merged.append((slot_start, slot_end))

        # Merge consecutive vacant slots
        if vacant_merged:
            merged = [vacant_merged[0]]
            for current in vacant_merged[1:]:
                if current[0] == merged[-1][1]:
                    merged[-1] = (merged[-1][0], current[1])
                else:
                    merged.append(current)
            vacant_by_day[day] = merged

    return render_template('public_room.html',
        room=room,
        active_semester=active_semester,
        schedule_by_day=schedule_by_day,
        subject_colors=subject_colors,
        days=days,
        seen_subjects=seen_subjects,
        seen_instructors=seen_instructors,
        vacant_by_day=vacant_by_day
    )
# ─────────────────────────────────────────
# ADMIN AUTH
# ─────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

# ─────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    rooms = Room.query.count()
    subjects = Subject.query.count()
    active_semester = Semester.query.filter_by(is_active=True).first()
    schedules = Schedule.query.count()
    instructors = Instructor.query.count()
    return render_template('admin/dashboard.html',
        room_count=rooms,
        subject_count=subjects,
        schedule_count=schedules,
        instructor_count=instructors,
        active_semester=active_semester
    )

# ─────────────────────────────────────────
# SEMESTER MANAGEMENT
# ─────────────────────────────────────────

@app.route('/admin/semesters')
@login_required
def admin_semesters():
    semesters = Semester.query.order_by(Semester.created_at.desc()).all()
    return render_template('admin/semesters.html', semesters=semesters)

@app.route('/admin/semesters/add', methods=['POST'])
@login_required
def admin_semester_add():
    label = request.form.get('label')
    if label:
        sem = Semester(label=label, is_active=False)
        db.session.add(sem)
        db.session.commit()
        flash('Semester added successfully.', 'success')
    return redirect(url_for('admin_semesters'))

@app.route('/admin/semesters/<int:sem_id>/activate', methods=['POST'])
@login_required
def admin_semester_activate(sem_id):
    Semester.query.update({'is_active': False})
    sem = Semester.query.get_or_404(sem_id)
    sem.is_active = True
    db.session.commit()
    flash(f'"{sem.label}" is now the active semester.', 'success')
    return redirect(url_for('admin_semesters'))

@app.route('/admin/semesters/<int:sem_id>/delete', methods=['POST'])
@login_required
def admin_semester_delete(sem_id):
    sem = Semester.query.get_or_404(sem_id)
    db.session.delete(sem)
    db.session.commit()
    flash('Semester deleted.', 'success')
    return redirect(url_for('admin_semesters'))

# ─────────────────────────────────────────
# ROOM MANAGEMENT
# ─────────────────────────────────────────

@app.route('/admin/rooms')
@login_required
def admin_rooms():
    rooms = Room.query.order_by(Room.name).all()
    return render_template('admin/rooms.html', rooms=rooms)

@app.route('/admin/rooms/add', methods=['GET', 'POST'])
@login_required
def admin_room_add():
    if request.method == 'POST':
        name = request.form.get('name')
        rules = request.form.get('rules')
        if name:
            room = Room(name=name, rules=rules)
            db.session.add(room)
            db.session.commit()
            flash('Room added successfully.', 'success')
            return redirect(url_for('admin_rooms'))
    return render_template('admin/room_form.html', room=None)

@app.route('/admin/rooms/<int:room_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_room_edit(room_id):
    room = Room.query.get_or_404(room_id)
    if request.method == 'POST':
        room.name = request.form.get('name')
        room.rules = request.form.get('rules')
        db.session.commit()
        flash('Room updated successfully.', 'success')
        return redirect(url_for('admin_rooms'))
    return render_template('admin/room_form.html', room=room)

@app.route('/admin/rooms/<int:room_id>/delete', methods=['POST'])
@login_required
def admin_room_delete(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted.', 'success')
    return redirect(url_for('admin_rooms'))

# ─────────────────────────────────────────
# ROOM RESERVATIONS (VACANT SLOTS)
# ─────────────────────────────────────────

@app.route('/admin/rooms/<int:room_id>/reservations')
@login_required
def admin_reservations(room_id):
    room = Room.query.get_or_404(room_id)
    semesters = Semester.query.order_by(Semester.created_at.desc()).all()
    active_semester = Semester.query.filter_by(is_active=True).first()

    sem_id = request.args.get('semester_id', active_semester.id if active_semester else None)
    reservations = []
    selected_semester = None
    if sem_id:
        selected_semester = Semester.query.get(sem_id)
        reservations = RoomReservation.query.filter_by(
            room_id=room_id,
            semester_id=sem_id
        ).order_by(RoomReservation.day, RoomReservation.time_start).all()

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    return render_template('admin/reservations.html',
        room=room,
        semesters=semesters,
        selected_semester=selected_semester,
        reservations=reservations,
        days=days
    )

@app.route('/admin/rooms/<int:room_id>/reservations/add', methods=['POST'])
@login_required
def admin_reservation_add(room_id):
    semester_id = request.form.get('semester_id')
    day = request.form.get('day')
    time_start_str = request.form.get('time_start')
    time_end_str = request.form.get('time_end')

    time_start = datetime.strptime(time_start_str, '%H:%M').time()
    time_end = datetime.strptime(time_end_str, '%H:%M').time()

    reservation = RoomReservation(
        room_id=room_id,
        semester_id=semester_id,
        day=day,
        time_start=time_start,
        time_end=time_end
    )
    db.session.add(reservation)
    db.session.commit()
    flash('Reservation added successfully.', 'success')
    return redirect(url_for('admin_reservations', room_id=room_id, semester_id=semester_id))

@app.route('/admin/reservations/<int:res_id>/delete', methods=['POST'])
@login_required
def admin_reservation_delete(res_id):
    reservation = RoomReservation.query.get_or_404(res_id)
    room_id = reservation.room_id
    semester_id = reservation.semester_id
    db.session.delete(reservation)
    db.session.commit()
    flash('Reservation deleted.', 'success')
    return redirect(url_for('admin_reservations', room_id=room_id, semester_id=semester_id))
# ─────────────────────────────────────────
# SCHEDULE MANAGEMENT
# ─────────────────────────────────────────

@app.route('/admin/rooms/<int:room_id>/schedule')
@login_required
def admin_schedule(room_id):
    room = Room.query.get_or_404(room_id)
    semesters = Semester.query.order_by(Semester.created_at.desc()).all()
    active_semester = Semester.query.filter_by(is_active=True).first()
    subjects = Subject.query.order_by(Subject.subject_code).all()
    instructors = Instructor.query.order_by(Instructor.name).all()

    sem_id = request.args.get('semester_id', active_semester.id if active_semester else None)
    schedules = []
    selected_semester = None
    if sem_id:
        selected_semester = Semester.query.get(sem_id)
        schedules = Schedule.query.filter_by(
            room_id=room_id,
            semester_id=sem_id
        ).order_by(Schedule.day, Schedule.time_start).all()

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    return render_template('admin/schedule.html',
        room=room,
        semesters=semesters,
        selected_semester=selected_semester,
        schedules=schedules,
        subjects=subjects,
        instructors=instructors,
        days=days
    )

@app.route('/admin/rooms/<int:room_id>/schedule/add', methods=['POST'])
@login_required
def admin_schedule_add(room_id):
    room = Room.query.get_or_404(room_id)
    semester_id = request.form.get('semester_id')
    subject_code = request.form.get('subject_code')
    subject_description = request.form.get('subject_description')
    instructor_id = request.form.get('instructor_id')
    instructor_name = request.form.get('instructor_name')
    day = request.form.get('day')
    time_start_str = request.form.get('time_start')
    time_end_str = request.form.get('time_end')

    time_start = datetime.strptime(time_start_str, '%H:%M').time()
    time_end = datetime.strptime(time_end_str, '%H:%M').time()

    # Get instructor name for storage
    if instructor_id:
        instr = db.session.get(Instructor, int(instructor_id))
        instructor_display = instr.name if instr else instructor_name
    else:
        instructor_display = instructor_name

    # Overlap check
    overlaps = Schedule.query.filter_by(
        room_id=room_id,
        semester_id=semester_id,
        day=day
    ).all()

    for existing in overlaps:
        if not (time_end <= existing.time_start or time_start >= existing.time_end):
            flash(f'⚠️ Schedule conflict! Overlaps with {existing.subject_code} ({existing.time_start.strftime("%I:%M %p")} - {existing.time_end.strftime("%I:%M %p")}).', 'error')
            return redirect(url_for('admin_schedule', room_id=room_id, semester_id=semester_id))

    schedule = Schedule(
        room_id=room_id,
        semester_id=semester_id,
        subject_code=subject_code,
        subject_description=subject_description,
        instructor=instructor_display,
        instructor_id=int(instructor_id) if instructor_id else None,
        day=day,
        time_start=time_start,
        time_end=time_end
    )
    db.session.add(schedule)
    db.session.commit()
    flash('Schedule added successfully.', 'success')
    return redirect(url_for('admin_schedule', room_id=room_id, semester_id=semester_id))

@app.route('/admin/schedule/<int:sched_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_schedule_edit(sched_id):
    sched = Schedule.query.get_or_404(sched_id)
    room = Room.query.get(sched.room_id)
    instructors = Instructor.query.order_by(Instructor.name).all()
    subjects = Subject.query.order_by(Subject.subject_code).all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    if request.method == 'POST':
        subject_code = request.form.get('subject_code')
        subject_description = request.form.get('subject_description')
        instructor_id = request.form.get('instructor_id')
        instructor_name = request.form.get('instructor_name')
        day = request.form.get('day')
        time_start_str = request.form.get('time_start')
        time_end_str = request.form.get('time_end')

        time_start = datetime.strptime(time_start_str, '%H:%M').time()
        time_end = datetime.strptime(time_end_str, '%H:%M').time()

        if instructor_id:
            instr = db.session.get(Instructor, int(instructor_id))
            instructor_display = instr.name if instr else instructor_name
        else:
            instructor_display = instructor_name

        # Overlap check excluding current schedule
        overlaps = Schedule.query.filter_by(
            room_id=sched.room_id,
            semester_id=sched.semester_id,
            day=day
        ).filter(Schedule.id != sched_id).all()

        for existing in overlaps:
            if not (time_end <= existing.time_start or time_start >= existing.time_end):
                flash(f'⚠️ Schedule conflict! Overlaps with {existing.subject_code} ({existing.time_start.strftime("%I:%M %p")} - {existing.time_end.strftime("%I:%M %p")}).', 'error')
                return redirect(url_for('admin_schedule_edit', sched_id=sched_id))

        sched.subject_code = subject_code
        sched.subject_description = subject_description
        sched.instructor = instructor_display
        sched.instructor_id = int(instructor_id) if instructor_id else None
        sched.day = day
        sched.time_start = time_start
        sched.time_end = time_end
        db.session.commit()
        flash('Schedule updated successfully.', 'success')
        return redirect(url_for('admin_schedule', room_id=sched.room_id, semester_id=sched.semester_id))

    return render_template('admin/schedule_edit.html',
        sched=sched,
        room=room,
        instructors=instructors,
        subjects=subjects,
        days=days
    )

@app.route('/admin/schedule/<int:sched_id>/delete', methods=['POST'])
@login_required
def admin_schedule_delete(sched_id):
    sched = Schedule.query.get_or_404(sched_id)
    room_id = sched.room_id
    semester_id = sched.semester_id
    db.session.delete(sched)
    db.session.commit()
    flash('Schedule entry deleted.', 'success')
    return redirect(url_for('admin_schedule', room_id=room_id, semester_id=semester_id))

# ─────────────────────────────────────────
# SUBJECT LIBRARY
# ─────────────────────────────────────────

@app.route('/admin/subjects')
@login_required
def admin_subjects():
    subjects = Subject.query.order_by(Subject.subject_code).all()
    return render_template('admin/subjects.html', subjects=subjects)

@app.route('/admin/subjects/add', methods=['POST'])
@login_required
def admin_subject_add():
    code = request.form.get('subject_code')
    desc = request.form.get('subject_description')
    if code and desc:
        subject = Subject(subject_code=code, subject_description=desc)
        db.session.add(subject)
        db.session.commit()
        flash('Subject added to library.', 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/subjects/<int:sub_id>/delete', methods=['POST'])
@login_required
def admin_subject_delete(sub_id):
    subject = Subject.query.get_or_404(sub_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted.', 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/subjects/<int:sub_id>/edit', methods=['POST'])
@login_required
def admin_subject_edit(sub_id):
    subject = Subject.query.get_or_404(sub_id)
    subject.color = request.form.get('color', '#3498db')
    db.session.commit()
    flash('Subject color updated.', 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/subjects/api')
@login_required
def admin_subjects_api():
    subjects = Subject.query.order_by(Subject.subject_code).all()
    return jsonify([{
        'code': s.subject_code,
        'description': s.subject_description
    } for s in subjects])

# ─────────────────────────────────────────
# INSTRUCTOR LIBRARY
# ─────────────────────────────────────────

@app.route('/admin/instructors')
@login_required
def admin_instructors():
    instructors = Instructor.query.order_by(Instructor.name).all()
    return render_template('admin/instructors.html', instructors=instructors)

@app.route('/admin/instructors/add', methods=['POST'])
@login_required
def admin_instructor_add():
    name = request.form.get('name')
    email = request.form.get('email')
    contact = request.form.get('contact')
    if name:
        instructor = Instructor(name=name, email=email, contact=contact)
        db.session.add(instructor)
        db.session.commit()
        flash('Instructor added successfully.', 'success')
    return redirect(url_for('admin_instructors'))

@app.route('/admin/instructors/<int:instr_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_instructor_edit(instr_id):
    instructor = Instructor.query.get_or_404(instr_id)
    if request.method == 'POST':
        instructor.name = request.form.get('name')
        instructor.email = request.form.get('email')
        instructor.contact = request.form.get('contact')
        db.session.commit()
        flash('Instructor updated.', 'success')
        return redirect(url_for('admin_instructors'))
    return render_template('admin/instructor_form.html', instructor=instructor)

@app.route('/admin/instructors/<int:instr_id>/delete', methods=['POST'])
@login_required
def admin_instructor_delete(instr_id):
    instructor = Instructor.query.get_or_404(instr_id)
    db.session.delete(instructor)
    db.session.commit()
    flash('Instructor deleted.', 'success')
    return redirect(url_for('admin_instructors'))

@app.route('/admin/instructors/api')
@login_required
def admin_instructors_api():
    instructors = Instructor.query.order_by(Instructor.name).all()
    return jsonify([{
        'id': i.id,
        'name': i.name,
        'email': i.email or '',
        'contact': i.contact or ''
    } for i in instructors])

# ─────────────────────────────────────────
# QR CODE
# ─────────────────────────────────────────
@app.route('/admin/rooms/<int:room_id>/qr')
@login_required
def admin_qr(room_id):
    room = Room.query.get_or_404(room_id)
    return render_template('admin/qr_page.html', room=room)

@app.route('/admin/rooms/<int:room_id>/qr/download')
@login_required
def admin_qr_download(room_id):
    from PIL import Image, ImageDraw, ImageFont
    room = Room.query.get_or_404(room_id)
    url = request.host_url + f'room/{room_id}'

    # Generate QR
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white').convert('RGB')

    qr_w, qr_h = qr_img.size

    # Create canvas with extra space for title and URL
    padding = 30
    title_height = 70
    url_height = 40
    total_height = qr_h + title_height + url_height + (padding * 2)
    total_width = qr_w + (padding * 2)

    canvas = Image.new('RGB', (total_width, total_height), 'white')
    draw = ImageDraw.Draw(canvas)

    # Try to use a font, fallback to default
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_url = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font_url = ImageFont.load_default()

    # Draw room name - wrap if too long
    max_width = total_width - (padding * 2)
    words = room.name.split()
    lines = []
    current_line = ''
    for word in words:
        test_line = current_line + (' ' if current_line else '') + word
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    line_height = 24
    total_text_height = len(lines) * line_height
    start_y = (title_height - total_text_height) // 2 + padding // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        text_w = bbox[2] - bbox[0]
        x = (total_width - text_w) // 2
        draw.text((x, start_y + i * line_height), line, fill='#222222', font=font_title)

    # Paste QR code
    canvas.paste(qr_img, (padding, padding + title_height))

    # Draw URL at bottom
    bbox2 = draw.textbbox((0, 0), url, font=font_url)
    url_w = bbox2[2] - bbox2[0]
    url_x = (total_width - url_w) // 2
    url_y = padding + title_height + qr_h + 10
    draw.text((url_x, url_y), url, fill='#555555', font=font_url)

    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png',
                     as_attachment=True,
                     download_name=f'QR_{room.name}.png')
# ─────────────────────────────────────────
# ADMIN SETTINGS
# ─────────────────────────────────────────

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        new_username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        admin = db.session.get(Admin, current_user.id)

        if not bcrypt.checkpw(current_password.encode('utf-8'), admin.password_hash.encode('utf-8')):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('admin_settings'))

        admin.username = new_username
        if new_password:
            admin.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin_settings'))

    return render_template('admin/settings.html')

# ─────────────────────────────────────────
# INIT DB + DEFAULT ADMIN
# ─────────────────────────────────────────
# ─────────────────────────────────────────
# ENROLLMENT - PUBLIC
# ─────────────────────────────────────────

@app.route('/enroll')
def public_enroll():
    settings = EnrollmentSettings.query.first()
    if not settings:
        settings = EnrollmentSettings()
    
    import json
    requirements = json.loads(settings.requirements) if settings.requirements else []
    courses = json.loads(settings.courses) if settings.courses else []
    
    return render_template('public_enroll.html',
        settings=settings,
        requirements=requirements,
        courses=courses
    )

@app.route('/enroll/shs')
def public_enroll_shs():
    settings = EnrollmentSettings.query.first()
    if not settings:
        settings = EnrollmentSettings()
    return render_template('public_enroll_shs.html', settings=settings)

@app.route('/enroll/download')
def enroll_download():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import os

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=12*mm, leftMargin=12*mm,
        topMargin=8*mm, bottomMargin=8*mm)

    styles = getSampleStyleSheet()
    elements = []

    # Header styles
    title_style = ParagraphStyle('title',
        fontSize=11, fontName='Helvetica-Bold',
        alignment=TA_CENTER, spaceAfter=2)
    sub_style = ParagraphStyle('sub',
        fontSize=9, fontName='Helvetica',
        alignment=TA_CENTER, spaceAfter=2)
    label_style = ParagraphStyle('label',
        fontSize=8, fontName='Helvetica-Bold',
        alignment=TA_LEFT)
    normal_style = ParagraphStyle('normal',
        fontSize=8, fontName='Helvetica',
        alignment=TA_LEFT)
    center_style = ParagraphStyle('center',
        fontSize=8, fontName='Helvetica',
        alignment=TA_CENTER)

    # ── HEADER ──
    logo_path = os.path.join(app.root_path, 'static', 'assets', 'acsi_logo.png')
    
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=18*mm, height=18*mm)
    else:
        logo = Paragraph('', normal_style)

    header_data = [[
        logo,
        [
            Paragraph('ACSI College Iloilo Inc.', title_style),
            Paragraph('The HOME of 200 Pesos Lang Down Payment', sub_style),
            Paragraph("STUDENT'S INFORMATION SHEET", ParagraphStyle('form_title',
                fontSize=12, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        ]
    ]]
    
    header_table = Table(header_data, colWidths=[22*mm, 153*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 1.5*mm))

    # ── INFO ROW ──
    info_data = [['Semester: _______________', 'School Year: _______________', 'Date: _______________']]
    info_table = Table(info_data, colWidths=[58*mm, 58*mm, 59*mm])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 1*mm))

    # ── STUDENT CLASSIFICATION ──
    elements.append(Paragraph('Student Classification (Please check)', label_style))
    elements.append(Spacer(1, 1*mm))
    
    class_data = [[
        '☐ Inquired', '☐ New (SHS)', '☐ Old', '☐ Returnee', '☐ With Special Needs'
    ],[
        '☐ Day Class', '☐ Night Class', '☐ Transferee', '', ''
    ]]
    class_table = Table(class_data, colWidths=[35*mm, 35*mm, 25*mm, 35*mm, 45*mm])
    class_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ]))
    elements.append(class_table)
    elements.append(Spacer(1, 2*mm))

    # ── NAME FIELDS ──
    def name_row(label):
        return [[Paragraph(f'<b>{label}:</b>', label_style), '']]
    
    def make_field_table(rows):
        t = Table(rows, colWidths=[35*mm, 140*mm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('LINEBELOW', (1,0), (1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 3),
        ]))
        return t

    elements.append(make_field_table([
        [Paragraph('<b>LAST NAME:</b>', label_style), ''],
        [Paragraph('<b>FIRST NAME:</b>', label_style), ''],
        [Paragraph('<b>MIDDLE NAME:</b>', label_style), ''],
        [Paragraph('<b>MAIDEN NAME:</b>', label_style), ''],
    ]))
    elements.append(Spacer(1, 1*mm))

    # ── ADDRESS ──
    elements.append(Paragraph('<b>Provincial Address:</b>', label_style))
    addr_data = [['Street/Zone/Phase/Block', 'Barangay', 'District', 'Municipality/City', 'Province']]
    addr_table = Table(addr_data, colWidths=[40*mm, 30*mm, 25*mm, 35*mm, 45*mm])
    addr_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(addr_table)
    elements.append(Spacer(1, 0.5*mm))

    elements.append(Paragraph('<b>City Address:</b>', label_style))
    elements.append(addr_table)
    elements.append(Spacer(1, 1*mm))

    # ── PERSONAL DETAILS ──
    personal_data = [
        ['Sex: _______________', 'Civil Status: _______________', 'Nationality: _______________'],
        ['Age: _______________', 'Date of Birth: _______________', 'Place of Birth: _______________'],
        ['Contact Number: _______________', 'Occupation: _______________', 'Religion: _______________'],
        ['Mother\'s Name: _______________', '', ''],
        ['Father\'s Name: _______________', '', ''],
        ['Guardian\'s Name: _______________', '', ''],
    ]
    personal_table = Table(personal_data, colWidths=[58*mm, 58*mm, 59*mm])
    personal_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('SPAN', (0,3), (2,3)),
        ('SPAN', (0,4), (2,4)),
        ('SPAN', (0,5), (2,5)),
    ]))
    elements.append(personal_table)
    elements.append(Spacer(1, 2*mm))

    # ── EDUCATIONAL BACKGROUND ──
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    elements.append(Paragraph('<b>EDUCATIONAL BACKGROUND</b>', ParagraphStyle('eb',
        fontSize=9, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2)))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    elements.append(Spacer(1, 1*mm))

    def edu_section(title):
        elems = []
        elems.append(Paragraph(f'<b>{title}</b>', label_style))
        sub_data = [['School Name:', 'School Year (Graduated):']]
        sub_table = Table(sub_data, colWidths=[120*mm, 55*mm])
        sub_table.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (0,0), 0.5, colors.black),
            ('LINEBELOW', (1,0), (1,0), 0.5, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        elems.append(sub_table)
        addr2_data = [['Street/Zone/Phase/Block', 'Barangay', 'District', 'Municipality/City', 'Province']]
        addr2_table = Table(addr2_data, colWidths=[40*mm, 30*mm, 25*mm, 35*mm, 45*mm])
        addr2_table.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('LINEABOVE', (0,0), (-1,0), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 1),
        ]))
        elems.append(Paragraph('School Address:', normal_style))
        elems.append(addr2_table)
        elems.append(Spacer(1, 2*mm))
        return elems

    elements.extend(edu_section('ELEMENTARY (Name of School)'))
    elements.extend(edu_section('SECONDARY EDUCATION - High School (Name of School)'))
    elements.extend(edu_section('TERTIARY EDUCATION - College (Name of School)\nFor Transferee/Short-Term Enrollee'))

    # ── COURSE TO ENROLL ──
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    elements.append(Paragraph('<b>COURSE TO ENROLL: (Please check)</b>', label_style))
    elements.append(Spacer(1, 1*mm))

    courses_list = [
        '☐ Bachelor of Science in Computer Science',
        '☐ Bachelor of Science in Information System',
        '☐ Associate in Computer Technology',
        '☐ Short Term Course (STC)',
    ]
    for course in courses_list:
        elements.append(Paragraph(course, normal_style))
        elements.append(Spacer(1, 1*mm))

    elements.append(Spacer(1, 3*mm))

    # ── SIGNATURES ──
    sig_data = [[
        "Student's Name & Signature\n\n___________________________",
        "Cashier's Signature\n\n___________________________",
        "Registrar's Signature\n\n___________________________",
    ]]
    sig_table = Table(sig_data, colWidths=[58*mm, 58*mm, 59*mm])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph('CR#: _______________', normal_style))

    
    doc.build(elements)
    buf.seek(0)

    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True,
                     download_name='ACSI_Enrollment_Form.pdf')

# ─────────────────────────────────────────
# ENROLLMENT - ADMIN
# ─────────────────────────────────────────

@app.route('/admin/enrollment')
@login_required
def admin_enrollment():
    settings = EnrollmentSettings.query.first()
    if not settings:
        settings = EnrollmentSettings()
        db.session.add(settings)
        db.session.commit()

    import json
    requirements = json.loads(settings.requirements) if settings.requirements else []
    courses = json.loads(settings.courses) if settings.courses else []

    return render_template('admin/enrollment.html',
        settings=settings,
        requirements=requirements,
        courses=courses
    )

@app.route('/admin/enrollment/update', methods=['POST'])
@login_required
def admin_enrollment_update():
    import json
    settings = EnrollmentSettings.query.first()
    if not settings:
        settings = EnrollmentSettings()
        db.session.add(settings)

    settings.school_email = request.form.get('school_email')
    settings.gcash_number = request.form.get('gcash_number')
    settings.gcash_name = request.form.get('gcash_name')
    settings.palawan_number = request.form.get('palawan_number')
    settings.palawan_name = request.form.get('palawan_name')
    settings.payment_notes = request.form.get('payment_notes')

    # Requirements
    reqs = request.form.getlist('requirements[]')
    reqs = [r.strip() for r in reqs if r.strip()]
    settings.requirements = json.dumps(reqs)

    # Courses
    courses = request.form.getlist('courses[]')
    courses = [c.strip() for c in courses if c.strip()]
    settings.courses = json.dumps(courses)

    db.session.commit()
    flash('Enrollment settings updated successfully.', 'success')
    return redirect(url_for('admin_enrollment'))

@app.route('/admin/enrollment/qr')
@login_required
def admin_enrollment_qr():
    return render_template('admin/enrollment_qr.html')

@app.route('/admin/enrollment/qr/download')
@login_required
def admin_enrollment_qr_download():
    from PIL import Image, ImageDraw, ImageFont
    url = request.host_url + 'enroll'

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white').convert('RGB')

    qr_w, qr_h = qr_img.size
    padding = 30
    title_height = 60
    url_height = 40
    total_height = qr_h + title_height + url_height + (padding * 2)
    total_width = qr_w + (padding * 2)

    canvas = Image.new('RGB', (total_width, total_height), 'white')
    draw = ImageDraw.Draw(canvas)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_url = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font_url = ImageFont.load_default()

    title = "ACSI College Iloilo — Enrollment"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    text_w = bbox[2] - bbox[0]
    draw.text(((total_width - text_w) // 2, padding), title, fill='#222222', font=font_title)

    canvas.paste(qr_img, (padding, padding + title_height))

    bbox2 = draw.textbbox((0, 0), url, font=font_url)
    url_w = bbox2[2] - bbox2[0]
    draw.text(((total_width - url_w) // 2, padding + title_height + qr_h + 10), url, fill='#555555', font=font_url)

    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png',
                     as_attachment=True,
                     download_name='QR_Enrollment.png')


def init_db():
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = Admin(username='admin', password_hash=hashed)
            db.session.add(admin)
            db.session.commit()
            print('✅ Default admin created: username=admin, password=admin123')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
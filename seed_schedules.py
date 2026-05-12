from app import app, db
from models import Schedule, Room, Subject, Instructor, Semester
from datetime import datetime

def t(time_str):
    return datetime.strptime(time_str, '%H:%M').time()

def get_room(name):
    return Room.query.filter(Room.name.ilike(f'%{name}%')).first()

def get_instructor(last_name):
    instr = Instructor.query.filter(Instructor.name.ilike(f'%{last_name}%')).first()
    return instr.id if instr else None

def get_instructor_name(last_name):
    instr = Instructor.query.filter(Instructor.name.ilike(f'%{last_name}%')).first()
    return instr.name if instr else last_name

def add_schedule(room_name, semester_id, day, time_start, time_end, subject_code, subject_desc, instructor_last):
    room = get_room(room_name)
    if not room:
        print(f'❌ Room not found: {room_name}')
        return

    overlaps = Schedule.query.filter_by(
        room_id=room.id,
        semester_id=semester_id,
        day=day
    ).all()

    ts = t(time_start)
    te = t(time_end)

    for existing in overlaps:
        if not (te <= existing.time_start or ts >= existing.time_end):
            print(f'⚠️ Overlap in {room_name} {day} {time_start}-{time_end} {subject_code}')
            return

    sched = Schedule(
        room_id=room.id,
        semester_id=semester_id,
        day=day,
        time_start=ts,
        time_end=te,
        subject_code=subject_code,
        subject_description=subject_desc,
        instructor=get_instructor_name(instructor_last),
        instructor_id=get_instructor(instructor_last)
    )
    db.session.add(sched)
    print(f'✅ {room_name} | {day} | {time_start}-{time_end} | {subject_code} | {instructor_last}')

with app.app_context():
    # First clear all existing schedules
    Schedule.query.delete()
    db.session.commit()
    print('🗑️ Cleared existing schedules')

    semester = Semester.query.filter_by(is_active=True).first()
    if not semester:
        print('❌ No active semester found!')
        exit()

    sem_id = semester.id
    print(f'📅 Using semester: {semester.label}')

    # ─────────────────────────────────────────
    # LABRADOR
    # ─────────────────────────────────────────

    # MONDAY
    add_schedule('Labrador', sem_id, 'Monday', '09:00', '10:00', 'CSC/ISC/ACT 101', 'CS/IS/ACT 1-A', 'Villamor')
    add_schedule('Labrador', sem_id, 'Monday', '10:00', '11:00', 'CSC/ISC/ACT 103', 'CS/IS/ACT 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Monday', '11:00', '12:00', 'CSC/ISC/ACT 203', 'CS/IS/ACT 2-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Monday', '12:00', '13:00', 'CSC 202/ACT 204', 'CS/ACT 2-A', 'Pacardo')
    add_schedule('Labrador', sem_id, 'Monday', '13:00', '14:00', 'ISC 312', 'IS 3-A', 'Pacardo')
    add_schedule('Labrador', sem_id, 'Monday', '14:00', '15:00', 'CSC/ISC/ACT 206', 'CS/IS/ACT 2-A', 'Pacardo')
    add_schedule('Labrador', sem_id, 'Monday', '15:00', '16:00', 'ISC 107', 'IS 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Monday', '16:00', '17:00', 'CSC 311', 'CS 3-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Monday', '17:00', '18:00', 'CSC 312', 'CS 3-A', 'Kintao')

    # TUESDAY
    add_schedule('Labrador', sem_id, 'Tuesday', '09:00', '10:00', 'CSC/ISC/ACT 101', 'CS/IS/ACT 1-A', 'Pacardo')
    add_schedule('Labrador', sem_id, 'Tuesday', '10:00', '11:00', 'CSC/ISC/ACT 201', 'CS/IS/ACT 1-A', 'Villamor')
    add_schedule('Labrador', sem_id, 'Tuesday', '11:00', '12:00', 'CSC/ISC/ACT 205', 'CS/IS/ACT 2-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Tuesday', '12:00', '13:00', 'CSC 303', 'CS 3-A', 'Villamor')
    add_schedule('Labrador', sem_id, 'Tuesday', '13:00', '14:00', 'CSC 313', 'CS 3-A', 'Pacardo')
    add_schedule('Labrador', sem_id, 'Tuesday', '14:00', '15:00', 'CSC/ISC/ACT 206', 'CS/IS/ACT 2-A', 'Pacardo')
    add_schedule('Labrador', sem_id, 'Tuesday', '15:00', '16:00', 'ISC 107', 'IS 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Tuesday', '16:00', '17:00', 'ACT 208', 'ACT 2-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Tuesday', '17:00', '18:00', 'CSC 401', 'CS 4-A', 'Pacardo')

    # WEDNESDAY
    add_schedule('Labrador', sem_id, 'Wednesday', '09:00', '10:00', 'CSC/ISC/ACT 102', 'CS/IS/ACT 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Wednesday', '10:00', '11:00', 'CSC/ISC/ACT 103', 'CS/IS/ACT 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Wednesday', '11:00', '12:00', 'CSC/ISC/ACT 203', 'CS/IS/ACT 2-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Wednesday', '12:00', '13:00', 'CSC 202/ACT 204', 'CS/ACT 2-A', 'Pacardo')
    add_schedule('Labrador', sem_id, 'Wednesday', '13:00', '14:00', 'ISC 106', 'IS 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Wednesday', '14:00', '15:00', 'CSC/ISC/ACT 106', 'CS/IS/ACT 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Wednesday', '15:00', '16:00', 'CSC/ACT 107', 'CS/ACT 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Wednesday', '16:00', '17:00', 'ISC 209', 'IS 2-A', 'Villamor')
    add_schedule('Labrador', sem_id, 'Wednesday', '17:00', '18:00', 'ISC 309', 'IS 3-A', 'Kintao')

    # THURSDAY
    add_schedule('Labrador', sem_id, 'Thursday', '09:00', '10:00', 'CSC/ISC/ACT 102', 'CS/IS/ACT 1-A', 'Villamor')
    add_schedule('Labrador', sem_id, 'Thursday', '10:00', '11:00', 'CSC/ISC/ACT 201', 'CS/IS/ACT 1-A', 'Villamor')
    add_schedule('Labrador', sem_id, 'Thursday', '11:00', '12:00', 'CSC/ISC/ACT 205', 'CS/IS/ACT 2-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Thursday', '12:00', '13:00', 'ICT 11', 'SHS 11-ICT', 'Pacardo')
    add_schedule('Labrador', sem_id, 'Thursday', '13:00', '14:00', 'CSC 302', 'CS 3-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Thursday', '14:00', '15:00', 'ISC/ACT 202', 'IS/ACT 2-A', 'Simora')
    add_schedule('Labrador', sem_id, 'Thursday', '15:00', '16:00', 'CSC/ACT 107', 'CS/ACT 1-A', 'Kintao')
    add_schedule('Labrador', sem_id, 'Thursday', '16:00', '17:00', 'CSC 403', 'CS 4-A', 'Villamor')
    add_schedule('Labrador', sem_id, 'Thursday', '17:00', '18:00', 'CSC 402', 'CS 4-A', 'Pacardo')

    # ─────────────────────────────────────────
    # QUEBEC
    # ─────────────────────────────────────────

    # MONDAY
    add_schedule('Quebec', sem_id, 'Monday', '10:00', '11:00', 'GE 201', 'CS/IS/ACT 2-A', 'Gener')
    add_schedule('Quebec', sem_id, 'Monday', '11:00', '12:00', 'MATH 11', 'SHS 11', 'Gener')
    add_schedule('Quebec', sem_id, 'Monday', '12:00', '13:00', 'ISC 402', 'IS 4-A', 'Villamor')
    add_schedule('Quebec', sem_id, 'Monday', '13:00', '14:00', 'ISC 204', 'IS 2-A', 'Pacardo')
    add_schedule('Quebec', sem_id, 'Monday', '14:00', '15:00', 'HUMSS/GAS 11', 'SHS 11-HUMSS/GAS', 'Gener')
    add_schedule('Quebec', sem_id, 'Monday', '15:00', '16:00', 'ISC 301', 'IS 3-A', 'Ladrido')
    add_schedule('Quebec', sem_id, 'Monday', '16:00', '17:00', 'ISC 301', 'IS 3-A', 'Ladrido')

    # TUESDAY
    add_schedule('Quebec', sem_id, 'Tuesday', '09:00', '10:00', 'GE 202', 'CS/IS/ACT 2-A', 'Gener')
    add_schedule('Quebec', sem_id, 'Tuesday', '10:00', '11:00', 'ENG 11', 'SHS 11', 'Ladrido')
    add_schedule('Quebec', sem_id, 'Tuesday', '11:00', '12:00', 'FIL 11', 'SHS 11', 'Gener')
    add_schedule('Quebec', sem_id, 'Tuesday', '12:00', '13:00', 'ISC 402', 'IS 4-A', 'Villamor')
    add_schedule('Quebec', sem_id, 'Tuesday', '13:00', '14:00', 'SOC 204', 'IS 2-A', 'Pacardo')
    add_schedule('Quebec', sem_id, 'Tuesday', '14:00', '15:00', 'HUMSS/GAS 11', 'SHS 11-HUMSS/GAS', 'Gener')

    # WEDNESDAY
    add_schedule('Quebec', sem_id, 'Wednesday', '10:00', '11:00', 'GE 201', 'CS/IS/ACT 2-A', 'Gener')
    add_schedule('Quebec', sem_id, 'Wednesday', '11:00', '12:00', 'MATH 11', 'SHS 11', 'Gener')
    add_schedule('Quebec', sem_id, 'Wednesday', '12:00', '13:00', 'ISC 402', 'IS 4-A', 'Villamor')
    add_schedule('Quebec', sem_id, 'Wednesday', '13:00', '14:00', 'ISC 204', 'IS 2-A', 'Pacardo')
    add_schedule('Quebec', sem_id, 'Wednesday', '14:00', '15:00', 'ENG 11A', 'SHS 11', 'Ladrido')

    # THURSDAY
    add_schedule('Quebec', sem_id, 'Thursday', '09:00', '10:00', 'GE 202', 'CS/IS/ACT 2-A', 'Gener')
    add_schedule('Quebec', sem_id, 'Thursday', '10:00', '11:00', 'ENG 11', 'SHS 11', 'Ladrido')
    add_schedule('Quebec', sem_id, 'Thursday', '11:00', '12:00', 'FIL 11', 'SHS 11', 'Gener')
    add_schedule('Quebec', sem_id, 'Thursday', '12:00', '13:00', 'CSC/ISC/ACT 101', 'CS/IS/ACT 1-A', 'Villamor')
    add_schedule('Quebec', sem_id, 'Thursday', '13:00', '14:00', 'SOC 204', 'IS 2-A', 'Pacardo')
    add_schedule('Quebec', sem_id, 'Thursday', '14:00', '15:00', 'CSC 406', 'CS 4-A', 'Kintao')
    add_schedule('Quebec', sem_id, 'Thursday', '15:00', '16:30', 'ISC 301', 'IS 3-A', 'Ladrido')

    # ─────────────────────────────────────────
    # REGINA
    # ─────────────────────────────────────────

    # MONDAY
    add_schedule('Regina', sem_id, 'Monday', '09:00', '10:00', 'SHS 11', 'SHS 11', 'Simora')
    add_schedule('Regina', sem_id, 'Monday', '10:00', '11:00', 'GE 102', 'CS/IS/ACT 1-A', 'Simora')
    add_schedule('Regina', sem_id, 'Monday', '11:00', '12:00', 'CSC/ISC/ACT 103', 'CS/IS/ACT 1-A', 'Ladrido')
    add_schedule('Regina', sem_id, 'Monday', '12:00', '13:00', 'GE 104', 'SHS 11-12', 'Ladrido')
    add_schedule('Regina', sem_id, 'Monday', '13:00', '14:00', 'GE 301', 'CS/IS 3-A', 'Ladrido')
    add_schedule('Regina', sem_id, 'Monday', '14:00', '15:00', 'ISC 401', 'IS 4-A', 'Villamor')
    add_schedule('Regina', sem_id, 'Monday', '15:00', '16:00', 'ISC 401', 'IS 4-A', 'Villamor')
    add_schedule('Regina', sem_id, 'Monday', '16:00', '17:30', 'CSC 306/ISC 307', 'CS/IS 3-A', 'Villamor')

    # TUESDAY
    add_schedule('Regina', sem_id, 'Tuesday', '09:00', '10:00', 'GE 101', 'CS/IS/ACT 1-A', 'Gener')
    add_schedule('Regina', sem_id, 'Tuesday', '10:00', '11:00', 'GE 103', 'CS/IS/ACT 1-A', 'Gener')
    add_schedule('Regina', sem_id, 'Tuesday', '11:00', '12:00', 'CSC/ISC/ACT 103', 'CS/IS/ACT 1-A', 'Ladrido')
    add_schedule('Regina', sem_id, 'Tuesday', '12:00', '13:00', 'CSC/ISC/ACT 102', 'CS/IS/ACT 1-A', 'Kintao')
    add_schedule('Regina', sem_id, 'Tuesday', '13:00', '14:00', 'GE 301', 'IS 3-A', 'Ladrido')
    add_schedule('Regina', sem_id, 'Tuesday', '14:00', '15:00', 'ISC 303', 'IS 3-A', 'Villamor')
    add_schedule('Regina', sem_id, 'Tuesday', '15:00', '16:00', 'ISC 401', 'IS 4-A', 'Villamor')
    add_schedule('Regina', sem_id, 'Tuesday', '16:00', '17:00', 'ISC 306', 'IS 3-A', 'Pacardo')

    # WEDNESDAY
    add_schedule('Regina', sem_id, 'Wednesday', '09:00', '10:00', 'SCI 11', 'SHS 11', 'Simora')
    add_schedule('Regina', sem_id, 'Wednesday', '10:00', '11:00', 'GE 102', 'CS/IS/ACT 1-A', 'Simora')
    add_schedule('Regina', sem_id, 'Wednesday', '11:00', '12:00', 'CSC/ISC/ACT 103', 'CS/IS/ACT 1-A', 'Ladrido')
    add_schedule('Regina', sem_id, 'Wednesday', '12:00', '13:00', 'ISC 302', 'IS 3-A', 'Kintao')
    add_schedule('Regina', sem_id, 'Wednesday', '13:00', '14:00', 'ISC 305', 'IS 3-A', 'Kintao')
    add_schedule('Regina', sem_id, 'Wednesday', '14:00', '15:00', 'ISC 401', 'IS 4-A', 'Villamor')
    add_schedule('Regina', sem_id, 'Wednesday', '15:00', '16:00', 'ISC 401', 'IS 4-A', 'Villamor')
    add_schedule('Regina', sem_id, 'Wednesday', '16:00', '17:30', 'CSC 306/ISC 307', 'CS/IS 3-A', 'Villamor')

    # THURSDAY
    add_schedule('Regina', sem_id, 'Thursday', '09:00', '10:00', 'GE 101', 'CS/IS/ACT 1-A', 'Gener')
    add_schedule('Regina', sem_id, 'Thursday', '10:00', '11:00', 'GE 103', 'CS/IS/ACT 1-A', 'Gener')
    add_schedule('Regina', sem_id, 'Thursday', '11:00', '12:00', 'CSC/ISC/ACT 103', 'CS/IS/ACT 1-A', 'Ladrido')
    add_schedule('Regina', sem_id, 'Thursday', '12:00', '13:00', 'ISC 302', 'IS 3-A', 'Kintao')
    add_schedule('Regina', sem_id, 'Thursday', '13:00', '14:00', 'ISC 305', 'IS 3-A', 'Kintao')
    add_schedule('Regina', sem_id, 'Thursday', '14:00', '15:00', 'ISC 401', 'IS 4-A', 'Villamor')
    add_schedule('Regina', sem_id, 'Thursday', '15:00', '16:00', 'ISC 401', 'IS 4-A', 'Villamor')
    add_schedule('Regina', sem_id, 'Thursday', '16:00', '17:00', 'ISC 306', 'IS 3-A', 'Pacardo')

    # ─────────────────────────────────────────
    # VICTORIA
    # ─────────────────────────────────────────

    # MONDAY
    add_schedule('Victoria', sem_id, 'Monday', '09:00', '10:00', 'PHI ART 21', 'SHS 12', 'Gener')
    add_schedule('Victoria', sem_id, 'Monday', '10:00', '11:00', 'PHILO 21', 'SHS 12', 'Ladrido')
    add_schedule('Victoria', sem_id, 'Monday', '12:00', '13:00', 'HUMSS 21B', 'SHS 12-HUMSS', 'Gener')
    add_schedule('Victoria', sem_id, 'Monday', '13:00', '14:00', 'ISC 406', 'IS 4-A', 'Villamor')
    add_schedule('Victoria', sem_id, 'Monday', '14:00', '15:00', 'ABM 11/GAS 21B', 'SHS 11-ABM', 'Ladrido')

    # TUESDAY
    add_schedule('Victoria', sem_id, 'Tuesday', '09:00', '10:00', 'PHYSCI 21', 'SHS 12', 'Ladrido')
    add_schedule('Victoria', sem_id, 'Tuesday', '11:00', '12:00', 'PEH 21', 'SHS 12', 'Simora')
    add_schedule('Victoria', sem_id, 'Tuesday', '12:00', '13:00', 'HUMSS 21B', 'SHS 12-HUMSS', 'Gener')
    add_schedule('Victoria', sem_id, 'Tuesday', '14:00', '15:00', 'CSC 204', 'CS 2-A', 'Pacardo')

    # WEDNESDAY
    add_schedule('Victoria', sem_id, 'Wednesday', '09:00', '10:00', 'PHI ART 21', 'SHS 12', 'Gener')
    add_schedule('Victoria', sem_id, 'Wednesday', '10:00', '11:00', 'PHILO 21', 'SHS 12', 'Ladrido')
    add_schedule('Victoria', sem_id, 'Wednesday', '12:00', '13:00', 'GAS 21A', 'SHS 12-GAS', 'Ladrido')
    add_schedule('Victoria', sem_id, 'Wednesday', '13:00', '14:00', 'CSC/ISC/ACT 103', 'CS/IS/ACT 1-A', 'Kintao')
    add_schedule('Victoria', sem_id, 'Wednesday', '14:00', '15:00', 'PE 203', 'CS/IS/ACT 2-A', 'Simora')
    add_schedule('Victoria', sem_id, 'Wednesday', '15:00', '16:00', 'FIL 21', 'SHS 12', 'Gener')
    add_schedule('Victoria', sem_id, 'Wednesday', '16:00', '17:00', 'PR 21', 'SHS 12', 'Ladrido')

    # THURSDAY
    add_schedule('Victoria', sem_id, 'Thursday', '09:00', '10:00', 'PHYSCI 21', 'SHS 12', 'Ladrido')
    add_schedule('Victoria', sem_id, 'Thursday', '10:00', '11:00', 'ABM 21A', 'SHS 12-ABM', 'Villamor')
    add_schedule('Victoria', sem_id, 'Thursday', '12:00', '13:00', 'GAS 21A', 'SHS 12-GAS', 'Ladrido')
    add_schedule('Victoria', sem_id, 'Thursday', '14:00', '15:00', 'CSC 204', 'CS 2-A', 'Pacardo')
    add_schedule('Victoria', sem_id, 'Thursday', '15:00', '16:00', 'FIL 21', 'SHS 12', 'Gener')
    add_schedule('Victoria', sem_id, 'Thursday', '16:00', '17:00', 'PR 21', 'SHS 12', 'Ladrido')

    # ─────────────────────────────────────────
    # WINNIPEG
    # ─────────────────────────────────────────

    # MONDAY
    add_schedule('Winnipeg', sem_id, 'Monday', '13:00', '14:00', 'NSTP 1', 'CS/IS/ACT 1-A', 'Simora')
    add_schedule('Winnipeg', sem_id, 'Monday', '14:00', '15:00', 'PE 101', 'CS/IS/ACT 1-A', 'Simora')

    # TUESDAY
    add_schedule('Winnipeg', sem_id, 'Tuesday', '14:00', '15:00', 'ABM 11/GAS 21B', 'SHS 11-ABM', 'Ladrido')

    # WEDNESDAY
    add_schedule('Winnipeg', sem_id, 'Wednesday', '13:00', '14:00', 'PE 11', 'SHS 11', 'Simora')
    add_schedule('Winnipeg', sem_id, 'Wednesday', '14:00', '15:00', 'ABM 21A', 'SHS 11-ABM', 'Ladrido')
    add_schedule('Winnipeg', sem_id, 'Wednesday', '15:00', '16:00', 'HUMSS 21B', 'SHS 12-HUMSS', 'Ladrido')

    # THURSDAY
    add_schedule('Winnipeg', sem_id, 'Thursday', '14:00', '15:00', 'ENG 11A', 'SHS 11', 'Ladrido')
    add_schedule('Winnipeg', sem_id, 'Thursday', '15:00', '16:00', 'HUMSS 21B', 'SHS 12-HUMSS', 'Ladrido')

    db.session.commit()
    print('\n✅ All schedules seeded successfully!')
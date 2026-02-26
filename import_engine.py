import pandas as pd
from models import StaffMaster
from utils import calculate_age, calculate_retirement

def import_staff(file_path, db):
    df = pd.read_excel(file_path)

    for _, row in df.iterrows():
        pf = str(row.get("PF No")).strip()
        if not pf:
            continue

        staff = db.get(StaffMaster, pf)
        if not staff:
            staff = StaffMaster(pf_no=pf)

        staff.staff_name = row.get("Name")
        staff.designation = row.get("Designation")
        staff.category = row.get("Category")
        staff.bill_unit_no = row.get("Bill Unit No")
        staff.hrms_id = row.get("HRMS ID")
        staff.mobile_no = row.get("Mobile No")
        staff.email = row.get("Email")
        staff.community = row.get("Community")
        staff.dob = row.get("Date of Birth")
        staff.date_of_appointment = row.get("Date of Appointment")
        staff.age = calculate_age(staff.dob)
        staff.date_of_retirement = calculate_retirement(staff.date_of_appointment)
        staff.qualification = row.get("Qualification")
        staff.mode_of_appointment = row.get("Mode of Appointment")
        staff.nominated_cli_name = row.get("Nominated CLI Name")

        db.merge(staff)

    db.commit()

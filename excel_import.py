# excel_import.py

import pandas as pd
from database import SessionLocal
from models import Staff
from datetime import datetime, date


# ------------------- DATE PARSER -------------------

def clean_date(value):
    """
    Convert Excel cell to Python date object.
    Returns None if empty or invalid.
    """
    if pd.isna(value) or str(value).strip() == "":
        return None

    if isinstance(value, pd.Timestamp):
        return value.date()

    try:
        dt = pd.to_datetime(value, dayfirst=True, errors="coerce")
        return dt.date() if pd.notna(dt) else None
    except:
        return None


# ------------------- AGE CALCULATOR -------------------

def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )


# ------------------- IMPORT FUNCTION -------------------

def import_staff_excel(file_path: str):

    df = pd.read_excel(file_path)

    # Normalize column names
    df.columns = [str(c).strip().upper() for c in df.columns]

    REQUIRED_COLUMNS = {
        "PF NO",
        "EMPLOYEE NAME",
        "DESIGNATION",
        "DATE OF JOINING",
        "DATE OF BIRTH",
        "DATE OF RETIREMENT",
        "CLI NAME",
        "MOBILE",
        "EMAIL",
    }

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    db = SessionLocal()

    inserted = 0
    skipped = 0
    skipped_details = []

    for idx, row in df.iterrows():
        try:
            pf_no = row.get("PF NO")

            if pd.isna(pf_no) or str(pf_no).strip() == "":
                skipped += 1
                skipped_details.append((idx + 2, "Missing PF NO"))
                continue

            dob = clean_date(row.get("DATE OF BIRTH"))
            calculated_age = calculate_age(dob)

            staff = Staff(
                pf_no=str(pf_no).strip(),
                name=row.get("EMPLOYEE NAME"),
                designation=row.get("DESIGNATION"),

                date_of_joining=clean_date(row.get("DATE OF JOINING")),
                hrms_id=row.get("HRMS ID"),
                community=row.get("COMMUNITY"),
                dob=dob,
                dor=clean_date(row.get("DATE OF RETIREMENT")),
                qualification=row.get("QUALIFICATION"),
                mode_of_appointment=row.get("MODE OF APPOINTMENT"),

                mobile=row.get("MOBILE"),
                email=row.get("EMAIL"),
                cli_name=row.get("CLI NAME"),
                bill_unit=row.get("BILL UNIT"),

                age=str(calculated_age) if calculated_age else None,
                dot=row.get("DOT"),
                pan=row.get("PAN"),
                aadhar=row.get("AADHAR"),

                prom_trg=row.get("PROM.TRG."),
                pme_due=clean_date(row.get("PME DUE")),
                gr_sr_due=clean_date(row.get("GR/SR DUE")),
                tech_ref_due=clean_date(row.get("TECH.REF.DUE")),

                gradation=row.get("GRADATION (A/B/C)"),
                date_of_gradation=clean_date(row.get("DATE OF GRADATION")),
                high_speed_psycho_date=clean_date(
                    row.get("HIGH SPEED PSYCHO. DONE DATE")
                ),

                remarks=row.get("REMARKS"),
            )

            db.merge(staff)
            inserted += 1

        except Exception as e:
            skipped += 1
            skipped_details.append((idx + 2, str(e)))

    db.commit()
    db.close()

    return inserted, skipped, skipped_details

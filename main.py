import os
import shutil
from datetime import datetime, date, timedelta

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import joinedload

from database import SessionLocal, engine
from models import Base, Staff, Leave
from excel_import import import_staff_excel

import pandas as pd
from io import BytesIO

# ================= BASE SETUP =================

app = FastAPI(title="HRMS")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

Base.metadata.create_all(bind=engine)

# ================= HELPER FUNCTIONS =================

def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except:
        return None


def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )

# ================= LOGIN =================

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin":
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/", status_code=302)

# ================= DASHBOARD =================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ================= STAFF MASTER =================

@app.get("/staff", response_class=HTMLResponse)
def staff_master(request: Request):
    db = SessionLocal()
    try:
        staff = db.query(Staff).order_by(Staff.pf_no).all()
    finally:
        db.close()

    return templates.TemplateResponse(
        "staff_master.html",
        {"request": request, "staff": staff}
    )

# ================= ADD STAFF =================

@app.get("/staff/add", response_class=HTMLResponse)
def add_staff_page(request: Request):
    return templates.TemplateResponse("add_staff.html", {"request": request})


@app.post("/staff/add")
def add_staff(
    pf_no: str = Form(...),
    name: str = Form(None),
    designation: str = Form(None),
    dob: str = Form(None),
):
    db = SessionLocal()

    try:
        existing = db.query(Staff).filter(Staff.pf_no == pf_no).first()
        if existing:
            return HTMLResponse("<h3>PF No already exists</h3>")

        parsed_dob = parse_date(dob)
        calculated_age = calculate_age(parsed_dob)

        new_staff = Staff(
            pf_no=pf_no,
            name=name,
            designation=designation,
            dob=parsed_dob,
            age=str(calculated_age) if calculated_age else None,
        )

        db.add(new_staff)
        db.commit()

    finally:
        db.close()

    return RedirectResponse("/staff", status_code=302)

# ================= EDIT STAFF =================

@app.get("/staff/edit/{pf_no}", response_class=HTMLResponse)
def edit_staff(request: Request, pf_no: str):
    db = SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.pf_no == pf_no).first()
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
    finally:
        db.close()

    return templates.TemplateResponse(
        "edit_staff.html",
        {"request": request, "staff": staff}
    )


@app.post("/staff/edit/{pf_no}")
def update_staff(
    pf_no: str,
    name: str = Form(None),
    designation: str = Form(None),
    hrms_id: str = Form(None),
    community: str = Form(None),
    date_of_joining: str = Form(None),
    dob: str = Form(None),
    dor: str = Form(None),
    mobile: str = Form(None),
    email: str = Form(None),
    cli_name: str = Form(None),
    qualification: str = Form(None),
    mode_of_appointment: str = Form(None),
    bill_unit: str = Form(None),
    dot: str = Form(None),
    pan: str = Form(None),
    aadhar: str = Form(None),
    prom_trg: str = Form(None),
    pme_due: str = Form(None),
    gr_sr_due: str = Form(None),
    tech_ref_due: str = Form(None),
    gradation: str = Form(None),
    date_of_gradation: str = Form(None),
    high_speed_psycho_date: str = Form(None),
    remarks: str = Form(None),
):
    db = SessionLocal()

    try:
        staff = db.query(Staff).filter(Staff.pf_no == pf_no).first()
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

        # Parse date fields
        parsed_dob = parse_date(dob)
        parsed_doj = parse_date(date_of_joining)
        parsed_dor = parse_date(dor)
        parsed_pme = parse_date(pme_due)
        parsed_gr = parse_date(gr_sr_due)
        parsed_tech = parse_date(tech_ref_due)
        parsed_gradation = parse_date(date_of_gradation)

        # Update fields
        staff.name = name
        staff.designation = designation
        staff.hrms_id = hrms_id
        staff.community = community

        staff.date_of_joining = parsed_doj
        staff.dob = parsed_dob
        staff.dor = parsed_dor

        staff.mobile = mobile
        staff.email = email
        staff.cli_name = cli_name

        staff.qualification = qualification
        staff.mode_of_appointment = mode_of_appointment
        staff.bill_unit = bill_unit

        staff.dot = dot
        staff.pan = pan
        staff.aadhar = aadhar

        staff.prom_trg = prom_trg
        staff.pme_due = parsed_pme
        staff.gr_sr_due = parsed_gr
        staff.tech_ref_due = parsed_tech

        staff.gradation = gradation
        staff.date_of_gradation = parsed_gradation
        staff.high_speed_psycho_date = high_speed_psycho_date

        staff.remarks = remarks

        # Auto recalc age
        if parsed_dob:
            staff.age = str(calculate_age(parsed_dob))

        db.commit()

    finally:
        db.close()

    return RedirectResponse("/staff", status_code=302)

# =====================================================
# ================= LEAVE MANAGEMENT ==================
# =====================================================

@app.get("/staff/{pf_no}/leave", response_class=HTMLResponse)
def view_leave(request: Request, pf_no: str):
    db = SessionLocal()
    try:
        staff = (
            db.query(Staff)
            .options(joinedload(Staff.leaves))
            .filter(Staff.pf_no == pf_no)
            .first()
        )
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
    finally:
        db.close()

    return templates.TemplateResponse(
        "leave.html",
        {"request": request, "staff": staff}
    )


@app.post("/staff/{pf_no}/leave")
def add_leave(
    pf_no: str,
    leave_type: str = Form(...),
    from_date: str = Form(...),
    to_date: str = Form(...),
    remarks: str = Form(None),
):
    db = SessionLocal()

    try:
        from_dt = parse_date(from_date)
        to_dt = parse_date(to_date)

        if not from_dt or not to_dt:
            return HTMLResponse("<h3>Invalid Date Format</h3>")

        total_days = (to_dt - from_dt).days + 1

        leave = Leave(
            pf_no=pf_no,
            leave_type=leave_type,
            from_date=from_dt,
            to_date=to_dt,
            days=total_days,
            remarks=remarks,
        )

        db.add(leave)
        db.commit()

    finally:
        db.close()

    return RedirectResponse(f"/staff/{pf_no}/leave", status_code=302)

# =====================================================
# ================= REPORTS SECTION ===================
# =====================================================

# =====================================================
# ================= REPORTS SECTION ===================
# =====================================================

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request):
    db = SessionLocal()
    try:
        # Get distinct designations and bill units
        designations = db.query(Staff.designation).distinct().all()
        bill_units = db.query(Staff.bill_unit).distinct().all()

        designations = sorted([d[0] for d in designations if d[0]])
        bill_units = sorted([b[0] for b in bill_units if b[0]])

    finally:
        db.close()

    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "designations": designations,
            "bill_units": bill_units
        }
    )


@app.post("/reports", response_class=HTMLResponse)
def generate_report(
    request: Request,
    report_type: str = Form(...),
    designation: str = Form(None),
    bill_unit: str = Form(None),
    period_type: str = Form(...),
    year: int = Form(...),
    month: int = Form(None),
    quarter: int = Form(None),
):
    db = SessionLocal()

    try:
        query = db.query(Staff)

        # 🎯 STEP 3 — FILTER LOGIC FOR ALL OPTION
        # If designation is empty string (ALL), no filter applied
        if designation and designation != "ALL":
            query = query.filter(Staff.designation == designation)

        if bill_unit and bill_unit != "ALL":
            query = query.filter(Staff.bill_unit == bill_unit)

        # ---- DATE RANGE ----
        if period_type == "monthly" and month:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year, 12, 31)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

        elif period_type == "quarterly" and quarter:
            quarter_map = {1: (1,3), 2: (4,6), 3: (7,9), 4: (10,12)}
            start_m, end_m = quarter_map.get(quarter, (1,3))
            start_date = date(year, start_m, 1)
            end_date = date(year, end_m + 1, 1) - timedelta(days=1)

        elif period_type == "yearly":
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        else:
            return HTMLResponse("<h3>Invalid Period</h3>")

        # ---- REPORT TYPE FILTER ----
        if report_type == "pme":
            results = query.filter(Staff.pme_due.between(start_date, end_date)).all()

        elif report_type == "gr":
            results = query.filter(Staff.gr_sr_due.between(start_date, end_date)).all()

        elif report_type == "tech":
            results = query.filter(Staff.tech_ref_due.between(start_date, end_date)).all()

        elif report_type == "gradation":
            results = query.filter(Staff.date_of_gradation.between(start_date, end_date)).all()

        else:
            results = []

    finally:
        db.close()

    return templates.TemplateResponse(
        "report_result.html",
        {
            "request": request,
            "results": results,
            "start_date": start_date,
            "end_date": end_date,
            "report_type": report_type
        }
    )
# ================= EXPORT STAFF =================

@app.get("/staff/export")
def export_staff():
    db = SessionLocal()
    try:
        staff = db.query(Staff).all()
    finally:
        db.close()

    data = []

    for s in staff:
        data.append({
            "PF NO": s.pf_no,
            "EMPLOYEE NAME": s.name,
            "DESIGNATION": s.designation,

            "DATE OF JOINING": s.date_of_joining,
            "HRMS ID": s.hrms_id,
            "COMMUNITY": s.community,

            "DATE OF BIRTH": s.dob,
            "DATE OF RETIREMENT": s.dor,

            "QUALIFICATION": s.qualification,
            "MODE OF APPOINTMENT": s.mode_of_appointment,

            "MOBILE": s.mobile,
            "EMAIL": s.email,
            "CLI NAME": s.cli_name,
            "BILL UNIT": s.bill_unit,

            "AGE": s.age,
            "DOT": s.dot,
            "PAN": s.pan,
            "AADHAR": s.aadhar,

            "PROM.TRG.": s.prom_trg,
            "PME DUE": s.pme_due,
            "GR/SR DUE": s.gr_sr_due,
            "TECH.REF.DUE": s.tech_ref_due,

            "GRADATION (A/B/C)": s.gradation,
            "DATE OF GRADATION": s.date_of_gradation,
            "HIGH SPEED PSYCHO. DONE DATE": s.high_speed_psycho_date,

            "REMARKS": s.remarks,
        })

    df = pd.DataFrame(data)

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=staff_export.xlsx"
        },
    )
# ================= UPLOAD =================

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        inserted, skipped, skipped_details = import_staff_excel(file_path)
    except Exception as e:
        return HTMLResponse(
            f"<h3 style='color:red'>Upload Failed</h3><pre>{e}</pre>",
            status_code=500
        )

    return templates.TemplateResponse(
        "upload_result.html",
        {
            "request": request,
            "inserted": inserted,
            "skipped": skipped,
            "skipped_details": skipped_details
        }
    )
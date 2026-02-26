from sqlalchemy import Column, String, Date, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Staff(Base):
    __tablename__ = "staff"

    pf_no = Column(String, primary_key=True, index=True)

    name = Column(String)
    designation = Column(String)

    date_of_joining = Column(Date)
    hrms_id = Column(String)
    community = Column(String)

    dob = Column(Date)
    dor = Column(Date)

    qualification = Column(String)
    mode_of_appointment = Column(String)

    mobile = Column(String)
    email = Column(String)
    cli_name = Column(String)

    bill_unit = Column(String)
    age = Column(String)
    dot = Column(String)

    pan = Column(String)
    aadhar = Column(String)

    prom_trg = Column(String)
    pme_due = Column(Date)
    gr_sr_due = Column(Date)
    tech_ref_due = Column(Date)

    gradation = Column(String)
    date_of_gradation = Column(Date)
    high_speed_psycho_date = Column(String)

    remarks = Column(String)
    extra_data = Column(JSON)

    # 🔹 Relationship to Leave table
    leaves = relationship(
        "Leave",
        back_populates="staff",
        cascade="all, delete"
    )


# =====================================================
# ================= LEAVE TABLE =======================
# =====================================================

class Leave(Base):
    __tablename__ = "leave_records"

    id = Column(Integer, primary_key=True, index=True)

    pf_no = Column(String, ForeignKey("staff.pf_no"))

    leave_type = Column(String)
    from_date = Column(Date)
    to_date = Column(Date)
    days = Column(Integer)
    remarks = Column(String)

    staff = relationship(
        "Staff",
        back_populates="leaves"
    )

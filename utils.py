from datetime import date
from dateutil.relativedelta import relativedelta

def calculate_age(dob):
    if not dob:
        return None
    return relativedelta(date.today(), dob).years

def calculate_retirement(doa):
    if not doa:
        return None
    return doa + relativedelta(years=60)

import csv
import hashlib
import sys
import os


FIELDNAMES_OUT = ["app_id", "decision", "reason", "score", "dti", "amount_approved", "term_approved"]
FIELDNAMES_AUDIT = ["app_id", "validation_errors", "bki_score", "delinquency", "smev_status", "score_total", "dti", "decision", "reason"]


def get_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except ValueError:
        return default


def get_int(val, default=0):
    try:
        if val is None or str(val).strip() == "":
            return default
        return int(val)
    except ValueError:
        return default


def bki_emulator(passport_hash):
    passport_hash = str(passport_hash).strip()
    if not passport_hash:
        return (400, True)
    h = int(hashlib.md5(passport_hash.encode()).hexdigest(), 16) % 10
    if h <= 5: return (600 + h * 20, False)
    elif 6 <= h <= 8: return (450 + h * 10, False)
    else: return (400, True)


def smev_emulator(client_id):
    client_id = str(client_id).strip()
    if not client_id:
        return "MISMATCH"
    h = int(hashlib.md5(client_id.encode()).hexdigest(), 16) % 10
    return "MISMATCH" if h == 0 else "MATCH"


def validate(app):
    errors = []
    if app.get("age"):
        if not (18 <= int(app["age"]) <= 70):
            errors.append(("age", "AGE_OUT_OF_RANGE"))
    if app.get('income'):
        if float(app["income"]) <= 0:
            errors.append(('income', 'MISSING_INCOME'))
    else:
        errors.append(('income', 'MISSING_INCOME'))
    if app.get('employment'):
        if app["employment"] not in ['employed', 'self-employed', 'retired', 'student', 'unemployed']:
            errors.append(('employment', 'INVALID_EMPLOYMENT'))
    if app.get('family'):
        if app['family'] not in ['single', 'married', 'children']:
            errors.append(('family', 'INVALID_FAMILY'))
    if app.get('amount'):
        if float(app['amount']) <= 0:
            errors.append(('amount', 'MISSING_AMOUNT'))
    if app.get('term'):
        if int(app['term']) <= 0:
            errors.append(('term', 'INVALID_TERM'))
    return errors


def score(app, bki_score, delinquency):
    income = float(app.get("income", 0))
    s_income = 30 if income >= 150000 else 20 if income >= 80000 else 10 if income >= 40000 else 0
    s_emp = {"employed": 25, "self-employed": 20, "retired": 10, "student": 5, "unemployed": 0}.get(app.get("employment"), 0)
    age = int(app.get('age', 0))
    s_age = 20 if 25 <= age <= 50 else 5 if 61 <= age <= 70 else 10
    family = app.get('family', '')
    s_family = 10 if family in ['single', 'married'] else 5
    s_bki = 20 if bki_score >= 700 else 15 if bki_score >= 600 else 10 if bki_score >= 500 else 0
    if delinquency:
        s_bki = 0
    total = s_income + s_emp + s_age + s_family + s_bki
    return total, {"income": s_income, "employment": s_emp, "age": s_age, "family": s_family, "bki": s_bki}


def compute_dti(amount, term, income):
    if not income or income <= 0:
        return None
    mr = 0.18 / 12
    payment = amount * mr / (1 - (1 + mr) ** (-term))
    return round(payment / income, 2)


def decide(app, score_total, dti, bki_score, delinquency, smev_status):
    if not (18 <= int(app.get('age', 0)) <= 70):
        return 'REFUSED', 'AGE_OUT_OF_RANGE'
    if app.get('employment') == 'unemployed':
        return 'REFUSED', 'INVALID_EMPLOYMENT'
    income = float(app.get('income', 0))
    if income <= 0:
        return 'REFUSED', 'MISSING_INCOME'
    if income < 30000:
        return 'REFUSED', 'LOW_INCOME'
    if dti is not None and dti > 0.5:
        return "REFUSED", "HIGH_DTI"
    if bki_score < 500 or delinquency:
        return 'REFUSED', 'BKI_DELINQUENCY'
    if int(app.get('amount', 0)) > income * 10:
        return 'REFUSED', 'AMOUNT_LIMIT'
    if score_total < 60:
        return "REFUSED", "LOW_SCORE"
    if smev_status == "MISMATCH":
        return "REFUSED", "SMEV_MISMATCH"
    return "APPROVED", ""


def process(app):
    app_id = app.get("app_id", "UNKNOWN")
    audit_record = {
        "app_id": app_id, "validation_errors": "", "bki_score": "",
        "delinquency": "", "smev_status": "", "score_total": "",
        "dti": "", "decision": "", "reason": ""
    }
    
    errors = validate(app)
    if errors:
        reason = errors[0][1]
        audit_record.update({"validation_errors": str(errors), "decision": "NEED_MORE_DATA", "reason": reason})
        return {"app_id": app_id, "decision": "NEED_MORE_DATA", "reason": reason, 
                "score": "", "dti": "", "amount_approved": "", "term_approved": ""}, audit_record
    
    bki_score_str = str(app.get("bki_score", "")).strip()
    if bki_score_str:
        bki_score = get_float(bki_score_str, 0.0)
        delinquency = bki_score < 500 
    else:
        bki_score, delinquency = bki_emulator(app.get("passport_hash", ""))
        
    smev_status_str = str(app.get("smev_status", "")).strip()
    if smev_status_str:
        smev = smev_status_str
    else:
        smev = smev_emulator(app.get("client_id", ""))
        
    dti_str = str(app.get("dti", "")).strip()
    if dti_str:
        dti = get_float(dti_str, None)
    else:
        amount = get_float(app.get("amount", ""), 0.0)
        term = get_int(app.get("term", ""), 0)
        income = get_float(app.get("income", ""), 0.0)
        dti = compute_dti(amount, term, income)

    score_total, _ = score(app, bki_score, delinquency)
    decision, reason = decide(app, score_total, dti, bki_score, delinquency, smev)
    
    approved_amount = app.get("amount") if decision == "APPROVED" else ""
    approved_term = app.get("term") if decision == "APPROVED" else ""
    
    result = {
        "app_id": app_id, "decision": decision, "reason": reason,
        "score": score_total, "dti": dti if dti is not None else "",
        "amount_approved": approved_amount, "term_approved": approved_term
    }
    audit_record.update({
        "bki_score": bki_score, "delinquency": delinquency, "smev_status": smev,
        "score_total": score_total, "dti": dti if dti is not None else "",
        "decision": decision, "reason": reason
    })
    return result, audit_record


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(script_dir, "application.csv")
    out_filename = "decisions.csv"
    audit_filename = "audit.csv"
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        src = os.path.abspath(sys.argv[1])
    if "--out" in sys.argv:
        out_filename = sys.argv[sys.argv.index("--out") + 1]
        
    src_dir = os.path.dirname(src)
    out = os.path.join(src_dir, os.path.basename(out_filename))
    audit = os.path.join(src_dir, audit_filename)
    
    try:
        with open(src, encoding="utf-8") as f:
            apps = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"Ошибка: Файл {src} не найден.")
        sys.exit(1)
        
    results = []
    audits = []
    for a in apps:
        res, aud = process(a)
        results.append(res)
        audits.append(aud)
        
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES_OUT)
        w.writeheader()
        w.writerows(results)
        
    if audits:
        with open(audit, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES_AUDIT)
            w.writeheader()
            w.writerows(audits)
            
    stats = {}
    for r in results:
        stats[r["decision"]] = stats.get(r["decision"], 0) + 1
        
    print(f"OK: Успешно обработано {len(results)} заявок.")
    print(f"    Файлы сохранены в папку: {src_dir}")
    print(f"    решения: {stats}")

if __name__ == "__main__":
    main()
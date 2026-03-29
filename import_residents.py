"""Import residents from the 2025-Dec Member Directory into the database."""
from app import app
from models import db, Unit, Resident
from residents_data import RESIDENTS


def make_email(name):
    """Convert 'First Last' → 'FirstLast@bellcoho.com', removing special chars."""
    # Remove apostrophes and spaces, preserve capitalisation
    parts = name.replace("'", "").split()
    return "".join(parts) + "@bellcoho.com"


with app.app_context():
    # Build unit number → id lookup
    units = {u.number: u.id for u in Unit.query.all()}

    added = 0
    skipped = 0
    for unit_num, name, phone in RESIDENTS:
        email = make_email(name)
        # Skip if already exists
        if Resident.query.filter_by(email=email).first():
            print(f"  SKIP (exists): {name}")
            skipped += 1
            continue
        unit_id = units.get(unit_num)
        if not unit_id:
            print(f"  WARN: unit {unit_num} not found for {name}")
        r = Resident(
            name=name,
            email=email,
            phone=phone,
            unit_id=unit_id,
        )
        db.session.add(r)
        added += 1
        print(f"  ADD: {name:25s}  unit={unit_num:2d}  {email}")

    db.session.commit()
    print(f"\nDone. Added {added}, skipped {skipped}.")

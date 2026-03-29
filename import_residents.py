"""Import residents from the 2025-Dec Member Directory into the database."""
from app import app
from models import db, Unit, Resident

RESIDENTS = [
    # (unit_number, name, phone)
    (1,  "Judy Perry",         "360.920.0295"),
    (1,  "Kerry Johnson",      "360.595.7570"),
    (2,  "Mary Swenson",       "360.961.1822"),
    (3,  "Katie Kauffman",     "206.718.4747"),
    (3,  "Jason Sears",        "360.223.3874"),
    (4,  "Christopher O'Dell", "360.393.0381"),
    (5,  "Matt Martin",        "360.927.2637"),
    (5,  "Kelsie Mullin",      "360.441.1319"),
    (6,  "Nancy Simmers",      "360.671.5685"),
    (7,  "Bob Dailey",         "512.925.0228"),
    (8,  "Mark Harfenist",     "360.223.0132"),
    (9,  "Dan Taylor",         "360.223.2087"),
    (9,  "Michelle Ballou",    "360.739.5757"),
    (10, "Becky Hale",         "360.393.9940"),
    (11, "Jane Madden",        "360.734.2677"),
    (11, "Edwin Simmers",      "360.927.0863"),
    (12, "Carol Makela",       "360.550.2219"),
    (13, "Kathy Chen",         "360.920.6879"),
    (14, "Karen Sheldon",      "206.235.3489"),
    (14, "Steve Hansen",       "206.235.3486"),
    (15, "Jade Flores",        "859.948.8025"),
    (15, "Tim Flores",         "307.267.8313"),
    (16, "Gail Kirgis",        "360.521.0833"),
    (16, "Tom Cornwall",       "208.340.1326"),
    (17, "Gary Bachman",       "360.941.5283"),
    (17, "Kelly Bachman",      "360.202.3761"),
    (17, "Lorin Bachman",      None),
    (18, "Dan Bothman",        "360.739.3744"),
    (18, "Adrian Emerson",     "206.954.0379"),
    (19, "Carol Butz",         "360.650.0077"),
    (20, "Kristin Haider",     "320.492.9424"),
    (20, "Varun Ramesh",       "608.320.7152"),
    (21, "Anne George",        "360.527.1741"),
    (22, "Darrell Sofield",    "360.224.7606"),
    (23, "Catherine Sheldon",  "206.226.3956"),
    (24, "Shirley Cooper",     "360.594.8744"),
    (25, "Lesley Rigg",        "360.223.6762"),
    (26, "Laurie Rotecki",     "360.713.7989"),
    (27, "Ellen Howard",       "206.524.4996"),
    (28, "Mary Jo Weslow",     "360.441.5618"),
    (29, "Dale Withers",       "971.338.3185"),
    (29, "Marilyn Withers",    "971.338.3426"),
    (30, "Linda Hilden",       "360.920.1383"),
    (30, "Julie McPheters",    "360.441.7169"),
    (31, "Dwight Moore",       "360.223.4958"),
    (31, "Marie MacWhyte",     "360.306.1532"),
    (32, "Lisa Beard",         "650.353.0335"),
    (32, "Scott Havill",       "650.575.2904"),
    (33, "Jaco ten Hove",      "206.200.5403"),
    (33, "Barbara ten Hove",   "206.451.0312"),
]


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

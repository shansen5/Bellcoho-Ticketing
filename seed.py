"""Seed script – populates Buildings (1-12), Units (1-33), categories, and a default admin user."""
from models import Building, Unit, BoardUser, Category, BudgetCategory


# Unit-to-building mapping for a 33-unit, 12-building community.
# Adjust these assignments to match your actual layout.
UNIT_BUILDING_MAP = {
    # Building: [unit numbers]
    1:  [1, 2, 3],
    2:  [4, 5, 6, 7, 8],
    3:  [9, 10, 11],
    4:  [12, 13, 14],
    5:  [15, 16],
    6:  [17, 18, 19],
    7:  [20, 21],
    8:  [22, 23, 24, 25],
    9:  [26, 27, 28, 29, 30],
    10: [31, 32, 33],
}

BUILDING_NAMES = {
    1: "2604 - 2608",
    2: "2620 - 2628",
    3: "2632 - 2636",
    4: "2640 - 2644",
    5: "2648 - 2650",
    6: "2654 - 2658",
    7: "2662 - 2664",
    8: "2670 - 2676",
    9: "2680 - 2688",
    10: "2692 - 2696",
    11: "Common House",
    12: "Workshop",
}


DEFAULT_BUDGET_CATEGORIES = [
    "Building Work Party",
    "Buildings Unpredictable",
    "Dryer vents",
    "Materials for painting, etc.",
    "Repairs to heat, water systems",
    "Smoke alarm check/batteries",
    "Sprinklers, fire extin., backflow",
    "Sump Pump Inspection/Repair",
    "Upper A Stair Treads",
    "Upper gutter cleaning",
    "Utility repairs",
    "Workshop expenses",
    "Grounds Unpredictable",
    "Lighting and electricity",
    "Pest control",
    "Pressure Washer",
    "Security",
]


DEFAULT_CATEGORIES = [
    'Buildings - Appliances',
    'Buildings - Electrical',
    'Buildings - Exterior',
    'Buildings - Heating',
    'Buildings - Plumbing',
    'Buildings - Structural',
    'Grounds - Parking',
    'Grounds - Path Lights',
    'Grounds - Pavement',
    'Other',
]


def seed_data(db):
    # Budget categories
    for name in DEFAULT_BUDGET_CATEGORIES:
        if not BudgetCategory.query.filter_by(name=name).first():
            db.session.add(BudgetCategory(name=name))
    db.session.flush()

    # Categories
    for name in DEFAULT_CATEGORIES:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.flush()

    # Buildings
    buildings = {}
    for num in range(1, 13):
        b = Building.query.filter_by(number=num).first()
        if not b:
            b = Building(number=num, name=BUILDING_NAMES.get(num, f"Building {num}"))
            db.session.add(b)
            db.session.flush()
        buildings[num] = b

    # Units
    for bldg_num, unit_numbers in UNIT_BUILDING_MAP.items():
        b = buildings[bldg_num]
        for unum in unit_numbers:
            u = Unit.query.filter_by(number=unum).first()
            if not u:
                u = Unit(number=unum, building_id=b.id)
                db.session.add(u)

    # Default admin board user (username: admin, password: admin – change immediately!)
    if not BoardUser.query.filter_by(username="admin").first():
        admin = BoardUser(username="admin", email="admin@example.com", is_admin=True)
        admin.set_password("admin")
        db.session.add(admin)
        print("  Created default admin user (username=admin, password=admin). CHANGE THIS!")

    db.session.commit()
    print("  Seeded 12 buildings and 33 units.")

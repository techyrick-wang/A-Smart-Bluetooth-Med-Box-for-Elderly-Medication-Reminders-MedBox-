"""Rick BioMedKit | 21-cell pill organizer + electronics bay + pin hinge.
Run in CQ-editor (Render/F5) or in Python with CadQuery installed.
All units are millimeters. Hinge tolerances require physical print testing.
"""
import cadquery as cq
from pathlib import Path


# -------------------- CONFIGURATION --------------------
LENGTH = 236.0
WIDTH = 95.0
BODY_HEIGHT = 18.0
BASE_FLOOR = 2.0
ELECTRONICS_LENGTH = 50.0
DAYS = 7
DOSES_PER_DAY = 3
OUTER_MARGIN = 2.0
DIVIDER_THICKNESS = 2.0
OUTER_CORNER_RADIUS = 2.0
LID_THICKNESS = 2.5
LID_OVERHANG_X = 0.0

HINGE_OUTER_RADIUS = 3.3
HINGE_HOLE_RADIUS = 1.50
PIN_RADIUS = 1.20
HINGE_GAP = 0.6
HINGE_KNUCKLE_LENGTH = 13.0
HINGE_Y = WIDTH + 2.0
HINGE_Z = BODY_HEIGHT + 1.2

# Exports go to Desktop if present, otherwise home directory.
desktop = Path.home() / 'Desktop'
OUTPUT = (desktop if desktop.is_dir() else Path.home()) / 'Rick_BioMedKit_exports'
OUTPUT.mkdir(parents=True, exist_ok=True)

assert DAYS == 7 and DOSES_PER_DAY == 3
assert 0 < BASE_FLOOR < BODY_HEIGHT
assert 2 * OUTER_MARGIN + (DOSES_PER_DAY - 1) * DIVIDER_THICKNESS < WIDTH
assert 2 * OUTER_MARGIN + (DAYS - 1) * DIVIDER_THICKNESS < LENGTH - ELECTRONICS_LENGTH
assert 0 < PIN_RADIUS < HINGE_HOLE_RADIUS < HINGE_OUTER_RADIUS

# -------------------- HELPERS --------------------
def block(dx, dy, dz, x, y, z):
    return cq.Workplane('XY').box(dx, dy, dz, centered=(False, False, False)).translate((x, y, z))

def cylinder_x(radius, length, x, y, z):
    return cq.Workplane('YZ', origin=(x, y, z)).circle(radius).extrude(length)

def knuckle(x, length):
    outer = cylinder_x(HINGE_OUTER_RADIUS, length, x, HINGE_Y, HINGE_Z)
    bore = cylinder_x(HINGE_HOLE_RADIUS, length + 0.2, x - 0.1, HINGE_Y, HINGE_Z)
    return outer.cut(bore)

# -------------------- BODY --------------------
body = block(LENGTH, WIDTH, BODY_HEIGHT, 0, 0, 0)
body = body.edges('|Z').fillet(OUTER_CORNER_RADIUS)

PILL_X0 = ELECTRONICS_LENGTH
PILL_LENGTH = LENGTH - PILL_X0
CELL_X = (PILL_LENGTH - 2 * OUTER_MARGIN - (DAYS - 1) * DIVIDER_THICKNESS) / DAYS
CELL_Y = (WIDTH - 2 * OUTER_MARGIN - (DOSES_PER_DAY - 1) * DIVIDER_THICKNESS) / DOSES_PER_DAY

for day in range(DAYS):
    for dose in range(DOSES_PER_DAY):
        px = PILL_X0 + OUTER_MARGIN + day * (CELL_X + DIVIDER_THICKNESS)
        py = OUTER_MARGIN + dose * (CELL_Y + DIVIDER_THICKNESS)
        body = body.cut(block(CELL_X, CELL_Y, BODY_HEIGHT - BASE_FLOOR + 1,
                              px, py, BASE_FLOOR))

# Electronics compartment stays uncovered, pending exact PCB/port dimensions.
body = body.cut(block(ELECTRONICS_LENGTH - DIVIDER_THICKNESS - OUTER_MARGIN,
                      WIDTH - 2 * OUTER_MARGIN, BODY_HEIGHT - BASE_FLOOR + 1,
                      OUTER_MARGIN, OUTER_MARGIN, BASE_FLOOR))

# -------------------- THREE-PIECE PIN HINGE --------------------
center_x = PILL_X0 + PILL_LENGTH / 2
K = HINGE_KNUCKLE_LENGTH
G = HINGE_GAP
x1 = center_x - (3 * K + 2 * G) / 2
x2 = x1 + K + G
x3 = x2 + K + G
bridge_y0 = WIDTH - 2.0
bridge_dy = HINGE_Y - bridge_y0

for sx in (x1, x3):
    bridge = block(K, bridge_dy, 3.4, sx, bridge_y0, HINGE_Z - 3.1)
    body = body.union(bridge).union(knuckle(sx, K))
    body = body.cut(cylinder_x(HINGE_HOLE_RADIUS, K + 0.3,
                               sx - 0.15, HINGE_Y, HINGE_Z))

# -------------------- MEDICINE-ONLY LID --------------------
lid = block(PILL_LENGTH + LID_OVERHANG_X, WIDTH,
            LID_THICKNESS, PILL_X0, 0, BODY_HEIGHT)
lid = lid.edges('|Z').fillet(OUTER_CORNER_RADIUS)

lid_bridge = block(K, bridge_dy, LID_THICKNESS, x2, bridge_y0, BODY_HEIGHT)
lid = lid.union(lid_bridge).union(knuckle(x2, K))
lid = lid.cut(cylinder_x(HINGE_HOLE_RADIUS, K + 0.3,
                         x2 - 0.15, HINGE_Y, HINGE_Z))
lid = lid.union(block(18.0, 5.0, LID_THICKNESS,
                      center_x - 9.0, -4.2, BODY_HEIGHT))

# Removable hinge pin, 2.4 mm nominal diameter.
pin_start = x1 - 1.0
pin_length = x3 + K - x1 + 2.0
pin = cylinder_x(PIN_RADIUS, pin_length, pin_start, HINGE_Y, HINGE_Z)

# -------------------- EXPORT --------------------
parts = {'Body': body, 'Pill_Lid': lid, 'Hinge_Pin': pin}
for name, part in parts.items():
    cq.exporters.export(part, str(OUTPUT / ('Rick_BioMedKit_' + name + '.step')))
    cq.exporters.export(part, str(OUTPUT / ('Rick_BioMedKit_' + name + '.stl')))

assembly = cq.Assembly(name='Rick_BioMedKit')
assembly.add(body, name='body', color=cq.Color(0.82, 0.84, 0.85))
assembly.add(lid, name='pill_lid', color=cq.Color(0.15, 0.55, 0.85))
assembly.add(pin, name='hinge_pin', color=cq.Color(0.90, 0.68, 0.25))
assembly.save(str(OUTPUT / 'Rick_BioMedKit_Assembly.step'))

if 'show_object' in globals():
    show_object(body, name='Body')
    show_object(lid, name='Pill_Lid')
    show_object(pin, name='Hinge_Pin')

print('21 compartments: %d columns x %d rows' % (DAYS, DOSES_PER_DAY))
print('Each medicine cavity: %.2f x %.2f x %.2f mm' % (CELL_X, CELL_Y, BODY_HEIGHT - BASE_FLOOR))
print('Export directory:', OUTPUT)

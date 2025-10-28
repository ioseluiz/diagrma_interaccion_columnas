from .material import SteelMaterial

REBAR_INFO = [
    {"number": "#3", "diameter": 0.9525, "area": 0.71},
    {"number": "#4", "diameter": 1.27, "area": 1.27},
    {"number": "#5", "diameter": 1.5875, "area": 2.0},
    {"number": "#6", "diameter": 1.905, "area": 2.84},
    {"number": "#7", "diameter": 2.2225, "area": 3.87},
    {"number": "#8", "diameter": 2.865, "area": 5.1},
    {"number": "#9", "diameter": 3.226, "area": 6.45},
]


class Rebar:
    def __init__(
        self,
        number: str,
        pos_x: float,
        pos_y: float,
        layer: int,
        steel_grade: SteelMaterial,
    ):
        self.number = number
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.layer = layer
        self.material = steel_grade

        # diameter
        self.diameter = self.get_diameter()
        # Area
        self.area = self.get_area()

    def get_diameter(self):
        return [x["diameter"] for x in REBAR_INFO if self.number == x["number"]][0]

    def get_area(self):
        return [x["area"] for x in REBAR_INFO if self.number == x["number"]][0]

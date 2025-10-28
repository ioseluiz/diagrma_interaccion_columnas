REBAR_INFO = [
    {"number": "#3", "diameter": 0.9525, "area": 0.71},
    {"number": "#4", "diameter": 1.27, "area": 1.27},
    {"number": "#5", "diameter": 1.5875, "area": 2.0},
    {"number": "#6", "diameter": 1.905, "area": 2.84},
    {"number": "#7", "diameter": 2.2225, "area": 3.87},
    {"number": "#8", "diameter": 2.865, "area": 5.1},
    {"number": "#9", "diameter": "3.226", "area": 6.45},
]


class Stirrup:
    def __init__(self, tie_rebar, tie_material):
        self.tie_rebar = tie_rebar
        self.tie_material = tie_material

        self.diameter = self.get_diameter()

    def get_diameter(self):
        return [x["diameter"] for x in REBAR_INFO if self.tie_rebar == x["number"]][0]

from .rebar import Rebar
from .material import ConcreteMaterial, SteelMaterial
from .stirrup import Stirrup


class RectangularColumn:
    def __init__(
        self,
        b: float,
        h: float,
        cover: float,
        concrete_material: ConcreteMaterial,
        rebar_number: str,
        r2_bars: int,
        r3_bars: int,
        rebar_material: SteelMaterial,
        tie_rebar: str,
        tie_material: SteelMaterial,
    ):
        self.b = b
        self.h = h
        self.cover = cover
        self.concrete_material = concrete_material
        self.rebar_number = rebar_number
        self.tie_rebar = tie_rebar
        self.r2_bars = r2_bars  # Horizontal direction
        self.r3_bars = r3_bars  # Vertical direction
        self.rebar_material = rebar_material
        self.tie_rebar = tie_rebar
        self.stirrrup_material = tie_material

        # Stirrup Rebar
        self.stirrup = Stirrup(self.tie_rebar, self.stirrrup_material)

        # Rebars
        self.rebars = []
        self.generate_rebars()

        # Calculate effective depth
        self.d = self.calculate_effective_depth()

        # Diagram Points
        self.diagram_points = []  # List of tuples of points

        self.calculate_point_1()
        self.calculate_point_2()

    def generate_rebars(self):
        # Generic_rebar
        generic_rebar = Rebar(self.rebar_number, 0, 0, 0, self.rebar_material)

        # Vertical Rebars
        left_pos_x = self.cover + self.stirrup.diameter + generic_rebar.diameter / 2
        right_pos_x = (
            self.b - self.cover - self.stirrup.diameter - generic_rebar.diameter / 2
        )
        coor_y = self.cover + self.stirrup.diameter + generic_rebar.diameter / 2
        spacing_y = (
            self.h - 2 * self.cover - 2 * self.stirrup.diameter - generic_rebar.diameter
        ) / (self.r3_bars - 1)
        for x in range(self.r3_bars):
            # Left Layer
            self.rebars.append(
                Rebar(self.rebar_number, left_pos_x, coor_y, x + 1, self.rebar_material)
            )

            # Right Layer
            self.rebars.append(
                Rebar(
                    self.rebar_number, right_pos_x, coor_y, x + 1, self.rebar_material
                )
            )
            coor_y += spacing_y

        # Horizontal Rebars
        bottom_pos_y = self.cover + self.stirrup.diameter + generic_rebar.diameter / 2
        top_pos_y = (
            self.h - self.cover - self.stirrup.diameter - generic_rebar.diameter / 2
        )
        spacing_x = (
            self.b - 2 * self.cover - 2 * self.stirrup.diameter - generic_rebar.diameter
        ) / (self.r2_bars - 1)
        coor_x = (
            self.cover + self.stirrup.diameter + generic_rebar.diameter / 2 + spacing_x
        )
        for y in range(self.r2_bars - 2):
            # Top Layer
            self.rebars.append(
                Rebar(
                    self.rebar_number,
                    coor_x,
                    top_pos_y,
                    self.r3_bars,
                    self.rebar_material,
                )
            )

            # Bottom Layer
            self.rebars.append(
                Rebar(self.rebar_number, coor_x, bottom_pos_y, 1, self.rebar_material)
            )

    def get_layer_rebars(self, layer):
        return [x for x in self.rebars if x.layer == layer]

    def get_layer_area(self, layer):
        total_area = 0
        for rebar in [x for x in self.rebars if x.layer == layer]:
            total_area += rebar.area
        return total_area

    def calculate_effective_depth(self):
        # Generic_rebar
        generic_rebar = Rebar(self.rebar_number, 0, 0, 0, self.rebar_material)
        # Get rebar most bottom position
        bottom_pos_y = (
            self.h - self.cover - self.stirrup.diameter - generic_rebar.diameter / 2
        )
        return bottom_pos_y

    def get_total_rebar_area(self):
        total_area = 0
        for x in self.rebars:
            total_area += x.area
        return total_area

    def calculate_point_1(self):
        # Neutral Axis in the infinite
        ## Iterate through r2_bars (vertical)
        cc = (
            0.85
            * self.concrete_material.fc
            * (self.b * self.h - self.get_total_rebar_area())
        )
        sum_p = 0
        for i in range(1, self.r3_bars + 1):
            # fs
            fs = self.rebar_material.fy

            # Total Rebar Area in the layer
            rebar_layer_area = self.get_layer_area(i)
            print(f"layer: {i}, area: {rebar_layer_area}")
            sum_p += rebar_layer_area * fs

        # Nominal Axial Load
        pn = cc + sum_p
        # Nominal Moment
        self.pn_1 = pn
        self.mn_1 = 0

    def calculate_point_2(self):
        # Neutral axis in the bottom of the section
        # Calculo de Fuerza de Compresion del concreto
        cc = (
            0.85
            * self.concrete_material.fc
            * (self.b * self.d - self.get_total_rebar_area())
        )
        sump = 0
        sum_mn = 0
        # Nunca es puede ser mayor a 0.002
        for i in range(1, self.r3_bars + 1):
            rebar_layer_area = self.get_layer_area(i)
            pos_y = [x.pos_y for x in self.rebars if i == x.layer][0]
            es = 0.003 * (pos_y) / self.h
            if es >= 0.002:
                es = 0.002
            fs = es * self.rebar_material.Es
            ps = fs * rebar_layer_area
            sump += ps
            if pos_y >= self.h / 2:
                dist = pos_y - self.h / 2
            else:
                dist = -(self.h / 2 - pos_y)
            sum_mn += ps * dist
            print(es, fs, ps)
        self.pn_2 = cc + sump

        # calculate nominal moment
        self.mn_2 = cc * (self.h / 2 - self.d / 2) + sum_mn

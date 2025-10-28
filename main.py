from elements.column import RectangularColumn
from elements.material import ConcreteMaterial, SteelMaterial


def main():
    # Create materials
    ## Concrete material
    conc_210 = ConcreteMaterial("concrete f'c=210kg/cm2", 210)
    conc_280 = ConcreteMaterial("concrete f'c=280kg/cm2", 280)

    # Steel Rebars
    rebar_grade_40 = SteelMaterial("rebar_grade_40", 2100)
    rebar_grade_60 = SteelMaterial("rebar_grade_60", 4200)

    # Concrete Column
    col_1 = RectangularColumn(
        b=30,
        h=60,
        cover=4,
        concrete_material=conc_280,
        rebar_number="#5",
        r2_bars=3,
        r3_bars=5,
        rebar_material=rebar_grade_60,
        tie_rebar="#3",
        tie_material=rebar_grade_40,
    )

    for x in col_1.rebars:
        print(f"layer: {x.layer}, pos_x: {x.pos_x}, pos_y: {x.pos_y}")

    print(col_1.pn_1, col_1.mn_1)
    print(col_1.pn_2, col_1.mn_2)


if __name__ == "__main__":
    main()

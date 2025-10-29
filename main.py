from elements.column import RectangularColumn
from elements.material import ConcreteMaterial, SteelMaterial
from elements.load import PuntoDeCarga


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

    # --- INICIO MODIFICACIÓN: CREAR PUNTOS DE CARGA ---
    # Unidades: Pu en Toneladas, Mu en Ton-m
    carga_combo_1 = PuntoDeCarga(name="CM-1 (1.4D+1.7L)", Pu=220.5, Mu=15.2)
    carga_combo_2 = PuntoDeCarga(name="CM-2 (Max M)", Pu=110.0, Mu=35.8)
    carga_combo_3 = PuntoDeCarga(name="CM-3 (Con Sismo)", Pu=85.0, Mu=-42.0)

    cargas_para_graficar = [carga_combo_1, carga_combo_2, carga_combo_3]

    # Generar el gráfico y pasar los puntos de carga
    col_1.plot_diagram(file_name="diagrama_col_1.png", load_points=cargas_para_graficar)

    print("Diagrama 'diagrama_col_1.png' generado exitosamente con puntos de carga.")


if __name__ == "__main__":
    main()

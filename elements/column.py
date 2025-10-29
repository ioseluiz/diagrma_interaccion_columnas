from .rebar import Rebar
from .material import ConcreteMaterial, SteelMaterial
from .stirrup import Stirrup
from utils.utils import get_beta
from .load import PuntoDeCarga

import matplotlib.pyplot as plt
import numpy as np


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
        self.points = []

        # Stirrup Rebar
        self.stirrup = Stirrup(self.tie_rebar, self.stirrrup_material)

        # Rebars
        self.rebars = []
        self.generate_rebars()

        # Calculate effective depth
        self.d = self.calculate_effective_depth()

        self.phi_pn_max = 0.0  # Inicializar (en kg)

        # Diagram Points
        # Punto 1: Compresión Pura
        self.calculate_point_1()
        self.points.append((self.mn_1, self.pn_1, 0.65))

        # Calcular Pn,max (ACI 318-19, 22.4.2.1)
        # phi_Pn_max = 0.80 * (phi * Pn0) (en kg)
        self.phi_pn_max = 0.80 * (0.65 * self.pn_1)

        # Puntos Intermedios (c variando)
        self.calculate_variable_points()

        # Punto Final: Tensión Pura
        self.calculate_point_tension()
        self.points.append((self.mn_tension, self.pn_tension, 0.90))

        # Ordenar todos los puntos por Pn (de mayor a menor)
        self.points.sort(key=lambda p: p[1], reverse=True)

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

    def get_layer_pos_y(self, layer_number):
        return [x.pos_y for x in self.rebars if layer_number == x.layer][0]

    def get_layer_position(self, c: float, layer_pos_y: float):
        if c > layer_pos_y:
            tipo = "compresion"
        else:
            tipo = "tension"
        return tipo

    def get_layer_pos_centroid(self, pos_centroid, pos_y):
        if pos_centroid > pos_y:
            # Clockwise
            type = "arriba_centroide"
        else:
            type = "abajo_centroide"
        return type

    def get_es(self, c: float, layer_pos_y: float):
        if c > layer_pos_y:
            # compresion
            es = 0.003 * (c - layer_pos_y / c)
            if es > 0.002:
                es = 0.002
        else:
            # tension
            es = 0.003 * (layer_pos_y - c) / c
            if es > 0.002:
                es = 0.002
        return es

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
        # Punto 1: Compresión Pura (c = infinito)
        # (ACI 318-19, Ecuación 22.4.2.2)

        ag = self.b * self.h
        ast = self.get_total_rebar_area()
        fc = self.concrete_material.fc
        fy = self.rebar_material.fy

        # Fuerza del Concreto (restando el área de acero)
        cc = 0.85 * fc * (ag - ast)

        # Fuerza del Acero (Todo el acero fluye)
        sum_p = ast * fy

        # Carga Nominal (Pn0)
        self.pn_1 = cc + sum_p
        # Momento Nominal
        self.mn_1 = 0.0

    def calculate_variable_points(self):
        # Deformación unitaria de fluencia del acero
        ey = self.rebar_material.fy / self.rebar_material.Es

        # Dist. al acero extremo en tensión (desde fibra superior)
        d_t = self.h - self.get_layer_pos_y(1)

        # Iterar la posición del eje neutro 'c'
        for x in range(101):
            c = self.h - (x / 100.0) * self.h

            if c < 1e-5:
                continue

            # --- CÁLCULO DE PHI ---
            et = 0.003 * (d_t - c) / c

            phi = 0.65  # Default para Compresión

            if et > ey:
                if et >= 0.005:  # Tensión
                    phi = 0.90
                else:  # Transición
                    phi = 0.65 + 0.25 * (et - ey) / (0.005 - ey)

            beta = get_beta(self.concrete_material.fc)
            a = c * beta

            if a > self.h:
                a = self.h

            Ccomp = 0.85 * self.concrete_material.fc * self.b * a
            arm_c = (self.h / 2.0) - (a / 2.0)
            Mn_c = Ccomp * arm_c

            sum_ps = 0.0
            sum_mn_s = 0.0

            for i in range(1, self.r3_bars + 1):
                layer_pos_y = self.get_layer_pos_y(i)
                area = self.get_layer_area(i)
                d_prime = self.h - layer_pos_y

                es = 0.003 * (c - d_prime) / c

                fs = es * self.rebar_material.Es
                if fs > self.rebar_material.fy:
                    fs = self.rebar_material.fy
                elif fs < -self.rebar_material.fy:
                    fs = -self.rebar_material.fy

                ps = area * fs
                arm_s = (self.h / 2.0) - d_prime
                Mn_s = ps * arm_s

                sum_ps += ps
                sum_mn_s += Mn_s

            pn = Ccomp + sum_ps
            mn = Mn_c + sum_mn_s

            self.points.append((mn, pn, phi))

    def calculate_point_tension(self):
        pn = -self.get_total_rebar_area() * self.rebar_material.fy
        mn = 0.0

        self.pn_tension = pn
        self.mn_tension = mn

    def plot_diagram(
        self,
        file_name="interaction_diagram.png",
        load_points: list[PuntoDeCarga] = None,
    ):
        """
        Grafica el diagrama de interacción Pn-Mn (Nominal) y phi*Pn-phi*Mn (Diseño).
        Aplica el límite de Pn,max del ACI 318-19.
        Convierte las unidades a Ton y Ton-m para el gráfico.

        Args:
            file_name (str): Nombre del archivo de salida.
            load_points (list[PuntoDeCarga], optional): Lista de puntos de carga
                                                       (Pu en Ton, Mu en Ton-m) a graficar.
        """

        # Factores de conversión
        p_factor = 1000.0  # kg a Ton
        m_factor = 100000.0  # kg-cm a Ton-m

        # 1. Separar y CONVERTIR los datos (de kg, kg-cm a Ton, Ton-m)
        mn_nominal = [p[0] / m_factor for p in self.points]
        pn_nominal = [p[1] / p_factor for p in self.points]

        mn_factored = [(p[0] * p[2]) / m_factor for p in self.points]  # phi * Mn
        pn_factored = [(p[1] * p[2]) / p_factor for p in self.points]  # phi * Pn

        # Guardar los valores de phi para las anotaciones
        phis = [p[2] for p in self.points]

        # Convertir el límite Pn,max a Ton
        phi_pn_max_ton = self.phi_pn_max / p_factor

        # Aplicar el límite phi*Pn,max (en Ton)
        pn_factored_capped = []
        for pn_val in pn_factored:
            if pn_val > phi_pn_max_ton:
                pn_factored_capped.append(phi_pn_max_ton)
            else:
                pn_factored_capped.append(pn_val)

        pn_factored = pn_factored_capped

        # 2. Añadir el lado simétrico (ya están en Ton y Ton-m)

        # --- Nominal ---
        mn_sym_nominal = [-x for x in mn_nominal if x != 0]
        pn_sym_nominal = [y for x, y in zip(mn_nominal, pn_nominal) if x != 0]
        mn_full_nominal = mn_sym_nominal[::-1] + mn_nominal
        pn_full_nominal = pn_sym_nominal[::-1] + pn_nominal

        # --- Diseño (Factored) ---
        mn_sym_factored = [-x for x in mn_factored if x != 0]
        pn_sym_factored = [y for x, y in zip(mn_factored, pn_factored) if x != 0]
        mn_full_factored = mn_sym_factored[::-1] + mn_factored
        pn_full_factored = pn_sym_factored[::-1] + pn_factored

        # 3. Crear el gráfico
        plt.figure(
            figsize=(12, 8)
        )  # MODIFICACIÓN: Ancho aumentado (12) para dar espacio a la leyenda

        # MODIFICACIÓN: Se quitaron markers y se usa linestyle='-' (sólido)
        plt.plot(
            mn_full_nominal,
            pn_full_nominal,
            linestyle="-",
            label="Resistencia Nominal (Pn-Mn)",
        )
        plt.plot(
            mn_full_factored,
            pn_full_factored,
            linestyle="-",
            label="Resistencia de Diseño ($\phi$Pn-$\phi$Mn) ACI 318-19",
            color="red",
        )

        # 4. Títulos y etiquetas
        bars = 2 * self.r3_bars + 2 * (self.r2_bars - 2)
        plt.title(
            f"Diagrama de Interacción (Columna {self.b} x {self.h} cm) - {bars}{self.rebar_number}"
        )
        plt.xlabel("Momento, M (Ton-m)")
        plt.ylabel("Carga Axial, P (Ton)")

        # 5. Visualización
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.axhline(0, color="black", linewidth=0.5)
        plt.axvline(0, color="black", linewidth=0.5)

        # --- INICIO MODIFICACIÓN: ANOTACIONES DE PHI ---
        # Usamos los datos antes de hacerlos simétricos
        np_phis = np.array(phis)

        # Zona de Compresión (phi = 0.65)
        idx_comp = np.where(np_phis == 0.65)[0]
        if len(idx_comp) > 0:
            # Tomamos un punto intermedio en la zona de compresión
            comp_point_idx = idx_comp[len(idx_comp) // 4]
            x = mn_factored[comp_point_idx] * 1.05  # Ligero offset
            y = pn_factored[comp_point_idx]
            if x > 0:  # Solo anotar en el lado positivo
                plt.text(
                    x,
                    y,
                    "$\phi=0.65$",
                    fontsize=8,
                    color="gray",
                    ha="left",
                    va="center",
                )

        # Zona de Tensión (phi = 0.90)
        idx_tens = np.where(np_phis == 0.90)[0]
        if len(idx_tens) > 0:
            # Tomamos un punto intermedio en la zona de tensión
            tens_point_idx = idx_tens[len(idx_tens) // 2]
            x = mn_factored[tens_point_idx] * 1.05  # Ligero offset
            y = pn_factored[tens_point_idx]
            if x > 0:  # Solo anotar en el lado positivo
                plt.text(
                    x,
                    y,
                    "$\phi=0.90$",
                    fontsize=8,
                    color="gray",
                    ha="left",
                    va="center",
                )

        # Zona de Transición (0.65 < phi < 0.90)
        idx_trans = np.where((np_phis > 0.65) & (np_phis < 0.90))[0]
        if len(idx_trans) > 0:
            # Tomamos un punto intermedio en la zona de transición
            trans_point_idx = idx_trans[len(idx_trans) // 2]
            x = mn_factored[trans_point_idx] * 1.05  # Ligero offset
            y = pn_factored[trans_point_idx]
            if x > 0:  # Solo anotar en el lado positivo
                plt.text(
                    x,
                    y,
                    "Transición $\phi$",
                    fontsize=8,
                    color="gray",
                    ha="left",
                    va="center",
                )
        # --- FIN MODIFICACIÓN: ANOTACIONES DE PHI ---

        # --- INICIO MODIFICACIÓN: GRAFICAR PUNTOS DE CARGA ---
        if load_points:
            for point in load_points:
                # Grafica el punto
                plt.plot(
                    point.Mu,
                    point.Pu,
                    "kx",
                    markersize=10,
                    markeredgewidth=3,
                    # La etiqueta completa se usará en la leyenda
                    label=f"Carga: {point.name} (Pu={point.Pu} T, Mu={point.Mu} T-m)",
                )

                # MODIFICACIÓN: El texto en el gráfico solo usa el nombre corto
                # Asume que el nombre es "CM-1 (desc...)" -> "CM-1"
                short_name = point.name.split(" ")[0]
                plt.text(
                    point.Mu,
                    point.Pu * 1.01,
                    f" {short_name}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    weight="bold",
                )
        # --- FIN MODIFICACIÓN ---

        # MODIFICACIÓN: Mover la leyenda fuera del gráfico
        # Coloca la leyenda fuera del área de ploteo, en la esquina superior derecha
        # MODIFICACIÓN: Mover la leyenda fuera del gráfico
        # Coloca la leyenda fuera del área de ploteo, en la esquina superior derecha
        # Aumentamos un poco el valor de 'x' en bbox_to_anchor a 1.05 o 1.06
        plt.legend(
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
            borderaxespad=0.0,
            fontsize="x-small",
        )  # MODIFICACIÓN: fontsize a 'x-small'

        # 6. Guardar
        # MODIFICACIÓN: Eliminar plt.subplots_adjust y usar plt.tight_layout()
        plt.tight_layout()  # <-- REEMPLAZA plt.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.1)

        plt.savefig(file_name)
        plt.close()

        return file_name

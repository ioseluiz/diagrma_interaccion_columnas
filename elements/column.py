from .rebar import Rebar
from .material import ConcreteMaterial, SteelMaterial
from .stirrup import Stirrup
from utils.utils import get_beta
from .load import PuntoDeCarga

import matplotlib.pyplot as plt
import matplotlib.patches as patches
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

    # En column.py, dentro de la clase RectangularColumn

    def plot_schematic_on_ax(self, ax_schemat):
        """
        Dibuja el esquema de la sección transversal de la columna
        en un 'Axes' de Matplotlib proporcionado.
        """
        ax_schemat.clear()
        ax_schemat.set_aspect("equal")
        ax_schemat.set_axis_off()  # Oculta los ejes X e Y

        # Mismo color de fondo que la GUI
        ax_schemat.set_facecolor("#d0d0d0")

        # 1. Dibujar el Concreto
        concreto = patches.Rectangle(
            (0, 0),
            self.b,
            self.h,
            fill=True,
            facecolor="#d0d0d0",
            edgecolor="#a0a0a0",
            lw=1,
        )
        ax_schemat.add_patch(concreto)

        # 2. Dibujar el Estribo
        stirrup_b = self.b - 2 * self.cover
        stirrup_h = self.h - 2 * self.cover
        estribo = patches.Rectangle(
            (self.cover, self.cover),
            stirrup_b,
            stirrup_h,
            fill=False,
            edgecolor="#505050",
            lw=2,
        )
        ax_schemat.add_patch(estribo)

        # 3. Dibujar las Barras de Refuerzo
        for rebar in self.rebars:
            barra = patches.Circle(
                (rebar.pos_x, rebar.pos_y),
                rebar.diameter / 2,
                fill=True,
                facecolor="#303030",
                edgecolor="#101010",
                lw=0.5,
            )
            ax_schemat.add_patch(barra)

        # 4. Ajustar los límites del dibujo
        margin = self.cover * 0.5
        ax_schemat.set_xlim(-margin, self.b + margin)
        ax_schemat.set_ylim(-margin, self.h + margin)

    def plot_diagram(
        self,
        ax=None,
        file_name="interaction_diagram.png",
        load_points: list[PuntoDeCarga] = None,
    ):
        """
        Grafica el diagrama de interacción Pn-Mn (Nominal) y phi*Pn-phi*Mn (Diseño).
        Si se proporciona 'ax' (un Axes de Matplotlib), dibuja sobre él.
        Si 'ax' es None, crea una nueva figura y la guarda en 'file_name'.
        """

        # Determina si se está creando un nuevo gráfico o dibujando en uno existente
        if ax is None:
            # MODIFICACIÓN: Aseguramos que la figura tenga el tamaño correcto
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111)
            save_and_close = True
        else:
            fig = ax.get_figure()
            save_and_close = False

        # ... (Factores de conversión y CÁLCULOS de mn_full_nominal, pn_full_nominal, etc.
        #      Tu código existente va aquí) ...

        # --- (Tu código de cálculo de Pn, Mn, phi, etc. va aquí) ---
        # Factores de conversión
        p_factor = 1000.0  # kg a Ton
        m_factor = 100000.0  # kg-cm a Ton-m

        # 1. Separar y CONVERTIR los datos
        mn_nominal = [p[0] / m_factor for p in self.points]
        pn_nominal = [p[1] / p_factor for p in self.points]
        mn_factored = [(p[0] * p[2]) / m_factor for p in self.points]  # phi * Mn
        pn_factored = [(p[1] * p[2]) / p_factor for p in self.points]  # phi * Pn
        phis = [p[2] for p in self.points]

        # Aplicar el límite phi*Pn,max
        phi_pn_max_ton = self.phi_pn_max / p_factor
        pn_factored_capped = []
        for pn_val in pn_factored:
            pn_factored_capped.append(min(pn_val, phi_pn_max_ton))
        pn_factored = pn_factored_capped

        # 2. Añadir el lado simétrico
        # Nominal
        mn_sym_nominal = [-x for x in mn_nominal if x != 0]
        pn_sym_nominal = [y for x, y in zip(mn_nominal, pn_nominal) if x != 0]
        mn_full_nominal = mn_sym_nominal[::-1] + mn_nominal
        pn_full_nominal = pn_sym_nominal[::-1] + pn_nominal

        # Diseño (Factored)
        mn_sym_factored = [-x for x in mn_factored if x != 0]
        pn_sym_factored = [y for x, y in zip(mn_factored, pn_factored) if x != 0]
        mn_full_factored = mn_sym_factored[::-1] + mn_factored
        pn_full_factored = pn_sym_factored[::-1] + pn_factored
        # --- (Fin del código de cálculo) ---

        # 3. Crear el gráfico (usando 'ax')
        ax.plot(
            mn_full_nominal,
            pn_full_nominal,
            linestyle="-",
            label="Resistencia Nominal (Pn-Mn)",
        )
        ax.plot(
            mn_full_factored,
            pn_full_factored,
            linestyle="-",
            label="Resistencia de Diseño ($\phi$Pn-$\phi$Mn)",
            color="red",
        )

        # 4. Títulos y etiquetas
        cant_rebar = 2 * self.r3_bars + 2 * (self.r2_bars - 2)
        ax.set_title(
            f"Diagrama de Interacción (Columna {self.b} x {self.h} cm - {cant_rebar}{self.rebar_number})"
        )
        ax.set_xlabel("Momento, M (Ton-m)")
        ax.set_ylabel("Carga Axial, P (Ton)")

        # 5. Visualización
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.axvline(0, color="black", linewidth=0.5)

        # ... (Tu código de anotaciones de PHI va aquí) ...

        # --- INICIO: SECCIÓN CRÍTICA PARA GRAFICAR CARGAS ---
        # Esto asegura que los puntos de carga se dibujen.
        if load_points:
            for point in load_points:
                # La etiqueta completa se usará en la leyenda
                label = f"Carga: {point.name} (Pu={point.Pu} T, Mu={point.Mu} T-m)"

                # Grafica el punto
                ax.plot(
                    point.Mu,
                    point.Pu,
                    "kx",
                    markersize=10,
                    markeredgewidth=3,
                    label=label,
                )

                # Texto en el gráfico solo usa el nombre corto
                short_name = point.name.split(" ")[0]
                ax.text(
                    point.Mu,
                    point.Pu * 1.01,
                    f" {short_name}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    weight="bold",
                )
        # --- FIN: SECCIÓN CRÍTICA ---

        # Mover la leyenda fuera del gráfico
        ax.legend(
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
            borderaxespad=0.0,
            fontsize="x-small",
        )

        # --- INICIO DE LA MODIFICACIÓN ---
        try:
            # Añadir el esquema usando fig.add_axes
            # Coordenadas relativas a la FIGURA [left, bottom, width, height]
            # (0,0) es abajo-izquierda, (1,1) es arriba-derecha

            # Puedes ajustar [0.77, 0.1, 0.2, 0.2] si es necesario
            # 0.77 = 77% desde la izquierda (justo en el espacio que dejaremos)
            # 0.1  = 10% desde abajo
            # 0.2  = 20% de ancho
            # 0.2  = 20% de alto
            ax_schematic = fig.add_axes([0.77, 0.1, 0.2, 0.2])

            self.plot_schematic_on_ax(ax_schematic)

        except Exception as e:
            print(f"Advertencia: No se pudo dibujar el esquema. Error: {e}")
        # --- FIN DE LA MODIFICACIÓN ---

        # 6. Guardar o devolver
        # --- MODIFICACIÓN: Reemplazar tight_layout() con subplots_adjust() ---
        # Ajusta el gráfico principal para dejar espacio a la derecha (1.0 - 0.75 = 0.25)
        # para la leyenda y el nuevo esquema.
        fig.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.1)

        if save_and_close:
            # Ya no se necesita fig.tight_layout() aquí
            fig.savefig(file_name)
            plt.close(fig)
            return file_name
        else:
            # Ya no se necesita fig.tight_layout() aquí
            return fig

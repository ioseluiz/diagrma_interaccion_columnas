import sys
import numpy as np
import matplotlib.pyplot as plt

# --- Imports de PyQt5 ---
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QGroupBox,
    QTabWidget,
    QMessageBox,
    QFileDialog,
    QListWidget,
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF
from PyQt5.QtCore import Qt, QRectF, QPointF

# --- Imports de Matplotlib para PyQt5 ---
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# --- Imports de tu proyecto ---
from elements.column import RectangularColumn
from elements.material import ConcreteMaterial, SteelMaterial
from elements.load import PuntoDeCarga
from elements.rebar import REBAR_INFO
from elements.stirrup import Stirrup


# -----------------------------------------------------------------
# WIDGET PARA EL ESQUEMA DE LA SECCIÓN TRANSVERSAL
# -----------------------------------------------------------------
class ColumnSchematicWidget(QWidget):
    """
    Un widget personalizado que dibuja la sección transversal de la columna
    usando QPainter.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.column = None
        self.setMinimumHeight(300)

    def update_data(self, column: RectangularColumn):
        """
        Recibe el objeto RectangularColumn y actualiza el widget
        para volver a dibujarlo.
        """
        self.column = column
        self.update()  # Llama a paintEvent()

    def paintEvent(self, event):
        """
        Se ejecuta cada vez que el widget necesita ser redibujado.
        """
        super().paintEvent(event)

        if not self.column:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 30  # Margen en píxeles

        # Calcular factor de escala para ajustar la columna al widget
        drawable_w = w - 2 * margin
        drawable_h = h - 2 * margin

        # Manejar división por cero si b o h son 0
        if self.column.b == 0 or self.column.h == 0:
            return

        scale_x = drawable_w / self.column.b
        scale_y = drawable_h / self.column.h
        scale = min(scale_x, scale_y)

        if scale <= 0:
            return

        # Calcular offsets para centrar el dibujo
        scaled_b = self.column.b * scale
        scaled_h = self.column.h * scale
        offset_x = (w - scaled_b) / 2
        offset_y = (h - scaled_h) / 2

        # --- Función auxiliar para transformar coordenadas ---
        def transform(col_x, col_y):
            # La columna (0,0) está abajo a la izquierda
            # QPainter (0,0) está arriba a la izquierda
            tx = offset_x + col_x * scale
            ty = offset_y + (self.column.h - col_y) * scale  # Invertir eje Y
            return QPointF(tx, ty)

        # 1. Dibujar el Concreto (Rectángulo exterior)
        painter.setPen(QPen(QColor("#a0a0a0"), 2))
        painter.setBrush(QBrush(QColor("#d0d0d0")))
        col_rect = QRectF(offset_x, offset_y, scaled_b, scaled_h)
        painter.drawRect(col_rect)

        # 2. Dibujar el Estribo (Rectángulo interior)
        painter.setPen(QPen(QColor("#505050"), 2 * scale))  # Grosor del estribo
        painter.setBrush(Qt.NoBrush)

        stirrup_b = self.column.b - 2 * self.column.cover
        stirrup_h = self.column.h - 2 * self.column.cover

        # Coordenadas del estribo
        p1 = transform(self.column.cover, self.column.cover)
        p2 = transform(self.column.b - self.column.cover, self.column.cover)
        p3 = transform(
            self.column.b - self.column.cover, self.column.h - self.column.cover
        )
        p4 = transform(self.column.cover, self.column.h - self.column.cover)

        polygon = QPolygonF([p1, p2, p3, p4])
        painter.drawPolygon(polygon)

        # 3. Dibujar las Barras de Refuerzo
        painter.setPen(QPen(QColor("#101010"), 1))
        painter.setBrush(QBrush(QColor("#303030")))

        if not self.column.rebars:
            return

        for rebar in self.column.rebars:
            center = transform(rebar.pos_x, rebar.pos_y)
            radius = (rebar.diameter / 2) * scale
            painter.drawEllipse(center, radius, radius)


# -----------------------------------------------------------------
# WIDGET DEL LIENZO DE MATPLOTLIB
# -----------------------------------------------------------------
class MplCanvas(QWidget):
    """
    Un widget que contiene la figura de Matplotlib, el lienzo
    y la barra de herramientas.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, column_obj, load_points_list):
        """
        Limpia la figura y le pide al objeto columna que dibuje
        el diagrama en su 'Axes'.
        """
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Llamamos a la función MODIFICADA de column.py
            column_obj.plot_diagram(ax=ax, load_points=load_points_list)

            # --- MODIFICACIÓN: ELIMINAR ESTA LÍNEA ---
            # self.figure.tight_layout() # <-- ¡Elimina o comenta esta línea!

            self.canvas.draw()

        except Exception as e:
            self.show_error(f"Error al graficar: {e}")

    def show_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()


# -----------------------------------------------------------------
# VENTANA PRINCIPAL DE LA APLICACIÓN
# -----------------------------------------------------------------
class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Diagrama de Interacción de Columnas")
        self.setGeometry(100, 100, 1400, 800)

        # Objeto columna que se generará
        self.column_object = None

        # --- NUEVO: Lista para almacenar los Puntos de Carga ---
        self.load_points_list = []

        # --- Layout principal ---
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        # --- Panel Izquierdo: Entradas ---
        input_panel = self.create_input_panel()
        main_layout.addWidget(input_panel, 1)  # Proporción 1

        # --- Panel Derecho: Salidas (Gráficos) ---
        output_panel = self.create_output_panel()
        main_layout.addWidget(output_panel, 3)  # Proporción 3

        self.setCentralWidget(main_widget)
        self.show()

    def create_input_panel(self):
        """
        Crea el panel lateral izquierdo con todos los campos
        de entrada de datos.
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # --- Propiedades de la Columna ---
        group_geom = QGroupBox("Geometría (cm)")
        form_geom = QFormLayout()
        self.b_input = QDoubleSpinBox()
        self.b_input.setRange(10, 500)
        self.b_input.setValue(30)
        self.h_input = QDoubleSpinBox()
        self.h_input.setRange(10, 500)
        self.h_input.setValue(60)
        self.cover_input = QDoubleSpinBox()
        self.cover_input.setRange(1, 10)
        self.cover_input.setValue(4)

        form_geom.addRow("Ancho (b):", self.b_input)
        form_geom.addRow("Altura (h):", self.h_input)
        form_geom.addRow("Recubrimiento (cover):", self.cover_input)
        group_geom.setLayout(form_geom)

        # --- Propiedades de Materiales ---
        group_mat = QGroupBox("Materiales (kg/cm²)")
        form_mat = QFormLayout()
        self.fc_input = QDoubleSpinBox()
        self.fc_input.setRange(100, 1000)
        self.fc_input.setValue(280)
        self.fy_input = QDoubleSpinBox()
        self.fy_input.setRange(2100, 6000)
        self.fy_input.setValue(4200)
        self.fy_tie_input = QDoubleSpinBox()
        self.fy_tie_input.setRange(2100, 6000)
        self.fy_tie_input.setValue(2100)

        form_mat.addRow("f'c (Concreto):", self.fc_input)
        form_mat.addRow("fy (Acero Principal):", self.fy_input)
        form_mat.addRow("fy (Estribo):", self.fy_tie_input)
        group_mat.setLayout(form_mat)

        # --- Propiedades de Refuerzo ---
        group_rebar = QGroupBox("Refuerzo")
        form_rebar = QFormLayout()

        self.rebar_main_input = QComboBox()
        self.rebar_tie_input = QComboBox()
        rebar_numbers = [r["number"] for r in REBAR_INFO]
        self.rebar_main_input.addItems(rebar_numbers)
        self.rebar_tie_input.addItems(rebar_numbers)
        self.rebar_main_input.setCurrentText("#5")
        self.rebar_tie_input.setCurrentText("#3")

        self.r3_bars_input = QSpinBox()  # Vertical
        self.r3_bars_input.setRange(2, 20)
        self.r3_bars_input.setValue(5)
        self.r2_bars_input = QSpinBox()  # Horizontal
        self.r2_bars_input.setRange(2, 20)
        self.r2_bars_input.setValue(3)

        form_rebar.addRow("Acero Principal:", self.rebar_main_input)
        form_rebar.addRow("Acero Estribo:", self.rebar_tie_input)
        form_rebar.addRow("Barras (dirección h, r3):", self.r3_bars_input)
        form_rebar.addRow("Barras (dirección b, r2):", self.r2_bars_input)
        group_rebar.setLayout(form_rebar)

        # --- NUEVO: Panel de Cargas ---
        group_loads = QGroupBox("Cargas Factorizadas")
        loads_layout = QVBoxLayout()

        form_loads = QFormLayout()
        self.load_name_input = QLineEdit("CM-1")
        self.load_pu_input = QDoubleSpinBox()
        self.load_pu_input.setRange(-10000, 10000)
        self.load_pu_input.setValue(220.5)
        self.load_pu_input.setSuffix(" Ton")
        self.load_mu_input = QDoubleSpinBox()
        self.load_mu_input.setRange(-10000, 10000)
        self.load_mu_input.setValue(15.2)
        self.load_mu_input.setSuffix(" Ton-m")

        form_loads.addRow("Nombre:", self.load_name_input)
        form_loads.addRow("Pu:", self.load_pu_input)
        form_loads.addRow("Mu:", self.load_mu_input)

        self.add_load_button = QPushButton("Añadir Carga")
        self.add_load_button.clicked.connect(self.add_load_point)

        self.load_list_widget = QListWidget()
        self.load_list_widget.setMinimumHeight(100)

        self.remove_load_button = QPushButton("Eliminar Carga Seleccionada")
        self.remove_load_button.clicked.connect(self.remove_load_point)

        loads_layout.addLayout(form_loads)
        loads_layout.addWidget(self.add_load_button)
        loads_layout.addWidget(self.load_list_widget)
        loads_layout.addWidget(self.remove_load_button)
        group_loads.setLayout(loads_layout)
        # --- FIN NUEVO ---

        # --- Botón de Generar ---
        self.generate_button = QPushButton("Generar Diagrama y Esquema")
        self.generate_button.setStyleSheet("font-weight: bold; padding: 5px;")
        self.generate_button.clicked.connect(self.run_generation)

        layout.addWidget(group_geom)
        layout.addWidget(group_mat)
        layout.addWidget(group_rebar)
        layout.addWidget(group_loads)  # --- NUEVO ---
        layout.addStretch(1)  # Empuja todo hacia arriba
        layout.addWidget(self.generate_button)

        return panel

    def create_output_panel(self):
        # ... (Esta función no cambia, déjala como estaba) ...
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.tabs = QTabWidget()
        self.plot_canvas = MplCanvas(self)
        self.tabs.addTab(self.plot_canvas, "Diagrama de Interacción")
        self.schematic_canvas = ColumnSchematicWidget(self)
        self.tabs.addTab(self.schematic_canvas, "Esquema de Sección Transversal")
        self.export_button = QPushButton("Exportar Diagrama como Imagen")
        self.export_button.clicked.connect(self.export_diagram)
        self.export_button.setEnabled(False)
        layout.addWidget(self.tabs)
        layout.addWidget(self.export_button)
        return panel

    # --- NUEVA FUNCIÓN ---
    def add_load_point(self):
        """
        Añade el punto de carga de los campos de entrada a la lista.
        """
        name = self.load_name_input.text()
        pu = self.load_pu_input.value()
        mu = self.load_mu_input.value()

        if not name:
            QMessageBox.warning(
                self, "Error", "El nombre de la carga no puede estar vacío."
            )
            return

        # 1. Crear el objeto
        load_point = PuntoDeCarga(name=name, Pu=pu, Mu=mu)

        # 2. Añadirlo a la lista de objetos
        self.load_points_list.append(load_point)

        # 3. Añadirlo a la lista visual (QListWidget)
        display_text = f"{name} (Pu={pu} T, Mu={mu} T-m)"
        self.load_list_widget.addItem(display_text)

        # 4. Limpiar campos
        self.load_name_input.setText(f"CM-{len(self.load_points_list) + 1}")
        self.load_pu_input.setValue(0)
        self.load_mu_input.setValue(0)

    # --- NUEVA FUNCIÓN ---
    def remove_load_point(self):
        """
        Elimina el punto de carga seleccionado de la lista.
        """
        current_row = self.load_list_widget.currentRow()

        if current_row >= 0:
            # 1. Eliminar de la lista visual
            self.load_list_widget.takeItem(current_row)
            # 2. Eliminar de la lista de objetos
            self.load_points_list.pop(current_row)

    def run_generation(self):
        """
        Función principal que se ejecuta al presionar el botón "Generar".
        """
        try:
            # 1. Leer todos los valores de la GUI (igual que antes)
            b = self.b_input.value()
            h = self.h_input.value()
            cover = self.cover_input.value()
            fc = self.fc_input.value()
            fy = self.fy_input.value()
            fy_tie = self.fy_tie_input.value()
            rebar_main = self.rebar_main_input.currentText()
            rebar_tie = self.rebar_tie_input.currentText()
            r3_bars = self.r3_bars_input.value()
            r2_bars = self.r2_bars_input.value()

            # 2. Crear objetos de material (igual que antes)
            conc_mat = ConcreteMaterial(f"Concreto f'c={fc}", fc)
            steel_mat = SteelMaterial(f"Acero fy={fy}", fy)
            tie_mat = SteelMaterial(f"Acero fy={fy_tie}", fy_tie)

            # 3. Crear el objeto RectangularColumn (igual que antes)
            self.column_object = RectangularColumn(
                b=b,
                h=h,
                cover=cover,
                concrete_material=conc_mat,
                rebar_number=rebar_main,
                r2_bars=r2_bars,
                r3_bars=r3_bars,
                rebar_material=steel_mat,
                tie_rebar=rebar_tie,
                tie_material=tie_mat,
            )

            # 4. MODIFICADO: Actualizar los gráficos
            # Ya no creamos una lista aquí, usamos la lista de la clase
            # que se llenó con la GUI.
            self.plot_canvas.plot(self.column_object, self.load_points_list)
            self.schematic_canvas.update_data(self.column_object)

            # 5. Activar el botón de exportar (igual que antes)
            self.export_button.setEnabled(True)

        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error al generar la columna")
            msg.setInformativeText(
                f"Ha ocurrido un error:\n{e}\n\nRevise los parámetros de entrada."
            )
            msg.setWindowTitle("Error de Cálculo")
            msg.exec_()

    def export_diagram(self):
        # ... (Esta función no cambia, déjala como estaba) ...
        if not self.column_object:
            QMessageBox.warning(self, "Error", "Primero debe generar un diagrama.")
            return
        filePath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Diagrama",
            "diagrama_interaccion.png",
            "Imágenes PNG (*.png);;Imágenes JPG (*.jpg);;Archivos PDF (*.pdf);;Todos los archivos (*)",
        )
        if filePath:
            try:
                self.plot_canvas.figure.savefig(filePath, bbox_inches="tight")
                QMessageBox.information(
                    self, "Éxito", f"Diagrama guardado en:\n{filePath}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error al Guardar", f"No se pudo guardar el archivo:\n{e}"
                )


# -----------------------------------------------------------------
# EJECUCIÓN DE LA APLICACIÓN
# -----------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    sys.exit(app.exec_())

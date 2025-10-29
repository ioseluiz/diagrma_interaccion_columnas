class Load:
    def __init__(self, name: str, type: str, magnitude: float, sign: str):
        self.name = name
        self.type = type
        self.magnitude = magnitude
        self.sign = sign


class LoadCombination:
    def __init__(self, name: str):
        self.name


class PuntoDeCarga:
    def __init__(self, name: str, Pu: float, Mu: float):
        """
        Representa un punto de carga factorizada (Pu, Mu) para graficar.

        Args:
            name (str): Nombre del punto (ej. "Combo 1.2D+1.6L")
            Pu (float): Carga axial factorizada (en **Toneladas**)
            Mu (float): Momento flector factorizado (en **Ton-m**)
        """
        self.name = name
        self.Pu = Pu
        self.Mu = Mu

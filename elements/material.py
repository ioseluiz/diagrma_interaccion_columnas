class Material:
    def __init__(self, name: str):
        self.name = name


class ConcreteMaterial(Material):
    def __init__(self, name: str, fc: float):
        self.name = name
        self.fc = fc
        self.Eu = 0.003  # Max Deformation Concrete

    def get_fc(self):
        return self.fc

    def get_Eu(self):
        return self.Eu


class SteelMaterial(Material):
    def __init__(self, name: str, fy: float):
        self.name = name
        self.fy = fy
        self.Es = 2100000  # kg/cm2

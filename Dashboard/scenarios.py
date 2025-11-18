"""
Escenarios predefinidos para simulación
"""

ESCENARIOS = {
    "prueba_rapida": {
        "nombre": "Prueba Rápida",
        "descripcion": "Prueba básica para verificar funcionamiento (1 min)",
        "num_vehiculos": 5,
        "T_simulacion": 4,
        "T_horizonte": 2,
        "fecha": "2024-09-15",
    },
    "demo_estandar": {
        "nombre": "Demo Estándar",
        "descripcion": "Visualización estándar para presentaciones (3 min)",
        "num_vehiculos": 20,
        "T_simulacion": 8,
        "T_horizonte": 4,
        "fecha": "2024-09-15",
    },
}

def obtener_escenario(nombre):
    """Obtiene la configuración de un escenario predefinido."""
    return ESCENARIOS.get(nombre, ESCENARIOS["demo_estandar"])

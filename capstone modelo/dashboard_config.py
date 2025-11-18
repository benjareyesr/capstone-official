"""
Configuración del Dashboard
Archivo para personalizar colores, estilos y parámetros de visualización
"""

# ============================================================================
# COLORES Y ESTILOS
# ============================================================================

COLORES = {
    'bateria_alta': 'green',      # >50%
    'bateria_media': 'yellow',    # 20-50%
    'bateria_baja': 'red',        # <20%
    'cargando': 'purple',         # En estación de carga
    'zona_normal': 'lightblue',   # Zonas sin estación
    'estacion': 'green',          # Estaciones de carga
}

# Umbrales de batería (porcentaje)
UMBRAL_BATERIA_ALTA = 50
UMBRAL_BATERIA_MEDIA = 20

# ============================================================================
# CONFIGURACIÓN DEL MAPA
# ============================================================================

MAPA_CONFIG = {
    'style': 'carto-positron',  # Opciones: 'carto-positron', 'open-street-map', 'carto-darkmatter'
    'center_lat': 40.75,
    'center_lon': -73.98,
    'zoom': 11.5,
    'height': 600,
}

# Tamaño de marcadores
TAMAÑO_ZONA = 8
TAMAÑO_ESTACION = 14
TAMAÑO_VEHICULO = 10

# Offset para evitar superposición de vehículos
OFFSET_VEHICULO = 0.001

# ============================================================================
# CONFIGURACIÓN DE GRÁFICOS
# ============================================================================

GRAFICOS_CONFIG = {
    'altura_utilidad': 250,
    'altura_bateria': 250,
    'bins_bateria': 10,
    'color_utilidad': 'green',
    'color_bateria': 'blue',
}

# ============================================================================
# VALORES POR DEFECTO
# ============================================================================

DEFAULTS = {
    'num_vehiculos': 20,
    'T_simulacion': 8,
    'T_horizonte': 4,
    'fecha': '2024-09-15',
}

# ============================================================================
# TEXTOS Y ETIQUETAS
# ============================================================================

TEXTOS = {
    'titulo_principal': '🚕 Dashboard - Vehículos Autónomos en Manhattan',
    'titulo_config': '⚙️ Configuración',
    'titulo_metricas': 'Métricas del Sistema',
    'boton_ejecutar': '▶️ Ejecutar Simulación',
    'boton_anterior': '⬅️ Anterior',
    'boton_siguiente': 'Siguiente ➡️',
}

# ============================================================================
# TOOLTIPS Y MENSAJES
# ============================================================================

TOOLTIPS = {
    'num_vehiculos': 'Número de vehículos a simular (menor número = más rápido)',
    'T_simulacion': 'Número total de periodos a simular (cada periodo = 15 min)',
    'T_horizonte': 'Ventana de tiempo para optimización (más grande = mejor pero más lento)',
    'fecha': 'Fecha para cargar demanda histórica',
}

MENSAJES = {
    'ejecutando': 'Ejecutando simulación... Esto puede tomar varios minutos.',
    'completado': '✅ Simulación completada!',
    'sin_datos': '👈 Configura los parámetros en el panel lateral y presiona "Ejecutar Simulación"',
    'error_gurobi': '❌ Error en Gurobi. Verifica tu licencia.',
    'error_datos': '❌ Error cargando datos. Verifica que los archivos existan.',
}

"""
Configuraciones predefinidas para diferentes escenarios de simulación
Usar estos presets en el dashboard para análisis específicos
"""

# ============================================================================
# ESCENARIOS PREDEFINIDOS
# ============================================================================

ESCENARIOS = {
    "prueba_rapida": {
        "nombre": "Prueba Rápida",
        "descripcion": "Prueba básica para verificar funcionamiento (1 min)",
        "num_vehiculos": 5,
        "T_simulacion": 4,
        "T_horizonte": 2,
        "fecha": "2024-09-15",
        "icono": "🧪"
    },
    
    "demo_estandar": {
        "nombre": "Demo Estándar",
        "descripcion": "Visualización estándar para presentaciones (3 min)",
        "num_vehiculos": 20,
        "T_simulacion": 8,
        "T_horizonte": 4,
        "fecha": "2024-09-15",
        "icono": "🎯"
    },
    
    "analisis_matutino": {
        "nombre": "Análisis Matutino",
        "descripcion": "Foco en horas pico de la mañana (6-10 AM)",
        "num_vehiculos": 30,
        "T_simulacion": 16,  # 4 horas, 16 periodos de 15 min
        "T_horizonte": 6,
        "fecha": "2024-09-15",
        "periodo_inicio": 24,  # 6 AM (24 * 15min = 360min = 6h)
        "icono": "🌅"
    },
    
    "hora_punta_tarde": {
        "nombre": "Hora Punta Tarde",
        "descripcion": "Análisis de tráfico vespertino (16-20h)",
        "num_vehiculos": 40,
        "T_simulacion": 16,
        "T_horizonte": 6,
        "fecha": "2024-09-15",
        "periodo_inicio": 64,  # 4 PM
        "icono": "🌆"
    },
    
    "fin_de_semana": {
        "nombre": "Fin de Semana",
        "descripcion": "Comportamiento en sábado",
        "num_vehiculos": 25,
        "T_simulacion": 12,
        "T_horizonte": 4,
        "fecha": "2024-09-21",  # Sábado
        "icono": "🎉"
    },
    
    "noche": {
        "nombre": "Operación Nocturna",
        "descripcion": "Demanda nocturna (22h-2AM)",
        "num_vehiculos": 15,
        "T_simulacion": 16,
        "T_horizonte": 4,
        "fecha": "2024-09-15",
        "periodo_inicio": 88,  # 10 PM
        "icono": "🌙"
    },
    
    "stress_test": {
        "nombre": "Stress Test",
        "descripcion": "Prueba con más vehículos y periodos (15 min)",
        "num_vehiculos": 50,
        "T_simulacion": 20,
        "T_horizonte": 6,
        "fecha": "2024-09-15",
        "icono": "💪"
    },
    
    "dia_completo_lite": {
        "nombre": "Día Completo (Lite)",
        "descripcion": "Simulación de 12 horas con flota reducida (30 min)",
        "num_vehiculos": 30,
        "T_simulacion": 48,  # 12 horas
        "T_horizonte": 6,
        "fecha": "2024-09-15",
        "icono": "☀️"
    },
    
    "comparacion_lunes_viernes": {
        "nombre": "Lunes vs Viernes",
        "descripcion": "Para comparar patrones (ejecutar 2 veces)",
        "num_vehiculos": 25,
        "T_simulacion": 12,
        "T_horizonte": 4,
        "fecha": "2024-09-15",  # Lunes, cambiar a 2024-09-19 para Viernes
        "icono": "📊"
    },
}

# ============================================================================
# CONFIGURACIONES DE ESTACIONES
# ============================================================================

CONFIGS_ESTACIONES = {
    "estandar": {
        "nombre": "Configuración Estándar",
        "zonas": [87, 116, 137, 151, 128, 186],
        "capacidad": 55,
        "tiempo_carga": 2
    },
    
    "alta_capacidad": {
        "nombre": "Alta Capacidad",
        "zonas": [87, 116, 137, 151, 128, 186],
        "capacidad": 80,
        "tiempo_carga": 2
    },
    
    "carga_rapida": {
        "nombre": "Carga Rápida",
        "zonas": [87, 116, 137, 151, 128, 186],
        "capacidad": 55,
        "tiempo_carga": 1
    },
    
    "red_extendida": {
        "nombre": "Red Extendida",
        "zonas": [87, 116, 137, 151, 128, 186, 100, 230, 163],  # 3 adicionales
        "capacidad": 45,
        "tiempo_carga": 2
    },
    
    "red_minima": {
        "nombre": "Red Mínima",
        "zonas": [87, 116, 137],  # Solo 3 estaciones
        "capacidad": 70,
        "tiempo_carga": 2
    }
}

# ============================================================================
# CONFIGURACIONES DE DEMANDA
# ============================================================================

CONFIGS_DEMANDA = {
    "demanda_real": {
        "nombre": "Demanda Real (5%)",
        "porcentaje": 0.05,
        "descripcion": "5% de la demanda histórica real"
    },
    
    "demanda_baja": {
        "nombre": "Demanda Baja (2%)",
        "porcentaje": 0.02,
        "descripcion": "Escenario de baja demanda"
    },
    
    "demanda_media": {
        "nombre": "Demanda Media (7%)",
        "porcentaje": 0.07,
        "descripcion": "Escenario de demanda media"
    },
    
    "demanda_alta": {
        "nombre": "Demanda Alta (10%)",
        "porcentaje": 0.10,
        "descripcion": "Escenario de alta demanda"
    },
    
    "demanda_extrema": {
        "nombre": "Demanda Extrema (15%)",
        "porcentaje": 0.15,
        "descripcion": "Stress test de capacidad"
    }
}

# ============================================================================
# EXPERIMENTOS PREDEFINIDOS
# ============================================================================

EXPERIMENTOS = {
    "exp_1_capacidad_estaciones": {
        "nombre": "Experimento 1: Impacto de Capacidad de Estaciones",
        "objetivo": "Evaluar cómo la capacidad de estaciones afecta la operación",
        "escenarios": [
            {
                "config": "demo_estandar",
                "estaciones": "estandar",
                "nombre": "Baseline (Cap: 55)"
            },
            {
                "config": "demo_estandar",
                "estaciones": "alta_capacidad",
                "nombre": "Alta Cap (80)"
            },
            {
                "config": "demo_estandar",
                "estaciones": "red_minima",
                "nombre": "Pocas Estaciones (70)"
            }
        ],
        "metricas_clave": ["utilidad_acumulada", "vehiculos_cargando_promedio", "bateria_promedio"]
    },
    
    "exp_2_hora_del_dia": {
        "nombre": "Experimento 2: Variación por Hora del Día",
        "objetivo": "Comparar operación en diferentes momentos del día",
        "escenarios": [
            {
                "config": "analisis_matutino",
                "nombre": "Mañana (6-10 AM)"
            },
            {
                "config": "demo_estandar",
                "nombre": "Medio Día (12-4 PM)"
            },
            {
                "config": "hora_punta_tarde",
                "nombre": "Hora Punta (4-8 PM)"
            },
            {
                "config": "noche",
                "nombre": "Noche (10 PM-2 AM)"
            }
        ],
        "metricas_clave": ["utilidad_por_vehiculo", "demanda_satisfecha", "viajes_totales"]
    },
    
    "exp_3_tamaño_flota": {
        "nombre": "Experimento 3: Tamaño Óptimo de Flota",
        "objetivo": "Determinar el número óptimo de vehículos",
        "escenarios": [
            {"config": "demo_estandar", "num_vehiculos": 10, "nombre": "Flota Pequeña"},
            {"config": "demo_estandar", "num_vehiculos": 20, "nombre": "Flota Media"},
            {"config": "demo_estandar", "num_vehiculos": 30, "nombre": "Flota Grande"},
            {"config": "demo_estandar", "num_vehiculos": 40, "nombre": "Flota Extra"}
        ],
        "metricas_clave": ["utilidad_total", "utilidad_por_vehiculo", "ocupacion_promedio"]
    },
    
    "exp_4_carga_rapida": {
        "nombre": "Experimento 4: Beneficio de Carga Rápida",
        "objetivo": "Evaluar impacto de reducir tiempo de carga",
        "escenarios": [
            {
                "config": "demo_estandar",
                "estaciones": "estandar",
                "nombre": "Carga Normal (2 periodos)"
            },
            {
                "config": "demo_estandar",
                "estaciones": "carga_rapida",
                "nombre": "Carga Rápida (1 periodo)"
            }
        ],
        "metricas_clave": ["tiempo_carga_total", "vehiculos_cargando_promedio", "utilidad"]
    }
}

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def obtener_escenario(nombre):
    """Obtiene la configuración de un escenario predefinido."""
    return ESCENARIOS.get(nombre, ESCENARIOS["demo_estandar"])

def listar_escenarios():
    """Lista todos los escenarios disponibles."""
    return [
        {
            "id": key,
            "nombre": val["nombre"],
            "descripcion": val["descripcion"],
            "icono": val["icono"]
        }
        for key, val in ESCENARIOS.items()
    ]

def obtener_config_estaciones(nombre):
    """Obtiene configuración de estaciones."""
    return CONFIGS_ESTACIONES.get(nombre, CONFIGS_ESTACIONES["estandar"])

def obtener_config_demanda(nombre):
    """Obtiene configuración de demanda."""
    return CONFIGS_DEMANDA.get(nombre, CONFIGS_DEMANDA["demanda_real"])

# ============================================================================
# RECOMENDACIONES DE USO
# ============================================================================

RECOMENDACIONES = {
    "presentacion": [
        "demo_estandar",
        "analisis_matutino",
        "fin_de_semana"
    ],
    
    "desarrollo": [
        "prueba_rapida",
        "demo_estandar"
    ],
    
    "analisis_profundo": [
        "stress_test",
        "dia_completo_lite",
        "hora_punta_tarde"
    ],
    
    "comparacion": [
        "comparacion_lunes_viernes",
        "exp_2_hora_del_dia"
    ]
}

# Ejemplo de uso:
# from escenarios_predefinidos import obtener_escenario
# config = obtener_escenario("demo_estandar")
# num_vehiculos = config["num_vehiculos"]
# T_simulacion = config["T_simulacion"]

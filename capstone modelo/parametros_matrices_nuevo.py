import pandas as pd
import numpy as np
import math
from pathlib import Path
import calendar

# ---------------------------------------------------------------------------
# 1. CONSTANTES GLOBALES
# ---------------------------------------------------------------------------

NUMERO_VEHICULOS = 4
AUTONOMIA_VEHICULO = 12
TIEMPO_RECARGA_PERIODOS = 8 # 110 minutos, 8 periodos
PERIODO_SIMULACION = 15 # minutos por periodo
BATERIA_MINIMA = 6
ZONAS_ESTACIONES_CARGA = [87, 116, 137, 151, 128, 186]
CAPACIDAD_MAXIMA_ESTACION = 55
COSTO_REUBICACION_MULTIPLIER = 1.25
PORCENTAJE_DEMANDA = 0.4 # Porcentaje de la demanda total a considerar

# ---------------------------------------------------------------------------
# 2. LÓGICA DE ZONAS Y MAPEO
# ---------------------------------------------------------------------------

ZONAS_MANHATTAN = [
    4, 12, 13, 24, 41, 42, 43, 45, 48, 50, 68, 74, 75, 79, 87, 88, 90, 100, 
    103, 107, 113, 114, 116, 120, 125, 127, 128, 137, 140, 141, 142, 143, 144, 
    148, 151, 152, 153, 158, 161, 162, 163, 164, 166, 170, 186, 194, 202, 209, 
    211, 224, 229, 230, 231, 232, 233, 234, 236, 237, 238, 239, 243, 244, 246, 
    249, 261, 262, 263
]
ZONAS_EQUIVALENTES = {104: 103, 105: 103}
def normalizar_zona(zona_id):
    return ZONAS_EQUIVALENTES.get(zona_id, zona_id)
ZONA_A_INDICE = {zona: i for i, zona in enumerate(ZONAS_MANHATTAN)}
INDICE_A_ZONA = {i: zona for i, zona in enumerate(ZONAS_MANHATTAN)}
N_ZONAS = len(ZONAS_MANHATTAN)

# ---------------------------------------------------------------------------
# 3. LECTURA DE CSV
# ---------------------------------------------------------------------------

def generar_matrices_base():
    # Ruta relativa al proyecto para la matriz de distancias y tiempos
    base_dir = Path(__file__).resolve().parent.parent
    ruta_csv = base_dir / 'Distancias zonas' / 'distancias_manhattan_zonas_con_tiempo_ingreso.csv'
    df = pd.read_csv(ruta_csv)
    matriz_distancias = np.zeros((N_ZONAS, N_ZONAS))
    matriz_tiempos_normal = np.zeros((N_ZONAS, N_ZONAS))
    matriz_tiempos_punta = np.zeros((N_ZONAS, N_ZONAS))
    matriz_tiempos_valle = np.zeros((N_ZONAS, N_ZONAS))
    matriz_ingresos = np.zeros((N_ZONAS, N_ZONAS))
    for _, row in df.iterrows():
        origen_id = int(row['origen_id'])
        destino_id = int(row['destino_id'])
        i = ZONA_A_INDICE[origen_id]
        j = ZONA_A_INDICE[destino_id]
        matriz_distancias[i][j] = row['distancia_km']
        matriz_tiempos_normal[i][j] = row['duracion_normal_min']
        matriz_tiempos_punta[i][j] = row['duracion_hora_punta_min']
        matriz_tiempos_valle[i][j] = row['duracion_hora_valle_min']
        matriz_ingresos[i][j] = row['ingreso_viaje_usd']
    return (matriz_distancias, matriz_tiempos_normal, matriz_tiempos_punta, 
            matriz_tiempos_valle, matriz_ingresos)

# ---------------------------------------------------------------------------
# 4. FUNCIÓN PRINCIPAL DE CARGA DE PARÁMETROS
# ---------------------------------------------------------------------------

def obtener_tipo_hora(t):
    """Devuelve 'punta', 'valle' o 'normal' según el período t"""
    hora_periodo = (t * PERIODO_SIMULACION) // 60
    if 0 <= hora_periodo <= 7:
        return 'valle'
    elif 16 <= hora_periodo <= 20:
        return 'punta'
    else:
        return 'normal'

def cargar_demanda_pronostico(T_total, fecha_dia_str):
    """
    Carga la demanda PROMEDIO (pronóstico) desde el CSV
    basado en el día de la semana de la fecha_dia_str.
    """
    print(f"Cargando demanda de PRONÓSTICO basado en el día tipo de {fecha_dia_str}...")
    # 1. Determinar el tipo de día (LUN, MAR_JUE, etc.)
    fecha = pd.Timestamp(fecha_dia_str)
    weekday = fecha.weekday() # 0=Lunes, 6=Domingo
    mapa_dia_grupo = {
        0: "LUN", 1: "MAR_JUE", 2: "MAR_JUE", 3: "MAR_JUE",
        4: "VIERNES", 5: "SABADO", 6: "DOMINGO"
    }
    tipo_dia_filtro = mapa_dia_grupo[weekday]
    print(f"Día de la semana detectado: {calendar.day_name[weekday]} (Grupo: {tipo_dia_filtro})")
    # 2. Cargar el CSV de pronóstico O-D
    base_dir = Path(__file__).resolve().parent.parent
    ruta_csv = base_dir / 'Datos' / 'lambda_zonal_OD_mat_full.csv'
    
    
    try:
        df_lambda = pd.read_csv(ruta_csv)
    except FileNotFoundError:
        print(f"ERROR: No se encontró 'lambda_zonal_OD_mat.csv'")
        raise

    # 3. Filtrar por el tipo de día
    df_lambda = df_lambda[df_lambda['tipo_dia_fino'] == tipo_dia_filtro]
    
    # 4. Convertir a la matriz (N, N, T)
    matriz_dem_pronostico = np.zeros((N_ZONAS, N_ZONAS, T_total))
    
    # Renombrar columnas de bucket (0, 1, ... 95) a enteros
    df_lambda.columns = [int(c) if c.isdigit() else c for c in df_lambda.columns]
    
    for _, row in df_lambda.iterrows():
        try:
            origen_id = normalizar_zona(int(row['PUlocationID']))
            destino_id = normalizar_zona(int(row['DOlocationID']))
            
            i = ZONA_A_INDICE[origen_id]
            j = ZONA_A_INDICE[destino_id]
            
            # (El filtro i != j ya se hizo al crear el CSV, pero por si acaso)
            if i != j:
                for t in range(T_total):
                    if t in df_lambda.columns:
                        # Redondear a entero (Poisson espera λ pero Gurobi necesita int)
                        matriz_dem_pronostico[i, j, t] = round(row[t])
        except (KeyError, ValueError):
            # Ignora zonas si no están en ZONAS_MANHATTAN o si hay un error de ID
            pass
            
    print("Carga de pronóstico completada.")
    return matriz_dem_pronostico

def cargar_parametros_modelo(T_total=4, fecha_dia_str='2024-09-15'):
    # Carga y pre-calcula TODOS los parámetros para el modelo Gurobi.
    print("Iniciando carga de parámetros...")

    # 1. Generar matrices base desde CSV
    (MATRIZ_DISTANCIAS, MATRIZ_TIEMPOS_NORMAL, MATRIZ_TIEMPOS_PUNTA, 
     MATRIZ_TIEMPOS_VALLE, MATRIZ_INGRESOS) = generar_matrices_base()

    # 2. Crear diccionario de parámetros p
    p = {}

    # 3. Nombres de parámetros más simples para que sea más fácil hacer el modelo
    p['T'] = T_total
    p['N'] = N_ZONAS
    p['A'] = NUMERO_VEHICULOS
    p['Tchg'] = TIEMPO_RECARGA_PERIODOS
    p['E_min'] = BATERIA_MINIMA
    p['Cargamax'] = AUTONOMIA_VEHICULO
    p['CapEstacion'] = CAPACIDAD_MAXIMA_ESTACION
    #p['d'] = np.round(MATRIZ_DISTANCIAS).astype(int)
    p['d'] = MATRIZ_DISTANCIAS

    # --------------------------------------------------------------------
    # 4. Cargar Demanda p.Dem[i][j][t]
    # --------------------------------------------------------------------
    print(f"Cargando demanda real para el día {fecha_dia_str}...")
    
    # 4a. Cargar archivo Parquet
    # Ruta relativa al proyecto para el archivo parquet de demanda
    base_dir = Path(__file__).resolve().parent.parent
    archivo_reducido = base_dir / 'Datos' / 'df_all_reducido_github.parquet'
    try:
        df_all = pd.read_parquet(archivo_reducido)
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo de demanda: {archivo_reducido}")
    df_all['pickup_datetime'] = pd.to_datetime(df_all['pickup_datetime'])

    # 4b. Filtrar por día
    fecha_dia = pd.Timestamp(fecha_dia_str)
    inicio_dia = fecha_dia
    fin_dia = fecha_dia + pd.Timedelta(days=1)
    df_dia = df_all[
        (df_all['pickup_datetime'] >= inicio_dia) & 
        (df_all['pickup_datetime'] < fin_dia)
    ]

    # 4c. Crear matriz de demanda y procesar. Usamos los parámetros p['N'] (67) y p['T'] (96)
    p['Dem'] = np.zeros((p['N'], p['N'], p['T']), dtype=int)
    for periodo in range(p['T']):
        hora = (periodo * PERIODO_SIMULACION) // 60
        min_inicio = (periodo * PERIODO_SIMULACION) % 60
        
        fecha_inicio = inicio_dia + pd.Timedelta(hours=hora, minutes=min_inicio)
        fecha_fin = fecha_inicio + pd.Timedelta(minutes=PERIODO_SIMULACION)
        
        viajes_periodo = df_dia[
            (df_dia['pickup_datetime'] >= fecha_inicio) & 
            (df_dia['pickup_datetime'] <= fecha_fin)
        ]
        
        # Aplicar porcentaje de demanda
        n_viajes = max(1, int(len(viajes_periodo) * PORCENTAJE_DEMANDA))
        if len(viajes_periodo) > 0:
            viajes_muestra = viajes_periodo.sample(n=min(n_viajes, len(viajes_periodo)), random_state=123+periodo)
        else:
            viajes_muestra = viajes_periodo
            
        # Contar viajes por par origen-destino
        # No cuenta la demanda de una zona a sí misma
        for _, row in viajes_muestra.iterrows():
            try:
                # Usar normalización para buscar el índice
                origen_id = normalizar_zona(int(row['PUlocationID']))
                destino_id = normalizar_zona(int(row['DOlocationID']))
    
                i = ZONA_A_INDICE[origen_id]
                j = ZONA_A_INDICE[destino_id]
                # Solo suma la demanda si el origen y el destino son DIFERENTES
                if i != j:
                    p['Dem'][i, j, periodo] += 1
            except KeyError:
                # Ignora viajes si el ID (ya normalizado) no está en ZONAS_MANHATTAN
                pass
    print("Carga de demanda completada.")

    
    p['Dem_Pronostico'] = cargar_demanda_pronostico(T_total, fecha_dia_str)


    # 5. Convertir IDs de Estación a ÍNDICES
    p['E'] = set() 
    for zona_id in ZONAS_ESTACIONES_CARGA:
        if zona_id in ZONA_A_INDICE:
            p['E'].add(ZONA_A_INDICE[zona_id])
    print(f"Estaciones de carga (índices): {p['E']}")

    # 6. Pre-calcular Precios y Costos [i][j][t]
    p['Pviaje'] = np.zeros((N_ZONAS, N_ZONAS, T_total))
    p['Creub'] = np.zeros((N_ZONAS, N_ZONAS, T_total))
    p['Pviaje_Pronostico'] = np.zeros((N_ZONAS, N_ZONAS, T_total))
    p['Creub_Pronostico'] = np.zeros((N_ZONAS, N_ZONAS, T_total))
    for i in range(N_ZONAS):
        for j in range(N_ZONAS):
            precio = MATRIZ_INGRESOS[i, j]
            costo = precio * COSTO_REUBICACION_MULTIPLIER
            for t in range(T_total):
                p['Pviaje'][i, j, t] = precio
                p['Creub'][i, j, t] = costo
                p['Pviaje_Pronostico'][i, j, t] = precio # Usar el mismo precio
                p['Creub_Pronostico'][i, j, t] = costo  # Usar el mismo costo
                

    # 7. Pre-calcular Mapa de Llegadas IMPORTANTE!
    print("Iniciando pre-cálculo del mapa de llegadas...")
    mapa_llegadas_viaje = {}
    
    for k_inicio in range(T_total):
        tipo_hora = obtener_tipo_hora(k_inicio)
        
        if tipo_hora == 'valle':
            matriz_tiempo = MATRIZ_TIEMPOS_VALLE
        elif tipo_hora == 'punta':
            matriz_tiempo = MATRIZ_TIEMPOS_PUNTA
        else:
            matriz_tiempo = MATRIZ_TIEMPOS_NORMAL

        for j_idx in range(N_ZONAS): # j = origen
            for i_idx in range(N_ZONAS): # i = destino
                if i_idx == j_idx: continue
                tiempo_min = matriz_tiempo[j_idx, i_idx]
                duracion_periodos = int(math.ceil(tiempo_min / PERIODO_SIMULACION))
                k_llegada = k_inicio + duracion_periodos
                if k_llegada < T_total: 
                    clave = (j_idx, i_idx, k_llegada)
                    if clave not in mapa_llegadas_viaje:
                        mapa_llegadas_viaje[clave] = []
                    mapa_llegadas_viaje[clave].append(k_inicio)
                    
    p['mapa_llegadas'] = mapa_llegadas_viaje
    print("Pre-cálculo de llegadas completado.")
    
    print("--- Carga de parámetros finalizada ---")
    return p
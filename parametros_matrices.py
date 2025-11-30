import pandas as pd
import numpy as np

# Lista ordenada de todas las zonas de Manhattan disponibles (67 zonas)
ZONAS_MANHATTAN = [
    4, 12, 13, 24, 41, 42, 43, 45, 48, 50, 68, 74, 75, 79, 87, 88, 90, 100, 
    103, 107, 113, 114, 116, 120, 125, 127, 128, 137, 140, 141, 142, 143, 144, 
    148, 151, 152, 153, 158, 161, 162, 163, 164, 166, 170, 186, 194, 202, 209, 
    211, 224, 229, 230, 231, 232, 233, 234, 236, 237, 238, 239, 243, 244, 246, 
    249, 261, 262, 263
]

# Mapeo de zonas equivalentes
# Zonas que representan la misma ubicación física pero con IDs diferentes
ZONAS_EQUIVALENTES = {
    104: 103,  # Governor's Island/Ellis Island/Liberty Island
    105: 103,  # Governor's Island/Ellis Island/Liberty Island
}

def normalizar_zona(zona_id):
    #Convierte zona_id a su equivalente en caso de que sea una zona alternativa
    return ZONAS_EQUIVALENTES.get(zona_id, zona_id)

# Diccionario para mapear ID de zona a índice en las matrices
ZONA_A_INDICE = {zona: i for i, zona in enumerate(ZONAS_MANHATTAN)}
# Diccionario para mapear índice a ID de zona
INDICE_A_ZONA = {i: zona for i, zona in enumerate(ZONAS_MANHATTAN)}
# Número total de zonas
N_ZONAS = len(ZONAS_MANHATTAN)



# Generar matrices desde CSV
def generar_matrices():
    # desde el archivo csv    
    # Cargar datos del CSV
    ruta_csv = '/Users/jmatas/Documents/capstone/Distancias zonas/distancias_manhattan_zonas_con_tiempo_ingreso.csv'
    df = pd.read_csv(ruta_csv)
    # Inicializar matrices con ceros
    matriz_distancias = np.zeros((N_ZONAS, N_ZONAS))
    matriz_tiempos_normal = np.zeros((N_ZONAS, N_ZONAS))
    matriz_tiempos_punta = np.zeros((N_ZONAS, N_ZONAS))
    matriz_tiempos_valle = np.zeros((N_ZONAS, N_ZONAS))
    matriz_ingresos = np.zeros((N_ZONAS, N_ZONAS))

    for _, row in df.iterrows():
        origen_id = int(row['origen_id'])
        destino_id = int(row['destino_id'])
        # Obtener índices en las matrices
        i = ZONA_A_INDICE[origen_id]
        j = ZONA_A_INDICE[destino_id]
        # Llenar matrices
        matriz_distancias[i][j] = row['distancia_km']
        matriz_tiempos_normal[i][j] = row['duracion_normal_min']
        matriz_tiempos_punta[i][j] = row['duracion_hora_punta_min']
        matriz_tiempos_valle[i][j] = row['duracion_hora_valle_min']
        matriz_ingresos[i][j] = row['ingreso_viaje_usd']
    return (matriz_distancias, matriz_tiempos_normal, matriz_tiempos_punta, 
            matriz_tiempos_valle, matriz_ingresos)


(MATRIZ_DISTANCIAS, MATRIZ_TIEMPOS_NORMAL, MATRIZ_TIEMPOS_PUNTA, 
 MATRIZ_TIEMPOS_VALLE, MATRIZ_INGRESOS) = generar_matrices()



# Funciones útiles

def obtener_distancia(zona_origen, zona_destino):
    """Obtiene distancia entre dos zonas usando las matrices"""
    # Normalizar zonas a sus equivalentes
    zona_origen = normalizar_zona(zona_origen)
    zona_destino = normalizar_zona(zona_destino)
    
    i = ZONA_A_INDICE[zona_origen]
    j = ZONA_A_INDICE[zona_destino]
    return MATRIZ_DISTANCIAS[i][j]

def obtener_tiempo(zona_origen, zona_destino, tipo_hora='normal'):
    """Obtiene tiempo de viaje entre dos zonas según tipo de hora"""
    # Normalizar zonas a sus equivalentes
    zona_origen = normalizar_zona(zona_origen)
    zona_destino = normalizar_zona(zona_destino)
    
    i = ZONA_A_INDICE[zona_origen]
    j = ZONA_A_INDICE[zona_destino]
    if tipo_hora == 'normal':
        return MATRIZ_TIEMPOS_NORMAL[i][j]
    elif tipo_hora == 'punta':
        return MATRIZ_TIEMPOS_PUNTA[i][j]
    elif tipo_hora == 'valle':
        return MATRIZ_TIEMPOS_VALLE[i][j]
    else:
        raise ValueError(f"Tipo de hora inválido: {tipo_hora}")

def obtener_ingreso(zona_origen, zona_destino):
    """Obtiene ingreso estimado del viaje entre dos zonas"""
    # Normalizar zonas a sus equivalentes
    zona_origen = normalizar_zona(zona_origen)
    zona_destino = normalizar_zona(zona_destino)
    
    i = ZONA_A_INDICE[zona_origen]
    j = ZONA_A_INDICE[zona_destino]
    return MATRIZ_INGRESOS[i][j]


#Prubea funcionamiento:
#a = obtener_distancia(186, 244)
#b = obtener_ingreso(186, 244)
#c = obtener_tiempo(186, 244, 'punta')
#d = obtener_tiempo(103, 4, 'punta')
#e = obtener_ingreso(105, 103)
#print(a)
#print(b)
#print(d)
#print(c)
#print(e)    
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import holidays

# Directorio base del proyecto (carpeta donde está este script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


manhattan_ids = [4, 12, 13, 24, 41, 42, 43, 45, 48, 50, 68, 74, 75, 79,
                 87, 88, 90, 100, 103, 104, 105, 107, 113, 114,
                 116, 120, 125, 127, 128, 137, 140, 141, 142, 143,
                 144, 148, 151, 152, 153, 158, 161, 162, 163, 164,
                 166, 170, 186, 194, 202, 209, 211, 224, 229, 230, 231,
                 232, 233, 234, 236, 237, 238, 239, 243, 244, 246, 249,
                 261, 262, 263]

print(len(manhattan_ids))

ruta_taxi_2024 = os.path.join(BASE_DIR, "Datos", "Datos viajes", "Datos taxi amarillo", "2024")
meses_2024 = ["07","08","09","10","11","12"]
archivos_taxi_2024 = [os.path.join(ruta_taxi_2024, f"yellow_tripdata_2024-{m}.parquet")
                      for m in meses_2024]
dfs = []
for archivo in archivos_taxi_2024:
    df_temp = pd.read_parquet(archivo)
    df_temp = df_temp[
        (df_temp["PULocationID"].isin(manhattan_ids)) & 
        (df_temp["DOLocationID"].isin(manhattan_ids))
    ].copy()
    df_temp['tpep_pickup_datetime'] = pd.to_datetime(df_temp['tpep_pickup_datetime'])
    df_temp['month'] = df_temp['tpep_pickup_datetime'].dt.month
    df_temp['weekday'] = df_temp['tpep_pickup_datetime'].dt.day_name()
    dfs.append(df_temp)

df_all_taxi_2024 = pd.concat(dfs, ignore_index=True)
df_all_taxi_2024 = df_all_taxi_2024[df_all_taxi_2024['month'].between(7, 12)]

ruta_taxi_2025 = os.path.join(BASE_DIR, "Datos", "Datos viajes", "Datos taxi amarillo", "2025")
archivos_taxi_2025 = sorted(glob.glob(os.path.join(ruta_taxi_2025, "yellow_tripdata_2025-0[1-6].parquet")))
dfs = []
for archivo in archivos_taxi_2025:
    df_temp = pd.read_parquet(archivo)
    df_temp = df_temp[
        (df_temp["PULocationID"].isin(manhattan_ids)) & 
        (df_temp["DOLocationID"].isin(manhattan_ids))
    ].copy()
    df_temp['tpep_pickup_datetime'] = pd.to_datetime(df_temp['tpep_pickup_datetime'])
    df_temp['month'] = df_temp['tpep_pickup_datetime'].dt.month
    df_temp['weekday'] = df_temp['tpep_pickup_datetime'].dt.day_name()
    dfs.append(df_temp)

df_all_taxi_2025 = pd.concat(dfs, ignore_index=True)
df_all_taxi_2025 = df_all_taxi_2025[df_all_taxi_2025['month'].between(1, 6)]

# Agregar columna de año a cada base
df_all_taxi_2024['year'] = 2024
df_all_taxi_2025['year'] = 2025
# Unir bases
df_all_taxi = pd.concat([df_all_taxi_2024, df_all_taxi_2025], ignore_index=True)

# Renombrar columnas clave para igualarlas con la de FHV
df_all_taxi = df_all_taxi.rename(columns={
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropOff_datetime",
    "PULocationID": "PUlocationID",
    "DOLocationID": "DOlocationID"
})
# Seleccionar solo las columnas que nos interesan
df_all_taxi = df_all_taxi[[
    "pickup_datetime", "dropOff_datetime", "PUlocationID", "DOlocationID", "month", "weekday", "year"
]]

# Cargar y unir los 6 archivos de meses
fhv_2025_dir = os.path.join(BASE_DIR, "Datos", "Datos viajes", "FHV", "2025")
archivos = sorted(glob.glob(os.path.join(fhv_2025_dir, "fhv_tripdata_2025-0[1-6].parquet")))
dfs = []
for archivo in archivos:
    df_temp = pd.read_parquet(archivo)
    df_temp = df_temp[
        (df_temp["PUlocationID"].isin(manhattan_ids)) & 
        (df_temp["DOlocationID"].isin(manhattan_ids))
    ].copy()
    df_temp['pickup_datetime'] = pd.to_datetime(df_temp['pickup_datetime'])
    df_temp['month'] = df_temp['pickup_datetime'].dt.month
    df_temp['weekday'] = df_temp['pickup_datetime'].dt.day_name()
    dfs.append(df_temp)
df_all = pd.concat(dfs, ignore_index=True)

fhv_2024_dir = os.path.join(BASE_DIR, "Datos", "Datos viajes", "FHV", "2024")
archivos_2024 = sorted(glob.glob(os.path.join(fhv_2024_dir, "fhv_tripdata_2024-*.parquet")))
dfs = []
for archivo in archivos_2024:
    df_temp = pd.read_parquet(archivo)
    df_temp = df_temp[
        (df_temp["PUlocationID"].isin(manhattan_ids)) & 
        (df_temp["DOlocationID"].isin(manhattan_ids))
    ].copy()
    df_temp['pickup_datetime'] = pd.to_datetime(df_temp['pickup_datetime'])
    df_temp['month'] = df_temp['pickup_datetime'].dt.month
    df_temp['weekday'] = df_temp['pickup_datetime'].dt.day_name()
    dfs.append(df_temp)
df_all_2024 = pd.concat(dfs, ignore_index=True)

# Limpiar y agregar columna year
fhv_2024_clean = df_all_2024[['pickup_datetime','dropOff_datetime',
                              'PUlocationID','DOlocationID','month','weekday']].copy()
fhv_2024_clean['year'] = fhv_2024_clean['pickup_datetime'].dt.year
fhv_2024_clean = fhv_2024_clean[fhv_2024_clean['month'].between(7,12)]

fhv_2025_clean = df_all[['pickup_datetime','dropOff_datetime',
                         'PUlocationID','DOlocationID','month','weekday']].copy()
fhv_2025_clean['year'] = fhv_2025_clean['pickup_datetime'].dt.year
fhv_2025_clean = fhv_2025_clean[fhv_2025_clean['month'].between(1,6)]

# Concatenar en uno solo
fhv_all = pd.concat([fhv_2024_clean, fhv_2025_clean], ignore_index=True)

# 1) FHV 
fhv_all['tipo'] = 'fhv'
# 2) Taxi amarillo
df_all_taxi['tipo'] = 'taxi'
# 3) Unir ambas bases
df_all = pd.concat([fhv_all, df_all_taxi], ignore_index=True)

# Asegurar datetime
df_all['pickup_datetime'] = pd.to_datetime(df_all['pickup_datetime'])
df_all['date'] = df_all['pickup_datetime'].dt.date

# Crear conjunto de feriados en USA (ej: New York)
us_holidays = holidays.US(years=df_all['pickup_datetime'].dt.year.unique(), state='NY')
# Filtrar quitando feriados
df_all = df_all[~df_all['date'].isin(us_holidays)]

print(df_all[['year','month','tipo']].value_counts().sort_index())

# Exportar a parquet completo
output_dir = os.path.join(BASE_DIR, "Datos")
df_all.to_parquet(os.path.join(output_dir, "df_all_procesado.parquet"), index=False)
print("Dataset completo exportado a:", os.path.join("Datos", "df_all_procesado.parquet"))

# GENERAR ARCHIVO REDUCIDO PARA GITHUB
# Filtrar solo el día que usamos en el modelo (2024-09-15) y días cercanos para tener más datos
fecha_objetivo = pd.to_datetime('2024-09-15').date()
fecha_inicio = pd.to_datetime('2024-09-14').date()  # Día anterior
fecha_fin = pd.to_datetime('2024-09-16').date()     # Día siguiente

# Filtrar datos de esos 3 días
df_reducido = df_all[df_all['date'].between(fecha_inicio, fecha_fin)].copy()

print(f"\nDataset reducido:")
print(f"Período: {fecha_inicio} a {fecha_fin}")
print(f"Registros originales: {len(df_all):,}")
print(f"Registros reducidos: {len(df_reducido):,}")
print(f"Reducción: {(1 - len(df_reducido)/len(df_all))*100:.1f}%")

# Exportar versión reducida para GitHub
df_reducido.to_parquet(os.path.join(output_dir, "df_all_reducido_github.parquet"), index=False)
print("Dataset reducido exportado a:", os.path.join("Datos", "df_all_reducido_github.parquet"))
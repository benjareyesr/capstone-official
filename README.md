# Capstone - Sistema de Optimización de Flota de Vehículos Eléctricos

## 📁 Estructura del Proyecto

### Carpeta `capstone modelo/`
Contiene los archivos principales del modelo de optimización:

- **`modelo_gurobi_rh.py`**: Modelo de optimización con Gurobi
  - ⚠️ **NO TOCAR** - Funciona perfectamente
  
- **`parametros_matrices_nuevo.py`**: Parámetros del modelo
  - ✅ **PUEDEN MODIFICAR**: Solo la sección **1. CONSTANTES GLOBALES**
  - ⚠️ **NO TOCAR**: El resto del archivo
  
- **`simulacion_rh.py`**: Simulación del horizonte rodante
  - ✅ **ESTE ES EL ARCHIVO QUE SE EJECUTA** para correr todo el sistema

### Carpeta `Datos/`
Contiene los datos necesarios para el modelo:

- **`df_all_reducido_github.parquet`**: Datos de demanda real (3 días: día objetivo ± 1 día)
  - Generado por `bdd.py`
  - Usado por `parametros_matrices_nuevo.py` para leer la demanda REAL
  
- **`lambda_zonal_OD_mat_representativo.csv`**: Datos de demanda pronosticada
  - Generado por el notebook `Forecast+SAA.ipynb`
  - Usado por `parametros_matrices_nuevo.py` para leer la demanda PRONOSTICADA

- **`df_all_procesado.parquet`**: Base de datos completa (julio 2024 - junio 2025)
  - ⚠️ **NO ESTÁ EN GITHUB** (archivo muy pesado)
  - Se genera ejecutando `bdd.py`
  - Necesario para ejecutar `Forecast+SAA.ipynb`

### Archivos Raíz

- **`bdd.py`**: Genera las bases de datos de viajes
- **`Forecast+SAA.ipynb`**: Genera el pronóstico de demanda

---

## 🚀 Cómo Ejecutar el Proyecto

### Primera Vez - Configuración Inicial

1. **Activar el ambiente virtual** (si existe):
   ```bash
   source .venv/bin/activate
   ```

2. **Generar la base de datos completa**:


### Ejecución Normal

**Para correr la simulación completa**:
```bash
cd "capstone modelo"
python simulacion_rh.py
```

**Para abrir el nuevo dashboard (Dash + Plotly)**:
```bash
pip install -r requirements.txt
python dash_app/app.py
```

---

## ⚙️ Configuración del Modelo

### Cambiar la Duración de la Simulación

En `simulacion_rh.py`, **línea 215**:

```python
K_TOTAL = 8     # Modifica este valor
```

**Importante**: La simulación ejecuta `K_TOTAL - 4` periodos (no `K_TOTAL` completo) porque en cada iteración se planifican los 4 periodos siguientes.

**Ejemplos**:
- `K_TOTAL = 8` → ejecuta **4 periodos** = **1 hora** (4 × 15 min)
- `K_TOTAL = 20` → ejecuta **16 periodos** = **4 horas** (16 × 15 min)
- `K_TOTAL = 96` → ejecuta **92 periodos** = **23 horas**

### Modificar Parámetros del Modelo

En `parametros_matrices_nuevo.py`, modificar solo la sección:

```python
# ============================================================
# 1. CONSTANTES GLOBALES
# ============================================================
```

✅ **Pueden cambiar**: Valores como número de autos, capacidad de batería, etc.  
⚠️ **NO tocar**: El resto del archivo

---

## 📊 Flujo de Datos

```
bdd.py
  ↓
  ├─→ df_all_procesado.parquet (completo, no en GitHub)
  └─→ df_all_reducido_github.parquet (3 días, en GitHub)

df_all_procesado.parquet
  ↓
Forecast+SAA.ipynb
  ↓
lambda_zonal_OD_mat_representativo.csv

df_all_reducido_github.parquet + lambda_zonal_OD_mat_representativo.csv
  ↓
parametros_matrices_nuevo.py
  ↓
simulacion_rh.py (← EJECUTAR ESTE)
  ↓
Resultados de la simulación
```

---

## 🛠️ Solución de Problemas

### Error: "No module named 'pandas'" (u otro módulo)
```bash
pip install pandas matplotlib seaborn holidays pyarrow gurobipy numpy
```

### Error: "FileNotFoundError" al ejecutar la simulación
Asegúrate de haber ejecutado `bdd.py` primero para generar los archivos de datos.

### La simulación tarda mucho
Reduce `K_TOTAL` en la línea 215 de `simulacion_rh.py` para hacer pruebas más rápidas.
## 🎯 Dashboard Dash (beta)

```bash
pip install -r requirements.txt
python dash_app/app.py
```

- Configura `K_TOTAL`, `T_HORIZONTE` y la fecha base desde la UI.
- El botón **“Ejecutar simulación”** ejecuta Gurobi (se requiere licencia activa).
- Gráficos disponibles:
   - Utilidad acumulada por periodo.
   - Barras apiladas con la distribución de acciones.
   - Heatmap de demanda no servida agregada.
   - Tabla con el detalle de vehículos para el periodo seleccionado.

> ⚠️ La primera versión prioriza KPIs tabulares/gráficos. El mapa geoespacial se añadirá cuando contemos con geometrías oficiales de las zonas NYC TLC.

## 🏗️ Estructura del Proyecto

```
capstone-official/
│
├── dash_app/
│   └── app.py                       # Nuevo dashboard (Dash + Plotly)
│
├── capstone modelo/
│   ├── modelo_gurobi_rh.py            # Modelo de optimización
│   ├── parametros_matrices_nuevo.py    # Parámetros del modelo
│   └── simulacion_rh.py               # Simulación principal
│
├── Datos/
│   ├── lambda_zonal_OD_mat_full.csv   # Matriz O-D de demanda
│   └── df_all_reducido_github.parquet # Datos históricos
│
├── Distancias zonas/
│   └── distancias_manhattan_zonas...  # Distancias entre zonas
│
├── requirements.txt                    # 🆕 Dependencias
└── README.md                          # Este archivo
```

## 🚀 Instalación

### Requisitos

- Python 3.8+
- Gurobi 11.0+ con licencia válida
- 4GB RAM mínimo (8GB recomendado)

### Pasos

1. **Clonar repositorio**:
   ```bash
   git clone https://github.com/benjareyesr/capstone-official.git
   cd capstone-official
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verificar sistema** (opcional, si deseas validar dependencias locales):
   ```bash
   python verificar_sistema.py
   ```

## 📊 Uso

### Modelo de Optimización

```python
import parametros_matrices_nuevo as pm
import modelo_gurobi_rh as mrh

# Cargar parámetros
p_full = pm.cargar_parametros_modelo(T_total=8, fecha_dia_str='2024-09-15')

# Resolver paso de optimización
decisiones = mrh.resolver_paso(p_horizonte, estado_inicial)
```

### Visualizaciones

Puedes explorar los resultados desde `dash_app/app.py` o exportar los datos de `simulacion_rh.py` para analizarlos en notebooks (Plotly, pandas, Power BI, etc.).

## 📈 Resultados

El modelo optimiza:
- ✅ **Asignación de viajes**: Maximiza ingresos por servicio
- ✅ **Reubicación**: Minimiza costos de movimientos vacíos
- ✅ **Gestión de batería**: Optimiza tiempos de carga
- ✅ **Capacidad de estaciones**: Respeta límites físicos

## 🛠️ Tecnologías

- **Python 3.8+**: Lenguaje principal
- **Gurobi**: Motor de optimización
- **Pandas/NumPy**: Procesamiento de datos
- **Plotly**: Visualizaciones interactivas
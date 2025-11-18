# 🚕 Capstone - Optimización de Vehículos Autónomos en Manhattan

## 📋 Descripción

Este proyecto implementa un modelo de optimización para la gestión de una flota de vehículos autónomos en Manhattan, NYC. Utiliza horizonte rodante con Gurobi para asignar óptimamente los vehículos y maximizar la utilidad del sistema.

## ✨ Características Principales

- **Modelo de optimización**: Horizonte rodante con Gurobi
- **67 zonas de Manhattan**: Cobertura completa del área
- **300 vehículos autónomos**: Flota completa (escalable)
- **6 estaciones de carga**: Distribuidas estratégicamente
- **Dashboard interactivo**: Visualización en tiempo real con Streamlit

## 🎯 Dashboard de Visualización

### Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar dashboard
cd "capstone modelo"
streamlit run dashboard.py
```

### Características del Dashboard

- 🗺️ **Mapa interactivo** de Manhattan con las 67 zonas
- 🚗 **Visualización de vehículos** con código de colores por estado de batería
- 📊 **Métricas en tiempo real**: utilidad, ocupación, batería promedio
- ⏮️ **Navegación entre periodos** con controles intuitivos
- 📈 **Gráficos de evolución** y distribución

## 🏗️ Estructura del Proyecto

```
capstone-official/
│
├── capstone modelo/
│   ├── dashboard.py                    # 🆕 Dashboard interactivo
│   ├── modelo_gurobi_rh.py            # Modelo de optimización
│   ├── parametros_matrices_nuevo.py    # Parámetros del modelo
│   └── simulacion_rh copy.py          # Simulación
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

3. **Verificar sistema**:
   ```bash
   python verificar_sistema.py
   ```

4. **Ejecutar dashboard**:
   ```bash
   cd "capstone modelo"
   streamlit run dashboard.py
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

### Dashboard Visual

1. Abrir dashboard: `streamlit run dashboard.py`
2. Configurar parámetros en panel lateral
3. Ejecutar simulación
4. Navegar entre periodos y analizar resultados

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
- **Streamlit**: Dashboard web interactivo
- **Plotly**: Visualizaciones interactivas
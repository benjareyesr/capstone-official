# Dashboard de Visualización - Vehículos Autónomos en Manhattan

Este proyecto implementa una interfaz gráfica interactiva para visualizar el comportamiento de un modelo de optimización de vehículos autónomos en Manhattan usando horizonte rodante.

## 🚀 Características

- **Visualización en mapa interactivo** de las 67 zonas de Manhattan
- **Navegación entre periodos** con controles de flechas y slider
- **Métricas en tiempo real**:
  - Vehículos activos vs. cargando
  - Batería promedio de la flota
  - Utilidad acumulada
- **Código de colores** para estado de vehículos:
  - 🟢 Verde: Batería alta (>50%)
  - 🟡 Amarillo: Batería media (20-50%)
  - 🔴 Rojo: Batería baja (<20%)
  - 🟣 Morado: Vehículo cargando
- **Gráficos de evolución**:
  - Evolución de la utilidad en el tiempo
  - Distribución de batería de la flota

## 📋 Requisitos Previos

1. **Python 3.8+**
2. **Gurobi** instalado y con licencia válida
3. **Datos**: Los siguientes archivos deben estar presentes:
   - `Datos/lambda_zonal_OD_mat_full.csv`
   - `Datos/df_all_reducido_github.parquet`
   - `Distancias zonas/distancias_manhattan_zonas_con_tiempo_ingreso.csv`

## 🔧 Instalación

1. **Clonar o navegar al directorio del proyecto**:
   ```bash
   cd capstone-official
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verificar instalación de Gurobi**:
   ```bash
   python -c "import gurobipy; print('Gurobi OK')"
   ```

## ▶️ Ejecución

Para ejecutar el dashboard:

```bash
cd "capstone modelo"
streamlit run dashboard.py
```

El dashboard se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 🎮 Uso

1. **Configurar parámetros** en el panel lateral:
   - Número de vehículos a simular (5-50, recomendado: 20)
   - Periodos a simular (4-20)
   - Horizonte de optimización (2-6)
   - Fecha de simulación

2. **Ejecutar simulación**: Click en "▶️ Ejecutar Simulación"
   - La primera ejecución puede tomar varios minutos
   - El progreso se mostrará en pantalla

3. **Navegar entre periodos**:
   - Usar botones "⬅️ Anterior" / "Siguiente ➡️"
   - Arrastrar el slider de periodo
   - Observar cambios en el mapa y métricas

4. **Analizar resultados**:
   - Posición de vehículos en el mapa
   - Estado de carga de cada vehículo (hover sobre marcador)
   - Evolución de utilidad y distribución de batería

## 🗺️ Estructura del Proyecto

```
capstone-official/
│
├── capstone modelo/
│   ├── dashboard.py                    # Interfaz gráfica principal
│   ├── modelo_gurobi_rh.py            # Modelo de optimización
│   ├── parametros_matrices_nuevo.py    # Carga de parámetros
│   └── simulacion_rh copy.py          # Lógica de simulación
│
├── Datos/
│   ├── lambda_zonal_OD_mat_full.csv
│   └── df_all_reducido_github.parquet
│
├── Distancias zonas/
│   └── distancias_manhattan_zonas_con_tiempo_ingreso.csv
│
└── requirements.txt
```

## ⚙️ Configuración Avanzada

### Modificar coordenadas de zonas

Las coordenadas de las zonas están en `dashboard.py` en el diccionario `COORDS_ZONAS`. Para mayor precisión, se pueden usar shapefiles reales de las zonas de Manhattan.

### Ajustar visualización

En `dashboard.py`, función `crear_mapa_manhattan()`:
- Modificar `zoom` para ajustar nivel de zoom inicial
- Cambiar `style` del mapbox (opciones: "carto-positron", "open-street-map", "carto-darkmatter")

### Escalabilidad

Para simular los 300 vehículos completos:
- Modificar rango del slider en `st.sidebar`
- Considerar aumentar `MIPGap` en `modelo_gurobi_rh.py` para acelerar resolución
- La visualización puede volverse más lenta con muchos vehículos

## 📊 Interpretación de Resultados

### Métricas Principales

- **Vehículos Activos**: Número de vehículos disponibles para servir demanda
- **Vehículos Cargando**: Número de vehículos en estaciones de carga
- **Batería Promedio**: Promedio de batería de la flota (km de autonomía)
- **Utilidad Acumulada**: Ganancia total del sistema (ingresos - costos)

### Estados de Vehículos

- **Verde (Batería Alta)**: >50% - Vehículo óptimo para servir demanda
- **Amarillo (Batería Media)**: 20-50% - Puede necesitar recarga pronto
- **Rojo (Batería Baja)**: <20% - Debe ir a estación de carga
- **Morado (Cargando)**: Vehículo fuera de servicio temporalmente

### Estaciones de Carga

Zonas con estaciones (marcadores verdes grandes):
- Zona 87, 116, 137, 151, 128, 186
- Capacidad máxima: 55 vehículos simultáneos
- Tiempo de carga: 2 periodos (configurable)

## 🐛 Troubleshooting

### Error: "No module named 'streamlit'"
```bash
pip install streamlit
```

### Error: Gurobi license
Verificar que tienes una licencia válida de Gurobi:
```bash
gurobi_cl --license
```

### Error: Archivo de datos no encontrado
Verificar que los archivos CSV/Parquet existen en las rutas correctas.

### Dashboard muy lento
- Reducir número de vehículos
- Reducir periodos de simulación
- Aumentar `MIPGap` en el modelo

## 📝 Notas

- La simulación usa 20 vehículos por defecto para visualización rápida
- El modelo completo tiene 300 vehículos (puede tomar mucho tiempo)
- Las coordenadas de zonas son aproximadas para visualización
- La demanda se escala a 5% de la real por defecto

## 👥 Créditos

Proyecto Capstone - Universidad Católica de Chile  
Optimización de Vehículos Autónomos en NYC

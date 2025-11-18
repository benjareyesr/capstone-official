# 🚀 Guía Rápida - Dashboard Vehículos Autónomos

## Inicio Rápido (5 minutos)

### 1. Instalar Dependencias

```bash
# Desde la carpeta principal del proyecto
pip install -r requirements.txt
```

### 2. Ejecutar Dashboard

```bash
cd "capstone modelo"
streamlit run dashboard.py
```

El navegador se abrirá automáticamente en `http://localhost:8501`

### 3. Configurar Simulación

En el panel lateral izquierdo:
- **Número de vehículos**: 20 (recomendado para empezar)
- **Periodos**: 8 (equivale a 2 horas, 15 min/periodo)
- **Horizonte**: 4 (ventana de optimización)
- **Fecha**: 2024-09-15 (lunes típico)

### 4. Ejecutar

Click en **"▶️ Ejecutar Simulación"**

⏱️ Primera ejecución: ~3-5 minutos (carga datos)
⏱️ Siguientes: ~1-2 minutos

### 5. Navegar

Usa los controles para moverte entre periodos:
- **⬅️ Anterior** / **Siguiente ➡️**: Botones
- **Slider**: Arrastra para saltar a periodo específico

---

## 📊 Interpretando el Dashboard

### Mapa Principal

**Marcadores Pequeños (Zonas)**
- 🔵 Azul claro: Zonas normales de Manhattan
- 🟢 Verde grande: Estaciones de carga

**Marcadores de Vehículos**
- 🟢 Verde: Batería alta (>50%) - Listo para servir
- 🟡 Amarillo: Batería media (20-50%) - Funcionando
- 🔴 Rojo: Batería baja (<20%) - Necesita recarga
- 🟣 Morado: Cargando - Fuera de servicio

**Hover (pasar mouse)**: Ver detalles de zona o vehículo

### Métricas Superiores

```
┌─────────────────┬──────────────────┬─────────────────┬─────────────────┐
│ Activos: 18     │ Cargando: 2      │ Batería: 245km  │ Utilidad: $450  │
└─────────────────┴──────────────────┴─────────────────┴─────────────────┘
```

- **Vehículos Activos**: Disponibles para servir demanda
- **Vehículos Cargando**: En estación (no disponibles)
- **Batería Promedio**: Autonomía media de la flota
- **Utilidad Acumulada**: Ganancia total (ingresos - costos)

### Gráficos Laterales

**Evolución de Utilidad** (arriba)
- Muestra cómo crece la ganancia con el tiempo
- Línea verde ascendente = buen desempeño

**Distribución de Batería** (abajo)
- Histograma de niveles de carga
- Ideal: Mayoría en lado derecho (carga alta)
- Preocupante: Muchos en lado izquierdo (carga baja)

---

## 🎯 Casos de Uso Típicos

### Caso 1: Análisis Rápido
```
Vehículos: 10
Periodos: 4
Horizonte: 2
```
⏱️ Tiempo: ~1 minuto
✅ Ideal para: Probar configuraciones

### Caso 2: Análisis Estándar
```
Vehículos: 20
Periodos: 8
Horizonte: 4
```
⏱️ Tiempo: ~3 minutos
✅ Ideal para: Visualización normal

### Caso 3: Simulación Completa
```
Vehículos: 50
Periodos: 16
Horizonte: 6
```
⏱️ Tiempo: ~10-15 minutos
✅ Ideal para: Análisis detallado

### Caso 4: Día Completo (Avanzado)
```
Vehículos: 300 (flota real)
Periodos: 96 (24 horas)
Horizonte: 8
```
⏱️ Tiempo: ~2-3 horas
⚠️ Requiere: Computador potente, paciencia

---

## 🔍 Análisis Avanzado

### Identificar Problemas

**Muchos vehículos rojos (batería baja)**
→ Pocas estaciones o mucha demanda
→ Solución: Agregar estaciones en `parametros_matrices_nuevo.py`

**Utilidad no crece**
→ Demanda muy baja o costos muy altos
→ Verificar: `PORCENTAJE_DEMANDA` en parámetros

**Todos los vehículos esperando**
→ No hay demanda suficiente
→ Aumentar `PORCENTAJE_DEMANDA` o probar otra fecha

### Optimizar Desempeño

1. **Acelerar resolución** (sacrifica optimalidad):
   ```python
   # En modelo_gurobi_rh.py, agregar:
   m.setParam('MIPGap', 0.05)  # 5% de tolerancia
   ```

2. **Reducir output de Gurobi**:
   ```python
   # Ya configurado por defecto:
   m.setParam('OutputFlag', 0)
   ```

3. **Menos vehículos** = Dashboard más fluido

---

## 🐛 Solución de Problemas Comunes

### "No se encontró archivo CSV"
```bash
# Verificar que existan:
ls "Datos/lambda_zonal_OD_mat_full.csv"
ls "Datos/df_all_reducido_github.parquet"
ls "Distancias zonas/distancias_manhattan_zonas_con_tiempo_ingreso.csv"
```

### "Gurobi license error"
```bash
# Verificar licencia:
gurobi_cl --license

# Si falla, descargar licencia desde:
# https://www.gurobi.com/downloads/
```

### Dashboard muy lento
1. Reducir número de vehículos (20 → 10)
2. Reducir periodos (8 → 4)
3. Cerrar otras aplicaciones pesadas

### "Port 8501 already in use"
```bash
# Cambiar puerto:
streamlit run dashboard.py --server.port 8502
```

---

## 💡 Tips y Trucos

### Comparar Escenarios

1. Ejecutar simulación con configuración A
2. Guardar screenshot de métricas finales
3. Recargar página (F5)
4. Ejecutar con configuración B
5. Comparar resultados

### Exportar Datos

Para análisis externo, modificar `dashboard.py`:
```python
# Al final de ejecutar_simulacion(), agregar:
import json
with open('resultados.json', 'w') as f:
    json.dump(historial, f)
```

### Cambiar Mapa

En `dashboard.py`, función `crear_mapa_manhattan()`:
```python
mapbox=dict(
    style="carto-darkmatter",  # Modo oscuro
    # o "open-street-map"       # Más detalle
)
```

---

## 📚 Recursos Adicionales

- **README completo**: `README_DASHBOARD.md`
- **Configuración avanzada**: `dashboard_config.py`
- **Test rápido**: `python test_dashboard.py`
- **Documentación Streamlit**: https://docs.streamlit.io/
- **Plotly Maps**: https://plotly.com/python/mapbox/

---

## 🆘 Soporte

**Problemas frecuentes**: Ver sección Troubleshooting en `README_DASHBOARD.md`

**Bugs o mejoras**: Crear issue en el repositorio del proyecto

---

## ✨ Próximos Pasos

Una vez dominado el dashboard básico:

1. Modificar parámetros del modelo (demanda, estaciones, etc.)
2. Agregar nuevas métricas al panel
3. Implementar animaciones automáticas entre periodos
4. Exportar reportes automáticos
5. Integrar con datos en tiempo real

¡Disfruta visualizando tu modelo de optimización! 🚕💨

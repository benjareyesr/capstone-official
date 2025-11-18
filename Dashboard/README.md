# Dashboard - Estructura y Uso

## 📁 Nuevastructura

La carpeta `Dashboard` contiene todos los archivos relacionados con la interfaz gráfica:

```
Dashboard/
├── __init__.py           # Inicialización del paquete
├── app.py               # Aplicación principal (mejorada)
├── config.py            # Configuración de colores y estilos
└── scenarios.py         # Escenarios predefinidos
```

## 🚀 Ejecución

### Desde la raíz del proyecto:

**Opción 1 - Python:**
```bash
python run_app.py
```

**Opción 2 - Streamlit directo:**
```bash
streamlit run Dashboard/app.py
```

**Opción 3 - Shell script:**
```bash
./run_dashboard.sh
```

## ✨ Mejoras Implementadas

### 1. Mostrar Periodos Dinámicamente ✅
- Los periodos se muestran conforme se optimizan
- No espera a que todos terminen
- Usa `st.container()` para actualizar progreso en tiempo real
- Cada periodo completado muestra `✅ Periodo X/Y completado`

### 2. Reorganización en Carpeta Dashboard ✅
- Todos los archivos en `Dashboard/` 
- `app.py` - aplicación principal
- `config.py` - configuración
- `scenarios.py` - escenarios predefinidos
- `__init__.py` - imports exportados
- Rutas corregidas para importar desde `capstone modelo/`

### 3. Botones Anterior/Siguiente ✅
- Ahora funcionan correctamente
- Usa `st.rerun()` para refrescar la UI
- Lógica mejorada con callbacks y session_state
- El slider también funciona normalmente

## 📝 Importes Internos

Desde cualquier lugar dentro de Dashboard:
```python
from Dashboard import COLORES, DEFAULTS, ESCENARIOS
```

O desde la raíz:
```python
from Dashboard.config import COLORES
from Dashboard.scenarios import obtener_escenario
```

## 🔍 Verificación de Rutas

El archivo `app.py` importa correctamente desde:
```python
PROYECTO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROYECTO_ROOT / "capstone modelo"))

import parametros_matrices_nuevo as pm
import modelo_gurobi_rh as mrh
```

Esto permite que funcione desde cualquier ubicación.

## 🐛 Troubleshooting

**"ModuleNotFoundError: No module named 'parametros_matrices_nuevo'"**
- Verifica que `capstone modelo/` existe en la raíz
- Asegúrate de ejecutar desde la carpeta raíz del proyecto

**Botones no funcionan**
- Limpiar caché del navegador (Ctrl+F5)
- Los botones ahora usan `st.rerun()` - debería funcionar

**Periodos no se muestran en tiempo real**
- El progreso aparece en un container actualizable
- Espera a que terminen los cálculos de cada periodo

## 📊 Próximas Mejoras

- [ ] Integración de escenarios predefinidos en UI
- [ ] Exportación de resultados a CSV
- [ ] Modo comparación lado a lado
- [ ] Animación automática entre periodos

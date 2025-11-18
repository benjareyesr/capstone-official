import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Agregar el path del módulo capstone
sys.path.append(str(Path(__file__).parent))

import parametros_matrices_nuevo as pm
import modelo_gurobi_rh as mrh
import random
import copy

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Dashboard - Vehículos Autónomos NYC",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONSTANTES Y DATOS DE ZONAS
# ============================================================================

ZONAS_MANHATTAN = pm.ZONAS_MANHATTAN
INDICE_A_ZONA = pm.INDICE_A_ZONA
ZONA_A_INDICE = pm.ZONA_A_INDICE
N_ZONAS = pm.N_ZONAS

# Coordenadas aproximadas del centro de cada zona de Manhattan (lat, lon)
# Estas son coordenadas simplificadas para visualización
# En producción, deberías usar un shapefile real de las zonas
COORDS_ZONAS = {
    4: (40.7614, -73.9776), 12: (40.7831, -73.9712), 13: (40.7817, -73.9743),
    24: (40.7549, -73.9840), 41: (40.7614, -73.9588), 42: (40.7489, -73.9680),
    43: (40.7217, -73.9845), 45: (40.7594, -73.9776), 48: (40.7217, -73.9930),
    50: (40.7644, -73.9745), 68: (40.7489, -73.9930), 74: (40.7265, -73.9870),
    75: (40.7489, -73.9588), 79: (40.7217, -74.0060), 87: (40.7594, -73.9712),
    88: (40.7614, -73.9776), 90: (40.7217, -73.9776), 100: (40.7489, -73.9930),
    103: (40.7549, -73.9840), 107: (40.7594, -73.9712), 113: (40.7265, -73.9930),
    114: (40.7594, -73.9588), 116: (40.7489, -73.9680), 120: (40.7549, -73.9840),
    125: (40.7489, -73.9776), 127: (40.7549, -73.9776), 128: (40.7489, -73.9680),
    137: (40.7594, -73.9712), 140: (40.7265, -73.9930), 141: (40.7217, -73.9845),
    142: (40.7217, -73.9776), 143: (40.7217, -73.9680), 144: (40.7217, -73.9588),
    148: (40.7489, -73.9680), 151: (40.7489, -73.9588), 152: (40.7489, -73.9680),
    153: (40.7549, -73.9776), 158: (40.7549, -73.9840), 161: (40.7594, -73.9776),
    162: (40.7644, -73.9712), 163: (40.7644, -73.9776), 164: (40.7644, -73.9840),
    166: (40.7489, -73.9930), 170: (40.7489, -73.9680), 186: (40.7489, -73.9588),
    194: (40.7217, -73.9930), 202: (40.7817, -73.9743), 209: (40.7831, -73.9712),
    211: (40.7817, -73.9680), 224: (40.7594, -73.9776), 229: (40.7265, -73.9870),
    230: (40.7265, -73.9776), 231: (40.7265, -73.9680), 232: (40.7265, -73.9588),
    233: (40.7265, -73.9930), 234: (40.7217, -73.9776), 236: (40.7217, -73.9680),
    237: (40.7217, -73.9588), 238: (40.7217, -73.9930), 239: (40.7217, -73.9845),
    243: (40.7489, -73.9776), 244: (40.7489, -73.9680), 246: (40.7489, -73.9588),
    249: (40.7549, -73.9840), 261: (40.7594, -73.9776), 262: (40.7594, -73.9712),
    263: (40.7594, -73.9588)
}

# Estaciones de carga
ESTACIONES_CARGA = pm.ZONAS_ESTACIONES_CARGA

# ============================================================================
# FUNCIONES DE SIMULACIÓN
# ============================================================================

def preparar_parametros_horizonte(p_full, k_inicio, T_horizonte):
    """Crea un diccionario de parámetros para el horizonte actual."""
    p_horizonte = copy.deepcopy(p_full)
    p_horizonte['T'] = T_horizonte
    
    def slice_param(param_full):
        if isinstance(param_full, dict):
            param_sliced = {}
            for i in param_full:
                param_sliced[i] = {}
                for j in param_full[i]:
                    param_sliced[i][j] = {}
                    for t_rel in range(T_horizonte):
                        t_abs = k_inicio + t_rel
                        if t_abs in param_full[i][j]:
                            param_sliced[i][j][t_rel] = param_full[i][j][t_abs]
                        else:
                            param_sliced[i][j][t_rel] = 0
            return param_sliced
        elif hasattr(param_full, 'shape') and len(param_full.shape) == 3:
            return param_full[:, :, k_inicio : k_inicio + T_horizonte]
        else:
            return param_full
    
    p_horizonte['Dem'] = slice_param(p_full['Dem'])
    p_horizonte['Pviaje'] = slice_param(p_full['Pviaje'])
    p_horizonte['Creub'] = slice_param(p_full['Creub'])
    
    return p_horizonte

def calcular_ocupacion_previa(estado_real, N, T_horizonte):
    """Calcula cuántos autos están ocupados cargando en cada estación."""
    ocupacion = {i: {t: 0 for t in range(T_horizonte)} for i in range(N)}
    for a in estado_real['A_indices']:
        if estado_real['estado_carga'][a] > 0:
            nodo = estado_real['pos'][a]
            tiempo_restante = estado_real['estado_carga'][a]
            for t in range(min(tiempo_restante, T_horizonte)):
                ocupacion[nodo][t] += 1
    return ocupacion

def ejecutar_simulacion(T_simulacion, T_horizonte, fecha_dia, num_vehiculos_visual=20):
    """
    Ejecuta la simulación completa y retorna historial de estados.
    num_vehiculos_visual: número de vehículos a simular (para visualización reducida)
    """
    
    # Cargar parámetros del modelo completo
    with st.spinner('Cargando parámetros del modelo...'):
        p_full = pm.cargar_parametros_modelo(T_total=T_simulacion, fecha_dia_str=fecha_dia)
    
    # Ajustar número de vehículos para visualización
    p_full['A'] = num_vehiculos_visual
    p_full['A_indices'] = list(range(num_vehiculos_visual))
    
    # Estado inicial
    estado_inicial = {
        'pos': {},
        'carga': {},
        'estado_carga': {},
        'A_indices': p_full['A_indices']
    }
    
    # Inicializar posiciones y carga aleatoriamente
    random.seed(42)
    for a in p_full['A_indices']:
        estado_inicial['pos'][a] = random.randint(0, N_ZONAS - 1)
        estado_inicial['carga'][a] = random.uniform(100, p_full['Cargamax'])
        estado_inicial['estado_carga'][a] = 0
    
    # Historial para guardar estados
    historial = []
    estado_real = copy.deepcopy(estado_inicial)
    utilidad_acumulada = 0.0
    
    # Simulación
    for k_paso in range(T_simulacion):
        # Guardar estado actual
        historial.append({
            'periodo': k_paso,
            'pos': copy.deepcopy(estado_real['pos']),
            'carga': copy.deepcopy(estado_real['carga']),
            'estado_carga': copy.deepcopy(estado_real['estado_carga']),
            'utilidad_acumulada': utilidad_acumulada
        })
        
        # Preparar horizonte
        p_horizonte = preparar_parametros_horizonte(p_full, k_paso, min(T_horizonte, T_simulacion - k_paso))
        
        # Calcular autos disponibles
        autos_disponibles = [a for a in p_full['A_indices'] if estado_real['estado_carga'][a] == 0]
        
        # Calcular ocupación previa
        ocupacion_previa = calcular_ocupacion_previa(estado_real, N_ZONAS, p_horizonte['T'])
        
        estado_paso = {
            'pos': estado_real['pos'],
            'carga': estado_real['carga'],
            'autos_disponibles': autos_disponibles,
            'ocupacion_previa': ocupacion_previa
        }
        
        # Resolver paso
        with st.spinner(f'Resolviendo periodo {k_paso+1}/{T_simulacion}...'):
            decisiones = mrh.resolver_paso(p_horizonte, estado_paso)
        
        # Actualizar estado real
        utilidad_paso = actualizar_estado_real(
            k_paso, estado_real, decisiones, p_full, utilidad_acumulada
        )
        utilidad_acumulada += utilidad_paso
    
    # Guardar estado final
    historial.append({
        'periodo': T_simulacion,
        'pos': copy.deepcopy(estado_real['pos']),
        'carga': copy.deepcopy(estado_real['carga']),
        'estado_carga': copy.deepcopy(estado_real['estado_carga']),
        'utilidad_acumulada': utilidad_acumulada
    })
    
    return historial, p_full

def actualizar_estado_real(k_paso, estado_real, decisiones, p_full, utilidad_acumulada):
    """Actualiza el estado real basado en las decisiones y retorna utilidad del paso."""
    utilidad_paso = 0.0
    
    # Actualizar autos que estaban cargando
    for a in p_full['A_indices']:
        if estado_real['estado_carga'][a] > 0:
            estado_real['estado_carga'][a] -= 1
            if estado_real['estado_carga'][a] == 0:
                estado_real['carga'][a] = p_full['Cargamax']
    
    # Implementar decisiones
    for a in p_full['A_indices']:
        if estado_real['estado_carga'][a] > 0:
            continue
        
        if a in decisiones.get('y', {}):
            i, j, profit = decisiones['y'][a]
            gasto = p_full['d'][i, j]
            estado_real['pos'][a] = j
            estado_real['carga'][a] -= gasto
            utilidad_paso += profit
        
        elif a in decisiones.get('z_dem', {}):
            i, j, cost = decisiones['z_dem'][a]
            gasto = p_full['d'][i, j]
            estado_real['pos'][a] = j
            estado_real['carga'][a] -= gasto
            utilidad_paso -= cost
        
        elif a in decisiones.get('z_carga', {}):
            i, j = decisiones['z_carga'][a]
            gasto = p_full['d'][i, j]
            estado_real['pos'][a] = j
            estado_real['carga'][a] -= gasto
        
        elif a in decisiones.get('ch', {}):
            i = decisiones['ch'][a]
            estado_real['pos'][a] = i
            periodos_restantes = p_full['Tchg'] - 1
            estado_real['estado_carga'][a] = periodos_restantes
            if periodos_restantes == 0:
                estado_real['carga'][a] = p_full['Cargamax']
        
        elif a in decisiones.get('esp', {}):
            i = decisiones['esp'][a]
            estado_real['pos'][a] = i
    
    # Penalización por demanda no servida
    for (i, j), (cantidad, costo) in decisiones.get('s', {}).items():
        utilidad_paso -= costo
    
    return utilidad_paso

# ============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================================================

def crear_mapa_manhattan(estado, periodo, p_full):
    """Crea el mapa de Manhattan con los vehículos."""
    
    # Crear DataFrame para las zonas
    zonas_data = []
    for zona_id in ZONAS_MANHATTAN:
        if zona_id in COORDS_ZONAS:
            idx = ZONA_A_INDICE[zona_id]
            lat, lon = COORDS_ZONAS[zona_id]
            es_estacion = zona_id in ESTACIONES_CARGA
            
            # Contar vehículos en esta zona
            num_vehiculos = sum(1 for a in p_full['A_indices'] if estado['pos'][a] == idx)
            
            zonas_data.append({
                'zona_id': zona_id,
                'lat': lat,
                'lon': lon,
                'es_estacion': es_estacion,
                'num_vehiculos': num_vehiculos
            })
    
    df_zonas = pd.DataFrame(zonas_data)
    
    # Crear figura
    fig = go.Figure()
    
    # Agregar zonas normales
    df_normal = df_zonas[~df_zonas['es_estacion']]
    fig.add_trace(go.Scattermapbox(
        lat=df_normal['lat'],
        lon=df_normal['lon'],
        mode='markers',
        marker=dict(size=8, color='lightblue', opacity=0.6),
        text=df_normal['zona_id'],
        name='Zonas',
        hovertemplate='<b>Zona %{text}</b><br>Vehículos: %{customdata}<extra></extra>',
        customdata=df_normal['num_vehiculos']
    ))
    
    # Agregar estaciones de carga
    df_estaciones = df_zonas[df_zonas['es_estacion']]
    fig.add_trace(go.Scattermapbox(
        lat=df_estaciones['lat'],
        lon=df_estaciones['lon'],
        mode='markers',
        marker=dict(size=14, color='green', symbol='circle', opacity=0.8),
        text=df_estaciones['zona_id'],
        name='Estaciones',
        hovertemplate='<b>Estación Zona %{text}</b><br>Vehículos: %{customdata}<extra></extra>',
        customdata=df_estaciones['num_vehiculos']
    ))
    
    # Agregar vehículos
    vehiculos_data = []
    for a in p_full['A_indices']:
        idx = estado['pos'][a]
        zona_id = INDICE_A_ZONA[idx]
        if zona_id in COORDS_ZONAS:
            lat, lon = COORDS_ZONAS[zona_id]
            carga_pct = (estado['carga'][a] / p_full['Cargamax']) * 100
            esta_cargando = estado['estado_carga'][a] > 0
            
            # Pequeño offset aleatorio para que no se superpongan
            lat_offset = np.random.uniform(-0.001, 0.001)
            lon_offset = np.random.uniform(-0.001, 0.001)
            
            vehiculos_data.append({
                'auto_id': a,
                'lat': lat + lat_offset,
                'lon': lon + lon_offset,
                'zona_id': zona_id,
                'carga': estado['carga'][a],
                'carga_pct': carga_pct,
                'cargando': esta_cargando,
                'tiempo_carga': estado['estado_carga'][a]
            })
    
    df_vehiculos = pd.DataFrame(vehiculos_data)
    
    # Clasificar vehículos por estado de batería
    if len(df_vehiculos) > 0:
        df_cargando = df_vehiculos[df_vehiculos['cargando']]
        df_alta = df_vehiculos[(~df_vehiculos['cargando']) & (df_vehiculos['carga_pct'] >= 50)]
        df_media = df_vehiculos[(~df_vehiculos['cargando']) & (df_vehiculos['carga_pct'] >= 20) & (df_vehiculos['carga_pct'] < 50)]
        df_baja = df_vehiculos[(~df_vehiculos['cargando']) & (df_vehiculos['carga_pct'] < 20)]
        
        # Vehículos cargando
        if len(df_cargando) > 0:
            fig.add_trace(go.Scattermapbox(
                lat=df_cargando['lat'],
                lon=df_cargando['lon'],
                mode='markers',
                marker=dict(size=10, color='purple', symbol='circle'),
                text=df_cargando['auto_id'],
                name='Cargando',
                hovertemplate='<b>Auto %{text}</b><br>Zona: %{customdata[0]}<br>Batería: %{customdata[1]:.1f}km<br>Cargando: %{customdata[2]} periodos<extra></extra>',
                customdata=df_cargando[['zona_id', 'carga', 'tiempo_carga']].values
            ))
        
        # Batería alta (verde)
        if len(df_alta) > 0:
            fig.add_trace(go.Scattermapbox(
                lat=df_alta['lat'],
                lon=df_alta['lon'],
                mode='markers',
                marker=dict(size=10, color='green', symbol='circle'),
                text=df_alta['auto_id'],
                name='Batería Alta',
                hovertemplate='<b>Auto %{text}</b><br>Zona: %{customdata[0]}<br>Batería: %{customdata[1]:.1f}km (%{customdata[2]:.0f}%)<extra></extra>',
                customdata=df_alta[['zona_id', 'carga', 'carga_pct']].values
            ))
        
        # Batería media (amarillo)
        if len(df_media) > 0:
            fig.add_trace(go.Scattermapbox(
                lat=df_media['lat'],
                lon=df_media['lon'],
                mode='markers',
                marker=dict(size=10, color='yellow', symbol='circle'),
                text=df_media['auto_id'],
                name='Batería Media',
                hovertemplate='<b>Auto %{text}</b><br>Zona: %{customdata[0]}<br>Batería: %{customdata[1]:.1f}km (%{customdata[2]:.0f}%)<extra></extra>',
                customdata=df_media[['zona_id', 'carga', 'carga_pct']].values
            ))
        
        # Batería baja (rojo)
        if len(df_baja) > 0:
            fig.add_trace(go.Scattermapbox(
                lat=df_baja['lat'],
                lon=df_baja['lon'],
                mode='markers',
                marker=dict(size=10, color='red', symbol='circle'),
                text=df_baja['auto_id'],
                name='Batería Baja',
                hovertemplate='<b>Auto %{text}</b><br>Zona: %{customdata[0]}<br>Batería: %{customdata[1]:.1f}km (%{customdata[2]:.0f}%)<extra></extra>',
                customdata=df_baja[['zona_id', 'carga', 'carga_pct']].values
            ))
    
    # Configurar layout del mapa
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=40.75, lon=-73.98),
            zoom=11.5
        ),
        height=600,
        margin=dict(l=0, r=0, t=40, b=0),
        title=f"Periodo {periodo}",
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    return fig

def crear_metricas_panel(historial, periodo_actual):
    """Crea el panel de métricas."""
    estado = historial[periodo_actual]
    
    # Calcular métricas
    num_vehiculos = len(estado['pos'])
    vehiculos_cargando = sum(1 for a in estado['estado_carga'] if estado['estado_carga'][a] > 0)
    vehiculos_activos = num_vehiculos - vehiculos_cargando
    
    # Batería promedio
    bateria_promedio = np.mean([estado['carga'][a] for a in estado['carga']])
    
    # Utilidad
    utilidad = estado['utilidad_acumulada']
    
    # Distribución de batería
    baterias = [estado['carga'][a] for a in estado['carga']]
    
    return {
        'num_vehiculos': num_vehiculos,
        'vehiculos_activos': vehiculos_activos,
        'vehiculos_cargando': vehiculos_cargando,
        'bateria_promedio': bateria_promedio,
        'utilidad': utilidad,
        'baterias': baterias
    }

# ============================================================================
# APLICACIÓN PRINCIPAL
# ============================================================================

def main():
    st.title("🚕 Dashboard - Vehículos Autónomos en Manhattan")
    st.markdown("---")
    
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        st.subheader("Parámetros de Simulación")
        num_vehiculos = st.slider("Número de vehículos", 5, 50, 20, 5)
        T_simulacion = st.slider("Periodos a simular", 4, 20, 8, 1)
        T_horizonte = st.slider("Horizonte de optimización", 2, 6, 4, 1)
        
        fecha_dia = st.date_input(
            "Fecha de simulación",
            value=pd.Timestamp("2024-09-15")
        ).strftime("%Y-%m-%d")
        
        st.markdown("---")
        
        if st.button("▶️ Ejecutar Simulación", type="primary"):
            st.session_state['ejecutar'] = True
    
    # Ejecutar simulación
    if 'historial' not in st.session_state or st.session_state.get('ejecutar', False):
        with st.spinner('Ejecutando simulación... Esto puede tomar varios minutos.'):
            historial, p_full = ejecutar_simulacion(
                T_simulacion, T_horizonte, fecha_dia, num_vehiculos
            )
            st.session_state['historial'] = historial
            st.session_state['p_full'] = p_full
            st.session_state['periodo_actual'] = 0
            st.session_state['ejecutar'] = False
        st.success('✅ Simulación completada!')
    
    # Mostrar resultados si hay historial
    if 'historial' in st.session_state:
        historial = st.session_state['historial']
        p_full = st.session_state['p_full']
        
        # Controles de navegación
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if st.button("⬅️ Anterior"):
                if st.session_state['periodo_actual'] > 0:
                    st.session_state['periodo_actual'] -= 1
        
        with col2:
            periodo_actual = st.slider(
                "Periodo",
                0,
                len(historial) - 1,
                st.session_state.get('periodo_actual', 0),
                key='slider_periodo'
            )
            st.session_state['periodo_actual'] = periodo_actual
        
        with col3:
            if st.button("Siguiente ➡️"):
                if st.session_state['periodo_actual'] < len(historial) - 1:
                    st.session_state['periodo_actual'] += 1
        
        # Mostrar métricas
        metricas = crear_metricas_panel(historial, periodo_actual)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Vehículos Activos", metricas['vehiculos_activos'])
        with col2:
            st.metric("Vehículos Cargando", metricas['vehiculos_cargando'])
        with col3:
            st.metric("Batería Promedio", f"{metricas['bateria_promedio']:.1f} km")
        with col4:
            st.metric("Utilidad Acumulada", f"${metricas['utilidad']:.2f}")
        
        st.markdown("---")
        
        # Mapa y gráficos
        col_mapa, col_graficos = st.columns([2, 1])
        
        with col_mapa:
            estado = historial[periodo_actual]
            fig_mapa = crear_mapa_manhattan(estado, periodo_actual, p_full)
            st.plotly_chart(fig_mapa, use_container_width=True)
        
        with col_graficos:
            # Gráfico de evolución de utilidad
            st.subheader("Evolución de Utilidad")
            utilidades = [h['utilidad_acumulada'] for h in historial]
            fig_utilidad = go.Figure()
            fig_utilidad.add_trace(go.Scatter(
                x=list(range(len(utilidades))),
                y=utilidades,
                mode='lines+markers',
                name='Utilidad',
                line=dict(color='green', width=2)
            ))
            fig_utilidad.update_layout(
                xaxis_title="Periodo",
                yaxis_title="Utilidad ($)",
                height=250,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_utilidad, use_container_width=True)
            
            # Distribución de batería
            st.subheader("Distribución de Batería")
            fig_bateria = go.Figure()
            fig_bateria.add_trace(go.Histogram(
                x=metricas['baterias'],
                nbinsx=10,
                marker_color='blue',
                name='Batería'
            ))
            fig_bateria.update_layout(
                xaxis_title="Batería (km)",
                yaxis_title="Frecuencia",
                height=250,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False
            )
            st.plotly_chart(fig_bateria, use_container_width=True)
        
        # Información adicional
        with st.expander("ℹ️ Información de la Simulación"):
            st.write(f"**Total de periodos:** {len(historial) - 1}")
            st.write(f"**Periodo actual:** {periodo_actual}")
            st.write(f"**Número de zonas:** {N_ZONAS}")
            st.write(f"**Estaciones de carga:** {len(ESTACIONES_CARGA)}")
            st.write(f"**Zonas con estaciones:** {', '.join(map(str, ESTACIONES_CARGA))}")
    
    else:
        st.info("👈 Configura los parámetros en el panel lateral y presiona 'Ejecutar Simulación'")

if __name__ == "__main__":
    main()

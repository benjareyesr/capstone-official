"""Dash application for visualizing the rolling-horizon simulation outputs."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

import dash
from dash import Input, Output, State, dcc, html, dash_table, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "capstone modelo"
DISTANCES_CSV = BASE_DIR / "Distancias zonas" / "distancias_manhattan_zonas_con_tiempo_ingreso.csv"
CENTROIDS_CSV = BASE_DIR / "Datos" / "taxi_zone_centroids.csv"

if not MODEL_DIR.exists():
    raise FileNotFoundError(f"No se encuentra la carpeta de modelo: {MODEL_DIR}")

if str(MODEL_DIR) not in sys.path:
    sys.path.append(str(MODEL_DIR))

try:  # Lazy import to keep app errors informative
    from simulacion_rh import ejecutar_simulacion, INDICE_A_ZONA
except ImportError as exc:  # pragma: no cover - guard for misconfigured paths
    raise RuntimeError(
        "No fue posible importar simulacion_rh.py. Revisa la ruta de 'capstone modelo'."
    ) from exc


def _cargar_catalogo_zonas() -> Dict[int, str]:
    if not DISTANCES_CSV.exists():
        return {}
    df = pd.read_csv(DISTANCES_CSV, usecols=["origen_id", "origen_zona"])
    df = df.drop_duplicates(subset="origen_id")
    return df.set_index("origen_id")["origen_zona"].to_dict()


ZONA_NOMBRES = _cargar_catalogo_zonas()


def _cargar_centroides_zonas() -> Dict[int, Dict[str, float]]:
    if not CENTROIDS_CSV.exists():
        return {}
    df = pd.read_csv(CENTROIDS_CSV)
    columnas = {col.lower(): col for col in df.columns}
    id_col = columnas.get('locationid', 'LocationID')
    lat_col = columnas.get('lat', 'lat')
    lon_col = columnas.get('lon', 'lon')
    zone_col = columnas.get('zone', 'zone')
    borough_col = columnas.get('borough', 'borough')
    df[id_col] = df[id_col].astype(int)
    # Si hay filas repetidas (puede ocurrir con multipolígonos), agregamos por promedio y tomamos el primero de texto
    if df[id_col].duplicated().any():
        df = df.groupby(id_col, as_index=False).agg({
            borough_col: 'first',
            zone_col: 'first',
            lat_col: 'mean',
            lon_col: 'mean',
        })
    df_unique = df.set_index(id_col)[[borough_col, zone_col, lat_col, lon_col]].rename(columns={
        borough_col: 'borough',
        zone_col: 'zone',
        lat_col: 'lat',
        lon_col: 'lon',
    })
    return df_unique.to_dict('index')


ZONA_COORDS = _cargar_centroides_zonas()


def etiqueta_zona(idx: int) -> str:
    zona_id = INDICE_A_ZONA.get(idx, idx)
    nombre = ZONA_NOMBRES.get(zona_id, "Sin nombre")
    return f"{zona_id} - {nombre}"


def coordenadas_zona(idx: int):
    zona_id = INDICE_A_ZONA.get(idx)
    if zona_id is None:
        return None
    datos = ZONA_COORDS.get(zona_id)
    if not datos:
        return None
    return {
        'zona_id': zona_id,
        'zona_nombre': datos['zone'],
        'lat': datos['lat'],
        'lon': datos['lon'],
    }


def default_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Ejecuta la simulación para ver datos',
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 14, 'color': '#6c757d'},
        }]
    )
    return fig


def default_map_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        geo=dict(
            projection_type='mercator',
            showland=True,
            landcolor='#f8f4ed',
            showcountries=False,
            showcoastlines=False,
            lataxis=dict(range=[40.65, 40.92]),
            lonaxis=dict(range=[-74.05, -73.90]),
            center=dict(lat=40.78, lon=-73.96),
            bgcolor='rgba(0,0,0,0)',
        ),
        template="plotly_white",
        margin=dict(l=0, r=0, t=40, b=0),
        annotations=[{
            'text': 'Ejecuta la simulación para ver movimientos',
            'xref': 'paper',
            'yref': 'paper',
            'y': 0.5,
            'showarrow': False,
            'font': {'size': 14, 'color': '#6c757d'},
        }]
    )
    return fig


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Capstone Mobility Dashboard",
)
server = app.server


controls = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                dbc.Label("Fecha base"),
                dcc.DatePickerSingle(
                    id='date-input',
                    date='2024-09-15',
                    display_format='YYYY-MM-DD',
                ),
            ], md=3),
            dbc.Col([
                dbc.Label("K_TOTAL (periodos)"),
                dbc.Input(id='input-k', type='number', min=6, step=1, value=8),
            ], md=3),
            dbc.Col([
                dbc.Label("T_HORIZONTE"),
                dbc.Input(id='input-h', type='number', min=2, step=1, value=4),
            ], md=3),
            dbc.Col([
                dbc.Label("Seed"),
                dbc.Input(id='input-seed', type='number', min=0, step=1, value=7),
            ], md=3),
        ], className='gy-3'),
        dbc.Row([
            dbc.Col([
                dbc.Label("Número de autos (max 30)"),
                dbc.Input(id='input-autos', type='number', min=1, max=30, step=1, value=4),
            ], md=3),
        ], className='gy-3'),
        dbc.Row([
            dbc.Col(
                dbc.Button("Ejecutar simulación", id='run-button', color='primary', className='w-100'),
                md=3,
            ),
        ], className='gy-3 mt-2'),
    ]),
    className='mb-3'
)

summary_cards = dbc.Row([
    dbc.Col(html.Div(id='card-utilidad'), md=4),
    dbc.Col(html.Div(id='card-viajes'), md=4),
    dbc.Col(html.Div(id='card-tiempo'), md=4),
], className='gy-3')

period_slider = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col(dbc.Label("Periodo a inspeccionar"), width=12),
            dbc.Col(dcc.Slider(id='period-slider', min=0, max=0, step=1, value=0, disabled=True), width=12),
        ])
    ]),
    className='mb-3'
)

acciones_table = dash_table.DataTable(
    id='acciones-table',
    data=[],
    columns=[],
    style_table={'height': '350px', 'overflowY': 'auto'},
    style_cell={'textAlign': 'left', 'padding': '6px'},
    style_header={'fontWeight': 'bold'},
)

app.layout = dbc.Container([
    html.H1("Dashboard de Optimización - Manhattan"),
    html.P("Visualiza la utilidad, acciones y demanda no servida del modelo de horizonte rodante."),
    controls,
    dbc.Alert(id='simulation-status', color='info', children='Ejecuta una simulación para comenzar.'),
    dcc.Store(id='simulation-store'),
    summary_cards,
    dbc.Row([
        dbc.Col(dcc.Graph(id='utilidad-line', figure=default_figure('Utilidad acumulada')), md=6),
        dbc.Col(dcc.Graph(id='acciones-bar', figure=default_figure('Acciones por periodo')), md=6),
    ], className='gy-3'),
    dbc.Row([
        dbc.Col(dcc.Graph(id='heatmap-demanda', figure=default_figure('Demanda no servida')), md=12),
    ], className='gy-3'),
    dbc.Row([
        dbc.Col(dcc.Graph(id='mapa-movilidad', figure=default_map_figure('Movimientos por periodo')), md=12),
    ], className='gy-3'),
    period_slider,
    dbc.Card([
        dbc.CardHeader("Detalle de acciones en el periodo seleccionado"),
        dbc.CardBody(acciones_table),
    ]),
], fluid=True, className='py-4')


def _build_marks(num_periods: int) -> Dict[int, str]:
    if num_periods <= 1:
        return {0: '0'}
    if num_periods <= 12:
        return {i: str(i) for i in range(num_periods)}
    step = max(1, num_periods // 12)
    return {i: str(i) for i in range(0, num_periods, step)}


def _build_map_figure(acciones: List[Dict], periodo: int) -> go.Figure:
    titulo = f"Movimientos de vehículos en el periodo {periodo}"
    if not acciones or not ZONA_COORDS:
        return default_map_figure(titulo)

    fig = default_map_figure(titulo)
    colores = px.colors.qualitative.Vivid
    marker_lats, marker_lons, marker_text, marker_colors = [], [], [], []

    for idx, accion in enumerate(acciones):
        coords_origen = coordenadas_zona(accion['origen_idx'])
        coords_destino = coordenadas_zona(accion['destino_idx'])
        if not coords_destino:
            continue

        color = colores[idx % len(colores)]
        hover = (
            f"Auto {accion['auto']} - {accion['tipo'].replace('_', ' ').title()}<br>"
            f"{coords_origen['zona_id'] if coords_origen else accion['origen_idx']} -> {coords_destino['zona_id']}<br>"
            f"Distancia: {accion['distancia']:.1f} km - Valor: ${accion['valor']:.2f}"
        )

        if coords_origen and (coords_origen['lat'] != coords_destino['lat'] or coords_origen['lon'] != coords_destino['lon']):
            fig.add_trace(go.Scattergeo(
                lat=[coords_origen['lat'], coords_destino['lat']],
                lon=[coords_origen['lon'], coords_destino['lon']],
                mode='lines',
                line=dict(color=color, width=2),
                hoverinfo='text',
                text=hover,
                showlegend=False,
            ))

        marker_lats.append(coords_destino['lat'])
        marker_lons.append(coords_destino['lon'])
        marker_text.append(f"Auto {accion['auto']} ({coords_destino['zona_id']})")
        marker_colors.append(color)

    if marker_lats:
        fig.add_trace(go.Scattergeo(
            lat=marker_lats,
            lon=marker_lons,
            mode='markers',
            marker=dict(size=9, color=marker_colors),
            text=marker_text,
            hoverinfo='text',
            showlegend=False,
        ))
        fig.update_layout(annotations=[])

    return fig


@app.callback(
    Output('simulation-store', 'data'),
    Output('simulation-status', 'children'),
    Output('simulation-status', 'color'),
    Output('period-slider', 'max'),
    Output('period-slider', 'value'),
    Output('period-slider', 'marks'),
    Output('period-slider', 'disabled'),
    Input('run-button', 'n_clicks'),
    State('date-input', 'date'),
    State('input-k', 'value'),
    State('input-h', 'value'),
    State('input-seed', 'value'),
    State('input-autos', 'value'),
    prevent_initial_call=True,
)
def run_simulation(n_clicks, fecha, k_total, t_horizonte, seed, num_autos):  # pragma: no cover - Dash runtime
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if not fecha:
        fecha = '2024-09-15'

    try:
        resultados = ejecutar_simulacion(
            K_TOTAL=int(k_total),
            T_HORIZONTE=int(t_horizonte),
            FECHA_STR=str(fecha),
            seed=int(seed or 7),
            numero_autos=int(num_autos or 4),
            capturar_historial=True,
            verbose=False,
        )
    except Exception as exc:  # pragma: no cover - surfaced to UI
        return (
            no_update,
            f"❌ Error al ejecutar la simulación: {exc}",
            'danger',
            no_update,
            no_update,
            no_update,
            no_update,
        )

    pasos = resultados.get('historial_pasos', [])
    pasos_len = len(pasos)
    slider_max = max(0, pasos_len - 1)
    payload = json.dumps(resultados, default=float)
    status = f"✅ Simulación completada en {resultados['tiempo_total_segundos']:.2f} segundos"
    return (
        payload,
        status,
        'success',
        slider_max,
        0,
        _build_marks(pasos_len) if pasos_len else {0: '0'},
        pasos_len == 0,
    )


def _default_card(label: str) -> dbc.Card:
    return dbc.Card(dbc.CardBody([
        html.H4('—', className='card-title'),
        html.P(label, className='card-text text-muted'),
    ]))


def _card(value: str, label: str) -> dbc.Card:
    return dbc.Card(dbc.CardBody([
        html.H4(value, className='card-title'),
        html.P(label, className='card-text text-muted'),
    ]))


@app.callback(
    Output('card-utilidad', 'children'),
    Output('card-viajes', 'children'),
    Output('card-tiempo', 'children'),
    Output('utilidad-line', 'figure'),
    Output('acciones-bar', 'figure'),
    Output('heatmap-demanda', 'figure'),
    Output('mapa-movilidad', 'figure'),
    Output('acciones-table', 'data'),
    Output('acciones-table', 'columns'),
    Input('simulation-store', 'data'),
    Input('period-slider', 'value'),
)
def update_visualizations(store_data, periodo_actual):  # pragma: no cover - Dash runtime
    if not store_data:
        empty_fig = default_figure('')
        empty_map = default_map_figure('Movimientos por periodo')
        return (
            _default_card('Utilidad total'),
            _default_card('Viajes no atendidos'),
            _default_card('Tiempo total (s)'),
            empty_fig,
            empty_fig,
            empty_fig,
            empty_map,
            [],
            [],
        )

    resultados = json.loads(store_data)
    historial = resultados.get('historial_pasos', [])
    if not historial:
        empty_fig = default_figure('')
        empty_map = default_map_figure('Movimientos por periodo')
        return (
            _card(f"${resultados['utilidad_total']:.2f}", 'Utilidad total'),
            _card(str(resultados['total_viajes_perdidos']), 'Viajes no atendidos'),
            _card(f"{resultados['tiempo_total_segundos']:.2f}s", 'Tiempo total'),
            empty_fig,
            empty_fig,
            empty_fig,
            empty_map,
            [],
            [],
        )

    utilidad_total = _card(f"${resultados['utilidad_total']:.2f}", 'Utilidad total')
    viajes_card = _card(str(resultados['total_viajes_perdidos']), 'Viajes no atendidos')
    tiempo_card = _card(f"{resultados['tiempo_total_segundos']:.2f}s", 'Tiempo total')

    df_historial = pd.DataFrame([
        {
            'periodo': paso['periodo'],
            'timestamp': paso['timestamp'],
            'utilidad_paso': paso['utilidad_paso'],
            'utilidad_acumulada': paso['utilidad_acumulada'],
            **paso['conteo_acciones'],
        }
        for paso in historial
    ])

    fig_utilidad = px.line(
        df_historial,
        x='timestamp',
        y='utilidad_acumulada',
        markers=True,
        labels={'timestamp': 'Tiempo', 'utilidad_acumulada': 'Utilidad acumulada'},
        title='Evolución de la utilidad acumulada',
    )
    fig_utilidad.update_layout(hovermode='x unified')

    df_acciones = df_historial.melt(
        id_vars=['periodo'],
        value_vars=['servicios', 'reubicaciones_demanda', 'reubicaciones_carga', 'cargas', 'esperas'],
        var_name='accion',
        value_name='cantidad',
    )
    fig_acciones = px.bar(
        df_acciones,
        x='periodo',
        y='cantidad',
        color='accion',
        barmode='stack',
        title='Distribución de acciones por periodo',
        labels={'periodo': 'Periodo', 'cantidad': 'Número de vehículos', 'accion': 'Acción'},
    )

    demanda_rows: List[Dict[str, str]] = []
    for paso in historial:
        for item in paso.get('demanda_no_servida', []):
            demanda_rows.append({
                'origen': etiqueta_zona(item['origen_idx']),
                'destino': etiqueta_zona(item['destino_idx']),
                'cantidad': item['cantidad'],
            })
    if demanda_rows:
        df_demanda = pd.DataFrame(demanda_rows)
        df_demanda = df_demanda.groupby(['origen', 'destino'], as_index=False)['cantidad'].sum()
        fig_demanda = px.density_heatmap(
            df_demanda,
            x='destino',
            y='origen',
            z='cantidad',
            color_continuous_scale='Reds',
            title='Demanda no servida acumulada',
            labels={'destino': 'Destino', 'origen': 'Origen', 'cantidad': 'Viajes perdidos'},
        )
    else:
        fig_demanda = default_figure('Demanda no servida')

    periodo_objetivo = periodo_actual or 0
    paso_seleccionado = next((p for p in historial if p['periodo'] == periodo_objetivo), historial[0])
    acciones = paso_seleccionado.get('acciones', [])
    data_table = [
        {
            'Vehículo': accion['auto'],
            'Acción': accion['tipo'],
            'Origen': etiqueta_zona(accion['origen_idx']),
            'Destino': etiqueta_zona(accion['destino_idx']),
            'Distancia (km)': round(accion['distancia'], 2),
            'Valor ($)': round(accion['valor'], 2),
            'Batería (km)': round(accion['bateria'], 2),
        }
        for accion in acciones
    ]
    columns = [{'name': col, 'id': col} for col in data_table[0].keys()] if data_table else []
    fig_mapa = _build_map_figure(acciones, periodo_objetivo)

    return (
        utilidad_total,
        viajes_card,
        tiempo_card,
        fig_utilidad,
        fig_acciones,
        fig_demanda,
        fig_mapa,
        data_table,
        columns,
    )


if __name__ == '__main__':  # pragma: no cover - manual execution
    app.run(debug=True)

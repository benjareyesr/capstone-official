import parametros_matrices_nuevo as pm
import modelo_gurobi_rh as mrh
import random
import copy
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

ZONAS_MANHATTAN = [
    4, 12, 13, 24, 41, 42, 43, 45, 48, 50, 68, 74, 75, 79, 87, 88, 90, 100, 
    103, 107, 113, 114, 116, 120, 125, 127, 128, 137, 140, 141, 142, 143, 144, 
    148, 151, 152, 153, 158, 161, 162, 163, 164, 166, 170, 186, 194, 202, 209, 
    211, 224, 229, 230, 231, 232, 233, 234, 236, 237, 238, 239, 243, 244, 246, 
    249, 261, 262, 263
]
ZONAS_EQUIVALENTES = {104: 103, 105: 103}
INDICE_A_ZONA = {i: zona for i, zona in enumerate(ZONAS_MANHATTAN)}

def idx_to_zona_func(idx):
    try:
        return INDICE_A_ZONA.get(idx, idx)
    except NameError:
        return idx


def preparar_parametros_horizonte(p_full, k_inicio, T_horizonte):
    # Crea un nuevo diccionario de parámetros para el horizonte actual.
    p_horizonte = copy.deepcopy(p_full) # Copia profunda para no modificar el original
    p_horizonte['T'] = T_horizonte
    
    def slice_param(param_full):
        if isinstance(param_full, dict):
            # Asumimos dict [i][j][t]
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
                            param_sliced[i][j][t_rel] = 0.0 # O un valor por defecto
            return param_sliced
        
        elif hasattr(param_full, 'shape') and len(param_full.shape) == 3:
             # Asumimos numpy array [i, j, t]
             return param_full[:, :, k_inicio : k_inicio + T_horizonte]
        
        else:
            # No rebanar (ej. 'N', 'A', 'Cargamax', 'd', 'mapa_llegadas')
            return param_full
        

    # DEMANDA REAL + PRONÓSTICO MIXTA
    p_horizonte['Dem'] = np.zeros((p_full['N'], p_full['N'], T_horizonte), dtype=int)
    for i in range(p_full['N']):
        for j in range(p_full['N']):
            # t = 0 del horizonte → demanda REAL del paso k
            p_horizonte['Dem'][i, j, 0] = p_full['Dem'][i, j, k_inicio]

            # t = 1..T_horizonte−1 → usar PRONÓSTICO
            for t_rel in range(1, T_horizonte):
                t_abs = k_inicio + t_rel
                if t_abs < p_full['T']:
                    p_horizonte['Dem'][i, j, t_rel] = p_full['Dem_Pronostico'][i, j, t_abs]
                else:
                    p_horizonte['Dem'][i, j, t_rel] = 0
    p_horizonte['Pviaje'] = slice_param(p_full['Pviaje_Pronostico'])
    p_horizonte['Creub'] = slice_param(p_full['Creub_Pronostico'])
    
    # 'mapa_llegadas' es relativo, no necesita rebanarse.
    
    return p_horizonte

def actualizar_estado_real(
    k_paso,
    estado_real,
    decisiones_t0,
    p_full,
    idx_to_zona_func,
    verbose=True,
):
    """
    Este es el "mini-simulador". Actualiza el estado real basado en las 
    decisiones de t=0.
    Actualiza el estado real y calcula la UTILIDAD OPERATIVA .
    Ingresos reales - Costos reales (sin penalización por demanda perdida).
    """
    
    utilidad_del_paso = 0.0
    N_nodos = p_full['N']
    acciones_aplicadas: List[Dict[str, Any]] = []
    demanda_perdida_detalle: List[Dict[str, Any]] = []
    
    # 1. Actualizar autos que estaban cargando
    for a in p_full['A_indices']: # Iterar sobre TODOS los autos
        if estado_real['estado_carga'][a] > 0:
            estado_real['estado_carga'][a] -= 1 # Reducir tiempo restante
            if estado_real['estado_carga'][a] == 0:
                estado_real['carga'][a] = p_full['Cargamax']

    # 2. Implementar decisiones para autos que estaban disponibles
    autos_disponibles = list(decisiones_t0.get('y', {}).keys()) + \
                        list(decisiones_t0.get('z_dem', {}).keys()) + \
                        list(decisiones_t0.get('z_carga', {}).keys()) + \
                        list(decisiones_t0.get('esp', {}).keys()) + \
                        list(decisiones_t0.get('ch', {}).keys())
    
    # Esto es para el cálculo de 's' real
    viajes_asignados = {}
    
    for a in autos_disponibles:
        if estado_real['estado_carga'][a] > 0:
            continue 

        accion_tomada = False
        
        if a in decisiones_t0['y']:
            i, j, profit_pronosticado = decisiones_t0['y'][a] # (Ignoramos el profit pronosticado)
            gasto = p_full['d'][i, j]
            estado_real['pos'][a] = j
            estado_real['carga'][a] -= gasto
            
            # --- SUMA INGRESO REAL ---
            profit_real = p_full['Pviaje'][i][j][k_paso] 
            utilidad_del_paso += profit_real
            
            zona_i = idx_to_zona_func(i)
            zona_j = idx_to_zona_func(j)
            if verbose:
                print(f"  > (k={k_paso}) Auto {a} SERVICIO: {zona_i}({i}) -> {zona_j}({j}). Gasto: {gasto:.1f}km. Ingreso: ${profit_real:.2f}. Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True
            acciones_aplicadas.append({
                'auto': a,
                'tipo': 'servicio',
                'origen_idx': i,
                'destino_idx': j,
                'origen_zona': zona_i,
                'destino_zona': zona_j,
                'distancia': gasto,
                'valor': profit_real,
                'bateria': estado_real['carga'][a],
            })
            
            par = (i, j)
            viajes_asignados[par] = viajes_asignados.get(par, 0) + 1

        elif a in decisiones_t0['z_dem']:
            i, j, cost_pronosticado = decisiones_t0['z_dem'][a] # (Ignoramos el costo pronosticado)
            gasto = p_full['d'][i, j]
            estado_real['pos'][a] = j
            estado_real['carga'][a] -= gasto
            
            # --- RESTA COSTO REAL ---
            cost_real = p_full['Creub'][i][j][k_paso]
            utilidad_del_paso -= cost_real
            
            zona_i = idx_to_zona_func(i)
            zona_j = idx_to_zona_func(j)
            if verbose:
                print(f"  > (k={k_paso}) Auto {a} REUB. DEMANDA: {zona_i}({i}) -> {zona_j}({j}). Gasto: {gasto:.1f}km. Costo: ${cost_real:.2f}. Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True
            acciones_aplicadas.append({
                'auto': a,
                'tipo': 'reubicacion_demanda',
                'origen_idx': i,
                'destino_idx': j,
                'origen_zona': zona_i,
                'destino_zona': zona_j,
                'distancia': gasto,
                'valor': -cost_real,
                'bateria': estado_real['carga'][a],
            })

        elif a in decisiones_t0['z_carga']:
            i, j = decisiones_t0['z_carga'][a]
            gasto = p_full['d'][i, j]
            estado_real['pos'][a] = j
            estado_real['carga'][a] -= gasto
            zona_i = idx_to_zona_func(i)
            zona_j = idx_to_zona_func(j)
            if verbose:
                print(f"  > (k={k_paso}) Auto {a} REUB. CARGA: {zona_i}({i}) -> {zona_j}({j}). Gasto: {gasto:.1f}km. Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True
            acciones_aplicadas.append({
                'auto': a,
                'tipo': 'reubicacion_carga',
                'origen_idx': i,
                'destino_idx': j,
                'origen_zona': zona_i,
                'destino_zona': zona_j,
                'distancia': gasto,
                'valor': 0.0,
                'bateria': estado_real['carga'][a],
            })

        elif a in decisiones_t0['ch']:
            i = decisiones_t0['ch'][a]
            estado_real['pos'][a] = i 
            periodos_restantes = p_full['Tchg'] - 1
            estado_real['estado_carga'][a] = periodos_restantes
            zona_i = idx_to_zona_func(i)
            if verbose:
                if periodos_restantes == 0:
                    print(f"  > (k={k_paso}) Auto {a} INICIA Y TERMINA CARGA (Tchg=1) en {zona_i}({i}). Batería: {estado_real['carga'][a]:.1f}km")
                else:
                    print(f"  > (k={k_paso}) Auto {a} INICIA CARGA en {zona_i}({i}). Ocupado por {p_full['Tchg']} periodos. Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True
            acciones_aplicadas.append({
                'auto': a,
                'tipo': 'carga',
                'origen_idx': i,
                'destino_idx': i,
                'origen_zona': zona_i,
                'destino_zona': zona_i,
                'distancia': 0.0,
                'valor': 0.0,
                'bateria': estado_real['carga'][a],
            })
            
        elif a in decisiones_t0['esp']:
            i = decisiones_t0['esp'][a]
            estado_real['pos'][a] = i 
            zona_i = idx_to_zona_func(i)
            if verbose:
                print(f"  > (k={k_paso}) Auto {a} ESPERA en {zona_i}({i}). Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True
            acciones_aplicadas.append({
                'auto': a,
                'tipo': 'espera',
                'origen_idx': i,
                'destino_idx': i,
                'origen_zona': zona_i,
                'destino_zona': zona_i,
                'distancia': 0.0,
                'valor': 0.0,
                'bateria': estado_real['carga'][a],
            })

    # 3. Reportar Demanda No Servida (Solo KPI, NO afecta utilidad)
    
    if verbose:
        print(f"  --- Demanda no servida REAL en k={k_paso} ---")
    # PENALIZACION_S = 0.5 # Tu penalización

    total_perdidos_paso = 0

    for i in range(N_nodos):
        for j in range(N_nodos):
            if i == j: continue
            
            demanda_real_ij = p_full['Dem'][i, j, k_paso] 
            
            if demanda_real_ij > 0:
                viajes_hechos_ij = viajes_asignados.get((i, j), 0)
                
                if viajes_hechos_ij < demanda_real_ij:
                    viajes_perdidos = demanda_real_ij - viajes_hechos_ij
                    total_perdidos_paso += viajes_perdidos
                    
                    # costo_s_real = viajes_perdidos * PENALIZACION_S
                    # utilidad_del_paso -= costo_s_real # <--- ¡COMENTADO! NO RESTAMOS
                    
                    zona_i = idx_to_zona_func(i)
                    zona_j = idx_to_zona_func(j)
                    if verbose:
                        print(f"    > De {zona_i}({i}) a {zona_j}({j}): {viajes_perdidos} viajes perdidos")
                    demanda_perdida_detalle.append({
                        'origen_idx': i,
                        'destino_idx': j,
                        'origen_zona': zona_i,
                        'destino_zona': zona_j,
                        'cantidad': viajes_perdidos,
                    })
    
    # 4. Imprimir utilidad OPERATIVA del paso
    if verbose:
        print(f"  ---------------------------------------------------")
        print(f"  UTILIDAD OPERATIVA DEL PASO k={k_paso}: ${utilidad_del_paso:.2f}")
        print(f"  TOTAL VIAJES PERDIDOS: {total_perdidos_paso}")
        print(f"  ---------------------------------------------------")

    return estado_real, utilidad_del_paso, acciones_aplicadas, demanda_perdida_detalle


def ejecutar_simulacion(
    K_TOTAL: int = 8,
    T_HORIZONTE: int = 4,
    FECHA_STR: str = '2024-09-15',
    seed: int = 7,
    numero_autos: int | None = None,
    capturar_historial: bool = False,
    verbose: bool = True,
):
    """Ejecuta la simulación de horizonte rodante.

    Cuando ``capturar_historial`` es ``True`` se retorna un diccionario con la
    evolución completa (útil para dashboards), en caso contrario solo se
    calcula la utilidad final imprimiendo logs en pantalla.
    """

    if T_HORIZONTE >= K_TOTAL:
        raise ValueError("T_HORIZONTE debe ser menor a K_TOTAL para ejecutar la simulación")

    if numero_autos is not None:
        if not (1 <= int(numero_autos) <= pm.MAX_NUMERO_VEHICULOS):
            raise ValueError(f"numero_autos debe estar entre 1 y {pm.MAX_NUMERO_VEHICULOS}")
        numero_autos = int(numero_autos)
    else:
        numero_autos = pm.NUMERO_VEHICULOS

    if verbose:
        print(f"Cargando parámetros para {K_TOTAL} periodos totales...")

    p_full = pm.cargar_parametros_modelo(
        T_total=K_TOTAL,
        fecha_dia_str=FECHA_STR,
        numero_vehiculos=numero_autos,
    )

    N_nodos = p_full['N']
    A_autos = p_full['A']
    p_full['A_indices'] = list(range(A_autos))

    if verbose:
        print(f"Simulación de Horizonte Rodante con {A_autos} autos, {N_nodos} nodos.")
        print(f"Horizonte total: {K_TOTAL} periodos ({(K_TOTAL*pm.PERIODO_SIMULACION)/60} horas)")
        print(f"Horizonte rodante: {T_HORIZONTE} periodos ({(T_HORIZONTE*pm.PERIODO_SIMULACION)/60} horas)")

    random.seed(seed)
    estado_real = {
        'pos': {a: random.choice(range(N_nodos)) for a in p_full['A_indices']},
        'carga': {a: p_full['Cargamax'] for a in p_full['A_indices']},
        'estado_carga': {a: 0 for a in p_full['A_indices']}
    }

    if verbose:
        print("Posiciones iniciales aleatorias:", estado_real['pos'])

    utilidad_total_acumulada = 0.0
    total_viajes_perdidos = 0
    pasos_historial: List[Dict[str, Any]] = []
    fecha_base = datetime.fromisoformat(FECHA_STR)
    tiempos_paso: List[float] = []

    for k in range(K_TOTAL - T_HORIZONTE):
        start_time = time.time()
        if verbose:
            hora = (k * pm.PERIODO_SIMULACION) // 60
            minuto = (k * pm.PERIODO_SIMULACION) % 60
            print(f"\n--- PASO DE SIMULACIÓN k = {k} ({hora}:{minuto:02d}) ---")

        autos_disponibles = [a for a in p_full['A_indices'] if estado_real['estado_carga'][a] == 0]
        if verbose:
            print(f"Autos disponibles: {len(autos_disponibles)} / {A_autos}")

        p_horizonte = preparar_parametros_horizonte(p_full, k, T_HORIZONTE)

        ocupacion_previa = {i: {t: 0 for t in range(T_HORIZONTE)} for i in range(N_nodos)}
        for a in p_full['A_indices']:
            if estado_real['estado_carga'][a] > 0:
                estacion_ocupada = estado_real['pos'][a]
                periodos_restantes = estado_real['estado_carga'][a]
                for t_rel in range(min(periodos_restantes, T_HORIZONTE)):
                    ocupacion_previa[estacion_ocupada][t_rel] += 1

        estado_inicial = {
            'autos_disponibles': autos_disponibles,
            'pos': estado_real['pos'],
            'carga': estado_real['carga'],
            'ocupacion_previa': ocupacion_previa,
        }

        decisiones_t0 = mrh.resolver_paso(p_horizonte, estado_inicial)

        estado_real, utilidad_del_paso, acciones_aplicadas, demanda_perdida = actualizar_estado_real(
            k,
            estado_real,
            decisiones_t0,
            p_full,
            idx_to_zona_func,
            verbose=verbose,
        )

        utilidad_total_acumulada += utilidad_del_paso
        total_viajes_perdidos += sum(item['cantidad'] for item in demanda_perdida)

        paso_dt = fecha_base + timedelta(minutes=pm.PERIODO_SIMULACION * k)
        paso_ts = paso_dt.isoformat()
        for accion in acciones_aplicadas:
            accion['periodo'] = k
            accion['timestamp'] = paso_ts
        for perdida in demanda_perdida:
            perdida['periodo'] = k
            perdida['timestamp'] = paso_ts

        duracion = time.time() - start_time
        tiempos_paso.append(duracion)
        if verbose:
            print(f"  [Tiempo de cómputo del paso: {duracion:.2f} segundos]")
            print(f"  UTILIDAD TOTAL ACUMULADA: ${utilidad_total_acumulada:.2f}")

        if capturar_historial:
            pasos_historial.append({
                'periodo': k,
                'timestamp': paso_ts,
                'autos_disponibles': len(autos_disponibles),
                'utilidad_paso': utilidad_del_paso,
                'utilidad_acumulada': utilidad_total_acumulada,
                'duracion_segundos': duracion,
                'acciones': acciones_aplicadas,
                'demanda_no_servida': demanda_perdida,
                'conteo_acciones': {
                    'servicios': len(decisiones_t0['y']),
                    'reubicaciones_demanda': len(decisiones_t0['z_dem']),
                    'reubicaciones_carga': len(decisiones_t0['z_carga']),
                    'cargas': len(decisiones_t0['ch']),
                    'esperas': len(decisiones_t0['esp']),
                },
            })

    if verbose:
        print(f"GANANCIA NETA TOTAL FINAL: ${utilidad_total_acumulada:.2f}")

    resultado = {
        'configuracion': {
            'K_TOTAL': K_TOTAL,
            'T_HORIZONTE': T_HORIZONTE,
            'FECHA_STR': FECHA_STR,
            'seed': seed,
            'numero_autos': numero_autos,
        },
        'utilidad_total': utilidad_total_acumulada,
        'pasos_ejecutados': K_TOTAL - T_HORIZONTE,
        'total_viajes_perdidos': total_viajes_perdidos,
        'estado_final': estado_real,
        'tiempo_total_segundos': sum(tiempos_paso),
    }

    if capturar_historial:
        resultado['historial_pasos'] = pasos_historial

    return resultado


if __name__ == "__main__":
    ejecutar_simulacion()
import parametros_matrices_nuevo as pm
import modelo_gurobi_rh as mrh
import random
import copy
import numpy as np
import time

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

def actualizar_estado_real(k_paso, estado_real, decisiones_t0, p_full, idx_to_zona_func):
    """
    Este es el "mini-simulador". Actualiza el estado real basado en las 
    decisiones de t=0.
    Actualiza el estado real y calcula la UTILIDAD OPERATIVA .
    Ingresos reales - Costos reales (sin penalización por demanda perdida).
    """
    
    utilidad_del_paso = 0.0
    N_nodos = p_full['N']
    
    # 1. Actualizar autos que estaban cargando
    for a in p_full['A_indices']: # Iterar sobre TODOS los autos
        if estado_real['estado_carga'][a] > 0:
            estado_real['estado_carga'][a] -= 1 # Reducir tiempo restante
            if estado_real['estado_carga'][a] == 0:
                # ¡Terminó de cargar! (Silenciosamente)
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
            print(f"  > (k={k_paso}) Auto {a} SERVICIO: {zona_i}({i}) -> {zona_j}({j}). Gasto: {gasto:.1f}km. Ingreso: ${profit_real:.2f}. Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True
            
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
            print(f"  > (k={k_paso}) Auto {a} REUB. DEMANDA: {zona_i}({i}) -> {zona_j}({j}). Gasto: {gasto:.1f}km. Costo: ${cost_real:.2f}. Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True

        elif a in decisiones_t0['z_carga']:
            i, j = decisiones_t0['z_carga'][a]
            gasto = p_full['d'][i, j]
            estado_real['pos'][a] = j
            estado_real['carga'][a] -= gasto
            zona_i = idx_to_zona_func(i)
            zona_j = idx_to_zona_func(j)
            print(f"  > (k={k_paso}) Auto {a} REUB. CARGA: {zona_i}({i}) -> {zona_j}({j}). Gasto: {gasto:.1f}km. Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True

        elif a in decisiones_t0['ch']:
            i = decisiones_t0['ch'][a]
            estado_real['pos'][a] = i 
            periodos_restantes = p_full['Tchg'] - 1
            estado_real['estado_carga'][a] = periodos_restantes
            zona_i = idx_to_zona_func(i)
            if periodos_restantes == 0:
                print(f"  > (k={k_paso}) Auto {a} INICIA Y TERMINA CARGA (Tchg=1) en {zona_i}({i}). Batería: {estado_real['carga'][a]:.1f}km")
            else:
                print(f"  > (k={k_paso}) Auto {a} INICIA CARGA en {zona_i}({i}). Ocupado por {p_full['Tchg']} periodos. Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True
            
        elif a in decisiones_t0['esp']:
            i = decisiones_t0['esp'][a]
            estado_real['pos'][a] = i 
            zona_i = idx_to_zona_func(i)
            print(f"  > (k={k_paso}) Auto {a} ESPERA en {zona_i}({i}). Batería: {estado_real['carga'][a]:.1f}km")
            accion_tomada = True

    # 3. Reportar Demanda No Servida (Solo KPI, NO afecta utilidad)
    
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
                    print(f"    > De {zona_i}({i}) a {zona_j}({j}): {viajes_perdidos} viajes perdidos")
    
    # 4. Imprimir utilidad OPERATIVA del paso
    print(f"  ---------------------------------------------------")
    print(f"  UTILIDAD OPERATIVA DEL PASO k={k_paso}: ${utilidad_del_paso:.2f}")
    print(f"  TOTAL VIAJES PERDIDOS: {total_perdidos_paso}")
    print(f"  ---------------------------------------------------")

    return estado_real, utilidad_del_paso


# --------------------------------------------------
# SCRIPT PRINCIPAL DE SIMULACIÓN
# --------------------------------------------------
def ejecutar_simulacion():
    
    # --- 1. CONFIGURACIÓN ---
    K_TOTAL = 8     # 24 horas * 4 periodos/hora
    T_HORIZONTE = 4    # Mirar 1 hora hacia adelante (4 * 15 min)
    FECHA_STR = '2024-09-15'
    
    print(f"Cargando parámetros para {K_TOTAL} periodos totales...")
    p_full = pm.cargar_parametros_modelo(T_total=K_TOTAL, fecha_dia_str=FECHA_STR)
    
    # (Añadimos esto para que sea más fácil iterar)
    N_nodos = p_full['N']
    A_autos = p_full['A']
    p_full['A_indices'] = list(range(A_autos))
    
    print(f"Simulación de Horizonte Rodante con {A_autos} autos, {N_nodos} nodos.")
    print(f"Horizonte total: {K_TOTAL} periodos ({(K_TOTAL*15)/60} horas)")
    print(f"Horizonte rodante: {T_HORIZONTE} periodos ({(T_HORIZONTE*15)/60} horas)")
    
    # --- 2. INICIALIZAR ESTADO REAL ---
    random.seed(7)
    estado_real = {
        'pos': {a: random.choice(range(N_nodos)) for a in p_full['A_indices']},
        'carga': {a: p_full['Cargamax'] for a in p_full['A_indices']},
        'estado_carga': {a: 0 for a in p_full['A_indices']} 
    }
    
    # --- NUEVO: Inicializar contadores de utilidad ---
    utilidad_total_acumulada = 0.0
    historial_acciones = []
    
    print("Posiciones iniciales aleatorias:", estado_real['pos'])
    
    # --- 3. BUCLE PRINCIPAL DE SIMULACIÓN ---
    for k in range(K_TOTAL - T_HORIZONTE): 
        # --- MEDIR TIEMPO ---
        start_time = time.time()

        print(f"\n--- PASO DE SIMULACIÓN k = {k} ({(k*15)//60}:{(k*15)%60:02d}) ---")
        
        # 3.1. Identificar autos disponibles vs. cargando
        autos_disponibles = [a for a in p_full['A_indices'] if estado_real['estado_carga'][a] == 0]
        
        print(f"Autos disponibles: {len(autos_disponibles)} / {A_autos}")
        
        # 3.2. Preparar parámetros para este horizonte
        p_horizonte = preparar_parametros_horizonte(p_full, k, T_HORIZONTE)
        
        
        # --- 3.3. (NUEVO) CALCULAR OCUPACIÓN PREVIA DE ESTACIONES ---
        # Pre-calculamos la ocupación para el horizonte T_HORIZONTE
        # ocupacion_previa[i][t] = cuántos autos (fuera de línea) 
        #                           están cargando en la estación 'i' en el período 't'
        
        ocupacion_previa = {i: {t: 0 for t in range(T_HORIZONTE)} for i in range(N_nodos)}
        
        for a in p_full['A_indices']:
            if estado_real['estado_carga'][a] > 0:
                # Este auto 'a' está cargando
                estacion_ocupada = estado_real['pos'][a]
                periodos_restantes = estado_real['estado_carga'][a]
                
                # Ocupará un puesto en esta estación por los próximos 'periodos_restantes'
                # (o hasta que se acabe el horizonte de planificación)
                for t_rel in range(min(periodos_restantes, T_HORIZONTE)):
                    ocupacion_previa[estacion_ocupada][t_rel] += 1
        
        # -----------------------------------------------------------------

        
        # 3.4. Preparar estado inicial para el modelo (AHORA INCLUYE OCUPACIÓN)
        estado_inicial = {
            'autos_disponibles': autos_disponibles,
            'pos': estado_real['pos'],
            'carga': estado_real['carga'],
            'ocupacion_previa': ocupacion_previa  # <-- Pasamos la nueva info
        }
        
        # 3.5. Resolver el paso de optimización
        decisiones_t0 = mrh.resolver_paso(p_horizonte, estado_inicial)
        
        # 3.6. Guardar y actualizar el estado real
        historial_acciones.append(decisiones_t0)
        estado_real, utilidad_del_paso = actualizar_estado_real(k, estado_real, decisiones_t0, p_full, idx_to_zona_func)
        
        utilidad_total_acumulada += utilidad_del_paso
        
        end_time = time.time()
        duracion = end_time - start_time
        print(f"  [Tiempo de cómputo del paso: {duracion:.2f} segundos]")
        print(f"  UTILIDAD TOTAL ACUMULADA: ${utilidad_total_acumulada:.2f}")
        
    print(f"GANANCIA NETA TOTAL FINAL: ${utilidad_total_acumulada:.2f}")
    # Aquí puedes añadir análisis del historial_acciones o del estado_real final

if __name__ == "__main__":
    ejecutar_simulacion()
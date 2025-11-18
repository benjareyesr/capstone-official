from gurobipy import Model, GRB, quicksum, LinExpr

def resolver_paso(p_horizonte, estado_inicial):
    # Resuelve un paso del modelo de optimización.
    m = Model("MODELO_HORIZONTE_RODANTE")
    m.setParam('OutputFlag', 0) # Desactiva el log de Gurobi para la simulación

    # --------------------------------------------------
    # PARÁMETROS
    # --------------------------------------------------
    
    # Extraer parámetros del horizonte
    N, T, E_min, Tchg = p_horizonte['N'], p_horizonte['T'], p_horizonte['E_min'], p_horizonte['Tchg']
    mapa_llegadas_viaje = p_horizonte['mapa_llegadas']
    # Solo optimizamos los autos que NO están cargando
    A_disponibles = estado_inicial['autos_disponibles']
    if not A_disponibles:
        print("No hay autos disponibles para optimizar en este paso.")
        return {} # Devolver decisiones vacías si no hay autos
    ocupacion_previa = estado_inicial['ocupacion_previa'] #CUantos autos ya están cargando en cada estación

    # --------------------------------------------------
    # VARIABLES
    # --------------------------------------------------

    # Las variables ahora se indexan por A_disponibles, no por range(A)
    y = m.addVars(N, N, T, A_disponibles, vtype=GRB.BINARY, name="y")
    z_dem = m.addVars(N, N, T, A_disponibles, vtype=GRB.BINARY, name="z_dem")
    z_carga = m.addVars(N, N, T, A_disponibles, vtype=GRB.BINARY, name="z_carga")
    esp = m.addVars(N, T, A_disponibles, vtype=GRB.BINARY, name="esp")
    ch = m.addVars(N, T, A_disponibles, vtype=GRB.BINARY, name="ch")
    pos = m.addVars(N, T, A_disponibles, vtype=GRB.BINARY, name="pos")
    carga = m.addVars(T+1, A_disponibles, vtype=GRB.CONTINUOUS, lb=0, ub=p_horizonte['Cargamax'], name="carga")
    finCarga = m.addVars(T+1, A_disponibles, vtype=GRB.BINARY, name="finCarga")
    bHigh = m.addVars(T, A_disponibles, vtype=GRB.BINARY, name="bHigh")
    s = m.addVars(N, N, T, vtype=GRB.INTEGER, name="s", lb=0)

    # --------------------------------------------------
    # FUNCIÓN OBJETIVO (CON VALOR TERMINAL)
    # --------------------------------------------------
    
    m.setObjective(
        quicksum(
            y[i, j, t, a] * p_horizonte['Pviaje'][i][j][t]
            for i in range(N) for j in range(N) for t in range(T) for a in A_disponibles
        )
        - quicksum(
            z_dem[i, j, t, a] * p_horizonte['Creub'][i][j][t]
            for i in range(N) for j in range(N) for t in range(T) for a in A_disponibles
        )
        - quicksum(
            s[i, j, t] * 0.5
            for i in range(N) for j in range(N) for t in range(T)
        )
    , GRB.MAXIMIZE
    )

    # -------------------------
    # RESTRICCIONES (Con A_disponibles)
    # -------------------------

    # 1) Vehículo inicia en un nodo (DESDE ESTADO REAL)
    for a in A_disponibles:
        nodo_inicial = estado_inicial['pos'][a]
        m.addConstr(pos[nodo_inicial, 0, a] == 1)

    # 2) Carga inicial (DESDE ESTADO REAL)
    for a in A_disponibles:
        carga_inicial = estado_inicial['carga'][a]
        m.addConstr(carga[0, a] == carga_inicial)

    # 3) Satisfacer la demanda
    for i in range(N):
        for t in range(T):
            for j in range(N):
                m.addConstr(
                    # La suma de 'y' ahora usa A_disponibles
                    quicksum(y[i, j, t, a] for a in A_disponibles) + s[i, j, t] == p_horizonte['Dem'][i, j, t]
                )

    # 4) Un auto solo puede hacer una acción por periodo
    for t in range(T):
        for a in A_disponibles:
            m.addConstr(quicksum(pos[i, t, a] for i in range(N)) <= 1)

    # 5) Relación acciones - posición
    for t in range(T):
        for a in A_disponibles:
            m.addConstr(
                quicksum(
                    y[i, j, t, a] + z_dem[i, j, t, a] + z_carga[i, j, t, a]
                    for i in range(N) for j in range(N)
                )
                + quicksum(esp[i, t, a] + ch[i, t, a] for i in range(N))
                == quicksum(pos[i, t, a] for i in range(N))
            )

    # 6) Acciones solo desde posición
    for t in range(T):
        for a in A_disponibles:
            for i in range(N):
                m.addConstr(quicksum(y[i, j, t, a] for j in range(N)) <= pos[i, t, a])
                m.addConstr(quicksum(z_dem[i, j, t, a] for j in range(N)) <= pos[i, t, a])
                m.addConstr(quicksum(z_carga[i, j, t, a] for j in range(N)) <= pos[i, t, a])
                m.addConstr(esp[i, t, a] <= pos[i, t, a])
                m.addConstr(ch[i, t, a] <= pos[i, t, a])

    # 7) Balance de flujo de posición
    for a in A_disponibles:
        for i in range(N):
            for t in range(T - 1):
                k_llegada = t + 1
                salidas_svc = quicksum(y[i, j, t, a] for j in range(N) if i != j)
                salidas_reb = quicksum(z_dem[i, j, t, a] + z_carga[i, j, t, a] for j in range(N) if i != j)
                salida_chg = ch[i, t, a]
                llegv, llegr, llegc = LinExpr(), LinExpr(), LinExpr()
                
                for j in range(N):
                    if i == j: continue
                    clave_viaje = (j, i, k_llegada); lista_k_inicio = mapa_llegadas_viaje.get(clave_viaje, [])
                    if lista_k_inicio:
                        llegv.add(quicksum(y[j, i, k_start, a] for k_start in lista_k_inicio))
                        llegr.add(quicksum(z_dem[j, i, k_start, a] + z_carga[j, i, k_start, a] for k_start in lista_k_inicio))
                
                k_inicio_carga = k_llegada - Tchg
                if k_inicio_carga >= 0 and i in p_horizonte['E']:
                    llegc = ch[i, k_inicio_carga, a]
                
                m.addConstr(pos[i, k_llegada, a] == pos[i, t, a] - salidas_svc - salidas_reb - salida_chg + llegv + llegr + llegc)

    # 8) Restricciones de carga (Capacidad, etc.)
    zonas_sin_estacion = [i for i in range(N) if i not in p_horizonte['E']]
    for i in zonas_sin_estacion:
        for t in range(T):
            for a in A_disponibles:
                ch[i, t, a].UB = 0
                
    destinos_sin_estacion = [j for j in range(N) if j not in p_horizonte['E']]
    for i in range(N):
        for j in destinos_sin_estacion:
            for t in range(T):
                for a in A_disponibles:
                    z_carga[i, j, t, a].UB = 0

    for i in p_horizonte['E']:
        for t in range(T): # T es T_HORIZONTE
            # 1. Autos que ESTE modelo decide enviar a cargar (lógica de ventana)
            # (Cuenta cuántos autos inician carga en la ventana [t-Tchg+1, t])
            inicio_ventana = max(0, t - Tchg + 1)
            autos_cargando_nuevos = quicksum(
                ch[i, t_prima, a]
                for a in A_disponibles
                for t_prima in range(inicio_ventana, t + 1)
            )

            # 2. Autos que YA ESTABAN cargando (información pre-calculada)
            # (Cuenta cuántos autos 'fuera de línea' están ocupando un 
            # puesto en el período 't')
            autos_cargando_previos = ocupacion_previa[i][t]
            # 3. La restricción real: Nuevos + Previos <= Capacidad
            m.addConstr(
                autos_cargando_nuevos + autos_cargando_previos <= p_horizonte['CapEstacion'],
                name=f"CapacidadEstacion_Real_{i}_{t}"
            )

    # 9) Evolución de la carga (Big-M)
    M_GRANDE = p_horizonte['Cargamax'] + 1.0
    for a in A_disponibles:
        for t in range(T):
            gasto_viaje_t = LinExpr()
            for i in range(N):
                for j in range(N):
                    if i == j: continue
                    gasto_viaje_t.add((y[i, j, t, a] + z_dem[i, j, t, a] + z_carga[i, j, t, a]) * p_horizonte['d'][i, j])
            
            ecuacion_base = carga[t, a] - gasto_viaje_t
            k_llegada = t + 1
            k_inicio_carga = k_llegada - Tchg
            
            if k_inicio_carga >= 0:
                m.addConstr(finCarga[k_llegada, a] == quicksum(ch[i, k_inicio_carga, a] for i in p_horizonte['E']))
            else:
                m.addConstr(finCarga[k_llegada, a] == 0)
            
            m.addConstr(carga[t+1, a] <= ecuacion_base + M_GRANDE * finCarga[k_llegada, a])
            m.addConstr(carga[t+1, a] >= ecuacion_base - M_GRANDE * finCarga[k_llegada, a])
            m.addConstr(carga[t+1, a] <= p_horizonte['Cargamax'] + M_GRANDE * (1 - finCarga[k_llegada, a]))
            m.addConstr(carga[t+1, a] >= p_horizonte['Cargamax'] - M_GRANDE * (1 - finCarga[k_llegada, a]))

    # 10) Restricciones de energía para viajes
    m.addConstrs(
        (carga[t, a] >= (p_horizonte['d'][i, j] + E_min) * y[i, j, t, a]
         for t in range(T) for a in A_disponibles for i in range(N) for j in range(N) if i != j),
    )
    m.addConstrs(
        (carga[t, a] >= (p_horizonte['d'][i, j] + E_min) * z_dem[i, j, t, a]
         for t in range(T) for a in A_disponibles for i in range(N) for j in range(N) if i != j),
    )
    m.addConstrs(
        (carga[t, a] >= p_horizonte['d'][i, j] * z_carga[i, j, t, a]
         for t in range(T) for a in A_disponibles for i in range(N) for j in range(N) if i != j),
    )

    # 11) Batería alta / baja (bHigh)
    M = p_horizonte['Cargamax']
    UMBRAL_ALTA = 10
    EPSILON_ROBUSTO = 1e-4
    
    for t in range(T):
        for a in A_disponibles:
            m.addConstr(carga[t, a] >= UMBRAL_ALTA - M * (1 - bHigh[t, a]))
            m.addConstr(carga[t, a] <= (UMBRAL_ALTA - EPSILON_ROBUSTO) + M * bHigh[t, a])
            m.addConstr(quicksum(y[i, j, t, a] for i in range(N) for j in range(N) if i != j) <= bHigh[t, a])
            m.addConstr(quicksum(esp[i, t, a] for i in range(N)) <= bHigh[t, a])
            m.addConstr(quicksum(z_dem[i, j, t, a] for i in range(N) for j in range(N) if i != j) <= bHigh[t, a])
            m.addConstr(quicksum(z_carga[i, j, t, a] for i in range(N) for j in range(N) if i != j) <= 1 - bHigh[t, a])
            # Solo permitir INICIAR carga (ch) si la batería es baja (bHigh=0)
            m.addConstr(quicksum(ch[i, t, a] for i in p_horizonte['E']) <= (1 - bHigh[t, a]))

    # -------------------------
    # OPTIMIZAR
    # -------------------------
    #m.setParam('MIPGap', 0.02)
    m.optimize()

    # -------------------------
    # EXTRACCIÓN DE RESULTADOS (SOLO t=0)
    # -------------------------
    
    decisiones_t0 = {
        'y': {}, 'z_dem': {}, 'z_carga': {}, 'esp': {}, 'ch': {},
        's': {}, 'ganancia_bruta': 0.0
    }
    
    if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
        
        # 1. Guardar acciones de vehículos
        for a in A_disponibles:
            accion_encontrada = False
            for i in range(N):
                for j in range(N):
                    if i != j:
                        if y[i, j, 0, a].X > 0.5:
                            profit = p_horizonte['Pviaje'][i][j][0]
                            decisiones_t0['y'][a] = (i, j, profit) # (i, j, ganancia)
                            accion_encontrada = True; break
                        if z_dem[i, j, 0, a].X > 0.5:
                            cost = p_horizonte['Creub'][i][j][0]
                            decisiones_t0['z_dem'][a] = (i, j, cost) # (i, j, costo)
                            accion_encontrada = True; break
                        if z_carga[i, j, 0, a].X > 0.5:
                            decisiones_t0['z_carga'][a] = (i, j)
                            accion_encontrada = True; break
                if accion_encontrada: break
            
            if not accion_encontrada:
                for i in range(N):
                    if esp[i, 0, a].X > 0.5:
                        decisiones_t0['esp'][a] = i
                        accion_encontrada = True; break
                    if ch[i, 0, a].X > 0.5:
                        decisiones_t0['ch'][a] = i
                        accion_encontrada = True; break
            
            if not accion_encontrada:
                decisiones_t0['esp'][a] = estado_inicial['pos'][a]

        # 2. Guardar demanda no servida (s) en t=0
        PENALIZACION_S = 0.5 
        for i in range(N):
            for j in range(N):
                if s[i, j, 0].X > 0.5:
                    cantidad = round(s[i, j, 0].X)
                    costo_s = cantidad * PENALIZACION_S
                    decisiones_t0['s'][(i, j)] = (cantidad, costo_s)

    else:
        print(f"ERROR: Modelo infactible en el paso. Forzando 'espera' para todos.")
        for a in A_disponibles:
            decisiones_t0['esp'][a] = estado_inicial['pos'][a]
            
    return decisiones_t0
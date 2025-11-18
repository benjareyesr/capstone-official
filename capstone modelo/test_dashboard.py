"""
Script de prueba rápida del dashboard.
Este script ejecuta una simulación corta para verificar que todo funciona.
"""

import sys
from pathlib import Path

# Agregar el path del módulo
sys.path.append(str(Path(__file__).parent))

import parametros_matrices_nuevo as pm
import modelo_gurobi_rh as mrh
import random
import copy

def test_dashboard_rapido():
    """Prueba rápida con pocos vehículos y periodos."""
    
    print("=" * 60)
    print("PRUEBA RÁPIDA DEL SISTEMA")
    print("=" * 60)
    
    # Configuración mínima
    T_simulacion = 3
    T_horizonte = 2
    num_vehiculos = 5
    fecha_dia = "2024-09-15"
    
    print(f"\n📊 Configuración:")
    print(f"   - Vehículos: {num_vehiculos}")
    print(f"   - Periodos: {T_simulacion}")
    print(f"   - Horizonte: {T_horizonte}")
    print(f"   - Fecha: {fecha_dia}")
    
    # Cargar parámetros
    print(f"\n⏳ Cargando parámetros del modelo...")
    p_full = pm.cargar_parametros_modelo(T_total=T_simulacion, fecha_dia_str=fecha_dia)
    
    # Ajustar número de vehículos
    p_full['A'] = num_vehiculos
    p_full['A_indices'] = list(range(num_vehiculos))
    
    # Estado inicial
    print(f"\n🚗 Inicializando {num_vehiculos} vehículos...")
    estado_inicial = {
        'pos': {},
        'carga': {},
        'estado_carga': {},
        'A_indices': p_full['A_indices']
    }
    
    random.seed(42)
    for a in p_full['A_indices']:
        estado_inicial['pos'][a] = random.randint(0, pm.N_ZONAS - 1)
        estado_inicial['carga'][a] = random.uniform(100, p_full['Cargamax'])
        estado_inicial['estado_carga'][a] = 0
        
        zona = pm.INDICE_A_ZONA[estado_inicial['pos'][a]]
        print(f"   Auto {a}: Zona {zona}, Batería {estado_inicial['carga'][a]:.1f}km")
    
    # Simulación
    print(f"\n🔄 Ejecutando simulación...")
    estado_real = copy.deepcopy(estado_inicial)
    utilidad_acumulada = 0.0
    
    for k_paso in range(T_simulacion):
        print(f"\n--- Periodo {k_paso} ---")
        
        # Preparar horizonte
        p_horizonte = copy.deepcopy(p_full)
        p_horizonte['T'] = min(T_horizonte, T_simulacion - k_paso)
        
        # Calcular autos disponibles
        autos_disponibles = [a for a in p_full['A_indices'] if estado_real['estado_carga'][a] == 0]
        print(f"Autos disponibles: {len(autos_disponibles)}/{num_vehiculos}")
        
        # Calcular ocupación previa
        ocupacion_previa = {i: {t: 0 for t in range(p_horizonte['T'])} for i in range(pm.N_ZONAS)}
        for a in estado_real['A_indices']:
            if estado_real['estado_carga'][a] > 0:
                nodo = estado_real['pos'][a]
                tiempo_restante = estado_real['estado_carga'][a]
                for t in range(min(tiempo_restante, p_horizonte['T'])):
                    ocupacion_previa[nodo][t] += 1
        
        estado_paso = {
            'pos': estado_real['pos'],
            'carga': estado_real['carga'],
            'autos_disponibles': autos_disponibles,
            'ocupacion_previa': ocupacion_previa
        }
        
        # Resolver paso
        print(f"Optimizando...")
        decisiones = mrh.resolver_paso(p_horizonte, estado_paso)
        
        # Actualizar estado
        utilidad_paso = 0.0
        
        # Actualizar autos cargando
        for a in p_full['A_indices']:
            if estado_real['estado_carga'][a] > 0:
                estado_real['estado_carga'][a] -= 1
                if estado_real['estado_carga'][a] == 0:
                    estado_real['carga'][a] = p_full['Cargamax']
                    zona = pm.INDICE_A_ZONA[estado_real['pos'][a]]
                    print(f"   ✓ Auto {a} terminó de cargar en zona {zona}")
        
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
                zona_i = pm.INDICE_A_ZONA[i]
                zona_j = pm.INDICE_A_ZONA[j]
                print(f"   🚕 Auto {a}: SERVICIO {zona_i}→{zona_j} (+${profit:.2f})")
            
            elif a in decisiones.get('ch', {}):
                i = decisiones['ch'][a]
                estado_real['pos'][a] = i
                periodos_restantes = p_full['Tchg'] - 1
                estado_real['estado_carga'][a] = periodos_restantes
                zona = pm.INDICE_A_ZONA[i]
                print(f"   🔌 Auto {a}: INICIA CARGA en zona {zona}")
            
            elif a in decisiones.get('esp', {}):
                i = decisiones['esp'][a]
                estado_real['pos'][a] = i
                zona = pm.INDICE_A_ZONA[i]
                print(f"   ⏸️  Auto {a}: ESPERA en zona {zona}")
        
        utilidad_acumulada += utilidad_paso
        print(f"Utilidad del periodo: ${utilidad_paso:.2f}")
        print(f"Utilidad acumulada: ${utilidad_acumulada:.2f}")
    
    print(f"\n✅ SIMULACIÓN COMPLETADA")
    print(f"=" * 60)
    print(f"Utilidad Total: ${utilidad_acumulada:.2f}")
    print(f"=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        test_dashboard_rapido()
        print("\n✅ El sistema está funcionando correctamente!")
        print("Ahora puedes ejecutar el dashboard completo con:")
        print("   streamlit run dashboard.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

# MONITOR ULTRA DETALLADO DE SIMULACIÓN 
# Control paso a paso con máximo detalle

import sys
sys.path.append('../')
sys.path.append('.')

from simulacion_caso_base_completa import SimuladorRideHailing
import datetime
import pandas as pd
import os
from parametros_matrices import obtener_tiempo

FECHA_SIMULACION = datetime.date(2024, 9, 15)
PERIODOS_MAXIMOS = 96  # 96 períodos = 24 horas


# Poner Flase si es que se quiere ir viendo los resultado periodo por periodo
AUTO_CONTINUAR = True

class MonitorUltraDetallado:
    def __init__(self):
        self.simulador = SimuladorRideHailing()
        self.log_detallado = []
        self.periodo_actual = 0
        
        # Configurar para máximo detalle
        print("🚗 MONITOR ULTRA DETALLADO - CONFIGURACIÓN INICIAL")
        print("="*70)
        print(f"📅 Fecha: {FECHA_SIMULACION}")
        print(f"🚗 Flota: {len(self.simulador.vehiculos)} vehículos")
        print(f"🗺️  Zonas con estaciones: {list(self.simulador.estaciones_carga.keys())}")
        print(f"⏱️  Períodos a simular: {PERIODOS_MAXIMOS}")
        print(f"🔋 Autonomía vehículos: {self.simulador.vehiculos[0].bateria_actual} km")
        print(f"📊 Demanda pronosticada cargada: {self.simulador.dem_pronostico is not None}")
        print("="*70)
        
        self.mostrar_configuracion_inicial()
    
    def obtener_tipo_hora(self, periodo):
        """Determina el tipo de hora según el período"""
        hora = (periodo * 15) // 60
        if 0 <= hora <= 7:
            return 'valle'
        elif 16 <= hora <= 20:
            return 'punta'
        else:
            return 'normal'
        
    def mostrar_configuracion_inicial(self):
        """Muestra el estado inicial de todo el sistema"""
        print("\\n🏁 ESTADO INICIAL DEL SISTEMA")
        print("-"*50)
        
        # Posiciones iniciales de vehículos
        print("🚗 POSICIONES INICIALES DE VEHÍCULOS:")
        for v in self.simulador.vehiculos:
            print(f"   • Vehículo {v.id}: Zona {v.zona_actual}, Batería: {v.bateria_actual} km")
        
        # Estaciones de carga
        print("\\n🔋 ESTACIONES DE CARGA:")
        for zona, info in self.simulador.estaciones_carga.items():
            print(f"   • Zona {zona}: Capacidad {info['capacidad_maxima']} vehículos")
        
        # Explicar parámetros clave (importar parámetros reales)
        from simulacion_caso_base_completa import PORCENTAJE_DEMANDA, NUMERO_VEHICULOS, TIEMPO_RECARGA, PERIODO_SIMULACION
        print(f"\\n⚙️ PARÁMETROS CLAVE:")
        print(f"   • Porcentaje de demanda real: {PORCENTAJE_DEMANDA*100:.1f}%")
        print(f"   • Tiempo de carga: {TIEMPO_RECARGA} minutos")
        print(f"   • Período de simulación: {PERIODO_SIMULACION} minutos")
        print(f"   • Número de vehículos: {NUMERO_VEHICULOS}")
        print(f"   • Umbral batería crítica: 9.0 km")
        
        self.esperar_entrada("\\n▶️  Presiona Enter para comenzar la simulación...")
    
    def ejecutar_simulacion_paso_a_paso(self):
        """Ejecuta la simulación paso a paso con control manual"""
        
        # CARGAR DEMANDA PRONOSTICADA ANTES DE COMENZAR
        print(f"\n📊 Cargando demanda pronosticada...")
        self.simulador.cargar_demanda_pronosticada(FECHA_SIMULACION, PERIODOS_MAXIMOS)
        print(f"✅ Demanda pronosticada cargada correctamente\n")
        
        for periodo in range(PERIODOS_MAXIMOS):
            self.periodo_actual = periodo
            
            print(f"\\n{'🔥'*25} PERÍODO {periodo} {'🔥'*25}")
            self.analizar_periodo_ultra_detallado(periodo)
            
            # Control manual para continuar
            if periodo < PERIODOS_MAXIMOS - 1:
                self.esperar_entrada(f"\\n⏸️  Período {periodo} completado. Presiona Enter para continuar al período {periodo+1}...")
        
        # Resumen final
        self.mostrar_resumen_final()
    
    def analizar_periodo_ultra_detallado(self, periodo):
        """Análisis ultra detallado de un período"""
        
        # 1. MOSTRAR CONTEXTO TEMPORAL
        hora_actual = (periodo * 15) // 60
        min_actual = (periodo * 15) % 60
        hora_fin = ((periodo + 1) * 15) // 60
        min_fin = ((periodo + 1) * 15) % 60
        
        print(f"🕐 TIEMPO: {hora_actual:02d}:{min_actual:02d} - {hora_fin:02d}:{min_fin:02d}")
        
        # CORRECCIÓN ESPECÍFICA: Solo actualizar estados de CARGA al principio
        # Los viajes siguen actualizándose al final del período como siempre
        if periodo > 0:
            print(f"\\n🔄 FINALIZANDO ACTIVIDADES QUE TERMINAN EN PERÍODO {periodo}")
            print("-"*40)
            for vehiculo in self.simulador.vehiculos:
                if vehiculo.tiempo_fin_actividad == periodo:
                    if vehiculo.estado == "cargando":
                        print(f"   ✅ V{vehiculo.id}: Terminando carga en zona {vehiculo.zona_actual}")
                        # Liberar espacio en la estación
                        zona_estacion = vehiculo.zona_actual
                        if zona_estacion in self.simulador.estaciones_carga:
                            self.simulador.estaciones_carga[zona_estacion]['vehiculos_cargando'] -= 1
                        vehiculo.finalizar_carga()
                    elif vehiculo.estado == "yendo_a_cargar":
                        print(f"   ✅ V{vehiculo.id}: Llegando a estación {vehiculo.estacion_carga_asignada}")
                        # Llegó a la estación, iniciar carga si hay espacio
                        zona_estacion = vehiculo.estacion_carga_asignada
                        if zona_estacion in self.simulador.estaciones_carga:
                            if (self.simulador.estaciones_carga[zona_estacion]['vehiculos_cargando'] < 
                                self.simulador.estaciones_carga[zona_estacion]['capacidad_maxima']):
                                # Hay espacio, iniciar carga
                                self.simulador.estaciones_carga[zona_estacion]['vehiculos_cargando'] += 1
                                vehiculo.zona_actual = zona_estacion
                                vehiculo.iniciar_carga(periodo)
                                print(f"   🔋 V{vehiculo.id}: Iniciando carga en estación {zona_estacion}")
                            else:
                                # No hay espacio, el vehículo se queda disponible
                                vehiculo.estado = "disponible"
                                vehiculo.zona_actual = zona_estacion
                                vehiculo.estacion_carga_asignada = None
                                print(f"   ⚠️  V{vehiculo.id}: Sin espacio en estación, quedando disponible")
        
        # 2. GESTIÓN DE CARGA (solo después del período 0)
        if periodo > 0:
            print(f"\\n🔋 GESTIÓN DE CARGA DEL PERÍODO {periodo}")
            print("-"*40)
            print("🔍 Verificando vehículos que necesitan cargar...")
            vehiculos_antes_carga = []
            for v in self.simulador.vehiculos:
                if v.estado == "disponible" and v.necesita_cargar():
                    vehiculos_antes_carga.append((v.id, v.zona_actual, v.bateria_actual))
                    print(f"   ⚠️ V{v.id}: Zona {v.zona_actual}, Batería {v.bateria_actual:.1f}km - NECESITA CARGAR")
            
            if vehiculos_antes_carga:
                print(f"🚗→🔌 Ejecutando gestión de carga...")
                self.simulador.gestionar_carga_vehiculos(periodo)
                
                # Verificar cambios después de gestión de carga
                print(f"📊 Estados después de gestión de carga:")
                for v_id, zona_original, bateria_original in vehiculos_antes_carga:
                    vehiculo = self.simulador.vehiculos[v_id]
                    if vehiculo.estado == "yendo_a_cargar":
                        print(f"   ✅ V{v_id}: Ahora {vehiculo.estado} hacia estación {vehiculo.estacion_carga_asignada}")
                    elif vehiculo.estado == "cargando":
                        print(f"   ✅ V{v_id}: Ahora {vehiculo.estado} en zona {vehiculo.zona_actual}")
                    else:
                        print(f"   ❓ V{v_id}: Estado inesperado: {vehiculo.estado}")
            else:
                print("   ✅ Ningún vehículo disponible necesita cargar")
        
        # 3. ESTADO INICIAL DEL PERÍODO (después de gestión de carga)
        print(f"\\n📊 ESTADO INICIAL DEL PERÍODO {periodo}")
        print("-"*40)
        self.mostrar_estado_vehiculos_detallado("INICIO")
        
        # 4. OBTENER Y ANALIZAR DEMANDA
        print(f"\\n📈 ANÁLISIS DE DEMANDA")
        print("-"*40)
        viajes_periodo = self.simulador.obtener_viajes_periodo(periodo, FECHA_SIMULACION)
        print(f"🎯 Total viajes solicitados: {len(viajes_periodo)}")
        
        if len(viajes_periodo) == 0:
            print("   ℹ️  Sin demanda en este período")
        else:
            print("📋 DETALLE DE TODOS LOS VIAJES SOLICITADOS:")
            tipo_hora = self.obtener_tipo_hora(periodo)
            for i, viaje in enumerate(viajes_periodo):
                tiempo_viaje = obtener_tiempo(viaje.zona_origen, viaje.zona_destino, tipo_hora)
                print(f"   {i+1:2d}. Zona {viaje.zona_origen:3d} → {viaje.zona_destino:3d} | "
                      f"{viaje.distancia_km:5.1f} km | {tiempo_viaje:3.0f} min | ${viaje.ingreso:6.2f}")
            
            # Análisis de demanda por zona
            demanda_por_zona = {}
            for viaje in viajes_periodo:
                zona = viaje.zona_origen
                demanda_por_zona[zona] = demanda_por_zona.get(zona, 0) + 1
            
            print(f"\\n📍 DEMANDA POR ZONA ORIGEN:")
            for zona in sorted(demanda_por_zona.keys()):
                print(f"   • Zona {zona}: {demanda_por_zona[zona]} viajes")
        
        # 5. ANÁLISIS DETALLADO DE CAPACIDAD
        if len(viajes_periodo) > 0:
            print(f"\\n🔍 ANÁLISIS DE CAPACIDAD DE ATENCIÓN")
            print("-"*40)
            self.analizar_capacidad_detallada(viajes_periodo)
        
        # 6. PROCESAR ASIGNACIONES
        print(f"\\n⚙️  PROCESANDO ASIGNACIONES...")
        print("-"*40)
        self.simulador.asignar_viajes_optimizado(viajes_periodo, periodo)
        
        # 7. MOSTRAR ASIGNACIONES REALIZADAS
        self.mostrar_asignaciones_realizadas(viajes_periodo)
        
        # 7.5. PROCESO DE REUBICACIÓN
        print(f"\n📍 REUBICACIÓN DE VEHÍCULOS OCIOSOS")
        print("-"*40)
        self.analizar_y_ejecutar_reubicacion(periodo)
        
        # 8. ACTUALIZAR ESTADOS (finalizar actividades) - SOLO VIAJES Y REUBICACIONES
        print(f"\n🔄 ACTUALIZANDO ESTADOS DE VIAJES Y REUBICACIONES...")
        for vehiculo in self.simulador.vehiculos:
            # Actualizar viajes y reubicaciones que terminan en este período
            if vehiculo.tiempo_fin_actividad == periodo:
                if vehiculo.estado == "en_viaje":
                    vehiculo.finalizar_viaje()
                elif vehiculo.estado == "reubicando":
                    vehiculo.finalizar_reubicacion()
        
        # 9. ESTADO POST-PERÍODO
        print(f"\\n📊 ESTADO FINAL DEL PERÍODO {periodo}")
        print("-"*40)
        self.mostrar_estado_vehiculos_detallado("DESPUÉS")
        
        # 10. RESUMEN DEL PERÍODO
        self.mostrar_resumen_periodo(viajes_periodo)
        
        # 11. REGISTRAR PARA ANÁLISIS POSTERIOR
        self.simulador.registrar_estado_periodo(periodo)
    
    def mostrar_estado_vehiculos_detallado(self, momento):
        """Muestra estado detallado de cada vehículo"""
        print(f"🚗 ESTADO DE VEHÍCULOS ({momento}):")
        
        for v in self.simulador.vehiculos:
            estado_emoji = {
                'disponible': '🟢',
                'en_viaje': '🚗',
                'cargando': '🔋',
                'yendo_a_cargar': '⚡',
                'reubicando': '📍'
            }.get(v.estado, '❓')
            
            info_extra = ""
            if v.estado == 'en_viaje' and v.viaje_actual:
                destino = v.viaje_actual['zona_destino']
                periodos_restantes = v.tiempo_fin_actividad - self.periodo_actual
                info_extra = f" → Zona {destino} (quedan {periodos_restantes} períodos)"
            elif v.estado == 'reubicando' and v.viaje_actual:
                destino = v.viaje_actual['zona_destino']
                periodos_restantes = v.tiempo_fin_actividad - self.periodo_actual
                costo = v.viaje_actual.get('costo', 0)
                info_extra = f" → Zona {destino} (${costo:.2f}, quedan {periodos_restantes} períodos)"
            elif v.estado == 'cargando':
                periodos_restantes = v.tiempo_fin_actividad - self.periodo_actual
                info_extra = f" en Zona {v.zona_actual} (quedan {periodos_restantes} períodos)"
            elif v.estado == 'yendo_a_cargar':
                estacion = v.estacion_carga_asignada
                periodos_restantes = v.tiempo_fin_actividad - self.periodo_actual
                info_extra = f" → Estación {estacion} (quedan {periodos_restantes} períodos)"
            
            print(f"   {estado_emoji} V{v.id}: Zona {v.zona_actual:3d} | "
                  f"🔋 {v.bateria_actual:5.1f} km | {v.estado}{info_extra}")
        
        # Estadísticas agregadas
        estados = {}
        bateria_total = 0
        for v in self.simulador.vehiculos:
            estados[v.estado] = estados.get(v.estado, 0) + 1
            bateria_total += v.bateria_actual
        
        bateria_promedio = bateria_total / len(self.simulador.vehiculos)
        print(f"\\n   📈 Resumen: {estados} | Batería promedio: {bateria_promedio:.1f} km")
        
        # Estado de estaciones de carga
        print(f"\\n🔋 ESTACIONES DE CARGA:")
        for zona, info in self.simulador.estaciones_carga.items():
            ocupacion = info['vehiculos_cargando']
            capacidad = info['capacidad_maxima']
            print(f"   • Zona {zona}: {ocupacion}/{capacidad} vehículos")
    
    def analizar_capacidad_detallada(self, viajes_periodo):
        """Analiza en detalle qué vehículos pueden atender qué viajes"""
        vehiculos_disponibles = [v for v in self.simulador.vehiculos if v.estado == "disponible"]
        print(f"🎯 Vehículos disponibles: {len(vehiculos_disponibles)} de {len(self.simulador.vehiculos)}")
        
        if len(vehiculos_disponibles) == 0:
            print("   ❌ Sin vehículos disponibles para asignar")
            return
        
        print(f"\\n🔍 ANÁLISIS VIAJE POR VIAJE:")
        tipo_hora = self.obtener_tipo_hora(self.periodo_actual)
        for i, viaje in enumerate(viajes_periodo):
            tiempo_viaje = obtener_tiempo(viaje.zona_origen, viaje.zona_destino, tipo_hora)
            print(f"\\n   Viaje {i+1}: Zona {viaje.zona_origen} → {viaje.zona_destino} ({viaje.distancia_km:.1f} km, {tiempo_viaje:.0f} min)")
            
            # Vehículos en la zona origen
            vehiculos_en_zona = [v for v in vehiculos_disponibles if v.zona_actual == viaje.zona_origen]
            print(f"   • Vehículos en zona origen {viaje.zona_origen}: {len(vehiculos_en_zona)}")
            
            if len(vehiculos_en_zona) == 0:
                print("     ❌ Sin vehículos en zona origen")
                continue
            
            # Analizar cada vehículo en la zona
            vehiculos_capaces = []
            for v in vehiculos_en_zona:
                puede = v.puede_realizar_viaje_completo(viaje.zona_origen, viaje.zona_destino)
                if puede:
                    vehiculos_capaces.append(v)
                    print(f"     ✅ V{v.id}: PUEDE (batería {v.bateria_actual:.1f} km)")
                else:
                    print(f"     ❌ V{v.id}: NO PUEDE (batería {v.bateria_actual:.1f} km insuficiente)")
            
            if len(vehiculos_capaces) > 0:
                mejor_vehiculo = max(vehiculos_capaces, key=lambda x: x.bateria_actual)
                print(f"     🎯 Mejor opción: V{mejor_vehiculo.id} (más batería)")
            else:
                print(f"     ⚠️  Ningún vehículo puede completar este viaje")
    
    def analizar_y_ejecutar_reubicacion(self, periodo):
        """Analiza y ejecuta la reubicación de vehículos ociosos"""
        # Identificar vehículos ociosos (solo disponibles, sin umbral de batería)
        vehiculos_ociosos = [v for v in self.simulador.vehiculos 
                            if v.estado == "disponible"]
        
        print(f"🔍 Vehículos ociosos disponibles: {len(vehiculos_ociosos)}")
        
        if len(vehiculos_ociosos) == 0:
            print("   ℹ️  Sin vehículos disponibles para reubicar")
            return
        
        for v in vehiculos_ociosos:
            print(f"   • V{v.id}: Zona {v.zona_actual}, Batería {v.bateria_actual:.1f} km")
        
        # Ejecutar reubicación (el método interno ya muestra logs detallados)
        print(f"\n🚗→📍 Ejecutando lógica de reubicación...")
        self.simulador.reubicar_vehiculos_ociosos(periodo)
        
        # Mostrar resultados de reubicación
        vehiculos_reubicados = [v for v in self.simulador.vehiculos if v.estado == "reubicando"]
        if len(vehiculos_reubicados) > 0:
            print(f"\n✅ Vehículos reubicados: {len(vehiculos_reubicados)}")
            for v in vehiculos_reubicados:
                destino = v.viaje_actual['zona_destino']
                costo = v.viaje_actual.get('costo_reub', 0)  # Usar 'costo_reub' en vez de 'costo'
                periodos_restantes = v.tiempo_fin_actividad - periodo
                print(f"   • V{v.id}: {v.viaje_actual['zona_origen']} → Zona {destino} ")
                print(f"     Costo: ${costo:.2f}, Llegada en {periodos_restantes} período(s)")
        else:
            print("   ℹ️  Ningún vehículo fue reubicado (todos muy lejos o sin zonas alcanzables)")
    
    def mostrar_asignaciones_realizadas(self, viajes_periodo):
        """Muestra qué asignaciones se realizaron efectivamente"""
        viajes_atendidos = [v for v in viajes_periodo if v.atendido]
        viajes_perdidos = [v for v in viajes_periodo if not v.atendido]
        
        print(f"✅ VIAJES ATENDIDOS: {len(viajes_atendidos)}")
        tipo_hora = self.obtener_tipo_hora(self.periodo_actual)
        for viaje in viajes_atendidos:
            # Encontrar qué vehículo se asignó
            vehiculo_asignado = None
            for v in self.simulador.vehiculos:
                if (v.estado == 'en_viaje' and v.viaje_actual and 
                    v.viaje_actual['zona_origen'] == viaje.zona_origen and
                    v.viaje_actual['zona_destino'] == viaje.zona_destino):
                    vehiculo_asignado = v
                    break
            
            if vehiculo_asignado:
                tiempo_viaje = obtener_tiempo(viaje.zona_origen, viaje.zona_destino, tipo_hora)
                print(f"   • V{vehiculo_asignado.id}: {viaje.zona_origen} → {viaje.zona_destino} "
                      f"({viaje.distancia_km:.1f} km, {tiempo_viaje:.0f} min, ${viaje.ingreso:.2f})")
        
        print(f"\\n❌ VIAJES PERDIDOS: {len(viajes_perdidos)}")
        for viaje in viajes_perdidos:
            tiempo_viaje = obtener_tiempo(viaje.zona_origen, viaje.zona_destino, tipo_hora)
            print(f"   • {viaje.zona_origen} → {viaje.zona_destino} ({viaje.distancia_km:.1f} km, {tiempo_viaje:.0f} min)")
    
    def mostrar_resumen_periodo(self, viajes_periodo):
        """Muestra resumen final del período"""
        atendidos = len([v for v in viajes_periodo if v.atendido])
        perdidos = len(viajes_periodo) - atendidos
        tasa_atencion = (atendidos / len(viajes_periodo) * 100) if len(viajes_periodo) > 0 else 0
        
        # Contar reubicaciones en este período
        reubicaciones_periodo = len([v for v in self.simulador.vehiculos if v.estado == "reubicando"])
        
        # Calcular costos de reubicación del período
        costos_reub_periodo = 0
        for v in self.simulador.vehiculos:
            if v.estado == "reubicando" and v.viaje_actual:
                costos_reub_periodo += v.viaje_actual.get('costo_reub', 0)
        
        print(f"\n📊 RESUMEN PERÍODO {self.periodo_actual}")
        print(f"   • Demanda: {len(viajes_periodo)} viajes")
        print(f"   • Atendidos: {atendidos} ({tasa_atencion:.1f}%)")
        print(f"   • Perdidos: {perdidos}")
        print(f"   • Reubicaciones: {reubicaciones_periodo} vehículos")
        
        if len(viajes_periodo) > 0:
            ingresos_periodo = sum(v.ingreso for v in viajes_periodo if v.atendido)
            ingresos_perdidos = sum(v.ingreso for v in viajes_periodo if not v.atendido)
            print(f"   • Ingresos generados: ${ingresos_periodo:.2f}")
            print(f"   • Ingresos perdidos: ${ingresos_perdidos:.2f}")
            print(f"   • Costos reubicación: ${costos_reub_periodo:.2f}")
            utilidad_neta_periodo = ingresos_periodo - costos_reub_periodo
            print(f"   • Utilidad neta período: ${utilidad_neta_periodo:.2f}")
    
    def mostrar_resumen_final(self):
        """Muestra resumen final completo"""
        print(f"\\n{'🏁'*25} RESUMEN FINAL {'🏁'*25}")
        
        # Calcular KPIs finales
        self.simulador.calcular_kpis_finales()
        kpis = self.simulador.kpis
        
        print(f"\n📈 RESULTADOS FINALES:")
        print(f"   • Períodos simulados: {self.periodo_actual + 1}")
        print(f"   • Viajes solicitados: {kpis['viajes_solicitados']}")
        print(f"   • Viajes atendidos: {kpis['viajes_atendidos']}")
        #print(f"   • Tasa de atención: {kpis['porcentaje_viajes_atendidos']:.1f}%")
        print(f"   • Reubicaciones totales: {kpis['total_reubicaciones']}")
        print(f"   • Ingresos totales: ${kpis['ingresos_totales']:.2f}")
        print(f"   • Costos reubicación: ${kpis['costos_reubicacion']:.2f}")
        print(f"   • Utilidad neta: ${kpis['ingresos_totales'] - kpis['costos_reubicacion']:.2f}")
        print(f"   • Km recorridos: {kpis['km_totales']:.1f} km")
        print(f"   • Eventos de carga: {kpis['total_eventos_carga']}")
        
        print(f"\\n🚗 ESTADO FINAL DE VEHÍCULOS:")
        for v in self.simulador.vehiculos:
            print(f"   • V{v.id}: {v.viajes_atendidos} viajes, {v.kilometros_recorridos:.1f} km, "
                  f"${v.ingresos_generados:.2f}, {v.veces_cargado} cargas")
        
        print(f"\\n✅ Simulación ultra detallada completada!")
    
    def esperar_entrada(self, mensaje):
        """Espera entrada del usuario para continuar"""
        if not AUTO_CONTINUAR:
            input(mensaje)
        else:
            print(mensaje)

# EJECUTAR MONITOR ULTRA DETALLADO
if __name__ == "__main__":
    print("🔬 MONITOR ULTRA DETALLADO - MÁXIMO CONTROL")
    print("="*60)
    print("ℹ️  Este monitor te permite ver CADA DETALLE de la simulación")
    print("ℹ️  Presiona Enter después de cada período para continuar")
    print("="*60)
    
    # Crear y ejecutar monitor
    monitor = MonitorUltraDetallado()
    monitor.ejecutar_simulacion_paso_a_paso()
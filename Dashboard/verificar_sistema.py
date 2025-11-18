"""
Script de verificación de dependencias
Ejecutar antes de usar el dashboard para asegurar que todo está instalado
"""

import sys

def verificar_dependencias():
    """Verifica que todas las librerías necesarias estén instaladas."""
    
    print("=" * 60)
    print("VERIFICACIÓN DE DEPENDENCIAS")
    print("=" * 60)
    print()
    
    dependencias = [
        ('streamlit', 'Streamlit'),
        ('plotly', 'Plotly'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('gurobipy', 'Gurobi'),
        ('pyarrow', 'PyArrow'),
    ]
    
    todas_ok = True
    
    for modulo, nombre in dependencias:
        try:
            __import__(modulo)
            if modulo == 'gurobipy':
                import gurobipy
                version = f"v{gurobipy.gurobi.version()[0]}.{gurobipy.gurobi.version()[1]}"
                print(f"✅ {nombre:15} - Instalado ({version})")
            else:
                mod = sys.modules[modulo]
                version = getattr(mod, '__version__', 'sin versión')
                print(f"✅ {nombre:15} - Instalado (v{version})")
        except ImportError:
            print(f"❌ {nombre:15} - NO instalado")
            todas_ok = False
        except Exception as e:
            print(f"⚠️  {nombre:15} - Error: {e}")
            todas_ok = False
    
    print()
    print("=" * 60)
    
    if todas_ok:
        print("✅ TODAS LAS DEPENDENCIAS ESTÁN INSTALADAS")
        print("=" * 60)
        print()
        print("Ahora puedes ejecutar el dashboard:")
        print("  cd 'capstone modelo'")
        print("  streamlit run dashboard.py")
        return True
    else:
        print("❌ FALTAN DEPENDENCIAS")
        print("=" * 60)
        print()
        print("Instala las dependencias faltantes con:")
        print("  pip install -r requirements.txt")
        return False

def verificar_archivos():
    """Verifica que existan los archivos de datos necesarios."""
    from pathlib import Path
    
    print()
    print("=" * 60)
    print("VERIFICACIÓN DE ARCHIVOS DE DATOS")
    print("=" * 60)
    print()
    
    base_dir = Path(__file__).parent
    
    archivos = [
        'Datos/lambda_zonal_OD_mat_full.csv',
        'Datos/df_all_reducido_github.parquet',
        'Distancias zonas/distancias_manhattan_zonas_con_tiempo_ingreso.csv',
    ]
    
    todos_ok = True
    
    for archivo in archivos:
        ruta = base_dir / archivo
        if ruta.exists():
            tamaño = ruta.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ {archivo:60} ({tamaño:.1f} MB)")
        else:
            print(f"❌ {archivo:60} - NO ENCONTRADO")
            todos_ok = False
    
    print()
    print("=" * 60)
    
    if todos_ok:
        print("✅ TODOS LOS ARCHIVOS DE DATOS ESTÁN PRESENTES")
    else:
        print("⚠️  FALTAN ALGUNOS ARCHIVOS DE DATOS")
        print("El dashboard podría no funcionar correctamente")
    
    print("=" * 60)
    
    return todos_ok

def verificar_gurobi_licencia():
    """Verifica que Gurobi tenga una licencia válida."""
    
    print()
    print("=" * 60)
    print("VERIFICACIÓN DE LICENCIA GUROBI")
    print("=" * 60)
    print()
    
    try:
        import gurobipy as gp
        # Intentar crear un modelo simple
        with gp.Env(params={'OutputFlag': 0}) as env:
            with gp.Model(env=env) as m:
                x = m.addVar()
                m.setObjective(x)
                m.optimize()
        
        print("✅ Gurobi tiene una licencia válida")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error con licencia de Gurobi: {e}")
        print()
        print("Soluciones:")
        print("1. Obtener una licencia académica gratuita:")
        print("   https://www.gurobi.com/academia/academic-program-and-licenses/")
        print()
        print("2. Instalar la licencia:")
        print("   grbgetkey XXXXX-XXXXX-XXXXX")
        print("=" * 60)
        return False

def main():
    """Función principal."""
    
    deps_ok = verificar_dependencias()
    
    if deps_ok:
        archivos_ok = verificar_archivos()
        gurobi_ok = verificar_gurobi_licencia()
        
        print()
        if deps_ok and archivos_ok and gurobi_ok:
            print("🎉 SISTEMA LISTO PARA USAR 🎉")
            print()
            print("Siguiente paso:")
            print("  cd 'capstone modelo'")
            print("  streamlit run dashboard.py")
        else:
            print("⚠️  SISTEMA PARCIALMENTE CONFIGURADO")
            print()
            print("Revisa los mensajes de error arriba")
    else:
        print()
        print("Por favor instala las dependencias primero")
    
    print()

if __name__ == "__main__":
    main()

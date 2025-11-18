"""
Script para lanzar el dashboard en Windows
Uso: python run_dashboard.py
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    print("🚕 Iniciando Dashboard - Vehículos Autónomos NYC")
    print()
    
    # Verificar si estamos en el directorio correcto
    if not Path("requirements.txt").exists():
        print("❌ Error: Ejecuta este script desde la carpeta principal del proyecto")
        sys.exit(1)
    
    # Verificar si streamlit está instalado
    try:
        import streamlit
        print("✅ Streamlit encontrado")
    except ImportError:
        print("⚠️  Streamlit no encontrado. Instalando dependencias...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print()
    
    # Cambiar al directorio del modelo
    modelo_dir = Path("capstone modelo")
    dashboard_file = modelo_dir / "dashboard.py"
    
    # Verificar que dashboard.py existe
    if not dashboard_file.exists():
        print("❌ Error: No se encontró dashboard.py")
        sys.exit(1)
    
    print("▶️  Abriendo dashboard en el navegador...")
    print()
    print("   URL: http://localhost:8501")
    print()
    print("   Presiona Ctrl+C para detener el dashboard")
    print()
    
    # Cambiar directorio y ejecutar streamlit
    os.chdir(modelo_dir)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"])
    except KeyboardInterrupt:
        print()
        print("👋 Dashboard cerrado")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

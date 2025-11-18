#!/bin/bash

# Script para lanzar el dashboard de forma sencilla
# Uso: ./run_dashboard.sh

echo "🚕 Iniciando Dashboard - Vehículos Autónomos NYC"
echo ""

# Verificar si estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Ejecuta este script desde la carpeta principal del proyecto"
    exit 1
fi

# Verificar si streamlit está instalado
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit no encontrado. Instalando dependencias..."
    pip install -r requirements.txt
    echo ""
fi

# Cambiar al directorio del modelo
cd "capstone modelo"

# Verificar que dashboard.py existe
if [ ! -f "dashboard.py" ]; then
    echo "❌ Error: No se encontró dashboard.py"
    exit 1
fi

echo "▶️  Abriendo dashboard en el navegador..."
echo ""
echo "   URL: http://localhost:8501"
echo ""
echo "   Presiona Ctrl+C para detener el dashboard"
echo ""

# Ejecutar streamlit
streamlit run dashboard.py

# Al salir
echo ""
echo "👋 Dashboard cerrado"

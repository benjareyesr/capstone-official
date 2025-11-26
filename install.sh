#!/bin/bash

# Script de instalación para el modelo de optimización
# Uso: ./install.sh

echo "=========================================="
echo "  Instalación Modelo - Capstone NYC"
echo "=========================================="
echo ""

# Verificar Python
echo "🔍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Por favor instala Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION encontrado"
echo ""

# Verificar pip
echo "🔍 Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 no encontrado. Instalando..."
    python3 -m ensurepip --upgrade
fi
echo "✓ pip encontrado"
echo ""

# Crear entorno virtual (opcional pero recomendado)
read -p "¿Crear entorno virtual? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Unix/macOS
        source venv/bin/activate
    fi
    
    echo "✓ Entorno virtual creado y activado"
    echo ""
fi

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip
echo ""

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Error instalando dependencias"
    exit 1
fi

echo "✓ Dependencias instaladas"
echo ""

# Verificar Gurobi
echo "🔍 Verificando Gurobi..."
python3 -c "import gurobipy; print('✓ Gurobi OK -', gurobipy.gurobi.version())" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Gurobi no está instalado o no tiene licencia válida"
    echo "   Por favor instala Gurobi y configura tu licencia:"
    echo "   https://www.gurobi.com/downloads/"
    echo ""
fi

# Verificar archivos de datos
echo "🔍 Verificando archivos de datos..."

ARCHIVOS_REQUERIDOS=(
    "Datos/lambda_zonal_OD_mat_full.csv"
    "Datos/df_all_reducido_github.parquet"
    "Distancias zonas/distancias_manhattan_zonas_con_tiempo_ingreso.csv"
)

FALTAN_ARCHIVOS=0

for archivo in "${ARCHIVOS_REQUERIDOS[@]}"; do
    if [ -f "$archivo" ]; then
        echo "  ✓ $archivo"
    else
        echo "  ❌ $archivo NO ENCONTRADO"
        FALTAN_ARCHIVOS=1
    fi
done

echo ""

if [ $FALTAN_ARCHIVOS -eq 1 ]; then
    echo "⚠️  Algunos archivos de datos no se encontraron"
    echo "   El modelo podría no ejecutarse correctamente"
    echo ""
fi

# Resumen
echo "=========================================="
echo "  ✅ INSTALACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "Para ejecutar la simulación base:"
echo "  cd 'capstone modelo'"
echo "  python simulacion_rh.py"
echo ""
echo "Para abrir el nuevo dashboard (beta):"
echo "  python dash_app/app.py"
echo ""
echo "Si creaste un entorno virtual, actívalo primero:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  venv\\Scripts\\activate"
else
    echo "  source venv/bin/activate"
fi
echo ""
echo "Consulta README.2.md para más detalles y próximos pasos."
echo ""

# Simulador de Máquinas de Turing - División de Trabajo / versión preliminar del proyecto y modularizada

## 🧑‍💻 Equipo de Desarrollo

### **Backend & Arquitectura del Sistema**
**👨‍💻 Daniel Barillas**  
*Responsable del desarrollo del backend y arquitectura del sistema*

**Tareas realizadas:**
- ✅ Diseño e implementación de la arquitectura modular del sistema
- ✅ Desarrollo del parser YAML manual sin dependencias externas
- ✅ Implementación del motor de Máquinas de Turing
- ✅ Creación de las estructuras de datos (`TuringMachine`, `Transition`, `InstantaneousDescription`)
- ✅ Desarrollo del sistema de validación de definiciones YAML
- ✅ Implementación del algoritmo de simulación paso a paso
- ✅ Creación del sistema de índices para búsqueda eficiente de transiciones
- ✅ Desarrollo del generador de diagramas Graphviz
- ✅ Implementación del sistema de manejo de blancos y comodines
- ✅ Creación de ejemplos predefinidos de MTs complejas

### **Frontend & Diseño de Interfaz**
**👨‍💻 Hugo Barillas**  
*Responsable del frontend y diseño de interfaz de usuario*

**Tareas realizadas:**
- ✅ Diseño e implementación de la interfaz Streamlit
- ✅ Desarrollo de componentes UI modernos y responsivos
- ✅ Creación del sistema de pestañas organizadas
- ✅ Implementación de visualización de descripciones instantáneas (IDs)
- ✅ Diseño del sistema de estadísticas y métricas
- ✅ Desarrollo de la barra lateral de configuración
- ✅ Implementación de la visualización de cinta con estilos CSS
- ✅ Creación del sistema de manejo de estado de sesión
- ✅ Diseño de la experiencia de usuario (UX) completa
- ✅ Implementación de modos de entrada (ejemplos, archivos, editor)

## 🏗️ Arquitectura del Sistema

```
turing_simulator/
├── 📁 backend/           (Daniel Barillas)
│   ├── models.py         # Estructuras de datos y lógica de MT
│   ├── parser.py         # Parser YAML manual
│   ├── validator.py      # Validación de definiciones
│   └── turing_machine.py # Constructor de MT desde YAML
├── 📁 frontend/          (Hugo Barillas)  
│   ├── ui_components.py  # Componentes de interfaz
│   └── tabs.py          # Sistema de pestañas
├── 📁 utils/             (Colaborativo)
│   ├── helpers.py       # Funciones auxiliares
│   └── examples.py      # Ejemplos predefinidos
└── main.py              # Punto de entrada (Integración)
```

# 🚀 Guía de Ejecución - Simulador de Máquinas de Turing

## 📋 Prerequisitos

### **Software Requerido**
- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Git (opcional, para clonar el repositorio)

### **Verificar Instalación**
```bash
python --version
pip --version
```

## 🛠️ Instalación Paso a Paso

### **1. Clonar o Descargar el Proyecto**

**Opción A: Clonar con Git**
```bash
git clone <https://github.com/DanielBarillasM/Proyecto-3_Grupo-4_Teoria-De-La-Computacion_Seccion-20.git>
git switch backend # Cualquiera de las dos sirve para esto
git switch frontend # Cualquiera de las dos sirve para esto
cd turing_simulator
```

**Opción B: Descargar manualmente**
- Descargar el proyecto como ZIP
- Extraer en una carpeta llamada `turing_simulator`
- Abrir terminal en esa carpeta

### **2. Crear Entorno Virtual (Recomendado)**

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### **3. Instalar Dependencias**

```bash
pip install -r requirements.txt
```

**Contenido de `requirements.txt`:**
```txt
streamlit>=1.28.0
pandas>=2.0.0
graphviz>=0.20.0
```

### **4. Instalar Graphviz (Opcional, para exportar diagramas)**

**Windows:**
- Descargar desde: https://graphviz.org/download/
- Instalar y agregar `C:\Program Files\Graphviz\bin` al PATH del sistema

**macOS:**
```bash
brew install graphviz
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install graphviz
```

## 🎮 Ejecutar la Aplicación

### **Comando Principal**
```bash
streamlit run main.py
```

### **Qué Esperar**
- La aplicación se abrirá automáticamente en tu navegador
- URL: `http://localhost:8501`
- Verás la interfaz principal con el header colorido

## 🎯 Modos de Uso

### **1. Modo Ejemplos Predefinidos** (Recomendado para empezar)
- Selecciona "📚 Ejemplos Predefinidos" en la barra lateral
- Elige uno de los 7 ejemplos disponibles
- Explora las diferentes pestañas

### **2. Modo Cargar Archivo**
- Selecciona "📁 Cargar Archivo"
- Sube tu archivo YAML con la definición de la MT
- La aplicación validará y procesará automáticamente

### **3. Modo Editor YAML**
- Selecciona "✏️ Editor YAML"  
- Escribe o pega tu definición YAML directamente
- Usa el template proporcionado como guía

## 🐛 Solución de Problemas Comunes

### **Error: "ModuleNotFoundError"**
```bash
# Reinstalar dependencias
pip install --upgrade -r requirements.txt
```

### **Error: Streamlit no encontrado**
```bash
pip install streamlit
```

### **Error: Puerto 8501 en uso**
```bash
# Usar puerto diferente
streamlit run main.py --server.port 8502
```

### **Error: Graphviz no instalado**
- Solo afecta la exportación de diagramas
- La aplicación funcionará sin Graphviz, pero no podrás exportar

### **Problemas de Importación**
```bash
# Verificar que estás en la carpeta correcta
cd turing_simulator
# Verificar estructura de archivos
ls -la
```

## 🎪 Características a Probar

### **Pestaña 📋 Información**
- Ver estados, alfabetos y tabla de transiciones
- Comprender la estructura de tu Máquina de Turing

### **Pestaña 📊 Diagrama** 
- Visualizar el autómata como grafo interactivo
- Ver estados iniciales/finales diferenciados por colores

### **Pestaña 🎯 Simulación**
- Ejecutar cadenas paso a paso
- Ver la cinta evolucionar en tiempo real
- Analizar descripciones instantáneas

### **Pestaña 📈 Estadísticas**
- Métricas de aceptación/rechazo
- Promedio de pasos por tipo de resultado
- Tabla resumen de simulaciones

## 🚀 Comando Rápido (Una vez configurado)

```bash
cd turing_simulator
streamlit run main.py
```

**¡Listo! La aplicación debería estar ejecutándose en el navegador.** 🌟

## 🎯 Características Implementadas

### **Backend (Daniel)**
- Parser YAML 100% manual sin PyYAML
- Motor de simulación con cache de memoria
- Sistema de transiciones deterministas con prioridades
- Validación exhaustiva de definiciones
- Generación automática de diagramas de estados
- Manejo robusto de errores y casos edge

### **Frontend (Hugo)**
- Interfaz Streamlit moderna y responsive
- 4 pestañas organizadas (Info, Diagrama, Simulación, Estadísticas)
- Visualización de cinta con estilos CSS personalizados
- Sistema de descripciones instantáneas expandibles
- Métricas y estadísticas en tiempo real
- 3 modos de entrada flexibles

## 🤝 Colaboración

El proyecto demostró una excelente división de responsabilidades donde:
- **Daniel** se enfocó en la robustez y eficiencia del motor de simulación
- **Hugo** priorizó la usabilidad y experiencia del usuario final
- Ambos colaboraron en la integración backend-frontend y definición de ejemplos

## 🚀 Resultado Final

Un simulador de Máquinas de Turing completo, eficiente y con una interfaz moderna que permite:
- Definir MTs complejas mediante YAML
- Visualizar ejecuciones paso a paso
- Analizar estadísticas de aceptación/rechazo
- Exportar diagramas y resultados
- Validar automáticamente las definiciones

**Fecha de desarrollo:** 29 de Octubre del 2025 / Nota: esta fue la versión 1.0 preliminar, antes de realizar las pruebas de usuario y ajustes finales.  
**Tecnologías:** Python, Streamlit, Graphviz, Pandas
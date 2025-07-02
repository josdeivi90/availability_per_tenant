# 🚀 KubeHealth Dashboard - Configuración de Desarrollo

Este documento describe cómo configurar el entorno de desarrollo local para **KubeHealth Dashboard**.

## 📋 **Prerrequisitos**

### **Sistema Operativo**
- ✅ macOS, Linux, o Windows con WSL2
- ✅ Acceso a terminal/línea de comandos

### **Software Requerido**
```bash
# Python 3.9+ (verificar versión)
python3 --version

# Node.js 16+ y npm (para Tailwind CSS)
node --version
npm --version

# Git (para clonar repositorio)
git --version

# Azure CLI (para autenticación)
az --version
```

### **Servicios Cloud**
- 🔑 **Cuenta Azure** con acceso a clústeres AKS
- 🔑 **API Token de PagerDuty** con permisos de lectura
- 🔑 **Token de GitHub** con permisos `actions:write` (para workflow dispatch)

---

## ⚙️ **Configuración - Paso a Paso**

### **1. Clonar y Configurar Variables de Entorno**

```bash
# Navegar al directorio del proyecto
cd "availability per tenant"

# Copiar archivo de variables de entorno
cp env.example .env

# Editar el archivo .env con tus credenciales
nano .env  # o usar tu editor preferido
```

**Variables obligatorias en `.env`:**
```bash
# Azure
AZURE_USER="tu-usuario@dominio.com"
AZURE_PASSWORD="tu-password-azure"

# PagerDuty
PAGERDUTY_API_TOKEN="tu-api-token-pagerduty"

# GitHub (para workflow dispatch)
GITHUB_TOKEN="ghp_tu-token-github"
```

### **2. Configurar Backend (Python)**

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r backend/requirements.txt

# Verificar instalación
python -c "import kubernetes, requests, azure.identity; print('✅ Dependencias instaladas correctamente')"
```

### **3. Configurar Frontend (Node.js/Tailwind)**

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias de Node.js
npm install

# Verificar instalación de Tailwind
npx tailwindcss --help

# Compilar CSS (desarrollo con watch)
npm run dev
# O compilar una vez:
npm run build-css-prod
```

### **4. Autenticación Azure**

```bash
# Login en Azure CLI
az login

# Verificar autenticación y listar clústeres AKS
az aks list --output table

# Si tienes clústeres con prefijo 'ftdsp-prod-aks-cluster-', deberías verlos listados
```

### **5. Verificar PagerDuty API**

```bash
# Probar conexión a PagerDuty (opcional)
curl -H "Authorization: Token token=TU_PAGERDUTY_TOKEN" \
     -H "Accept: application/vnd.pagerduty+json;version=2" \
     https://api.pagerduty.com/users/me
```

---

## 🧪 **Verificación de Configuración**

### **Test del Backend**
```bash
# Desde el directorio raíz, con venv activado
cd backend
python -c "
import os
from dotenv import load_dotenv
load_dotenv('../.env')

required_vars = ['AZURE_USER', 'PAGERDUTY_API_TOKEN']
missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f'❌ Variables faltantes: {missing}')
else:
    print('✅ Variables de entorno configuradas')
"
```

### **Test del Frontend**
```bash
# Desde frontend/, verificar que el CSS se compiló
cd frontend
ls -la assets/css/style.css

# Si existe y tiene contenido (> 1KB), está funcionando
```

---

## 📁 **Estructura Final**

Después de la configuración, deberías tener:

```
availability per tenant/
├── .env                           # ✅ Variables de entorno (TU COPIA)
├── env.example                    # ✅ Plantilla de variables
├── SETUP.md                       # ✅ Esta documentación
├── backend/
│   ├── requirements.txt           # ✅ Dependencias Python
│   ├── main.py                    # 🚧 (Fase 2)
│   ├── azure_client.py           # 🚧 (Fase 2)
│   ├── kubernetes_analyzer.py    # 🚧 (Fase 2)
│   ├── pagerduty_client.py       # 🚧 (Fase 2)
│   └── data_processor.py         # 🚧 (Fase 2)
├── frontend/
│   ├── package.json              # ✅ Configuración npm
│   ├── tailwind.config.js        # ✅ Configuración Tailwind
│   ├── assets/
│   │   ├── css/
│   │   │   ├── input.css         # ✅ CSS input Tailwind
│   │   │   └── style.css         # ✅ CSS compilado
│   │   └── js/
│   │       └── main.js           # 🚧 (Fase 3)
│   └── index.html                # 🚧 (Fase 3)
└── tenants.json                  # ✅ (NO TOCAR)
```

---

## 🔧 **Comandos Útiles**

```bash
# Recompilar CSS cuando hagas cambios
cd frontend && npm run dev

# Activar entorno Python
source venv/bin/activate

# Verificar estado de Azure CLI
az account show

# Ver logs de compilación CSS
cd frontend && npx tailwindcss -i ./assets/css/input.css -o ./assets/css/style.css --watch --verbose
```

---

## ❗ **Solución de Problemas**

### **Python/Backend**
- **Error de importación:** Verifica que el `venv` esté activado
- **Azure CLI:** Ejecuta `az login` si hay errores de autenticación
- **Dependencias:** `pip install --upgrade pip` y vuelve a instalar

### **Frontend/Node.js**
- **Tailwind no compila:** Verifica que `npm install` se haya ejecutado correctamente
- **CSS vacío:** Asegúrate de que `input.css` tenga las directivas `@tailwind`
- **Permisos:** En Windows, ejecutar terminal como administrador

---

## ✅ **Siguientes Pasos**

Una vez completada esta configuración, estarás listo para:
- **Fase 2:** Desarrollo del Backend (Python)
- **Fase 3:** Desarrollo del Frontend (HTML/JS)
- **Fase 4:** Testing Local
- **Fase 5:** GitHub Actions

¡La configuración base está completa! 🎉 
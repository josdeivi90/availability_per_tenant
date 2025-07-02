# **KubeHealth Dashboard \- Monitor de Estado de Kubernetes y PagerDuty**

Este documento describe la arquitectura y el funcionamiento de **KubeHealth Dashboard**, una aplicación web diseñada para monitorear la salud de clústeres de Kubernetes en Azure, correlacionar el estado de la infraestructura con incidentes de PagerDuty y proporcionar un estado general a través de un modelo de inferencia.

La aplicación se ejecuta como un flujo de trabajo de GitHub Actions y presenta los resultados en una interfaz de usuario limpia y reactiva.

## **📋 Tabla de Contenidos**

1. [Funcionalidades Principales](https://www.google.com/search?q=%23-funcionalidades-principales)  
2. [Arquitectura de la Aplicación](https://www.google.com/search?q=%23%EF%B8%8F-arquitectura-de-la-aplicaci%C3%B3n)  
3. [Tecnologías Utilizadas](https://www.google.com/search?q=%23-tecnolog%C3%ADas-utilizadas)  
4. [Estructura del Proyecto](https://www.google.com/search?q=%23-estructura-del-proyecto)  
5. [Flujo de Trabajo Detallado](https://www.google.com/search?q=%23-flujo-de-trabajo-detallado)  
6. [Configuración del Entorno](https://www.google.com/search?q=%23%EF%B8%8F-configuraci%C3%B3n-del-entorno)  
7. [Componentes Clave](https://www.google.com/search?q=%23-componentes-clave)  
   * [Backend (Python)](https://www.google.com/search?q=%23backend-python)  
   * [Frontend (JavaScript)](https://www.google.com/search?q=%23frontend-javascript)  
   * [GitHub Action](https://www.google.com/search?q=%23github-action)  
8. [Contrato de Datos (API)](https://www.google.com/search?q=%23-contrato-de-datos-api)  
9. [Uso y Despliegue](https://www.google.com/search?q=%23-uso-y-despliegue)

## **✨ Funcionalidades Principales**

* **Conexión Segura a Azure:** Utiliza credenciales de usuario (az login) para autenticarse con Azure.  
* **Descubrimiento Automático de Clústeres:** Escanea y filtra clústeres de Azure Kubernetes Service (AKS) que coincidan con el prefijo ftdsp-prod-aks-cluster-.  
* **Análisis Enfocado en Namespaces:** Analiza únicamente los namespaces cuyo nombre es un UUID, representando organizaciones de clientes.  
* **Mapeo de Tenant:** Traduce los UUIDs de los namespaces a nombres de organizaciones legibles usando un archivo tenants.json.  
* **Análisis Profundo de Pods:**  
  * Evalúa el estado de los pods (Running, Failed, Pending).  
  * Detecta contenedores con problemas comunes como CrashLoopBackOff y reinicios excesivos.  
  * Calcula el porcentaje de disponibilidad de la infraestructura por namespace.  
* **Integración con PagerDuty:** Obtiene incidentes activos o recientes relacionados con los servicios monitoreados, vinculándolos a los namespaces afectados.  
* **Modelo de Inferencia:** Procesa los datos recolectados (estado de pods, incidentes) para generar un estado de salud general (Saludable, Advertencia, Crítico).  
* **Visualización de Datos:**  
  * Un panel de control con gráficos (usando Chart.js) que muestra la salud histórica y los incidentes.  
  * Ventana de visualización de datos de hasta 2 meses.  
* **Actualización de Datos:**  
  * **Automática:** El sistema se actualiza cada 30 minutos.  
  * **Bajo Demanda:** Un botón en la interfaz permite disparar una actualización inmediata. La UI indica visualmente cuando una actualización está en curso.  
* **Historial de Datos:** Almacena reportes históricos durante 1 mes, generando una "foto" del estado del clúster cada 30 minutos.  
* **Procesamiento Paralelo:** Capacidad para analizar múltiples clústeres de forma simultánea para mayor eficiencia.  
* **Configuración Flexible:** Gestionado a través de variables de entorno para facilitar el despliegue en diferentes entornos.  
* **Orquestación con GitHub Actions:** Todo el proceso de backend está encapsulado en un workflow de GitHub Actions, garantizando la portabilidad y automatización.

## **🏗️ Arquitectura de la Aplicación**

El sistema se divide en tres componentes principales:

1. **Backend (Python Script):**  
   * Es el cerebro de la aplicación. Se ejecuta dentro de un workflow de GitHub Actions.  
   * Se conecta a Azure y PagerDuty.  
   * Realiza el análisis de los clústeres y pods.  
   * Procesa los datos y genera un archivo status.json con los resultados consolidados.  
   * Este archivo se almacena como un artefacto o en una ubicación accesible para el frontend (ej. GitHub Pages).  
2. **Frontend (HTML, Vanilla JS, Tailwind CSS):**  
   * Es una página estática que consume el archivo status.json generado por el backend.  
   * Renderiza los gráficos y la información del estado usando Chart.js.  
   * Contiene el botón "Actualizar Ahora", que dispara el workflow de GitHub Actions a través de un evento workflow\_dispatch.  
   * Consulta periódicamente si hay un nuevo status.json disponible.  
3. **Orquestador (GitHub Actions):**  
   * Define el flujo de trabajo que ejecuta el script de Python.  
   * Se activa de dos maneras:  
     * **Programada (schedule):** Cada 30 minutos.  
     * **Manual (workflow\_dispatch):** Al ser invocado por el frontend.  
   * Gestiona las credenciales y variables de entorno de forma segura.

## **💻 Tecnologías Utilizadas**

* **Backend:** Python 3.9+  
* **Frontend:**  
  * HTML5  
  * JavaScript (ES6+ Vanilla)  
  * [Tailwind CSS](https://tailwindcss.com/)  
  * [Chart.js](https://www.chartjs.org/)  
* **Plataforma Cloud:** Microsoft Azure (AKS)  
* **CI/CD y Orquestación:** [GitHub Actions](https://github.com/features/actions)  
* **Dependencias Python:** kubernetes, azure-cli, requests  
* **Dependencias Frontend:** Ninguna, se usan CDNs para las librerías.

## **📁 Estructura del Proyecto**

.  
├── .github/  
│   └── workflows/  
│       └── main.yml         \# Definición del workflow de GitHub Actions  
├── backend/  
│   ├── main.py              \# Script principal que orquesta el análisis  
│   ├── azure\_client.py      \# Lógica para conectar y descubrir clústeres en Azure  
│   ├── kubernetes\_analyzer.py \# Lógica para analizar pods y namespaces  
│   ├── pagerduty\_client.py  \# Lógica para obtener incidentes de PagerDuty  
│   ├── data\_processor.py    \# Lógica para procesar datos y aplicar el modelo de inferencia  
│   └── requirements.txt     \# Dependencias de Python  
├── frontend/  
│   ├── index.html           \# Estructura de la página web  
│   ├── assets/  
│   │   └── js/  
│   │       └── main.js      \# Lógica del frontend (fetch, Chart.js, UI)  
│   │   └── css/  
│   │       └── style.css    \# Archivo de estilos (output de Tailwind)  
│   └── tailwind.config.js   \# Configuración de Tailwind CSS  
├── .env.example             \# Ejemplo de variables de entorno necesarias  
├── tenants.json             \# Mapeo de UUID de namespaces a nombres de organizaciones  
└── README.md                \# Este archivo

## **🔄 Flujo de Trabajo Detallado**

1. **Disparo del Workflow:**  
   * **Automático:** Un cron en main.yml se activa cada 30 minutos.  
   * **Manual:** El usuario hace clic en "Actualizar Ahora" en el frontend. El JS del frontend realiza una llamada a la API de GitHub para disparar el evento workflow\_dispatch.  
2. **Ejecución en GitHub Actions:**  
   * El runner de GitHub se inicializa.  
   * Se hace checkout del código del repositorio.  
   * Se configura el entorno de Python y se instalan las dependencias de requirements.txt.  
   * Se configuran las credenciales de Azure usando az login con los secretos almacenados en GitHub.  
3. **Ejecución del Backend (main.py):**  
   * El script comienza y registra la hora de inicio.  
   * **Descubrimiento:** Llama a azure\_client.py para listar todos los clústeres AKS y filtra los que empiezan por ftdsp-prod-aks-cluster-.  
   * **Análisis en Paralelo:** Para cada clúster encontrado:  
     * Obtiene las credenciales del clúster (az aks get-credentials).  
     * kubernetes\_analyzer.py lista todos los namespaces.  
     * Filtra los namespaces que son UUIDs válidos.  
     * Para cada namespace UUID:  
       * Obtiene el estado de todos los pods (Running, Pending, Failed).  
       * Revisa los contenedores en busca de CrashLoopBackOff o reinicios altos.  
       * pagerduty\_client.py consulta la API de PagerDuty buscando incidentes relacionados.  
       * data\_processor.py calcula el % de disponibilidad y lo asocia con el nombre del tenant (de tenants.json).  
   * **Agregación y Modelo de Inferencia:**  
     * data\_processor.py consolida los datos de todos los clústeres y namespaces.  
     * Aplica una lógica de inferencia simple (ej: si la disponibilidad \< 95% o hay incidentes activos, el estado es Advertencia).  
     * Genera la estructura final del archivo status.json.  
4. **Publicación de Resultados:**  
   * El script guarda el status.json resultante.  
   * El workflow de GitHub Actions publica este archivo como un artefacto o lo sube a la rama de gh-pages para que el frontend pueda acceder a él.  
5. **Actualización del Frontend:**  
   * El main.js del frontend, que ya está cargado en el navegador del usuario, tiene una función (setInterval) que comprueba si la fecha de modificación del status.json ha cambiado.  
   * Cuando detecta un archivo nuevo, lo descarga, parsea el JSON y actualiza los gráficos y la UI con los nuevos datos.  
   * Si la actualización fue manual, el JS puede mostrar un estado de "Cargando..." y sondear más agresivamente la disponibilidad del nuevo archivo.

## **🛠️ Configuración del Entorno**

**Prerrequisitos:**

* Cuenta de Azure con permisos para leer clústeres AKS.  
* Cuenta de servicio o usuario para az login.  
* Token de API de PagerDuty.  
* Repositorio de GitHub con Actions habilitado.

Variables de Entorno / Secretos de GitHub:  
Se debe crear un archivo .env localmente para desarrollo y configurar los siguientes secretos en el repositorio de GitHub (Settings \> Secrets and variables \> Actions):  
\# .env.example

\# Credenciales de Azure  
AZURE\_USER=""  
AZURE\_PASSWORD=""

\# Token de la API de PagerDuty  
PAGERDUTY\_API\_TOKEN=""

\# ID del servicio de PagerDuty a monitorear (opcional, para filtrar)  
PAGERDUTY\_SERVICE\_ID=""

\# Token de GitHub para disparar el workflow desde el frontend  
\# Permisos requeridos: actions:write  
GITHUB\_TOKEN=""

## **🧩 Componentes Clave**

### **Backend (Python)**

* **main.py**: Orquesta el flujo. Llama a los otros módulos en secuencia y maneja el procesamiento paralelo.  
* **azure\_client.py**: Encapsula la lógica de az login y el descubrimiento de clústeres. Devuelve una lista de nombres de clústeres a analizar.  
* **kubernetes\_analyzer.py**: Utiliza la librería kubernetes-client de Python. Se conecta a un clúster específico y extrae información detallada de los pods y namespaces.  
* **pagerduty\_client.py**: Realiza peticiones GET a la API de PagerDuty. Filtra incidentes por servicio o fecha.  
* **data\_processor.py**: Contiene la lógica de negocio. Mapea UUIDs, calcula porcentajes y ejecuta el modelo de inferencia para determinar el estado (health\_status).

### **Frontend (JavaScript)**

* **main.js**:  
  * **init()**: Se ejecuta al cargar la página. Llama a fetchData() por primera vez y configura los gráficos de Chart.js con datos vacíos.  
  * **fetchData()**: Descarga el status.json. Al completarse, llama a updateUI().  
  * **updateUI(data)**: Recibe el JSON, actualiza los títulos, los KPIs y los datos de los gráficos (chart.data.datasets \= ...; chart.update();). Muestra la fecha de la "Última Actualización".  
  * **triggerWorkflow()**: Se asocia al botón "Actualizar Ahora". Muestra un spinner/mensaje de "Actualizando...". Realiza una petición POST a la API de GitHub Actions para iniciar el workflow.  
  * **startPolling()**: Se inicia después de un disparo manual para verificar la llegada del nuevo status.json.

### **GitHub Action**

* **main.yml**:  
  * on:: Define los triggers.  
    on:  
      workflow\_dispatch: \# Para disparo manual  
      schedule:  
        \- cron: '\*/30 \* \* \* \*' \# Cada 30 minutos

  * jobs:: Define el trabajo de análisis.  
    * steps::  
      * actions/checkout@v3  
      * azure/login@v1: Inicia sesión en Azure usando secretos.  
      * actions/setup-python@v4: Configura Python.  
      * run: pip install \-r backend/requirements.txt  
      * run: python backend/main.py: Ejecuta el análisis.  
      * actions/upload-artifact@v3: Sube el status.json como artefacto (o un paso para hacer commit a gh-pages).

## **📄 Contrato de Datos (API)**

El backend debe generar un status.json con una estructura predecible para que el frontend pueda consumirlo sin errores.

**Ejemplo de status.json:**

{  
  "last\_updated": "2023-10-27T10:30:00Z",  
  "overall\_status": "Advertencia",  
  "summary": {  
    "total\_clusters": 2,  
    "total\_namespaces\_monitored": 15,  
    "pods\_running": 150,  
    "pods\_with\_issues": 5,  
    "active\_incidents": 1  
  },  
  "clusters": \[  
    {  
      "name": "ftdsp-prod-aks-cluster-01",  
      "status": "Saludable",  
      "namespaces": \[  
        {  
          "uuid": "052e3aed-e210-4869-ae4b-062c02654ca7",  
          "organization\_name": "G3 Innovaciones SAPI de C.V.",  
          "status": "Saludable",  
          "availability\_percentage": 100,  
          "pods": {  
            "running": 20,  
            "pending": 0,  
            "failed": 0,  
            "restarts": 2  
          },  
          "related\_incidents": \[\]  
        }  
      \]  
    },  
    {  
      "name": "ftdsp-prod-aks-cluster-02",  
      "status": "Advertencia",  
      "namespaces": \[  
        {  
          "uuid": "33cd3010-8cc6-4548-8205-cb09ffc73140",  
          "organization\_name": "Abbott Diabetes Care",  
          "status": "Advertencia",  
          "availability\_percentage": 90,  
          "pods": {  
            "running": 18,  
            "pending": 1,  
            "failed": 1,  
            "restarts": 15  
          },  
          "related\_incidents": \[  
            {  
              "id": "P12345",  
              "title": "API response times are high",  
              "url": "https://abbott.pagerduty.com/incidents/P12345",  
              "created\_at": "2023-10-27T10:00:00Z"  
            }  
          \]  
        }  
      \]  
    }  
  \],  
  "historical\_data": {  
    "timestamps": \["2023-10-27T09:30:00Z", "2023-10-27T10:00:00Z", "2023-10-27T10:30:00Z"\],  
    "availability\_history": \[98, 97, 95\],  
    "incident\_history": \[0, 1, 1\]  
  }  
}

## **🚀 Uso y Despliegue**

1. **Clonar el repositorio.**  
2. **Configurar los secretos** en GitHub.  
3. **Desarrollo Local (Backend):**  
   * Crear un entorno virtual: python \-m venv venv  
   * Activar: source venv/bin/activate  
   * Instalar dependencias: pip install \-r backend/requirements.txt  
   * Configurar el archivo .env.  
   * Ejecutar az login manualmente.  
   * Ejecutar el script: python backend/main.py.  
4. **Desarrollo Local (Frontend):**  
   * Instalar dependencias de Tailwind: npm install.  
   * Iniciar el compilador de Tailwind: npm run watch.  
   * Abrir frontend/index.html en un navegador (se recomienda un servidor local como Live Server en VSCode).  
5. **Despliegue:**  
   * El workflow de GitHub Actions se encargará de la ejecución del backend.  
   * El frontend (HTML/JS/CSS) se puede desplegar usando **GitHub Pages**, apuntando a la carpeta frontend.  
   * Asegúrate de que el workflow actualice el status.json en la rama y carpeta que GitHub Pages está sirviendo.
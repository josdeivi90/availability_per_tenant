# 🔧 Configuración de GitHub Actions para KubeHealth Dashboard

Esta guía te ayudará a configurar todos los secretos y ajustes necesarios en tu repositorio de GitHub para que el workflow de **KubeHealth Dashboard** funcione correctamente.

## 📋 **Requisitos Previos**

- ✅ Repositorio creado en GitHub
- ✅ Acceso de administrador al repositorio
- ✅ Cuenta de Azure con permisos de AKS
- ✅ Token de API de PagerDuty
- ✅ Azure CLI instalado localmente (para configuración inicial)

---

## 🔑 **1. Configurar Secretos de GitHub**

Ve a tu repositorio en GitHub: **Settings > Secrets and variables > Actions**

### **Secretos Obligatorios (Configuración Simplificada para Testing):**

#### **1.1 Azure User (AZURE_USER)**
```bash
# Tu email de usuario de Azure
tu-usuario@dominio.com
```

#### **1.2 Azure Password (AZURE_PASSWORD)**
```bash
# Tu contraseña de Azure
tu-password-azure
```

> **💡 Nota:** Esta configuración usa tu login personal de Azure, ideal para testing y desarrollo inicial. Para producción se recomienda usar Service Principal.

### **Configuración Alternativa para Producción (Service Principal):**

Si prefieres usar Service Principal en lugar de credenciales personales:

#### **1.3 Azure Credentials (AZURE_CREDENTIALS) - ALTERNATIVA**
```bash
# En tu terminal local, ejecuta:
az ad sp create-for-rbac --name "kubehealth-dashboard" \
    --role="AKS Cluster User" \
    --scopes="/subscriptions/TU_SUBSCRIPTION_ID" \
    --sdk-auth
```

Copia la salida JSON completa y agrégala como secreto `AZURE_CREDENTIALS`:
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

#### **1.4 PagerDuty API Token (PAGERDUTY_API_TOKEN)**
```bash
# Token de API de PagerDuty con permisos de lectura
# Formato: u+xxxxxxxxxx o similar
u+123456789abcdef123456789abcdef12
```

### **Secretos Opcionales:**

#### **1.5 PagerDuty Service ID (PAGERDUTY_SERVICE_ID)**
```bash
# ID específico del servicio a monitorear (opcional)
PABCDEF
```

---

## 🔧 **2. Configurar GitHub Pages**

### **2.1 Habilitar GitHub Pages**
1. Ve a **Settings > Pages**
2. En **Source**, selecciona **"GitHub Actions"**
3. ✅ GitHub Pages se configurará automáticamente con el workflow

### **2.2 Configurar Permisos del Workflow**
1. Ve a **Settings > Actions > General**
2. En **Workflow permissions**, selecciona:
   - ✅ **"Read and write permissions"**
   - ✅ **"Allow GitHub Actions to create and approve pull requests"**

---

## 🚀 **3. Probar la Configuración**

### **3.1 Verificar Secretos**
```bash
# Ejecuta este comando en tu terminal local para verificar Azure:
az login
az account show
az aks list --output table

# Para PagerDuty:
curl -H "Authorization: Token token=TU_PAGERDUTY_TOKEN" \
     -H "Accept: application/vnd.pagerduty+json;version=2" \
     https://api.pagerduty.com/services
```

### **3.2 Ejecutar Workflow Manualmente**
1. Ve a **Actions > 🚀 KubeHealth Dashboard - Data Collection**
2. Haz clic en **"Run workflow"**
3. Selecciona la opción **"debug_mode"** para ver más logs
4. ✅ El workflow debería ejecutarse sin errores

---

## 📊 **4. Configurar Triggers Automáticos**

El workflow ya está configurado para ejecutarse:
- ⏱️ **Cada 30 minutos** automáticamente
- 🖱️ **Manualmente** desde la interfaz de GitHub
- 🔄 **En cada push** a la rama `main` (si hay cambios en backend)

---

## 🔍 **5. Monitoreo y Troubleshooting**

### **5.1 Logs del Workflow**
- Ve a **Actions** para ver el historial de ejecuciones
- Cada job muestra logs detallados con emojis para facilitar la lectura

### **5.2 Problemas Comunes**

#### **❌ Error de Autenticación Azure**
```bash
# Verificar credenciales
az account show

# Re-crear service principal si es necesario
az ad sp create-for-rbac --name "kubehealth-dashboard-new" \
    --role="AKS Cluster User" \
    --scopes="/subscriptions/TU_SUBSCRIPTION_ID" \
    --sdk-auth
```

#### **❌ Error de PagerDuty API**
```bash
# Verificar token
curl -H "Authorization: Token token=TU_TOKEN" \
     https://api.pagerduty.com/users/me
```

#### **❌ Error de GitHub Pages**
- Verificar que GitHub Pages esté habilitado
- Revisar permisos del workflow
- Asegurar que el repositorio sea público (o tener GitHub Pro)

### **5.3 Artifacts y Datos**
- Los archivos `status.json` se guardan como artifacts por 30 días
- GitHub Pages se actualiza automáticamente con cada ejecución exitosa

---

## 📱 **6. Acceso al Dashboard**

Una vez configurado, podrás acceder al dashboard en:
```
https://TU_USUARIO.github.io/TU_REPOSITORIO
```

### **6.1 Funcionalidades Disponibles**
- 📊 **Visualización en tiempo real** del estado de los clusters
- 📈 **Gráficos históricos** de disponibilidad
- 🔄 **Botón "Actualizar Ahora"** que dispara el workflow manualmente
- 📱 **Responsive design** para móviles y tablets

---

## 🔒 **7. Seguridad**

### **7.1 Mejores Prácticas**
- ✅ Usar service principals con permisos mínimos
- ✅ Rotar tokens de API regularmente
- ✅ Revisar logs de workflow periódicamente
- ✅ Mantener secretos actualizados

### **7.2 Permisos de Azure**
El service principal necesita únicamente:
- **AKS Cluster User**: Para leer información de clusters
- **Reader**: Para listar recursos (opcional)

---

## 📞 **8. Soporte**

Si encuentras problemas:
1. 🔍 Revisa los logs del workflow en **Actions**
2. 📋 Verifica que todos los secretos estén configurados
3. 🧪 Ejecuta las pruebas locales de conectividad
4. 📚 Consulta la documentación en `SETUP.md`

---

## ✅ **Lista de Verificación**

- [ ] Secretos de GitHub configurados
- [ ] GitHub Pages habilitado
- [ ] Permisos de workflow correctos
- [ ] Azure CLI y PagerDuty API funcionando
- [ ] Primer workflow ejecutado exitosamente
- [ ] Dashboard accesible en GitHub Pages

¡Una vez completados todos estos pasos, tu **KubeHealth Dashboard** estará completamente operativo! 🎉 
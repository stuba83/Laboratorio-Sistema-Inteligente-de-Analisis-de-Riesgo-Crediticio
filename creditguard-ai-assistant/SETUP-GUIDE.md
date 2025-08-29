# 🛠️ Guía de Configuración - CreditGuard AI Assistant

## 📋 **Prerrequisitos**

### ☁️ **Azure Subscription**
- Suscripción activa de Azure
- Permisos de Contributor en el resource group
- Azure CLI instalado y configurado

### 💻 **Ambiente Local**
- Python 3.9 o superior
- VS Code con extensiones de Azure
- Git configurado
- PowerShell (para scripts de deployment)

## 🚀 **Instalación Paso a Paso**

### **Paso 1: Configuración Inicial**
```bash
# Clonar el repositorio
git clone https://github.com/your-username/creditguard-ai-assistant.git
cd creditguard-ai-assistant

# Crear ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### **Paso 2: Configuración de Azure**
```bash
# Login a Azure
az login

# Configurar subscription
az account set --subscription "your-subscription-id"

# Crear resource group
az group create --name rg-creditguard-ai --location eastus
```

### **Paso 3: Desplegar Servicios**
```powershell
# Ejecutar deployment script
./infrastructure/deploy-azure-resources.ps1
```

### **Paso 4: Configurar Variables de Entorno**
```bash
# Copiar template
cp .env.template .env

# Editar .env con los valores de Azure
# (Los valores se obtienen del deployment anterior)
```

### **Paso 5: Preparar Datos**
```bash
# Ejecutar notebook de preparación de datos
jupyter notebook notebooks/01-data-preparation.ipynb
```

## 🧪 **Testing**
```bash
# Ejecutar tests
pytest tests/

# Test específico del agente
python -m pytest tests/test_agent.py -v
```

## 📊 **Monitoreo**
- Application Insights: Portal de Azure
- Logs: Azure Monitor
- Métricas: Dashboards personalizados

## 🆘 **Troubleshooting**
Ver [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) para problemas comunes.

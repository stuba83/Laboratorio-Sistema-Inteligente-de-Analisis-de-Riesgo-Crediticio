# 🏗️ Guía Completa de Despliegue de Infraestructura
## **CreditGuard AI Assistant - De Zero a Hero**

---

**👨‍💼 Instructor:** Steven Uba - Azure Digital Solution Engineer - Data and AI  
**⏱️ Duración estimada:** 60-90 minutos  
**🎯 Objetivo:** Desplegar infraestructura completa y datos ficticios listos para el laboratorio

---

## 📋 **Prerrequisitos**

### **☁️ Azure Requirements**
- ✅ **Suscripción Azure activa** con permisos de Contributor
- ✅ **Azure CLI instalado** y configurado
- ✅ **PowerShell 7+** (Windows) o **Bash** (Linux/Mac)
- ✅ **Git** configurado con acceso al repositorio

### **💰 Estimación de costos**
- **VM Standard_D4s_v3**: ~$140/mes
- **Azure OpenAI**: Pay-per-use (~$20-50 para el lab)
- **Azure AI Search Standard**: ~$250/mes
- **Cosmos DB**: ~$25/mes (RU mínimas)
- **Storage + Otros servicios**: ~$10/mes
- **💡 Total estimado**: ~$425/mes (apagar VM cuando no se use)

### **🔐 Permisos necesarios**
```bash
# Verificar permisos actuales
az role assignment list --assignee $(az account show --query user.name -o tsv) --all
```

---

## 🚀 **Fase 1: Preparación del Ambiente**

### **Paso 1.1: Clonar y configurar repositorio**
```bash
# 1. Clonar el repositorio
git clone https://github.com/your-username/creditguard-ai-assistant.git
cd creditguard-ai-assistant/infrastructure

# 2. Verificar archivos necesarios
ls -la
# Debe mostrar:
# - azure-resources.json
# - deploy-azure-resources.ps1  
# - vm-setup.sh
```

### **Paso 1.2: Configurar variables de ambiente**
```bash
# Configurar información personal
export OWNER_NAME="Tu Nombre Completo"
export RESOURCE_GROUP="rg-creditguard-$(echo $USER | tr '[:upper:]' '[:lower:]')"
export LOCATION="eastus"
export ADMIN_PASSWORD="CreditGuard2024!"  # Cambiar por password seguro
```

### **Paso 1.3: Verificar quotas de Azure**
```bash
# Verificar quotas disponibles
az vm list-usage --location eastus --output table

# Verificar disponibilidad de servicios AI
az cognitiveservices account list-kinds --location eastus
```

---

## 🏗️ **Fase 2: Despliegue de Infraestructura**

### **Paso 2.1: Ejecutar deployment**
```powershell
# PowerShell - Ejecutar desde infrastructure/
./deploy-azure-resources.ps1 `
    -OwnerName "Tu Nombre" `
    -ResourceGroupName "rg-creditguard-tu-nombre" `
    -AdminPassword (ConvertTo-SecureString "CreditGuard2024!" -AsPlainText -Force) `
    -Location "eastus" `
    -Environment "dev"
```

```bash
# Bash alternativo (convertir script a bash si es necesario)
chmod +x deploy-azure-resources.sh
./deploy-azure-resources.sh \
    --owner-name "Tu Nombre" \
    --resource-group "rg-creditguard-tu-nombre" \
    --admin-password "CreditGuard2024!" \
    --location "eastus" \
    --environment "dev"
```

### **Paso 2.2: Monitorear el deployment**
```bash
# Ver estado del deployment
az deployment group list --resource-group "rg-creditguard-tu-nombre" --output table

# Ver detalles específicos
az deployment group show \
    --resource-group "rg-creditguard-tu-nombre" \
    --name "azure-resources" \
    --query "properties.provisioningState"
```

### **Paso 2.3: Guardar información de conexión**
```bash
# Obtener outputs del deployment
az deployment group show \
    --resource-group "rg-creditguard-tu-nombre" \
    --name "azure-resources" \
    --query "properties.outputs" > deployment-outputs.json

# Ver información importante
cat deployment-outputs.json | jq '.deploymentSummary.value'
```

**📝 IMPORTANTE:** Guarda la información de conexión en un lugar seguro:
- 🌐 VM Public IP y FQDN
- 🔑 Service endpoints y keys
- 🔐 Connection strings

---

## 💻 **Fase 3: Configuración de la VM de Desarrollo**

### **Paso 3.1: Conectar a la VM**
```bash
# Obtener información de conexión
VM_IP=$(az deployment group show --resource-group "rg-creditguard-tu-nombre" --name "azure-resources" --query "properties.outputs.vmPublicIP.value" -o tsv)

# Conectar via SSH
ssh azureuser@$VM_IP
```

### **Paso 3.2: Ejecutar setup de la VM**
```bash
# Una vez conectado a la VM:

# 1. Descargar script de setup
wget https://raw.githubusercontent.com/your-username/creditguard-ai-assistant/main/infrastructure/vm-setup.sh

# 2. Dar permisos y ejecutar
chmod +x vm-setup.sh
./vm-setup.sh

# 3. El script tomará 15-20 minutos en completarse
# Seguir las instrucciones en pantalla
```

### **Paso 3.3: Verificar instalación**
```bash
# Después del setup, verificar que todo esté funcionando
source ~/.bashrc
sysinfo

# Debería mostrar todas las herramientas instaladas
```

### **Paso 3.4: Configurar acceso remoto**
```bash
# Iniciar Jupyter para verificar acceso remoto
lab

# Desde tu navegador local, acceder a:
# http://VM_IP:8888
```

---

## 🗄️ **Fase 4: Generación de Datos Ficticios**

### **Paso 4.1: Clonar repositorio en la VM**
```bash
# En la VM, activar ambiente de desarrollo
creditguard

# Clonar el proyecto
cd ~/Development/CreditGuard
git clone https://github.com/your-username/creditguard-ai-assistant.git .
```

### **Paso 4.2: Configurar variables de entorno**
```bash
# Copiar template de environment
cp .env.template .env

# Editar con información real del deployment
nano .env
```

**📝 Completar .env con información del deployment:**
```bash
# Ejemplo de valores a completar:
AZURE_OPENAI_ENDPOINT=https://creditguard-dev-openai-abc123.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
COSMOS_DB_ENDPOINT=https://creditguard-dev-cosmos-abc123.documents.azure.com:443/
COSMOS_DB_KEY=your_cosmos_key_here
# ... etc
```

### **Paso 4.3: Ejecutar generación de datos**
```bash
# Ejecutar notebook de preparación de datos
jupyter lab notebooks/01-data-preparation.ipynb

# O ejecutar script directo
python src/utils/data_generator.py --generate-all
```

---

## 📊 **Fase 5: Configuración de Servicios Azure**

### **Paso 5.1: Configurar Azure OpenAI**
```bash
# Crear deployments necesarios
OPENAI_RESOURCE="creditguard-dev-openai-abc123"

# GPT-4o deployment
az cognitiveservices account deployment create \
    --name $OPENAI_RESOURCE \
    --resource-group "rg-creditguard-tu-nombre" \
    --deployment-name "gpt-4o" \
    --model-name "gpt-4o" \
    --model-version "2024-05-13" \
    --model-format "OpenAI" \
    --sku-name "Standard" \
    --sku-capacity 10

# Ada embeddings deployment
az cognitiveservices account deployment create \
    --name $OPENAI_RESOURCE \
    --resource-group "rg-creditguard-tu-nombre" \
    --deployment-name "text-embedding-ada-002" \
    --model-name "text-embedding-ada-002" \
    --model-version "2" \
    --model-format "OpenAI" \
    --sku-name "Standard" \
    --sku-capacity 5
```

### **Paso 5.2: Configurar Cosmos DB**
```bash
# Crear database y container
COSMOS_ACCOUNT="creditguard-dev-cosmos-abc123"

# Crear database
az cosmosdb sql database create \
    --account-name $COSMOS_ACCOUNT \
    --resource-group "rg-creditguard-tu-nombre" \
    --name "CreditGuardDB"

# Crear container para customers
az cosmosdb sql container create \
    --account-name $COSMOS_ACCOUNT \
    --resource-group "rg-creditguard-tu-nombre" \
    --database-name "CreditGuardDB" \
    --name "Customers" \
    --partition-key-path "/customerId" \
    --throughput 400

# Crear container para applications  
az cosmosdb sql container create \
    --account-name $COSMOS_ACCOUNT \
    --resource-group "rg-creditguard-tu-nombre" \
    --database-name "CreditGuardDB" \
    --name "Applications" \
    --partition-key-path "/applicationId" \
    --throughput 400
```

### **Paso 5.3: Configurar AI Search**
```bash
# El servicio ya está creado, ahora crear índices
python src/services/ai_search_service.py --create-indexes
```

---

## 📋 **Datos Ficticios Generados**

### **👥 Customer Profiles (1,000 registros)**
```json
{
  "customerId": "CUST_001",
  "personalInfo": {
    "firstName": "Juan",
    "lastName": "Pérez",
    "age": 35,
    "occupation": "Software Engineer",
    "annualIncome": 75000,
    "employmentYears": 5,
    "education": "Bachelor's",
    "maritalStatus": "Married"
  },
  "financialProfile": {
    "currentAccounts": ["savings", "checking"],
    "creditHistory": "good",
    "debtToIncome": 0.35,
    "paymentHistory": "excellent",
    "bankruptcyHistory": false,
    "creditScore": 750
  },
  "addressInfo": {
    "street": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "zipCode": "78701",
    "yearsAtAddress": 3,
    "homeOwnership": "rent"
  },
  "riskFactors": {
    "addressStability": "high",
    "incomeVerification": "verified",
    "previousApplications": 1,
    "fraudAlerts": false
  }
}
```

### **💳 Credit Card Products**
```json
{
  "productId": "PLATINUM_001",
  "name": "Platinum Rewards Card",
  "category": "premium",
  "requirements": {
    "minimumIncome": 70000,
    "minimumCreditScore": 750,
    "employmentStatus": "full-time",
    "debtToIncomeMax": 0.40
  },
  "benefits": {
    "creditLimit": {"min": 10000, "max": 50000},
    "apr": 16.99,
    "rewardsRate": 0.02,
    "annualFee": 95,
    "introOffers": {
      "aprMonths": 12,
      "aprRate": 0.0,
      "bonusPoints": 50000
    }
  }
}
```

### **📋 Credit Policies (PDF sintético)**
```markdown
# FinanceFirst Bank - Credit Card Approval Policies v2.4

## Risk Assessment Matrix
- **Excellent (750+)**: Auto-approve up to $25,000
- **Good (700-749)**: Manual review up to $15,000  
- **Fair (650-699)**: Require additional verification
- **Poor (<650)**: Deny or secured card only

## Income Verification Requirements
- W2 employees: 2 years employment history
- Self-employed: 2 years tax returns
- Minimum DTI ratio: 40% or less
```

### **📖 Procedures Manual**
```markdown
# Credit Risk Assessment Procedures

## KYC (Know Your Customer) Requirements
1. Identity verification
2. Address confirmation
3. Income verification
4. Employment verification

## AML (Anti-Money Laundering) Checks
1. OFAC screening
2. PEP (Politically Exposed Person) check
3. Sanctions list verification

## Fraud Detection Protocols
1. Device fingerprinting
2. Behavioral analysis
3. Geographic risk assessment
4. Velocity checks
```

---

## 🧪 **Fase 6: Verificación y Testing**

### **Paso 6.1: Test de conectividad**
```python
# Ejecutar en Jupyter notebook
# Test básico de todos los servicios

# Azure OpenAI
from azure.openai import AzureOpenAI
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview"
)

# Test simple
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello from CreditGuard!"}]
)
print(response.choices[0].message.content)
```

### **Paso 6.2: Test de datos**
```bash
# Verificar datos en Cosmos DB
python src/utils/data_generator.py --verify-data

# Verificar índices en AI Search
python src/services/ai_search_service.py --verify-indexes
```

### **Paso 6.3: Test de embeddings**
```python
# Test de embeddings y vector search
python src/services/embeddings_service.py --test-embeddings
```

---

## 📊 **Monitoreo y Troubleshooting**

### **🔍 Comandos útiles de verificación**
```bash
# Ver todos los recursos creados
az resource list --resource-group "rg-creditguard-tu-nombre" --output table

# Verificar estado de servicios
az monitor metrics list --resource $RESOURCE_ID --metric "Requests"

# Ver logs de Application Insights
az monitor log-analytics query \
    --workspace $WORKSPACE_ID \
    --analytics-query "requests | limit 10"
```

### **⚠️ Problemas comunes**

#### **1. ARM Template falla**
```bash
# Ver detalles del error
az deployment group show \
    --resource-group "rg-creditguard-tu-nombre" \
    --name "azure-resources" \
    --query "properties.error"

# Soluciones comunes:
# - Verificar quotas de la suscripción
# - Cambiar región si hay limitaciones
# - Verificar nombres únicos de servicios
```

#### **2. VM no accesible**
```bash
# Verificar NSG rules
az network nsg rule list \
    --resource-group "rg-creditguard-tu-nombre" \
    --nsg-name "creditguard-dev-nsg" \
    --output table

# Verificar IP pública
az network public-ip show \
    --resource-group "rg-creditguard-tu-nombre" \
    --name "creditguard-dev-pip" \
    --query "ipAddress"
```

#### **3. Servicios AI no responden**
```bash
# Verificar keys y endpoints
az cognitiveservices account keys list \
    --name "creditguard-dev-openai-abc123" \
    --resource-group "rg-creditguard-tu-nombre"

# Test de conectividad
curl -H "Ocp-Apim-Subscription-Key: YOUR_KEY" \
     https://your-service.cognitiveservices.azure.com/
```

---

## ✅ **Checklist de Verificación Final**

### **🏗️ Infraestructura**
- [ ] ✅ Todos los recursos Azure desplegados
- [ ] ✅ VM accesible via SSH
- [ ] ✅ Jupyter Lab funcionando en puerto 8888
- [ ] ✅ VS Code configurado con extensiones

### **🤖 Servicios AI**
- [ ] ✅ Azure OpenAI con deployments GPT-4o y Ada
- [ ] ✅ Azure AI Search con índices creados
- [ ] ✅ Cognitive Services para Text-to-Speech
- [ ] ✅ Todas las keys y endpoints configurados

### **🗄️ Datos**
- [ ] ✅ Cosmos DB con databases y containers
- [ ] ✅ 1,000+ customer profiles generados
- [ ] ✅ Credit policies y procedures cargados
- [ ] ✅ Embeddings creados e indexados

### **🧪 Testing**
- [ ] ✅ Test de conectividad a todos los servicios
- [ ] ✅ Generación de embeddings funcionando
- [ ] ✅ Búsqueda semántica operativa
- [ ] ✅ Datos ficticios accesibles

---

## 🎯 **Próximos Pasos**

Una vez completado este despliegue:

1. **📚 Explorar datos**: Familiarizarse con los datasets generados
2. **🧪 Ejecutar notebooks**: Correr los notebooks de preparación
3. **🤖 Desarrollar agente**: Comenzar implementación del CreditGuard AI Assistant
4. **📊 Configurar monitoreo**: Setup de dashboards y alertas
5. **🚀 Testing E2E**: Pruebas de extremo a extremo del sistema

---

**🎉 ¡Felicitaciones! Tu infraestructura CreditGuard AI Assistant está lista para el desarrollo.**

**📧 Soporte:** Steven Uba - Azure Digital Solution Engineer - Data and AI  
**📖 Documentación completa:** `creditguard-ai-assistant/README.md`
# 🏦 CreditGuard AI Assistant

## **Sistema Inteligente de Análisis de Riesgo Crediticio**

### 👨‍💼 **Autor**
**Steven Uba** - Sr. Azure Digital Solution Engineer - Data and AI

### 🎯 **Descripción**
CreditGuard AI Assistant es una solución completa de análisis de riesgo crediticio que utiliza Azure AI Services para automatizar el proceso de evaluación de solicitudes de tarjetas de crédito.

### 🏗️ **Arquitectura**
- **🤖 Azure AI Foundry Agent Service** - Orchestración principal
- **🧠 Azure OpenAI (GPT-4o)** - Análisis inteligente
- **🔍 Azure AI Search** - Base de conocimiento (RAG)
- **🗄️ Azure Cosmos DB** - Base de datos de clientes
- **🗣️ Azure Speech Services** - Text-to-Speech
- **🌐 Bing Search** - Inteligencia de mercado

### 🚀 **Quick Start**

1. **Clonar repositorio:**
   ```bash
   git clone https://github.com/your-username/creditguard-ai-assistant.git
   cd creditguard-ai-assistant
   ```

2. **Configurar ambiente:**
   ```bash
   cp .env.template .env
   # Editar .env con tus valores de Azure
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Desplegar infraestructura:**
   ```bash
   # Desde PowerShell
   ./infrastructure/deploy-azure-resources.ps1
   ```

5. **Ejecutar el agente:**
   ```bash
   python src/agents/credit_risk_agent.py
   ```

### 📚 **Documentación**
- [📖 Setup Guide](SETUP-GUIDE.md) - Guía completa de instalación
- [🏗️ Architecture](docs/architecture.md) - Documentación de arquitectura
- [🧪 Testing](docs/testing.md) - Guías de testing

### 🤝 **Contribuciones**
¡Las contribuciones son bienvenidas! Por favor lee las [guías de contribución](CONTRIBUTING.md) antes de enviar un PR.

### 📄 **Licencia**
Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

**🎯 Construyendo el futuro del análisis crediticio con Azure AI**

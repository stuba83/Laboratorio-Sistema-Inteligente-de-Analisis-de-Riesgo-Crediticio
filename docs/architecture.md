# 🏗️ Arquitectura del Sistema CreditGuard AI Assistant

**Instructor:** Steven Uba - Azure Digital Solution Engineer - Data and AI  
**Versión:** 1.0.0  
**Fecha:** Diciembre 2024

---

## 📊 Diagrama de Arquitectura General

```mermaid
graph TB
    %% External Systems
    subgraph "🌐 Sistemas Externos"
        CB[Credit Bureau APIs<br/>Experian, Equifax, TransUnion]
        BING[Bing Search API<br/>Market Intelligence]
        BUREAU[Bureau de Crédito API<br/>Simulado]
    end

    %% User Interface Layer
    subgraph "💻 Capa de Presentación"
        VS[VS Code<br/>Development Environment]
        JUP[Jupyter Notebooks<br/>Analysis & Testing]
        CLI[Azure CLI<br/>Deployment & Management]
    end

    %% Application Layer
    subgraph "🤖 Capa de Aplicación"
        AGENT[CreditRiskAgent<br/>Orchestrator Principal]
        
        subgraph "🔌 Plugins"
            CBP[CreditBureauPlugin<br/>Datos de Crédito]
            MRP[MarketResearchPlugin<br/>Inteligencia de Mercado]
            VCP[VoiceCommunicationPlugin<br/>Text-to-Speech]
        end
    end

    %% Business Logic Layer
    subgraph "⚙️ Capa de Lógica de Negocio"
        RC[RiskCalculator<br/>Algoritmos de Riesgo]
        SK[Semantic Kernel<br/>AI Orchestration]
        RAG[RAG System<br/>Retrieval Augmented Generation]
    end

    %% Azure AI Services Layer
    subgraph "🧠 Azure AI Services"
        AOI[Azure OpenAI<br/>GPT-4o & Ada Embeddings]
        AIS[Azure AI Search<br/>Vector & Semantic Search]
        SPEECH[Azure Speech Services<br/>Text-to-Speech]
        FOUNDRY[Azure AI Foundry<br/>Agent Service]
    end

    %% Data Layer
    subgraph "🗄️ Capa de Datos"
        COSMOS[Azure Cosmos DB<br/>NoSQL Database]
        STORAGE[Azure Blob Storage<br/>Documents & Media]
        CACHE[In-Memory Cache<br/>Embeddings & Results]
    end

    %% Infrastructure Layer
    subgraph "☁️ Infraestructura Azure"
        VM[Azure Virtual Machine<br/>Data Science VM Ubuntu]
        VNET[Virtual Network<br/>Secure Networking]
        KV[Azure Key Vault<br/>Secrets Management]
        MONITOR[Azure Monitor<br/>Logging & Analytics]
    end

    %% Connections
    VS --> AGENT
    JUP --> AGENT
    CLI --> VM

    AGENT --> CBP
    AGENT --> MRP
    AGENT --> VCP
    AGENT --> RC
    AGENT --> SK

    CBP --> CB
    CBP --> BUREAU
    MRP --> BING
    VCP --> SPEECH

    SK --> AOI
    RAG --> AIS
    RAG --> AOI

    AGENT --> COSMOS
    AGENT --> STORAGE
    AGENT --> CACHE

    AOI --> FOUNDRY
    AIS --> FOUNDRY

    VM --> VNET
    AGENT --> KV
    AGENT --> MONITOR

    %% Styling
    classDef external fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    classDef ui fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef app fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef business fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef ai fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef data fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef infra fill:#f1f8e9,stroke:#689f38,stroke-width:2px

    class CB,BING,BUREAU external
    class VS,JUP,CLI ui
    class AGENT,CBP,MRP,VCP app
    class RC,SK,RAG business
    class AOI,AIS,SPEECH,FOUNDRY ai
    class COSMOS,STORAGE,CACHE data
    class VM,VNET,KV,MONITOR infra
```

---

## 🔄 Flujo de Procesamiento de Evaluación de Riesgo

```mermaid
sequenceDiagram
    participant U as Usuario/Sistema
    participant A as CreditRiskAgent
    participant CB as CreditBureauPlugin
    participant MR as MarketResearchPlugin
    participant RC as RiskCalculator
    participant AI as Azure OpenAI
    participant DB as Cosmos DB
    participant VC as VoicePlugin

    U->>A: Solicitar evaluación de riesgo
    
    Note over A: 1. Inicialización
    A->>DB: Recuperar perfil del cliente
    
    Note over A: 2. Recopilación de datos
    par Datos de crédito
        A->>CB: Obtener reporte de crédito
        CB->>CB: Simular llamadas a bureaus
        CB-->>A: Retornar datos consolidados
    and Investigación de mercado
        A->>MR: Buscar tendencias de fraude
        MR->>MR: Consultar Bing Search API
        MR-->>A: Retornar intelligence de mercado
    end

    Note over A: 3. Análisis de riesgo
    A->>RC: Calcular riesgo comprehensivo
    RC->>RC: Aplicar algoritmos multi-dimensionales
    RC-->>A: Retornar assessment detallado

    Note over A: 4. Análisis con IA
    A->>AI: Análisis con GPT-4o
    AI->>AI: Procesar contexto y políticas
    AI-->>A: Retornar análisis inteligente

    Note over A: 5. Toma de decisión
    A->>A: Combinar todos los factores
    A->>DB: Almacenar evaluación
    
    Note over A: 6. Comunicación
    opt Si se requiere voz
        A->>VC: Generar resumen de voz
        VC-->>A: Retornar audio
    end

    A-->>U: Retornar decisión completa
```

---

## 🏛️ Arquitectura de Datos

```mermaid
erDiagram
    CUSTOMERS {
        string customerId PK
        object personalInfo
        object financialProfile
        object addressInfo
        string customerSegment
        float riskScore
        datetime lastUpdated
    }

    APPLICATIONS {
        string applicationId PK
        string customerId FK
        string productType
        float requestedLimit
        string status
        datetime createdTimestamp
    }

    RISK_EVALUATIONS {
        string id PK
        string customerId FK
        float overallRiskScore
        string riskLevel
        array riskFactors
        array marketInsights
        datetime evaluationTimestamp
    }

    CREDIT_DECISIONS {
        string id PK
        string customerId FK
        string applicationId FK
        string outcome
        float approvedLimit
        array conditions
        string reasoning
        datetime decisionTimestamp
    }

    COMPLIANCE_REPORTS {
        string id PK
        string customerId FK
        string applicationId FK
        float complianceScore
        object regulatoryChecks
        array auditTrail
        datetime reportTimestamp
    }

    AUDIT_LOGS {
        string id PK
        string operationType
        string documentId
        string userId
        object details
        datetime timestamp
    }

    CUSTOMERS ||--o{ APPLICATIONS : "has many"
    CUSTOMERS ||--o{ RISK_EVALUATIONS : "has many"
    APPLICATIONS ||--|| CREDIT_DECISIONS : "results in"
    APPLICATIONS ||--|| COMPLIANCE_REPORTS : "generates"
    CUSTOMERS ||--o{ AUDIT_LOGS : "tracked by"
```

---

## 🔌 Arquitectura de Plugins

```mermaid
graph LR
    subgraph "🎯 Plugin Interface"
        PI[Plugin Interface<br/>Standardized Methods]
    end

    subgraph "🏛️ Credit Bureau Plugin"
        CBP[CreditBureauPlugin]
        CBM[Multi-Bureau Integration]
        CBC[Caching Layer]
        CBV[Data Validation]
        
        CBP --> CBM
        CBM --> CBC
        CBC --> CBV
    end

    subgraph "📰 Market Research Plugin"
        MRP[MarketResearchPlugin]
        BAS[Bing API Service]
        MRA[Market Analysis]
        FTD[Fraud Trend Detection]
        
        MRP --> BAS
        BAS --> MRA
        MRA --> FTD
    end

    subgraph "🗣️ Voice Communication Plugin"
        VCP[VoiceCommunicationPlugin]
        ASS[Azure Speech Service]
        VPM[Voice Profile Manager]
        TTS[Text-to-Speech Engine]
        
        VCP --> ASS
        ASS --> VPM
        VPM --> TTS
    end

    PI --> CBP
    PI --> MRP
    PI --> VCP

    %% External connections
    CBM -.-> EXT1[External Credit Bureaus]
    BAS -.-> EXT2[Bing Search API]
    ASS -.-> EXT3[Azure Speech Services]
```

---

## 🧠 Arquitectura de IA y RAG

```mermaid
graph TB
    subgraph "📥 Input Processing"
        QP[Query Processing]
        TC[Text Chunking]
        PP[Policy Parsing]
    end

    subgraph "🔍 Embeddings & Search"
        EMB[Azure OpenAI<br/>Ada Embeddings]
        VS[Vector Store<br/>Azure AI Search]
        SS[Semantic Search]
        HS[Hybrid Search]
    end

    subgraph "🧠 AI Processing"
        GPT[Azure OpenAI<br/>GPT-4o]
        SK[Semantic Kernel<br/>Orchestration]
        PC[Prompt Construction]
    end

    subgraph "📤 Output Generation"
        RG[Response Generation]
        VC[Voice Conversion]
        RF[Report Formatting]
    end

    subgraph "🗄️ Knowledge Base"
        POL[Credit Policies]
        PROC[Procedures Manual]
        REG[Regulatory Guidelines]
        HIST[Historical Decisions]
    end

    QP --> EMB
    TC --> EMB
    PP --> EMB

    EMB --> VS
    VS --> SS
    VS --> HS

    SS --> PC
    HS --> PC
    PC --> SK
    SK --> GPT

    GPT --> RG
    RG --> VC
    RG --> RF

    POL --> VS
    PROC --> VS
    REG --> VS
    HIST --> VS

    %% Styling
    classDef input fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef search fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef ai fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef output fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef kb fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class QP,TC,PP input
    class EMB,VS,SS,HS search
    class GPT,SK,PC ai
    class RG,VC,RF output
    class POL,PROC,REG,HIST kb
```

---

## 🛡️ Arquitectura de Seguridad y Compliance

```mermaid
graph TB
    subgraph "🔐 Authentication & Authorization"
        AAD[Azure Active Directory]
        RBAC[Role-Based Access Control]
        KV[Azure Key Vault]
    end

    subgraph "🛡️ Security Controls"
        NSG[Network Security Groups]
        WAF[Web Application Firewall]
        DDP[Data Loss Prevention]
    end

    subgraph "📊 Monitoring & Compliance"
        AL[Azure Monitor Logs]
        SC[Security Center]
        COMP[Compliance Dashboard]
    end

    subgraph "🔒 Data Protection"
        ENC[Encryption at Rest/Transit]
        PII[PII Detection & Masking]
        AUDIT[Audit Logging]
    end

    AAD --> RBAC
    RBAC --> KV
    NSG --> WAF
    WAF --> DDP
    AL --> SC
    SC --> COMP
    ENC --> PII
    PII --> AUDIT

    %% Cross-connections
    KV -.-> ENC
    AUDIT -.-> AL
    COMP -.-> AUDIT
```

---

## ⚡ Patrones de Rendimiento y Escalabilidad

```mermaid
graph LR
    subgraph "🎯 Load Balancing"
        LB[Azure Load Balancer]
        AG[Application Gateway]
    end

    subgraph "💾 Caching Strategy"
        RC[Redis Cache]
        MC[Memory Cache]
        CDN[Content Delivery Network]
    end

    subgraph "📈 Auto Scaling"
        VMSS[VM Scale Sets]
        AS[Auto Scaling Rules]
        HPA[Horizontal Pod Autoscaler]
    end

    subgraph "🔄 Async Processing"
        SB[Service Bus]
        EH[Event Hubs]
        AF[Azure Functions]
    end

    LB --> AG
    RC --> MC
    MC --> CDN
    VMSS --> AS
    AS --> HPA
    SB --> EH
    EH --> AF

    %% Performance optimizations
    AG -.-> CDN
    MC -.-> RC
    AF -.-> SB
```

---

## 🚀 Pipeline de Deployment

```mermaid
graph LR
    subgraph "💻 Development"
        DEV[Local Development]
        GIT[Git Repository]
        PR[Pull Request]
    end

    subgraph "🧪 CI/CD Pipeline"
        BUILD[Azure DevOps Build]
        TEST[Automated Testing]
        SCAN[Security Scanning]
    end

    subgraph "🌍 Environments"
        DEV_ENV[Development]
        STAGE[Staging]
        PROD[Production]
    end

    subgraph "📦 Deployment"
        ARM[ARM Templates]
        TERRAFORM[Terraform]
        HELM[Helm Charts]
    end

    DEV --> GIT
    GIT --> PR
    PR --> BUILD
    BUILD --> TEST
    TEST --> SCAN
    SCAN --> DEV_ENV
    DEV_ENV --> STAGE
    STAGE --> PROD

    ARM --> DEV_ENV
    TERRAFORM --> STAGE
    HELM --> PROD
```

---

## 📚 Componentes Técnicos Detallados

### 🤖 CreditRiskAgent
- **Función**: Orchestrador principal del sistema
- **Responsabilidades**:
  - Coordinación de plugins
  - Evaluación integral de riesgo
  - Toma de decisiones automatizada
  - Generación de reportes de compliance

### 🔌 Sistema de Plugins
- **CreditBureauPlugin**: Integración con bureaus de crédito
- **MarketResearchPlugin**: Inteligencia de mercado en tiempo real
- **VoiceCommunicationPlugin**: Síntesis de voz para comunicaciones

### 🧠 Azure AI Services
- **Azure OpenAI**: GPT-4o para análisis y Ada-002 para embeddings
- **Azure AI Search**: Búsqueda vectorial y semántica
- **Azure Speech Services**: Text-to-speech multiidioma

### 🗄️ Persistencia de Datos
- **Azure Cosmos DB**: Base de datos NoSQL para datos transaccionales
- **Azure Blob Storage**: Almacenamiento de documentos y media
- **Azure AI Search**: Índices vectoriales para RAG

### ⚙️ Lógica de Negocio
- **RiskCalculator**: Algoritmos avanzados de scoring
- **Semantic Kernel**: Orchestración de IA
- **RAG System**: Retrieval Augmented Generation

---

## 🏷️ Ubicación del Archivo

**📍 Guardar como:** `docs/architecture.md`

Este diagrama proporciona una visión completa de cómo todos los componentes del sistema CreditGuard AI Assistant se conectan e interactúan, facilitando la comprensión tanto para estudiantes como para implementadores del sistema.
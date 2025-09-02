# 🏦 CreditGuard AI Assistant - Infrastructure Deployment Script
# 👨‍💼 Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
# 📅 Version: 1.0.0

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "rg-creditguard-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectName = "creditguard",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "test", "prod")]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$OwnerName,
    
    [Parameter(Mandatory=$true)]
    [SecureString]$AdminPassword,
    
    [Parameter(Mandatory=$false)]
    [string]$AdminUsername = "azureuser",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("Standard_D2s_v3", "Standard_D4s_v3", "Standard_D8s_v3")]
    [string]$VmSize = "Standard_D4s_v3",
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf
)

# 🎨 Colores para output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# 📋 Header del script
Clear-Host
Write-ColorOutput "🏦===============================================" "Cyan"
Write-ColorOutput "   CreditGuard AI Assistant - Infrastructure   " "Cyan" 
Write-ColorOutput "   Azure AI Services Training Lab              " "Cyan"
Write-ColorOutput "===============================================🏦" "Cyan"
Write-Host ""
Write-ColorOutput "👨‍💼 Instructor: Steven Uba - Azure Digital Solution Engineer" "Yellow"
Write-Host ""

# 🔍 Detectar información del usuario si no se proporciona
if ([string]::IsNullOrEmpty($OwnerName)) {
    try {
        # Intentar obtener el nombre del usuario actual de Azure
        $currentUser = az account show --query "user.name" -o tsv 2>$null
        if ([string]::IsNullOrEmpty($currentUser)) {
            $OwnerName = $env:USERNAME
            if ([string]::IsNullOrEmpty($OwnerName)) {
                $OwnerName = "Lab-Student-$(Get-Random -Minimum 100 -Maximum 999)"
            }
        } else {
            $OwnerName = $currentUser
        }
        Write-ColorOutput "📝 Detected Owner: $OwnerName" "Green"
    } catch {
        $OwnerName = "Lab-Student-$(Get-Random -Minimum 100 -Maximum 999)"
        Write-ColorOutput "📝 Generated Owner: $OwnerName" "Yellow"
    }
} else {
    Write-ColorOutput "📝 Using provided Owner: $OwnerName" "Green"
}

# 📊 Mostrar configuración del deployment
Write-ColorOutput "🔧 Deployment Configuration:" "White"
Write-Host "   📁 Resource Group: $ResourceGroupName"
Write-Host "   🌍 Location: $Location" 
Write-Host "   🏷️  Project: $ProjectName"
Write-Host "   🔖 Environment: $Environment"
Write-Host "   👤 Owner: $OwnerName"
Write-Host "   💻 VM Size: $VmSize"
Write-Host "   🔑 Admin User: $AdminUsername"
Write-Host ""

# 🤔 Confirmación del usuario
if (-not $WhatIf) {
    $confirmation = Read-Host "¿Continuar with deployment? (y/N)"
    if ($confirmation -ne 'y' -and $confirmation -ne 'Y' -and $confirmation -ne 'yes') {
        Write-ColorOutput "❌ Deployment cancelled by user." "Red"
        exit 1
    }
}

# 🔐 Verificar Azure CLI login
Write-ColorOutput "🔐 Checking Azure CLI authentication..." "Yellow"
try {
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        Write-ColorOutput "⚠️  Not logged into Azure. Initiating login..." "Yellow"
        az login
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "❌ Azure login failed." "Red"
            exit 1
        }
    } else {
        Write-ColorOutput "✅ Already logged into Azure as: $($account.user.name)" "Green"
        Write-ColorOutput "   📋 Subscription: $($account.name)" "Cyan"
    }
} catch {
    Write-ColorOutput "❌ Error checking Azure authentication: $($_.Exception.Message)" "Red"
    exit 1
}

# 📁 Crear Resource Group
Write-ColorOutput "📁 Creating/Validating Resource Group..." "Yellow"
try {
    $rg = az group show --name $ResourceGroupName 2>$null | ConvertFrom-Json
    if ($rg) {
        Write-ColorOutput "✅ Resource Group '$ResourceGroupName' already exists." "Green"
    } else {
        Write-ColorOutput "📁 Creating Resource Group '$ResourceGroupName'..." "Yellow"
        az group create --name $ResourceGroupName --location $Location
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create resource group"
        }
        Write-ColorOutput "✅ Resource Group created successfully." "Green"
    }
} catch {
    Write-ColorOutput "❌ Error with Resource Group: $($_.Exception.Message)" "Red"
    exit 1
}

# 🏗️ Desplegar ARM Template
Write-ColorOutput "🚀 Starting ARM Template deployment..." "Yellow"
Write-ColorOutput "   ⏱️  This may take 10-15 minutes..." "Cyan"
Write-Host ""

if ($WhatIf) {
    Write-ColorOutput "🔍 Running What-If analysis..." "Cyan"
    $deploymentCommand = @"
az deployment group what-if ``
    --resource-group "$ResourceGroupName" ``
    --template-file "azure-resources.json" ``
    --parameters ``
        projectName="$ProjectName" ``
        environment="$Environment" ``
        location="$Location" ``
        ownerName="$OwnerName" ``
        administratorLogin="$AdminUsername" ``
        administratorPassword="$([System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminPassword)))" ``
        vmSize="$VmSize"
"@
} else {
    $deploymentCommand = @"
az deployment group create ``
    --resource-group "$ResourceGroupName" ``
    --template-file "azure-resources.json" ``
    --parameters ``
        projectName="$ProjectName" ``
        environment="$Environment" ``
        location="$Location" ``
        ownerName="$OwnerName" ``
        administratorLogin="$AdminUsername" ``
        administratorPassword="$([System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminPassword)))" ``
        vmSize="$VmSize"
"@
}

try {
    Invoke-Expression $deploymentCommand
    if ($LASTEXITCODE -ne 0) {
        throw "ARM template deployment failed"
    }
    
    if (-not $WhatIf) {
        Write-ColorOutput "✅ Infrastructure deployment completed successfully!" "Green"
        
        # 📊 Obtener outputs del deployment
        Write-ColorOutput "📊 Retrieving deployment outputs..." "Yellow"
        $outputs = az deployment group show --resource-group $ResourceGroupName --name "azure-resources" --query "properties.outputs" | ConvertFrom-Json
        
        if ($outputs) {
            Write-Host ""
            Write-ColorOutput "🔗 Deployment Summary:" "Cyan"
            Write-ColorOutput "===========================================" "Cyan"
            
            if ($outputs.deploymentSummary.value) {
                $summary = $outputs.deploymentSummary.value
                Write-Host "📋 Project: $($summary.projectName)"
                Write-Host "🔖 Environment: $($summary.environment)"
                Write-Host "👤 Owner: $OwnerName"
                Write-Host "🌍 Location: $($summary.location)"
                Write-Host "📁 Resource Group: $($summary.resourceGroupName)"
                Write-Host ""
                
                if ($summary.vmAccessInfo) {
                    Write-ColorOutput "💻 VM Access Information:" "Green"
                    Write-Host "   🌐 Public IP: $($summary.vmAccessInfo.publicIP)"
                    Write-Host "   🔗 FQDN: $($summary.vmAccessInfo.fqdn)"
                    Write-Host "   👤 Username: $($summary.vmAccessInfo.adminUsername)"
                    Write-Host "   🔑 SSH Command: $($summary.vmAccessInfo.sshCommand)"
                }
            }
            
            # 🔑 Información importante de conexión
            Write-Host ""
            Write-ColorOutput "🔑 Important Connection Information:" "Yellow"
            Write-ColorOutput "Save this information securely!" "Red"
            Write-Host ""
            
            if ($outputs.openAIEndpoint.value) {
                Write-Host "🤖 Azure OpenAI Endpoint: $($outputs.openAIEndpoint.value)"
            }
            if ($outputs.searchServiceEndpoint.value) {
                Write-Host "🔍 AI Search Endpoint: $($outputs.searchServiceEndpoint.value)" 
            }
            if ($outputs.cosmosDBEndpoint.value) {
                Write-Host "🗄️  Cosmos DB Endpoint: $($outputs.cosmosDBEndpoint.value)"
            }
            if ($outputs.keyVaultUri.value) {
                Write-Host "🔒 Key Vault URI: $($outputs.keyVaultUri.value)"
            }
        }
        
        Write-Host ""
        Write-ColorOutput "📝 Next Steps:" "Green"
        Write-Host "1. 🔐 Copy the connection information above"
        Write-Host "2. 💻 Connect to your VM using the SSH command"
        Write-Host "3. 📋 Update your .env file with the service endpoints"
        Write-Host "4. 🚀 Start the CreditGuard AI Assistant setup"
        Write-Host ""
        Write-ColorOutput "📖 For detailed instructions, see: creditguard-ai-assistant/SETUP-GUIDE.md" "Cyan"
        
    } else {
        Write-ColorOutput "✅ What-If analysis completed. Review the changes above." "Green"
    }
    
} catch {
    Write-ColorOutput "❌ Deployment failed: $($_.Exception.Message)" "Red"
    Write-Host ""
    Write-ColorOutput "🔍 Troubleshooting tips:" "Yellow"
    Write-Host "1. Check that you have sufficient permissions in the subscription"
    Write-Host "2. Verify that the selected VM size is available in the region"
    Write-Host "3. Ensure your password meets Azure complexity requirements"
    Write-Host "4. Check Azure service quotas for your subscription"
    Write-Host ""
    Write-ColorOutput "📞 Need help? Contact: Steven Uba - Azure Digital Solution Engineer" "Cyan"
    exit 1
}

Write-Host ""
Write-ColorOutput "🎉 CreditGuard AI Assistant infrastructure is ready!" "Green"
Write-ColorOutput "Happy learning! 🚀" "Yellow"
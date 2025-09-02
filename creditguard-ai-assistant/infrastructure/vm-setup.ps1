# 🏦 CreditGuard AI Assistant - VM Setup Script
# 👨‍💼 Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
# 🐧 Target: Ubuntu 20.04 Data Science VM
# 📅 Version: 1.0.0

#!/bin/bash

# 🎨 Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 📝 Función para logging
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" 
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 📋 Header del script
clear
echo -e "${CYAN}🏦======================================================${NC}"
echo -e "${CYAN}   CreditGuard AI Assistant - VM Development Setup   ${NC}"
echo -e "${CYAN}   Ubuntu 20.04 Data Science VM Configuration        ${NC}"  
echo -e "${CYAN}======================================================🏦${NC}"
echo ""
echo -e "${YELLOW}👨‍💼 Instructor: Steven Uba - Azure Digital Solution Engineer${NC}"
echo -e "${YELLOW}📧 Support: steven.uba@microsoft.com${NC}"
echo ""

# 🔍 Verificar que estamos en Ubuntu
if [[ ! -f /etc/lsb-release ]] || ! grep -q "Ubuntu" /etc/lsb-release; then
    log_error "This script is designed for Ubuntu. Current OS not supported."
    exit 1
fi

OS_VERSION=$(lsb_release -rs)
log_info "Detected OS: Ubuntu $OS_VERSION"

# 🔄 Función para verificar y reintentar comandos
retry_command() {
    local cmd="$1"
    local desc="$2"
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Attempting $desc (try $attempt/$max_attempts)..."
        if eval "$cmd"; then
            log_success "$desc completed successfully"
            return 0
        else
            log_warning "$desc failed on attempt $attempt"
            if [ $attempt -eq $max_attempts ]; then
                log_error "$desc failed after $max_attempts attempts"
                return 1
            fi
            sleep 5
            ((attempt++))
        fi
    done
}

# 🔧 Actualizar sistema
log_info "🔄 Starting system update..."
retry_command "sudo apt update && sudo apt upgrade -y" "System update"

# 📦 Instalar dependencias del sistema
log_info "📦 Installing system dependencies..."
SYSTEM_PACKAGES="curl wget git vim nano htop tree unzip build-essential software-properties-common apt-transport-https ca-certificates gnupg lsb-release"
retry_command "sudo apt install -y $SYSTEM_PACKAGES" "System packages installation"

# 🐍 Configurar Python y pip
log_info "🐍 Configuring Python environment..."
retry_command "sudo apt install -y python3.9 python3.9-dev python3.9-venv python3-pip" "Python installation"
retry_command "sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1" "Python alternatives"
retry_command "python3 -m pip install --upgrade pip setuptools wheel" "Pip upgrade"

# 📝 Instalar Jupyter y extensiones
log_info "📝 Installing Jupyter and extensions..."
retry_command "python3 -m pip install jupyter jupyterlab notebook ipywidgets" "Jupyter installation"
retry_command "python3 -m pip install jupyter_contrib_nbextensions" "Jupyter extensions"
retry_command "jupyter contrib nbextension install --user" "Jupyter extensions configuration"

# 🔧 Instalar Azure CLI
log_info "☁️ Installing Azure CLI..."
retry_command "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash" "Azure CLI installation"

# 🐳 Instalar Docker
log_info "🐳 Installing Docker..."
retry_command "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg" "Docker GPG key"
retry_command "echo \"deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null" "Docker repository"
retry_command "sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin" "Docker installation"
retry_command "sudo usermod -aG docker $USER" "Docker user configuration"

# 📦 Instalar Node.js y npm (para algunas extensiones)
log_info "📦 Installing Node.js..."
retry_command "curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -" "Node.js repository setup"
retry_command "sudo apt install -y nodejs" "Node.js installation"

# 💻 Instalar VS Code
log_info "💻 Installing Visual Studio Code..."
retry_command "wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg" "VS Code GPG key"
retry_command "sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/" "VS Code key installation"
retry_command "sudo sh -c 'echo \"deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main\" > /etc/apt/sources.list.d/vscode.list'" "VS Code repository"
retry_command "sudo apt update && sudo apt install -y code" "VS Code installation"

# 🔌 Instalar extensiones de VS Code
log_info "🔌 Installing VS Code extensions..."
VSCODE_EXTENSIONS=(
    "ms-python.python"
    "ms-python.black-formatter" 
    "ms-python.flake8"
    "ms-python.pylint"
    "ms-vscode.azure-account"
    "ms-azuretools.azure-dev"
    "ms-azuretools.vscode-azure-functions-core"
    "ms-vscode.vscode-json"
    "ms-vscode.PowerShell"
    "GitHub.copilot"
    "ms-toolsai.jupyter"
    "ms-toolsai.vscode-jupyter-cell-tags"
    "ms-toolsai.vscode-jupyter-slideshow"
    "redhat.vscode-yaml"
    "formulahendry.auto-rename-tag"
    "esbenp.prettier-vscode"
    "bradlc.vscode-tailwindcss"
)

for extension in "${VSCODE_EXTENSIONS[@]}"; do
    log_info "Installing VS Code extension: $extension"
    code --install-extension "$extension" --force 2>/dev/null || log_warning "Failed to install extension: $extension"
done

# 🐍 Crear ambiente virtual para el proyecto
log_info "🐍 Creating Python virtual environment..."
VENV_PATH="/home/$USER/creditguard-venv"
retry_command "python3 -m venv $VENV_PATH" "Virtual environment creation"
retry_command "source $VENV_PATH/bin/activate && pip install --upgrade pip" "Virtual environment pip upgrade"

# 📦 Pre-instalar paquetes Python comunes
log_info "📦 Pre-installing common Python packages..."
PYTHON_PACKAGES=(
    "azure-ai-foundry"
    "azure-openai"
    "azure-search-documents"
    "azure-cosmos"
    "azure-keyvault-secrets"
    "azure-storage-blob"
    "azure-cognitiveservices-speech"
    "semantic-kernel"
    "pandas"
    "numpy"
    "requests"
    "python-dotenv" 
    "scikit-learn"
    "matplotlib"
    "seaborn"
    "jupyter"
    "pytest"
    "pytest-asyncio"
    "black"
    "flake8"
    "fastapi"
    "uvicorn"
)

# Instalar paquetes en el venv
for package in "${PYTHON_PACKAGES[@]}"; do
    log_info "Installing Python package: $package"
    source $VENV_PATH/bin/activate && pip install "$package" 2>/dev/null || log_warning "Failed to install package: $package"
done

# 🔧 Configurar Git
log_info "🔧 Configuring Git (will prompt for user info)..."
echo ""
echo -e "${YELLOW}Please enter your Git configuration:${NC}"
read -p "Git Username: " git_username
read -p "Git Email: " git_email

if [[ -n "$git_username" && -n "$git_email" ]]; then
    git config --global user.name "$git_username"
    git config --global user.email "$git_email"
    git config --global init.defaultBranch main
    git config --global pull.rebase false
    log_success "Git configured successfully"
else
    log_warning "Git configuration skipped - you can configure it later with 'git config --global user.name' and 'git config --global user.email'"
fi

# 📁 Crear estructura de directorios
log_info "📁 Creating development directories..."
DEV_DIRS=(
    "/home/$USER/Development"
    "/home/$USER/Development/CreditGuard" 
    "/home/$USER/Development/Notebooks"
    "/home/$USER/Development/Scripts"
    "/home/$USER/.jupyter"
)

for dir in "${DEV_DIRS[@]}"; do
    mkdir -p "$dir"
    log_success "Created directory: $dir"
done

# 📝 Configurar Jupyter 
log_info "📝 Configuring Jupyter..."
cat > /home/$USER/.jupyter/jupyter_notebook_config.py << 'EOF'
# 🏦 CreditGuard AI Assistant - Jupyter Configuration
# 👨‍💼 Steven Uba - Azure Digital Solution Engineer - Data and AI

c = get_config()

# Network configuration
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
c.NotebookApp.allow_remote_access = True

# Security
c.NotebookApp.token = ''
c.NotebookApp.password = ''
c.NotebookApp.allow_origin = '*'
c.NotebookApp.disable_check_xsrf = True

# Directory
c.NotebookApp.notebook_dir = '/home/USER_PLACEHOLDER/Development'

# Extensions
c.NotebookApp.nbserver_extensions = {
    'jupyter_contrib_nbextensions': True
}
EOF

# Reemplazar placeholder con usuario actual
sed -i "s/USER_PLACEHOLDER/$USER/g" /home/$USER/.jupyter/jupyter_notebook_config.py

# 🔧 Crear script de activación del ambiente
log_info "🔧 Creating environment activation script..."
cat > /home/$USER/activate-creditguard.sh << EOF
#!/bin/bash
# 🏦 CreditGuard AI Assistant - Environment Activation
# 👨‍💼 Steven Uba - Azure Digital Solution Engineer - Data and AI

echo "🏦 Activating CreditGuard AI Assistant Development Environment..."
echo "👨‍💼 Instructor: Steven Uba"
echo ""

# Activar virtual environment
source $VENV_PATH/bin/activate
echo "✅ Python virtual environment activated"

# Cambiar al directorio de desarrollo
cd /home/$USER/Development/CreditGuard
echo "📁 Changed to development directory"

# Mostrar información del ambiente
echo ""
echo "🔧 Environment Information:"
echo "   🐍 Python: \$(python --version)"
echo "   📦 Pip: \$(pip --version)"
echo "   📁 Working Directory: \$(pwd)"
echo "   🌐 Virtual Environment: $VENV_PATH"
echo ""
echo "🚀 Ready for CreditGuard AI Assistant development!"
echo ""
echo "💡 Useful commands:"
echo "   - Start Jupyter: jupyter lab"
echo "   - Install package: pip install <package>"
echo "   - Deactivate: deactivate"
echo ""
EOF

chmod +x /home/$USER/activate-creditguard.sh

# 📋 Crear script de información del sistema
log_info "📋 Creating system info script..."
cat > /home/$USER/system-info.sh << 'EOF'
#!/bin/bash
# 🏦 CreditGuard AI Assistant - System Information
# 👨‍💼 Steven Uba - Azure Digital Solution Engineer - Data and AI

echo "🏦 CreditGuard AI Assistant - System Information"
echo "=============================================="
echo ""
echo "🖥️  System Information:"
echo "   OS: $(lsb_release -d | cut -f2)"
echo "   Kernel: $(uname -r)"
echo "   Architecture: $(uname -m)"
echo "   Memory: $(free -h | awk '/^Mem:/ {print $2}') total"
echo "   Storage: $(df -h / | awk 'NR==2 {print $2}') total, $(df -h / | awk 'NR==2 {print $4}') available"
echo ""
echo "🐍 Python Environment:"
echo "   System Python: $(python3 --version)"
echo "   Virtual Environment: $VENV_PATH"
echo ""
echo "☁️  Azure Tools:"
echo "   Azure CLI: $(az --version | head -1)"
echo ""
echo "💻 Development Tools:"
echo "   VS Code: $(code --version | head -1)"
echo "   Git: $(git --version)"
echo "   Docker: $(docker --version)"
echo "   Node.js: $(node --version)"
echo "   NPM: $(npm --version)"
echo ""
echo "🔧 Useful Paths:"
echo "   Home: $HOME"
echo "   Development: $HOME/Development"
echo "   Virtual Environment: $VENV_PATH"
echo "   Jupyter Config: $HOME/.jupyter"
echo ""
echo "🚀 Ready for Azure AI development!"
EOF

chmod +x /home/$USER/system-info.sh

# 🔄 Configurar bashrc
log_info "🔄 Configuring shell environment..."
cat >> /home/$USER/.bashrc << 'EOF'

# 🏦 CreditGuard AI Assistant - Shell Configuration
# 👨‍💼 Steven Uba - Azure Digital Solution Engineer - Data and AI

# Aliases útiles
alias ll='ls -alF'
alias la='ls -A' 
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias creditguard='source ~/activate-creditguard.sh'
alias sysinfo='~/system-info.sh'
alias lab='cd ~/Development && jupyter lab --no-browser --port=8888 --ip=0.0.0.0'

# Environment variables
export EDITOR=nano
export BROWSER=none
export PYTHONPATH="$PYTHONPATH:$HOME/Development"

# Welcome message
echo "🏦 Welcome to CreditGuard AI Assistant Development Environment!"
echo "💡 Type 'creditguard' to activate the development environment"
echo "📊 Type 'sysinfo' to see system information"
echo "🚀 Type 'lab' to start Jupyter Lab"
EOF

# 🎯 Configurar firewall para Jupyter
log_info "🛡️ Configuring firewall for Jupyter..."
sudo ufw allow 8888 2>/dev/null || log_warning "Could not configure firewall - you may need to open port 8888 manually"

# 🧹 Limpiar archivos temporales
log_info "🧹 Cleaning up temporary files..."
rm -f packages.microsoft.gpg 2>/dev/null || true
sudo apt autoremove -y 2>/dev/null || true
sudo apt autoclean 2>/dev/null || true

# ✅ Resumen final
log_success "🎉 VM Setup completed successfully!"
echo ""
echo -e "${CYAN}📋 Installation Summary:${NC}"
echo "   ✅ System updated and dependencies installed"
echo "   ✅ Python 3.9 with virtual environment configured" 
echo "   ✅ Azure CLI installed and ready"
echo "   ✅ VS Code with Azure extensions installed"
echo "   ✅ Docker installed and configured"
echo "   ✅ Jupyter Lab configured for remote access"
echo "   ✅ Development directories created"
echo "   ✅ Shell environment configured"
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo "1. 🔄 Restart your shell: source ~/.bashrc"
echo "2. 🏦 Activate environment: creditguard"
echo "3. 📊 Check system info: sysinfo" 
echo "4. 📝 Start Jupyter: lab"
echo "5. 🌐 Access Jupyter at: http://YOUR_VM_IP:8888"
echo ""
echo -e "${GREEN}💡 Quick Commands:${NC}"
echo "   creditguard  - Activate development environment"
echo "   sysinfo      - Show system information"
echo "   lab          - Start Jupyter Lab"
echo ""
echo -e "${CYAN}📧 Support: Steven Uba - Azure Digital Solution Engineer${NC}"
echo -e "${CYAN}📖 Documentation: creditguard-ai-assistant/SETUP-GUIDE.md${NC}"
echo ""
echo -e "${GREEN}🎯 Your CreditGuard AI Assistant development environment is ready!${NC}"

# 🔄 Recordar al usuario que reinicie la shell
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Please run 'source ~/.bashrc' or restart your terminal to apply all changes.${NC}"
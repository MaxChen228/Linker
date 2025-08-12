#!/bin/bash

# CSS Testing Setup Script
# Sets up the complete automated testing environment for CSS changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Check requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Node.js
    if ! command -v node > /dev/null 2>&1; then
        log_error "Node.js is required but not installed"
        echo "Please install Node.js from https://nodejs.org/"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        log_error "Node.js version 16+ is required (current: $(node --version))"
        exit 1
    fi
    
    log_success "Node.js $(node --version) ✓"
    
    # Check npm
    if ! command -v npm > /dev/null 2>&1; then
        log_error "npm is required but not installed"
        exit 1
    fi
    
    log_success "npm $(npm --version) ✓"
    
    # Check Python (for the web server)
    if ! command -v python3 > /dev/null 2>&1 && ! command -v python > /dev/null 2>&1; then
        log_warning "Python not found - may need manual server setup"
    else
        log_success "Python available ✓"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing Node.js dependencies..."
    
    if npm install; then
        log_success "Dependencies installed successfully"
    else
        log_error "Failed to install dependencies"
        exit 1
    fi
    
    # Install Playwright browsers
    log_info "Installing Playwright browsers..."
    
    if npx playwright install; then
        log_success "Playwright browsers installed"
    else
        log_warning "Playwright browser installation failed - may need manual setup"
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating required directories..."
    
    DIRECTORIES=(
        "css-backups"
        "test-reports"
        "tests/visual/screenshots"
        "tests/visual/reports"
        "tests/visual/test-results"
    )
    
    for dir in "${DIRECTORIES[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
    
    log_success "All directories created"
}

# Set up git hooks (if in git repo)
setup_git_hooks() {
    if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        log_info "Setting up git hooks..."
        
        # Create pre-commit hook for CSS validation
        HOOK_FILE=".husky/pre-commit"
        
        if [ ! -f "$HOOK_FILE" ]; then
            cat > "$HOOK_FILE" << 'EOF'
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

# Run CSS validation before commit
if git diff --cached --name-only | grep -E '\.(css)$' > /dev/null; then
  echo "🎨 CSS changes detected, running validation..."
  npm run lint:css:check
fi
EOF
            chmod +x "$HOOK_FILE"
            log_success "Git pre-commit hook created"
        else
            log_info "Git hook already exists"
        fi
    else
        log_info "Not in a git repository - skipping git hooks"
    fi
}

# Validate setup
validate_setup() {
    log_info "Validating setup..."
    
    # Check if scripts are executable
    SCRIPTS=(
        "scripts/test-css-changes.sh"
        "scripts/quick-rollback.sh"
        "scripts/css-performance-monitor.js"
    )
    
    for script in "${SCRIPTS[@]}"; do
        if [ ! -x "$script" ]; then
            log_warning "Making $script executable..."
            chmod +x "$script"
        fi
    done
    
    # Test stylelint
    if npm run lint:css:check > /dev/null 2>&1; then
        log_success "Stylelint validation working ✓"
    else
        log_warning "Stylelint validation has issues (check CSS files)"
    fi
    
    # Test performance monitor
    if node scripts/css-performance-monitor.js > /dev/null 2>&1; then
        log_success "Performance monitoring working ✓"
    else
        log_warning "Performance monitor has issues"
    fi
    
    # Check if server can start
    if command -v uvicorn > /dev/null 2>&1; then
        log_success "FastAPI server available ✓"
    elif command -v python3 > /dev/null 2>&1; then
        log_warning "uvicorn not found - install with: pip install uvicorn"
    else
        log_warning "Python server setup may be needed"
    fi
}

# Generate initial baseline
generate_baseline() {
    log_info "Generating initial test baseline..."
    
    # Create initial backup
    if ./scripts/test-css-changes.sh --backup; then
        log_success "Initial backup created"
    else
        log_warning "Could not create initial backup"
    fi
    
    # Ask if user wants to generate visual baselines
    echo ""
    echo "🎯 Do you want to generate initial visual test baselines?"
    echo "   This will start the server and capture reference screenshots."
    echo "   (y/N)"
    read -r generate_baselines
    
    if [ "$generate_baselines" = "y" ] || [ "$generate_baselines" = "Y" ] || [ "$generate_baselines" = "yes" ]; then
        log_info "Starting server and generating baselines..."
        
        # Check if server is already running
        if curl -s http://localhost:8000 > /dev/null 2>&1; then
            log_info "Server is already running"
        else
            log_info "Starting development server..."
            uvicorn web.main:app --host 127.0.0.1 --port 8000 > test-reports/setup-server.log 2>&1 &
            SERVER_PID=$!
            
            # Wait for server to start
            for i in {1..30}; do
                if curl -s http://localhost:8000 > /dev/null 2>&1; then
                    log_success "Server started"
                    break
                fi
                sleep 1
            done
        fi
        
        # Generate baselines
        if npm run test:visual:update > test-reports/setup-baselines.log 2>&1; then
            log_success "Visual baselines generated"
        else
            log_error "Failed to generate baselines - check test-reports/setup-baselines.log"
        fi
        
        # Stop server if we started it
        if [ -n "$SERVER_PID" ]; then
            kill $SERVER_PID 2>/dev/null || true
            log_info "Development server stopped"
        fi
    else
        log_info "Skipping baseline generation - you can run 'npm run test:visual:update' later"
    fi
}

# Show completion message
show_completion() {
    echo ""
    echo "🎉 CSS Testing Environment Setup Complete!"
    echo "=========================================="
    echo ""
    echo "📚 Quick Start Guide:"
    echo ""
    echo "1. Run full test suite:"
    echo "   npm run test:css"
    echo ""
    echo "2. Run specific tests:"
    echo "   npm run test:css:validate    # CSS validation only"
    echo "   npm run test:css:visual      # Visual regression only"
    echo "   npm run test:css:performance # Performance analysis"
    echo ""
    echo "3. Visual testing:"
    echo "   npm run test:visual          # Run visual tests"
    echo "   npm run test:visual:update   # Update baselines"
    echo "   npm run test:visual:report   # View test report"
    echo ""
    echo "4. Rollback procedures:"
    echo "   npm run css:rollback:quick   # Quick rollback"
    echo "   npm run css:rollback:list    # List backups"
    echo ""
    echo "📖 Documentation:"
    echo "   tests/visual/README.md       # Complete testing guide"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   ./scripts/test-css-changes.sh --help"
    echo "   ./scripts/quick-rollback.sh --help"
    echo ""
    
    if [ -f "test-reports/setup-server.log" ]; then
        echo "📄 Setup logs available in test-reports/"
    fi
}

# Main execution
main() {
    echo "🚀 CSS Testing Environment Setup"
    echo "================================="
    echo ""
    
    check_requirements
    echo ""
    
    install_dependencies
    echo ""
    
    create_directories
    echo ""
    
    setup_git_hooks
    echo ""
    
    validate_setup
    echo ""
    
    generate_baseline
    echo ""
    
    show_completion
}

# Handle interruption
trap 'echo -e "\n${YELLOW}Setup interrupted${NC}"; exit 1' INT

# Run main function
main "$@"
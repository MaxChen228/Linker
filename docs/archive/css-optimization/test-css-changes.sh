#!/bin/bash

# CSS Testing Automation Script
# Comprehensive script to validate CSS changes quickly and catch visual regressions

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CSS_DIR="web/static/css"
BACKUP_DIR="css-backups"
REPORTS_DIR="test-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

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

# Create required directories
create_directories() {
    log_info "Creating required directories..."
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$REPORTS_DIR"
    mkdir -p "tests/visual/screenshots"
    mkdir -p "tests/visual/reports"
}

# Backup current CSS files
backup_css() {
    log_info "Backing up CSS files..."
    BACKUP_PATH="$BACKUP_DIR/css_backup_$TIMESTAMP"
    cp -r "$CSS_DIR" "$BACKUP_PATH"
    echo "$BACKUP_PATH" > "$BACKUP_DIR/latest_backup.txt"
    log_success "CSS backed up to $BACKUP_PATH"
}

# Restore CSS from backup
restore_css() {
    if [ ! -f "$BACKUP_DIR/latest_backup.txt" ]; then
        log_error "No backup found to restore from"
        exit 1
    fi
    
    LATEST_BACKUP=$(cat "$BACKUP_DIR/latest_backup.txt")
    if [ ! -d "$LATEST_BACKUP" ]; then
        log_error "Backup directory $LATEST_BACKUP not found"
        exit 1
    fi
    
    log_info "Restoring CSS from $LATEST_BACKUP..."
    rm -rf "$CSS_DIR"
    cp -r "$LATEST_BACKUP" "$CSS_DIR"
    log_success "CSS restored from backup"
}

# Run stylelint validation
run_stylelint() {
    log_info "Running stylelint validation..."
    
    if npm run lint:css:check > "$REPORTS_DIR/stylelint_$TIMESTAMP.log" 2>&1; then
        log_success "Stylelint validation passed"
        return 0
    else
        log_error "Stylelint validation failed"
        echo "Check $REPORTS_DIR/stylelint_$TIMESTAMP.log for details"
        return 1
    fi
}

# Run CSS performance analysis
run_performance_analysis() {
    log_info "Running CSS performance analysis..."
    
    if node scripts/css-performance-monitor.js > "$REPORTS_DIR/performance_$TIMESTAMP.log" 2>&1; then
        log_success "Performance analysis completed"
        # Copy the generated JSON report to our reports directory
        if [ -f "css-performance-report.json" ]; then
            mv "css-performance-report.json" "$REPORTS_DIR/performance_$TIMESTAMP.json"
        fi
        return 0
    else
        log_error "Performance analysis failed"
        echo "Check $REPORTS_DIR/performance_$TIMESTAMP.log for details"
        return 1
    fi
}

# Check if server is running
check_server() {
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Start development server if not running
start_server() {
    if check_server; then
        log_info "Development server is already running"
        return 0
    fi
    
    log_info "Starting development server..."
    uvicorn web.main:app --host 127.0.0.1 --port 8000 > "$REPORTS_DIR/server_$TIMESTAMP.log" 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    for i in {1..30}; do
        if check_server; then
            log_success "Development server started (PID: $SERVER_PID)"
            echo $SERVER_PID > "$REPORTS_DIR/server.pid"
            return 0
        fi
        sleep 1
    done
    
    log_error "Failed to start development server"
    return 1
}

# Stop development server
stop_server() {
    if [ -f "$REPORTS_DIR/server.pid" ]; then
        SERVER_PID=$(cat "$REPORTS_DIR/server.pid")
        if kill -0 $SERVER_PID 2>/dev/null; then
            log_info "Stopping development server (PID: $SERVER_PID)"
            kill $SERVER_PID
            rm "$REPORTS_DIR/server.pid"
            log_success "Development server stopped"
        fi
    fi
}

# Run visual regression tests
run_visual_tests() {
    log_info "Running visual regression tests..."
    
    if ! check_server; then
        log_error "Development server is not running"
        return 1
    fi
    
    # Run Playwright tests
    if npx playwright test --config=tests/visual/playwright.config.js > "$REPORTS_DIR/visual_$TIMESTAMP.log" 2>&1; then
        log_success "Visual regression tests passed"
        return 0
    else
        log_error "Visual regression tests failed"
        echo "Check $REPORTS_DIR/visual_$TIMESTAMP.log for details"
        echo "View detailed report: npx playwright show-report tests/visual/reports"
        return 1
    fi
}

# Run CSS validation tests
run_css_validation() {
    log_info "Running CSS validation tests..."
    
    if ! check_server; then
        log_error "Development server is not running"
        return 1
    fi
    
    # Run CSS-specific Playwright tests
    if npx playwright test tests/visual/css-validation.spec.js --config=tests/visual/playwright.config.js > "$REPORTS_DIR/css_validation_$TIMESTAMP.log" 2>&1; then
        log_success "CSS validation tests passed"
        return 0
    else
        log_error "CSS validation tests failed"
        echo "Check $REPORTS_DIR/css_validation_$TIMESTAMP.log for details"
        return 1
    fi
}

# Generate comprehensive report
generate_report() {
    log_info "Generating comprehensive test report..."
    
    REPORT_FILE="$REPORTS_DIR/test_summary_$TIMESTAMP.md"
    
    cat > "$REPORT_FILE" << EOF
# CSS Testing Report - $(date)

## Test Summary

### Configuration
- CSS Directory: $CSS_DIR
- Backup Directory: $BACKUP_DIR
- Test Timestamp: $TIMESTAMP

### Test Results

EOF

    # Add stylelint results
    if [ -f "$REPORTS_DIR/stylelint_$TIMESTAMP.log" ]; then
        echo "#### Stylelint Validation" >> "$REPORT_FILE"
        if grep -q "error" "$REPORTS_DIR/stylelint_$TIMESTAMP.log"; then
            echo "❌ **FAILED** - Stylelint validation found errors" >> "$REPORT_FILE"
        else
            echo "✅ **PASSED** - No stylelint errors found" >> "$REPORT_FILE"
        fi
        echo "" >> "$REPORT_FILE"
    fi

    # Add performance results
    if [ -f "$REPORTS_DIR/performance_$TIMESTAMP.json" ]; then
        echo "#### Performance Analysis" >> "$REPORT_FILE"
        echo "✅ **COMPLETED** - See performance_$TIMESTAMP.json for details" >> "$REPORT_FILE"
        
        # Extract key metrics if possible
        if command -v jq > /dev/null 2>&1; then
            TOTAL_SIZE=$(jq -r '.metrics.totalSizeKB' "$REPORTS_DIR/performance_$TIMESTAMP.json" 2>/dev/null || echo "N/A")
            TOTAL_FILES=$(jq -r '.totalFiles' "$REPORTS_DIR/performance_$TIMESTAMP.json" 2>/dev/null || echo "N/A")
            echo "- Total CSS size: ${TOTAL_SIZE}KB" >> "$REPORT_FILE"
            echo "- Total files: $TOTAL_FILES" >> "$REPORT_FILE"
        fi
        echo "" >> "$REPORT_FILE"
    fi

    # Add visual test results
    if [ -f "$REPORTS_DIR/visual_$TIMESTAMP.log" ]; then
        echo "#### Visual Regression Tests" >> "$REPORT_FILE"
        if grep -q "failed" "$REPORTS_DIR/visual_$TIMESTAMP.log"; then
            echo "❌ **FAILED** - Visual regression tests found differences" >> "$REPORT_FILE"
        else
            echo "✅ **PASSED** - No visual regressions detected" >> "$REPORT_FILE"
        fi
        echo "" >> "$REPORT_FILE"
    fi

    # Add quick actions
    cat >> "$REPORT_FILE" << EOF
### Quick Actions

#### View Detailed Reports
\`\`\`bash
# View visual test report
npx playwright show-report tests/visual/reports

# View performance report
cat $REPORTS_DIR/performance_$TIMESTAMP.json

# View stylelint report
cat $REPORTS_DIR/stylelint_$TIMESTAMP.log
\`\`\`

#### Rollback if Needed
\`\`\`bash
# Restore CSS from backup
./scripts/test-css-changes.sh --restore
\`\`\`

#### Re-run Tests
\`\`\`bash
# Run full test suite
./scripts/test-css-changes.sh --full

# Run only validation
./scripts/test-css-changes.sh --validate

# Run only visual tests
./scripts/test-css-changes.sh --visual
\`\`\`

---
Generated on $(date)
EOF

    log_success "Test report generated: $REPORT_FILE"
    echo "View report: cat $REPORT_FILE"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "CSS Testing Automation Script"
    echo ""
    echo "Options:"
    echo "  --help, -h         Show this help message"
    echo "  --full             Run full test suite (default)"
    echo "  --validate         Run validation tests only (stylelint + CSS validation)"
    echo "  --visual           Run visual regression tests only"
    echo "  --performance      Run performance analysis only"
    echo "  --backup           Create CSS backup only"
    echo "  --restore          Restore CSS from latest backup"
    echo "  --start-server     Start development server only"
    echo "  --stop-server      Stop development server only"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run full test suite"
    echo "  $0 --validate      # Run validation tests only"
    echo "  $0 --visual        # Run visual tests only"
    echo "  $0 --restore       # Restore from backup"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    # Note: We don't auto-stop the server in case user wants to debug
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution
main() {
    local option="${1:-full}"
    
    case "$option" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --restore)
            restore_css
            exit 0
            ;;
        --backup)
            create_directories
            backup_css
            exit 0
            ;;
        --start-server)
            create_directories
            start_server
            exit 0
            ;;
        --stop-server)
            stop_server
            exit 0
            ;;
        --validate)
            create_directories
            backup_css
            run_stylelint
            start_server
            run_css_validation
            generate_report
            ;;
        --visual)
            create_directories
            start_server
            run_visual_tests
            generate_report
            ;;
        --performance)
            create_directories
            run_performance_analysis
            generate_report
            ;;
        --full|*)
            log_info "Running full CSS test suite..."
            create_directories
            backup_css
            
            # Run validation tests
            STYLELINT_PASSED=true
            if ! run_stylelint; then
                STYLELINT_PASSED=false
                log_warning "Continuing despite stylelint errors..."
            fi
            
            # Run performance analysis
            run_performance_analysis
            
            # Start server and run browser tests
            start_server
            
            VISUAL_PASSED=true
            if ! run_visual_tests; then
                VISUAL_PASSED=false
                log_warning "Visual tests failed"
            fi
            
            CSS_VALIDATION_PASSED=true
            if ! run_css_validation; then
                CSS_VALIDATION_PASSED=false
                log_warning "CSS validation tests failed"
            fi
            
            # Generate report
            generate_report
            
            # Show summary
            echo ""
            log_info "=== TEST SUMMARY ==="
            [ "$STYLELINT_PASSED" = true ] && log_success "✅ Stylelint validation" || log_error "❌ Stylelint validation"
            log_success "✅ Performance analysis"
            [ "$VISUAL_PASSED" = true ] && log_success "✅ Visual regression tests" || log_error "❌ Visual regression tests"
            [ "$CSS_VALIDATION_PASSED" = true ] && log_success "✅ CSS validation tests" || log_error "❌ CSS validation tests"
            
            if [ "$STYLELINT_PASSED" = true ] && [ "$VISUAL_PASSED" = true ] && [ "$CSS_VALIDATION_PASSED" = true ]; then
                log_success "🎉 All tests passed!"
                exit 0
            else
                log_warning "⚠️  Some tests failed. Check reports for details."
                echo "Backup available for rollback if needed: $(cat $BACKUP_DIR/latest_backup.txt 2>/dev/null || echo 'N/A')"
                exit 1
            fi
            ;;
    esac
}

# Run main function with all arguments
main "$@"
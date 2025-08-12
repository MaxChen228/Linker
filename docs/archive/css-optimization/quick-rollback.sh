#!/bin/bash

# Quick CSS Rollback Script
# Provides fast rollback procedures for CSS changes with safety checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CSS_DIR="web/static/css"
BACKUP_DIR="css-backups"
ROLLBACK_LOG="$BACKUP_DIR/rollback.log"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$ROLLBACK_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" >> "$ROLLBACK_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$ROLLBACK_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$ROLLBACK_LOG"
}

# Ensure backup directory exists
ensure_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi
}

# List available backups
list_backups() {
    ensure_backup_dir
    
    log_info "Available backups:"
    echo ""
    
    if [ ! "$(ls -A $BACKUP_DIR/css_backup_* 2>/dev/null)" ]; then
        log_warning "No backups found in $BACKUP_DIR"
        return 1
    fi
    
    # List backups with details
    for backup in "$BACKUP_DIR"/css_backup_*; do
        if [ -d "$backup" ]; then
            BACKUP_NAME=$(basename "$backup")
            BACKUP_DATE=$(echo "$BACKUP_NAME" | sed 's/css_backup_//' | sed 's/_/ /' | sed 's/\(.\{4\}\)\(.\{2\}\)\(.\{2\}\) \(.\{2\}\)\(.\{2\}\)\(.\{2\}\)/\1-\2-\3 \4:\5:\6/')
            BACKUP_SIZE=$(du -sh "$backup" | cut -f1)
            BACKUP_FILES=$(find "$backup" -name "*.css" | wc -l | tr -d ' ')
            
            echo "  📁 $BACKUP_NAME"
            echo "     Date: $BACKUP_DATE"
            echo "     Size: $BACKUP_SIZE"
            echo "     Files: $BACKUP_FILES CSS files"
            echo ""
        fi
    done
    
    # Show latest backup
    if [ -f "$BACKUP_DIR/latest_backup.txt" ]; then
        LATEST=$(cat "$BACKUP_DIR/latest_backup.txt")
        echo "🔄 Latest backup: $(basename "$LATEST")"
    fi
}

# Show current CSS status
show_current_status() {
    log_info "Current CSS status:"
    
    if [ ! -d "$CSS_DIR" ]; then
        log_error "CSS directory not found: $CSS_DIR"
        return 1
    fi
    
    CSS_SIZE=$(du -sh "$CSS_DIR" | cut -f1)
    CSS_FILES=$(find "$CSS_DIR" -name "*.css" | wc -l | tr -d ' ')
    LAST_MODIFIED=$(find "$CSS_DIR" -name "*.css" -exec stat -f "%m %N" {} \; | sort -n | tail -1 | cut -d' ' -f2- | xargs stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S")
    
    echo "  📁 Directory: $CSS_DIR"
    echo "  📊 Size: $CSS_SIZE"
    echo "  📝 Files: $CSS_FILES CSS files"
    echo "  🕒 Last modified: $LAST_MODIFIED"
    echo ""
}

# Create emergency backup before rollback
create_emergency_backup() {
    log_info "Creating emergency backup before rollback..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    EMERGENCY_BACKUP="$BACKUP_DIR/emergency_before_rollback_$TIMESTAMP"
    
    cp -r "$CSS_DIR" "$EMERGENCY_BACKUP"
    echo "$EMERGENCY_BACKUP" > "$BACKUP_DIR/emergency_backup.txt"
    
    log_success "Emergency backup created: $EMERGENCY_BACKUP"
}

# Validate backup before rollback
validate_backup() {
    local backup_path="$1"
    
    if [ ! -d "$backup_path" ]; then
        log_error "Backup directory not found: $backup_path"
        return 1
    fi
    
    # Check if backup has CSS files
    CSS_COUNT=$(find "$backup_path" -name "*.css" | wc -l | tr -d ' ')
    if [ "$CSS_COUNT" -eq 0 ]; then
        log_error "No CSS files found in backup: $backup_path"
        return 1
    fi
    
    # Check backup integrity (basic check)
    for css_file in "$backup_path"/*.css; do
        if [ -f "$css_file" ]; then
            if ! head -1 "$css_file" > /dev/null 2>&1; then
                log_error "Corrupted file detected: $css_file"
                return 1
            fi
        fi
    done
    
    log_success "Backup validation passed: $CSS_COUNT CSS files found"
    return 0
}

# Perform rollback
perform_rollback() {
    local backup_path="$1"
    local skip_backup="${2:-false}"
    
    log_info "Starting rollback to: $(basename "$backup_path")"
    
    # Validate backup first
    if ! validate_backup "$backup_path"; then
        log_error "Backup validation failed. Aborting rollback."
        return 1
    fi
    
    # Create emergency backup unless skipped
    if [ "$skip_backup" != "true" ]; then
        create_emergency_backup
    fi
    
    # Remove current CSS directory
    log_info "Removing current CSS files..."
    rm -rf "$CSS_DIR"
    
    # Restore from backup
    log_info "Restoring CSS from backup..."
    cp -r "$backup_path" "$CSS_DIR"
    
    # Update latest backup pointer
    echo "$backup_path" > "$BACKUP_DIR/latest_backup.txt"
    
    log_success "Rollback completed successfully!"
    
    # Show post-rollback status
    echo ""
    show_current_status
}

# Quick rollback to latest backup
quick_rollback() {
    if [ ! -f "$BACKUP_DIR/latest_backup.txt" ]; then
        log_error "No latest backup reference found"
        echo "Available backups:"
        list_backups
        return 1
    fi
    
    LATEST_BACKUP=$(cat "$BACKUP_DIR/latest_backup.txt")
    
    if [ ! -d "$LATEST_BACKUP" ]; then
        log_error "Latest backup directory not found: $LATEST_BACKUP"
        return 1
    fi
    
    echo "🔄 Rolling back to latest backup: $(basename "$LATEST_BACKUP")"
    echo ""
    
    perform_rollback "$LATEST_BACKUP"
}

# Interactive rollback selection
interactive_rollback() {
    list_backups
    
    echo ""
    echo "Enter the backup name to rollback to (or 'q' to quit):"
    read -r backup_choice
    
    if [ "$backup_choice" = "q" ] || [ "$backup_choice" = "quit" ]; then
        log_info "Rollback cancelled"
        return 0
    fi
    
    BACKUP_PATH="$BACKUP_DIR/$backup_choice"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        # Try with css_backup_ prefix
        BACKUP_PATH="$BACKUP_DIR/css_backup_$backup_choice"
        if [ ! -d "$BACKUP_PATH" ]; then
            log_error "Backup not found: $backup_choice"
            return 1
        fi
    fi
    
    echo ""
    echo "⚠️  This will replace all current CSS files with the backup."
    echo "Backup to restore: $(basename "$BACKUP_PATH")"
    echo ""
    echo "Continue? (y/N)"
    read -r confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ] || [ "$confirm" = "yes" ]; then
        perform_rollback "$BACKUP_PATH"
    else
        log_info "Rollback cancelled"
    fi
}

# Compare current state with backup
compare_with_backup() {
    local backup_path="$1"
    
    if [ ! -d "$backup_path" ]; then
        log_error "Backup directory not found: $backup_path"
        return 1
    fi
    
    log_info "Comparing current CSS with backup: $(basename "$backup_path")"
    echo ""
    
    # Use diff to compare directories
    if command -v diff > /dev/null 2>&1; then
        diff -r "$backup_path" "$CSS_DIR" || true
    else
        log_warning "diff command not available. Manual comparison needed."
    fi
}

# Rollback specific files only
partial_rollback() {
    local backup_path="$1"
    shift
    local files=("$@")
    
    if [ ! -d "$backup_path" ]; then
        log_error "Backup directory not found: $backup_path"
        return 1
    fi
    
    if [ ${#files[@]} -eq 0 ]; then
        log_error "No files specified for partial rollback"
        return 1
    fi
    
    log_info "Performing partial rollback from: $(basename "$backup_path")"
    
    # Create emergency backup of current state
    create_emergency_backup
    
    for file in "${files[@]}"; do
        BACKUP_FILE="$backup_path/$file"
        TARGET_FILE="$CSS_DIR/$file"
        
        if [ -f "$BACKUP_FILE" ]; then
            log_info "Restoring: $file"
            cp "$BACKUP_FILE" "$TARGET_FILE"
        else
            log_warning "File not found in backup: $file"
        fi
    done
    
    log_success "Partial rollback completed"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTION] [PARAMETERS]"
    echo ""
    echo "Quick CSS Rollback Script"
    echo ""
    echo "Options:"
    echo "  --help, -h              Show this help message"
    echo "  --list, -l              List available backups"
    echo "  --status, -s            Show current CSS status"
    echo "  --quick, -q             Quick rollback to latest backup"
    echo "  --interactive, -i       Interactive backup selection"
    echo "  --rollback BACKUP       Rollback to specific backup"
    echo "  --compare BACKUP        Compare current state with backup"
    echo "  --partial BACKUP FILES  Rollback specific files only"
    echo "  --emergency             Show emergency recovery options"
    echo ""
    echo "Examples:"
    echo "  $0 --list                                    # List all backups"
    echo "  $0 --quick                                   # Quick rollback to latest"
    echo "  $0 --rollback css_backup_20241201_143022     # Rollback to specific backup"
    echo "  $0 --partial css_backup_20241201_143022 styles.css components.css"
    echo "  $0 --compare css_backup_20241201_143022      # Compare with backup"
}

# Emergency recovery options
show_emergency_options() {
    echo "🚨 Emergency Recovery Options"
    echo "============================="
    echo ""
    
    # Check for emergency backup
    if [ -f "$BACKUP_DIR/emergency_backup.txt" ]; then
        EMERGENCY_BACKUP=$(cat "$BACKUP_DIR/emergency_backup.txt")
        if [ -d "$EMERGENCY_BACKUP" ]; then
            echo "🔄 Emergency backup available:"
            echo "   $EMERGENCY_BACKUP"
            echo "   Restore with: $0 --rollback $(basename "$EMERGENCY_BACKUP")"
            echo ""
        fi
    fi
    
    # Show git options if available
    if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        echo "📚 Git recovery options:"
        echo "   git checkout HEAD -- $CSS_DIR    # Restore from git"
        echo "   git stash                         # Stash current changes"
        echo "   git reset --hard HEAD             # Hard reset (DESTRUCTIVE)"
        echo ""
    fi
    
    # Show manual backup options
    echo "📁 Manual backup locations to check:"
    echo "   $BACKUP_DIR/                      # Script backups"
    echo "   ~/.trash/                         # Trash (macOS)"
    echo "   /tmp/                            # Temporary files"
    echo ""
    
    echo "🛠️  Manual recovery steps:"
    echo "   1. Check if CSS files exist in any backup location"
    echo "   2. Verify file integrity before restoring"
    echo "   3. Test CSS after restoration"
    echo "   4. Consider running validation: ./scripts/test-css-changes.sh --validate"
}

# Main execution
main() {
    ensure_backup_dir
    
    case "${1:-help}" in
        --help|-h|help)
            show_usage
            ;;
        --list|-l)
            list_backups
            ;;
        --status|-s)
            show_current_status
            ;;
        --quick|-q)
            quick_rollback
            ;;
        --interactive|-i)
            interactive_rollback
            ;;
        --rollback)
            if [ -z "$2" ]; then
                log_error "Backup name required for rollback"
                echo "Use --list to see available backups"
                exit 1
            fi
            
            BACKUP_PATH="$BACKUP_DIR/$2"
            if [ ! -d "$BACKUP_PATH" ]; then
                # Try with css_backup_ prefix
                BACKUP_PATH="$BACKUP_DIR/css_backup_$2"
            fi
            
            perform_rollback "$BACKUP_PATH"
            ;;
        --compare)
            if [ -z "$2" ]; then
                log_error "Backup name required for comparison"
                exit 1
            fi
            
            BACKUP_PATH="$BACKUP_DIR/$2"
            if [ ! -d "$BACKUP_PATH" ]; then
                BACKUP_PATH="$BACKUP_DIR/css_backup_$2"
            fi
            
            compare_with_backup "$BACKUP_PATH"
            ;;
        --partial)
            if [ -z "$2" ]; then
                log_error "Backup name required for partial rollback"
                exit 1
            fi
            
            BACKUP_PATH="$BACKUP_DIR/$2"
            if [ ! -d "$BACKUP_PATH" ]; then
                BACKUP_PATH="$BACKUP_DIR/css_backup_$2"
            fi
            
            shift 2  # Remove script name and backup name
            partial_rollback "$BACKUP_PATH" "$@"
            ;;
        --emergency)
            show_emergency_options
            ;;
        *)
            log_error "Unknown option: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
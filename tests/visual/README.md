# CSS Testing & Visual Regression Setup

This directory contains a comprehensive automated testing environment for CSS changes, designed to catch visual regressions and validate CSS changes quickly and reliably.

## 🎯 Overview

The testing setup includes:

- **Visual Regression Testing**: Screenshot comparison across multiple browsers and viewports
- **CSS Validation**: Automated stylelint validation with comprehensive rules
- **Performance Monitoring**: CSS file size, parse time, and optimization analysis
- **Quick Rollback**: Fast rollback procedures with safety checks
- **Automated Testing Scripts**: One-command testing for common scenarios

## 📁 Directory Structure

```
tests/visual/
├── README.md                    # This file
├── playwright.config.js         # Playwright configuration
├── pages.spec.js               # Visual regression tests for pages
├── css-validation.spec.js       # CSS-specific validation tests
├── screenshots/                 # Baseline screenshots (auto-generated)
├── reports/                     # Test reports and results
└── test-results/               # Test artifacts and failure screenshots
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Run Full CSS Test Suite

```bash
# Complete test suite (recommended)
npm run test:css

# Or use the direct script
./scripts/test-css-changes.sh
```

### 3. Generate Baseline Screenshots (First Time)

```bash
# Generate initial screenshots for comparison
npm run test:visual:update
```

## 🔧 Available Commands

### Testing Scripts

```bash
# Full test suite
npm run test:css                 # Complete CSS validation and testing
npm run test:css:full           # Same as above (explicit)
npm run test:css:validate       # CSS validation only
npm run test:css:visual         # Visual regression tests only
npm run test:css:performance    # Performance analysis only

# Visual regression specific
npm run test:visual             # Run visual tests
npm run test:visual:update      # Update baseline screenshots
npm run test:visual:report      # Open test report

# Performance monitoring
npm run css:performance        # Analyze CSS performance

# Rollback procedures
npm run css:rollback:quick      # Quick rollback to latest backup
npm run css:rollback:list       # List available backups
npm run css:rollback:interactive # Interactive backup selection
```

### Direct Script Usage

```bash
# Test script options
./scripts/test-css-changes.sh --full        # Full test suite
./scripts/test-css-changes.sh --validate    # Validation only
./scripts/test-css-changes.sh --visual      # Visual tests only
./scripts/test-css-changes.sh --performance # Performance only
./scripts/test-css-changes.sh --backup      # Create backup only
./scripts/test-css-changes.sh --restore     # Restore from backup

# Rollback script options
./scripts/quick-rollback.sh --list          # List backups
./scripts/quick-rollback.sh --quick         # Quick rollback
./scripts/quick-rollback.sh --interactive   # Choose backup
./scripts/quick-rollback.sh --status        # Show current status
./scripts/quick-rollback.sh --emergency     # Emergency recovery
```

## 🧪 Test Types

### 1. Visual Regression Tests

**Files**: `pages.spec.js`

Tests that capture screenshots of key pages and components across multiple:
- **Browsers**: Chrome, Firefox, Safari (WebKit)
- **Devices**: Desktop, tablet, mobile viewports
- **States**: Normal, hover, focus, filled forms

**Key Features**:
- Full page and viewport screenshots
- Component-specific testing (buttons, forms, cards)
- Responsive breakpoint testing
- Animation and dynamic content handling

### 2. CSS Validation Tests

**Files**: `css-validation.spec.js`

Browser-based tests that validate:
- CSS parsing and loading
- Performance metrics (file sizes, load times)
- Accessibility concerns (contrast, focus indicators)
- CSS rules utilization

### 3. Stylelint Validation

**Configuration**: `.stylelintrc.json`

Comprehensive CSS linting covering:
- Syntax errors and best practices
- Code formatting and consistency
- Performance optimizations
- Accessibility guidelines
- Custom property naming conventions

### 4. Performance Monitoring

**Script**: `scripts/css-performance-monitor.js`

Analyzes:
- File sizes and compression potential
- Selector complexity and duplicates
- Media query usage
- Custom property adoption
- Optimization suggestions

## 📊 Test Reports

All test results are saved in timestamped reports:

```
test-reports/
├── test_summary_TIMESTAMP.md          # Comprehensive test summary
├── stylelint_TIMESTAMP.log            # Stylelint validation results
├── performance_TIMESTAMP.json         # Performance analysis data
├── visual_TIMESTAMP.log               # Visual test results
└── css_validation_TIMESTAMP.log       # CSS validation test results
```

### Visual Test Reports

Playwright generates detailed HTML reports with:
- Screenshot comparisons
- Failure details
- Browser-specific results
- Test timelines

Access with: `npm run test:visual:report`

## 🔄 Backup & Rollback System

### Automatic Backups

The test system automatically creates backups before running tests:
- Timestamped backups in `css-backups/`
- Emergency backups before rollbacks
- Latest backup tracking

### Rollback Options

```bash
# Quick rollback to latest backup
npm run css:rollback:quick

# List all available backups
npm run css:rollback:list

# Interactive backup selection
npm run css:rollback:interactive

# Rollback specific files only
./scripts/quick-rollback.sh --partial BACKUP_NAME file1.css file2.css

# Compare current state with backup
./scripts/quick-rollback.sh --compare BACKUP_NAME
```

## ⚙️ Configuration

### Playwright Configuration

**File**: `playwright.config.js`

Key settings:
- Base URL: `http://localhost:8000`
- Auto-start development server
- Multiple browser projects
- Screenshot thresholds (0.1% pixel difference)
- Network idle waiting

### Stylelint Configuration

**File**: `.stylelintrc.json`

Comprehensive rules for:
- Error prevention
- Code consistency
- Performance optimization
- Accessibility compliance
- Naming conventions

### Visual Test Customization

Modify `pages.spec.js` to:
- Add new pages for testing
- Adjust viewport sizes
- Configure component selectors
- Customize screenshot options

## 🛠️ Troubleshooting

### Common Issues

1. **Server Not Starting**
   ```bash
   # Check if port 8000 is available
   lsof -i :8000
   
   # Start server manually
   uvicorn web.main:app --host 127.0.0.1 --port 8000
   ```

2. **Visual Tests Failing**
   ```bash
   # Update baseline screenshots
   npm run test:visual:update
   
   # View detailed failure report
   npm run test:visual:report
   ```

3. **Stylelint Errors**
   ```bash
   # Auto-fix issues
   npm run lint:css
   
   # Check specific errors
   npm run lint:css:check
   ```

4. **Backup Issues**
   ```bash
   # Check backup status
   ./scripts/quick-rollback.sh --status
   
   # Emergency recovery options
   ./scripts/quick-rollback.sh --emergency
   ```

### Test Performance Issues

- **Slow tests**: Reduce viewport combinations or test scope
- **Large screenshots**: Configure clipping areas for components
- **Server timeout**: Increase timeout in `playwright.config.js`
- **Memory issues**: Run tests with `--workers=1` for CI

## 🎯 Best Practices

### Before Making CSS Changes

1. Run baseline tests to ensure current state is clean
2. Create manual backup if making significant changes
3. Document expected visual changes

### During Development

1. Run validation tests frequently (`npm run test:css:validate`)
2. Use performance monitoring to track file size growth
3. Test responsive breakpoints early

### Before Deployment

1. Run full test suite (`npm run test:css`)
2. Review all test reports
3. Update baseline screenshots if changes are intentional
4. Verify rollback procedures work

### Maintaining Tests

1. Update screenshots when UI changes are intentional
2. Add new pages/components to test coverage
3. Review and update stylelint rules periodically
4. Clean up old backups regularly

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Stylelint Rules Reference](https://stylelint.io/user-guide/rules/)
- [CSS Performance Best Practices](https://web.dev/fast/)
- [Visual Regression Testing Guide](https://playwright.dev/docs/test-snapshots)

## 🤝 Contributing

When adding new tests:

1. Follow existing naming conventions
2. Add appropriate documentation
3. Test across all supported browsers
4. Update this README if adding new features

---

**Last Updated**: December 2024  
**Maintained By**: Development Team
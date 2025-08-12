# CSS Monitoring System

A comprehensive CSS monitoring and optimization tracking system for the Linker project. This system tracks CSS file sizes, optimization metrics, and generates detailed reports to help maintain code quality and performance.

## Features

### 📊 Comprehensive Metrics Tracking
- **File Sizes**: Individual and total CSS bundle sizes
- **Code Quality**: Hardcoded values detection (px, rgba, !important)
- **CSS Variables**: Usage and definition tracking
- **Media Queries**: Responsive design metrics
- **CSS Rules**: Selectors and rules counting
- **Optimization Suggestions**: Automated recommendations

### 📈 Trend Analysis
- Historical data tracking
- Size change monitoring
- Performance regression detection
- JSON-based trend reports

### 🔄 Real-time Monitoring
- File watcher for automatic monitoring
- Pre-commit hook integration
- Threshold-based quality gates
- CI/CD integration ready

## Quick Start

### Installation
Dependencies are already included in the project's `package.json`. If you need to install them separately:

```bash
npm install chokidar glob
```

### Basic Usage

```bash
# Run monitoring once
npm run css:monitor

# Generate detailed reports
npm run css:report

# Start file watcher
npm run css:monitor:watch

# Run pre-commit hook
npm run css:monitor:hook
```

## Commands Reference

### Core Monitoring Commands

| Command | Description |
|---------|-------------|
| `npm run css:monitor` | Run CSS monitoring analysis once |
| `npm run css:monitor:watch` | Start file watcher for continuous monitoring |
| `npm run css:monitor:hook` | Run pre-commit hook with threshold checks |
| `npm run css:report` | Generate comprehensive reports |

### Direct Node.js Usage

```bash
# Basic monitoring
node build-monitor.js

# Watch mode
node build-monitor.js watch

# Pre-commit hook
node css-monitor-hook.js

# Help
node build-monitor.js help
```

## Report Structure

### Generated Reports

The monitoring system generates several types of reports in `reports/css-monitoring/`:

#### 1. Summary Report (`summary.md`)
- Human-readable overview
- Key metrics and trends
- Optimization suggestions
- Top largest files

#### 2. Detailed Report (`detailed.json`)
- Complete metrics data
- File-by-file analysis
- Machine-readable format

#### 3. Trends Report (`trends.json`)
- Historical data points
- Size evolution tracking
- Performance trends

#### 4. Metrics Storage (`metrics.json`)
- Latest run results
- Previous run comparison
- Timestamp tracking

### Sample Summary Report

```markdown
# CSS Monitoring Summary

**Generated:** 2025/8/12 下午12:16:48

## Overview

| Metric | Value |
|--------|-------|
| Total Files | 44 |
| Total Size | 940.67KB (963246 bytes) |
| Total Lines | 27,349 |
| CSS Rules | 3,710 |
| CSS Selectors | 4,004 |

## Code Quality Metrics

| Metric | Count | Unique Values |
|--------|-------|---------------|
| Hardcoded Pixels | 1697 | 51 |
| Hardcoded Colors | 0 | 0 |
| CSS Variable Usage | 6856 | 404 |
| !important Usage | 172 | - |

## Optimization Suggestions

1. 🔴 **SIZE:** Total CSS size is 940.67KB. Consider splitting into smaller files.
2. 🟡 **MAINTAINABILITY:** Found 1697 hardcoded pixel values.
3. 🟡 **SPECIFICITY:** Found 172 !important declarations.
```

## Metrics Tracked

### File-Level Metrics
- **File size** (bytes and KB)
- **Line count**
- **Hardcoded pixel values** (count and unique values)
- **Hardcoded colors** (rgba, rgb, hex values)
- **CSS variable usage** (var() calls and definitions)
- **!important declarations**
- **Media queries**
- **CSS rules and selectors**

### Project-Level Totals
- **Total bundle size**
- **Aggregated code quality metrics**
- **Unique value collections**
- **Cross-file comparisons**

## Pre-commit Hook Integration

### Threshold Configuration

The pre-commit hook (`css-monitor-hook.js`) enforces these default thresholds:

```javascript
const thresholds = {
    maxSizeKB: 1000,           // Maximum total CSS size
    maxHardcodedPixels: 1800,  // Maximum hardcoded pixel values
    maxHardcodedColors: 50,    // Maximum hardcoded color values
    maxImportant: 200,         // Maximum !important usage
    maxFileSizeKB: 400         // Maximum individual file size
};
```

### Setup Pre-commit Hook

To integrate with Husky (if not already configured):

```bash
# Install husky if not present
npm install --save-dev husky

# Add pre-commit hook
npx husky add .husky/pre-commit "npm run css:monitor:hook"
```

### Hook Behavior

- ✅ **Pass**: All thresholds met, commit proceeds
- ❌ **Fail**: Thresholds exceeded, commit blocked
- ⚠️ **Error**: Monitoring failure, commit proceeds with warning

## Optimization Suggestions

The system automatically generates optimization suggestions based on metrics:

### Size Optimization
- **Large Bundle**: Suggests file splitting when total size > 500KB
- **Large Files**: Identifies individual files > 400KB

### Code Quality
- **Hardcoded Values**: Suggests CSS variables when many hardcoded values detected
- **Specificity Issues**: Warns about excessive !important usage
- **Maintainability**: Recommends design token adoption

### Performance
- **Bundle Splitting**: For better caching and loading
- **Dead Code**: Suggests unused style removal
- **Variable Adoption**: For better maintainability

## Advanced Usage

### Custom Monitoring

```javascript
const CSSBuildMonitor = require('./build-monitor.js');

const monitor = new CSSBuildMonitor();

// Run custom analysis
monitor.monitor().then(metrics => {
    console.log('CSS Size:', metrics.totals.totalSizeKB + 'KB');
    console.log('Hardcoded pixels:', metrics.totals.totalHardcodedPixels);
});
```

### File Watching

```javascript
// Start watching for changes
monitor.watch();

// Monitor will automatically re-run when CSS files change
```

### Custom Thresholds

```javascript
const CSSMonitorHook = require('./css-monitor-hook.js');

const hook = new CSSMonitorHook();

// Customize thresholds
hook.thresholds.maxSizeKB = 800;
hook.thresholds.maxHardcodedPixels = 1500;

hook.run();
```

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: CSS Monitoring
  run: |
    npm run css:monitor
    # Upload reports as artifacts
    mkdir -p artifacts
    cp -r reports/css-monitoring artifacts/
```

### Build Process Integration

```javascript
// webpack.config.js or similar
const CSSBuildMonitor = require('./build-monitor.js');

module.exports = {
    // ... webpack config
    plugins: [
        // ... other plugins
        {
            apply: (compiler) => {
                compiler.hooks.afterEmit.tapAsync('CSSMonitor', (compilation, callback) => {
                    const monitor = new CSSBuildMonitor();
                    monitor.monitor().then(() => callback()).catch(callback);
                });
            }
        }
    ]
};
```

### Pre-build Monitoring

```bash
# In build scripts
npm run css:monitor
if [ $? -ne 0 ]; then
    echo "CSS monitoring failed, aborting build"
    exit 1
fi
npm run build
```

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Make scripts executable
chmod +x build-monitor.js css-monitor-hook.js
```

#### Missing Dependencies
```bash
# Reinstall dependencies
npm install
```

#### Report Generation Failures
```bash
# Check directory permissions
mkdir -p reports/css-monitoring
chmod 755 reports/css-monitoring
```

### Debug Mode

```bash
# Run with verbose output
DEBUG=css-monitor node build-monitor.js
```

### Error Recovery

If monitoring fails:
1. Check CSS file accessibility
2. Verify Node.js version (>=14.0.0)
3. Ensure write permissions for reports directory
4. Check for syntax errors in CSS files

## Performance Considerations

### Monitoring Performance
- **File Count**: ~44 CSS files processed in <2 seconds
- **Memory Usage**: ~50MB peak for full analysis
- **Report Generation**: <1 second for all reports

### Optimization Impact
- **Bundle Analysis**: Identifies 940KB+ CSS with optimization opportunities
- **Variable Usage**: Tracks 6800+ CSS variable usages
- **Hardcoded Detection**: Finds 1600+ hardcoded values for optimization

## Roadmap

### Planned Features
- [ ] CSS-in-JS monitoring support
- [ ] SASS/SCSS source analysis
- [ ] Performance budget integration
- [ ] Visual regression tracking
- [ ] Automated optimization suggestions
- [ ] IDE integration (VS Code extension)

### Integration Targets
- [ ] PostCSS plugin version
- [ ] Webpack plugin
- [ ] Vite plugin
- [ ] GitHub Actions workflow

## Contributing

### Adding New Metrics

1. Extend the `analyzeCSSFile` method in `build-monitor.js`
2. Add metric calculation logic
3. Update report templates
4. Add threshold checks in `css-monitor-hook.js`
5. Update documentation

### Custom Analyzers

```javascript
// Example custom analyzer
const analyzer = {
    analyze(content) {
        // Custom analysis logic
        return {
            customMetric: calculateCustomMetric(content)
        };
    }
};

// Add to monitor
monitor.addAnalyzer(analyzer);
```

## License

This monitoring system is part of the Linker project and follows the same license terms.

---

For questions or issues, please refer to the main project documentation or create an issue in the project repository.
# CSS Tree-shaking Report

Generated: 2025/8/12 下午1:15:27

## Summary

- **Total Files Processed**: 33
- **Original Total Size**: 240.66 KB
- **Optimized Total Size**: 131.25 KB
- **Total Savings**: 109.41 KB (45.46% reduction)

## File Details

| File | Original Size | Optimized Size | Savings | Reduction % |
|------|---------------|----------------|---------|-------------|
| knowledge.css | 24.41 KB | 12.31 KB | 12.1 KB | 49.58% |
| forms.css | 11.76 KB | 3.69 KB | 8.07 KB | 68.65% |
| colors.css | 9 KB | 1.75 KB | 7.24 KB | 80.5% |
| loading.css | 10.78 KB | 3.92 KB | 6.87 KB | 63.69% |
| badges.css | 16.06 KB | 9.25 KB | 6.81 KB | 42.41% |
| cards.css | 9.07 KB | 3.16 KB | 5.91 KB | 65.13% |
| animations.css | 6.44 KB | 1.12 KB | 5.32 KB | 82.66% |
| practice.css | 20.47 KB | 15.4 KB | 5.07 KB | 24.75% |
| modals.css | 10.96 KB | 6.29 KB | 4.67 KB | 42.59% |
| practice-tags.css | 14.19 KB | 10.26 KB | 3.92 KB | 27.66% |
| shadows.css | 4 KB | 80 Bytes | 3.92 KB | 98.04% |
| knowledge-detail.css | 16.93 KB | 13.31 KB | 3.62 KB | 21.37% |
| buttons.css | 12.61 KB | 9.17 KB | 3.45 KB | 27.33% |
| examples.css | 5.41 KB | 2.04 KB | 3.37 KB | 62.3% |
| glass.css | 3.29 KB | 0 Bytes | 3.29 KB | 100% |
| typography.css | 6.12 KB | 3.51 KB | 2.61 KB | 42.59% |
| index.css | 10.09 KB | 7.57 KB | 2.52 KB | 24.95% |
| pattern-detail.css | 9.42 KB | 7.41 KB | 2.01 KB | 21.33% |
| performance.css | 2.04 KB | 37 Bytes | 2 KB | 98.23% |
| patterns.css | 7.18 KB | 5.32 KB | 1.86 KB | 25.94% |
| will-change.css | 2.66 KB | 882 Bytes | 1.79 KB | 67.56% |
| practice-queue.css | 7.28 KB | 5.53 KB | 1.75 KB | 24.04% |
| components.css | 3.41 KB | 1.9 KB | 1.5 KB | 44.15% |
| grid.css | 1.84 KB | 426 Bytes | 1.42 KB | 77.34% |
| dimensions.css | 1.39 KB | 0 Bytes | 1.39 KB | 100% |
| reset.css | 3.36 KB | 2.25 KB | 1.11 KB | 33.11% |
| z-index.css | 1.09 KB | 0 Bytes | 1.09 KB | 100% |
| spacing.css | 1.09 KB | 0 Bytes | 1.09 KB | 100% |
| layout.css | 3.06 KB | 2.05 KB | 1.02 KB | 33.24% |
| utilities.css | 2.67 KB | 1.77 KB | 924 Bytes | 33.78% |
| effects.css | 830 Bytes | 0 Bytes | 830 Bytes | 100% |
| index.css | 1.43 KB | 896 Bytes | 570 Bytes | 38.88% |
| border-radius.css | 357 Bytes | 0 Bytes | 357 Bytes | 100% |

## Top 5 Space Savers

1. **knowledge.css**: 12.1 KB saved (49.58% reduction)
2. **forms.css**: 8.07 KB saved (68.65% reduction)
3. **colors.css**: 7.24 KB saved (80.5% reduction)
4. **loading.css**: 6.87 KB saved (63.69% reduction)
5. **badges.css**: 6.81 KB saved (42.41% reduction)

## Build Configuration

This build used the following optimizations:

- **PurgeCSS**: Removed unused CSS rules based on HTML templates and JavaScript files
- **PostCSS Plugins**:
  - `postcss-combine-duplicated-selectors`: Combined duplicate selectors
  - `postcss-merge-rules`: Merged similar CSS rules
  - `postcss-discard-duplicates`: Removed duplicate rules
  - `cssnano`: Minified and optimized CSS

## Safelist Configuration

The build preserved:
- Essential HTML elements and common component classes
- Design system utility classes and tokens
- Dynamic classes and data attributes
- CSS variables and keyframe animations
- Interactive states and responsive variants

## Next Steps

1. Review the optimized CSS files in `web/static/css/dist/`
2. Test the application to ensure no styles were incorrectly removed
3. Update your production deployment to use the optimized CSS files
4. Monitor for any missing styles and update the safelist if needed

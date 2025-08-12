# CSS Selector Duplication Analysis Report

## Executive Summary

- **Total CSS Files Analyzed**: 32
- **Total Selectors Found**: 1356
- **Unique Selectors**: 1164
- **Duplicate Selectors**: 145
- **Total Duplicate Instances**: 337
- **Duplication Percentage**: 14.16%

## Key Findings

### Potential Reduction
- **Selectors that can be consolidated**: 145
- **Total duplicate instances that can be removed**: 192
- **Estimated reduction in CSS size**: 14.2%

## Most Duplicated Selectors

The following selectors appear in multiple files and should be considered for consolidation:

### 1. `:root` (17 times)
**Found in files:**
- design-system/03-components/buttons.css
- design-system/01-tokens/typography.css
- design-system/01-tokens/typography.css
- design-system/01-tokens/typography.css
- design-system/01-tokens/typography.css
- design-system/01-tokens/typography.css
- design-system/01-tokens/spacing.css
- design-system/01-tokens/animations.css
- design-system/01-tokens/colors.css
- design-system/01-tokens/performance.css
- design-system/01-tokens/shadows.css
- design-system/01-tokens/shadows.css
- design-system/01-tokens/shadows.css
- design-system/01-tokens/z-index.css
- design-system/01-tokens/glass.css
- design-system/01-tokens/effects.css
- design-system/01-tokens/border-radius.css

### 2. `.stat-item` (5 times)
**Found in files:**
- pages/practice-tags.css
- pages/knowledge.css
- pages/patterns.css
- pages/knowledge-detail.css
- design-system/03-components/cards.css

### 3. `.empty-state` (4 times)
**Found in files:**
- components.css
- pages/examples.css
- pages/practice.css
- pages/index.css

### 4. `.progress-bar` (4 times)
**Found in files:**
- pages/practice-tags.css
- pages/practice.css
- pages/practice-queue.css
- design-system/03-components/loading.css

### 5. `.sentence-label` (4 times)
**Found in files:**
- pages/examples.css
- pages/knowledge.css
- pages/knowledge-detail.css
- pages/knowledge-detail.css

### 6. `.section-title` (3 times)
**Found in files:**
- components.css
- pages/knowledge.css
- pages/knowledge-detail.css

### 7. `.empty-state svg` (3 times)
**Found in files:**
- components.css
- pages/examples.css
- pages/practice.css

### 8. `.empty-state h3` (3 times)
**Found in files:**
- components.css
- pages/examples.css
- pages/practice.css

### 9. `.empty-state p` (3 times)
**Found in files:**
- components.css
- pages/examples.css
- pages/practice.css

### 10. `.stat-label` (3 times)
**Found in files:**
- pages/practice-tags.css
- pages/knowledge-detail.css
- design-system/03-components/cards.css

### 11. `.stat-value` (3 times)
**Found in files:**
- pages/practice-tags.css
- pages/knowledge-detail.css
- design-system/03-components/cards.css

### 12. `.examples-label` (3 times)
**Found in files:**
- pages/examples.css
- pages/examples.css
- pages/knowledge.css

### 13. `.example-item` (3 times)
**Found in files:**
- pages/examples.css
- pages/examples.css
- pages/patterns.css

### 14. `.example-zh` (3 times)
**Found in files:**
- pages/examples.css
- pages/patterns.css
- pages/patterns.css

### 15. `.example-en` (3 times)
**Found in files:**
- pages/examples.css
- pages/patterns.css
- pages/patterns.css

### 16. `.no-results` (3 times)
**Found in files:**
- pages/examples.css
- pages/knowledge.css
- pages/patterns.css

### 17. `.no-results svg` (3 times)
**Found in files:**
- pages/examples.css
- pages/knowledge.css
- pages/patterns.css

### 18. `.no-results p` (3 times)
**Found in files:**
- pages/examples.css
- pages/knowledge.css
- pages/patterns.css

### 19. `.sentence-text` (3 times)
**Found in files:**
- pages/examples.css
- pages/knowledge.css
- pages/knowledge-detail.css

### 20. `.queue-header` (3 times)
**Found in files:**
- pages/practice.css
- pages/knowledge.css
- pages/practice-queue.css

... and 125 more duplicated selectors.

## Files with Most Duplicate Selectors

- **pages/knowledge.css**: 61 duplicate selectors
- **pages/practice.css**: 33 duplicate selectors
- **pages/examples.css**: 31 duplicate selectors
- **pages/patterns.css**: 27 duplicate selectors
- **pages/practice-queue.css**: 26 duplicate selectors
- **pages/knowledge-detail.css**: 24 duplicate selectors
- **design-system/03-components/cards.css**: 20 duplicate selectors
- **design-system/01-tokens/will-change.css**: 18 duplicate selectors
- **pages/pattern-detail.css**: 12 duplicate selectors
- **design-system/03-components/forms.css**: 11 duplicate selectors

## Detailed File Analysis

### components.css
- Total selectors: 25
- Duplicate selectors: 10
- Duplicated selectors in this file:
  - `.empty-state p` (also in: pages/examples.css, pages/practice.css)
  - `.toast.show` (also in: pages/examples.css)
  - `.examples .en` (also in: pages/examples.css)
  - `.empty-state h3` (also in: pages/examples.css, pages/practice.css)
  - `.examples .zh` (also in: pages/examples.css)
  - ... and 5 more

### pages/practice-tags.css
- Total selectors: 97
- Duplicate selectors: 5
- Duplicated selectors in this file:
  - `.progress-bar` (also in: pages/practice.css, pages/practice-queue.css, design-system/03-components/loading.css)
  - `.hint-icon` (also in: pages/practice.css)
  - `.stat-label` (also in: pages/knowledge-detail.css, design-system/03-components/cards.css)
  - `.stat-value` (also in: pages/knowledge-detail.css, design-system/03-components/cards.css)
  - `.stat-item` (also in: pages/knowledge.css, pages/patterns.css, pages/knowledge-detail.css, design-system/03-components/cards.css)

### pages/examples.css
- Total selectors: 46
- Duplicate selectors: 31
- Duplicated selectors in this file:
  - `.no-results h3` (also in: pages/knowledge.css)
  - `.examples-section` (also in: pages/pattern-detail.css)
  - `.example-en` (also in: pages/patterns.css, pages/patterns.css)
  - `.no-results svg` (also in: pages/knowledge.css, pages/patterns.css)
  - `.empty-state` (also in: components.css, pages/practice.css, pages/index.css)
  - ... and 23 more

### pages/practice.css
- Total selectors: 113
- Duplicate selectors: 33
- Duplicated selectors in this file:
  - `.queue-item` (also in: pages/knowledge.css, pages/practice-queue.css)
  - `.progress-bar` (also in: pages/practice-tags.css, pages/practice-queue.css, design-system/03-components/loading.css)
  - `.queue-item[data-status="generating"]` (also in: pages/practice-queue.css)
  - `.queue-item.add-new` (also in: pages/practice-queue.css)
  - `.queue-item-text` (also in: pages/practice-queue.css)
  - ... and 28 more

### pages/knowledge.css
- Total selectors: 156
- Duplicate selectors: 61
- Duplicated selectors in this file:
  - `.no-results h3` (also in: pages/examples.css)
  - `.queue-item` (also in: pages/practice.css, pages/practice-queue.css)
  - `.group-header` (also in: design-system/03-components/cards.css)
  - `.progress-ring` (also in: design-system/03-components/cards.css)
  - `.page-title` (also in: pages/patterns.css)
  - ... and 53 more

### pages/index.css
- Total selectors: 67
- Duplicate selectors: 8
- Duplicated selectors in this file:
  - `.mastery-indicator` (also in: pages/knowledge.css, design-system/03-components/cards.css)
  - `.mastery-fill` (also in: pages/knowledge-detail.css)
  - `.mastery-text` (also in: pages/knowledge-detail.css)
  - `.action-section` (also in: )
  - `.empty-state` (also in: components.css, pages/examples.css, pages/practice.css)
  - ... and 2 more

### pages/practice-queue.css
- Total selectors: 50
- Duplicate selectors: 26
- Duplicated selectors in this file:
  - `.queue-item` (also in: pages/practice.css, pages/knowledge.css)
  - `.progress-bar` (also in: pages/practice-tags.css, pages/practice.css, design-system/03-components/loading.css)
  - `.queue-item[data-status="generating"]` (also in: pages/practice.css)
  - `.queue-item.add-new` (also in: pages/practice.css)
  - `.queue-item-text` (also in: pages/practice.css)
  - ... and 21 more

### pages/patterns.css
- Total selectors: 43
- Duplicate selectors: 27
- Duplicated selectors in this file:
  - `.example-en` (also in: pages/examples.css)
  - `.page-title` (also in: pages/knowledge.css)
  - `.filter-section` (also in: pages/knowledge.css)
  - `.no-results svg` (also in: pages/examples.css, pages/knowledge.css)
  - `.example-zh` (also in: pages/examples.css)
  - ... and 20 more

### pages/knowledge-detail.css
- Total selectors: 92
- Duplicate selectors: 24
- Duplicated selectors in this file:
  - `.subtype-badge` (also in: design-system/03-components/badges.css)
  - `.mastery-fill` (also in: pages/index.css)
  - `.mastery-text` (also in: pages/index.css)
  - `.mistake-card` (also in: pages/pattern-detail.css)
  - `.correct-answer` (also in: )
  - ... and 13 more

### pages/pattern-detail.css
- Total selectors: 59
- Duplicate selectors: 12
- Duplicated selectors in this file:
  - `.pattern-formula` (also in: pages/patterns.css)
  - `.examples-section` (also in: pages/examples.css)
  - `.mistake-card` (also in: pages/knowledge-detail.css)
  - `.wrong` (also in: )
  - `.mistakes-section` (also in: pages/knowledge-detail.css)
  - ... and 3 more

### design-system/index.css
- Total selectors: 0
- Duplicate selectors: 0

### design-system/03-components/modals.css
- Total selectors: 65
- Duplicate selectors: 2
- Duplicated selectors in this file:
  - `.modal[data-glass="true"]` (also in: design-system/01-tokens/will-change.css)
  - `.modal` (also in: design-system/01-tokens/will-change.css)

### design-system/03-components/loading.css
- Total selectors: 66
- Duplicate selectors: 5
- Duplicated selectors in this file:
  - `.progress-bar` (also in: pages/practice-tags.css, pages/practice.css, pages/practice-queue.css)
  - `.btn[data-loading="true"]` (also in: design-system/03-components/buttons.css)
  - `.btn[data-loading="true"]::after` (also in: design-system/03-components/buttons.css)
  - `.spinner` (also in: design-system/01-tokens/will-change.css)
  - `.skeleton` (also in: design-system/01-tokens/will-change.css)

### design-system/03-components/forms.css
- Total selectors: 106
- Duplicate selectors: 11
- Duplicated selectors in this file:
  - `textarea:focus` (also in: design-system/01-tokens/will-change.css)
  - `.form-control[data-status="error"]` (also in: )
  - `select` (also in: design-system/02-base/reset.css)
  - `textarea` (also in: design-system/02-base/reset.css)
  - `.answer-input` (also in: pages/practice.css)
  - ... and 3 more

### design-system/03-components/badges.css
- Total selectors: 40
- Duplicate selectors: 4
- Duplicated selectors in this file:
  - `.subtype-badge` (also in: pages/knowledge-detail.css)
  - `.mastery-badge` (also in: pages/knowledge.css)
  - `.category-badge` (also in: pages/patterns.css, pages/knowledge-detail.css)
  - `.stat-badge` (also in: pages/knowledge.css, pages/patterns.css)

### design-system/03-components/buttons.css
- Total selectors: 66
- Duplicate selectors: 4
- Duplicated selectors in this file:
  - `.btn` (also in: design-system/01-tokens/will-change.css)
  - `.btn[data-loading="true"]::after` (also in: design-system/03-components/loading.css)
  - `.btn[data-loading="true"]` (also in: design-system/03-components/loading.css)
  - `:root` (also in: design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/03-components/cards.css
- Total selectors: 47
- Duplicate selectors: 20
- Duplicated selectors in this file:
  - `.card[data-interactive="true"]:hover` (also in: design-system/01-tokens/will-change.css)
  - `.group-header` (also in: pages/knowledge.css)
  - `.progress-ring` (also in: pages/knowledge.css)
  - `.card-header` (also in: pages/knowledge.css)
  - `.progress-ring svg` (also in: pages/knowledge.css)
  - ... and 15 more

### design-system/03-components/utilities.css
- Total selectors: 10
- Duplicate selectors: 0

### design-system/04-layouts/grid.css
- Total selectors: 5
- Duplicate selectors: 4
- Duplicated selectors in this file:
  - `.knowledge-groups` (also in: pages/knowledge.css)
  - `.group-instances` (also in: pages/knowledge.css)
  - `.patterns-grid` (also in: pages/patterns.css)
  - `.cards-grid` (also in: pages/knowledge.css)

### design-system/04-layouts/layout.css
- Total selectors: 20
- Duplicate selectors: 4
- Duplicated selectors in this file:
  - `main` (also in: design-system/02-base/reset.css)
  - `header.container` (also in: design-system/01-tokens/will-change.css)
  - `nav a:hover` (also in: design-system/01-tokens/will-change.css)
  - `nav a` (also in: design-system/01-tokens/will-change.css)

### design-system/02-base/reset.css
- Total selectors: 38
- Duplicate selectors: 7
- Duplicated selectors in this file:
  - `main` (also in: design-system/04-layouts/layout.css)
  - `img` (also in: )
  - `textarea` (also in: design-system/03-components/forms.css, design-system/03-components/forms.css)
  - `select` (also in: design-system/03-components/forms.css, design-system/03-components/forms.css)
  - `button` (also in: )

### design-system/01-tokens/typography.css
- Total selectors: 17
- Duplicate selectors: 5
- Duplicated selectors in this file:
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/spacing.css
- Total selectors: 1
- Duplicate selectors: 1
- Duplicated selectors in this file:
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/animations.css
- Total selectors: 13
- Duplicate selectors: 3
- Duplicated selectors in this file:
  - `.animate-scale-in` (also in: design-system/01-tokens/will-change.css)
  - `.animate-fade-in` (also in: design-system/01-tokens/will-change.css)
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/colors.css
- Total selectors: 21
- Duplicate selectors: 1
- Duplicated selectors in this file:
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/performance.css
- Total selectors: 14
- Duplicate selectors: 4
- Duplicated selectors in this file:
  - `.will-animate-opacity` (also in: design-system/01-tokens/will-change.css)
  - `.animation-done` (also in: design-system/01-tokens/will-change.css)
  - `.will-animate` (also in: design-system/01-tokens/will-change.css)
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/shadows.css
- Total selectors: 22
- Duplicate selectors: 3
- Duplicated selectors in this file:
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/z-index.css
- Total selectors: 13
- Duplicate selectors: 1
- Duplicated selectors in this file:
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/will-change.css
- Total selectors: 41
- Duplicate selectors: 18
- Duplicated selectors in this file:
  - `.will-animate-opacity` (also in: design-system/01-tokens/performance.css)
  - `.card[data-interactive="true"]:hover` (also in: design-system/03-components/cards.css)
  - `.modal[data-glass="true"]` (also in: design-system/03-components/modals.css)
  - `.btn` (also in: design-system/03-components/buttons.css)
  - `.animation-done` (also in: design-system/01-tokens/performance.css)
  - ... and 13 more

### design-system/01-tokens/glass.css
- Total selectors: 1
- Duplicate selectors: 1
- Duplicated selectors in this file:
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/effects.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/effects.css
- Total selectors: 1
- Duplicate selectors: 1
- Duplicated selectors in this file:
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/border-radius.css)

### design-system/01-tokens/border-radius.css
- Total selectors: 1
- Duplicate selectors: 1
- Duplicated selectors in this file:
  - `:root` (also in: design-system/03-components/buttons.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/typography.css, design-system/01-tokens/spacing.css, design-system/01-tokens/animations.css, design-system/01-tokens/colors.css, design-system/01-tokens/performance.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/shadows.css, design-system/01-tokens/z-index.css, design-system/01-tokens/glass.css, design-system/01-tokens/effects.css)

## Actionable Recommendations

### 1. High Priority Consolidation
Focus on selectors that appear in 3+ files:
- `:root` (17 files)
- `.stat-item` (5 files)
- `.empty-state` (4 files)
- `.progress-bar` (4 files)
- `.sentence-label` (4 files)
- `.section-title` (3 files)
- `.empty-state svg` (3 files)
- `.empty-state h3` (3 files)
- `.empty-state p` (3 files)
- `.stat-label` (3 files)

### 2. Medium Priority Consolidation
Selectors appearing in exactly 2 files:
- 117 selectors appear in exactly 2 files

### 3. Consolidation Strategy

1. **Create Shared Component Files**: Move commonly duplicated selectors to shared component CSS files
2. **Establish CSS Architecture**: Implement a clear hierarchy (tokens → base → components → pages)
3. **Use CSS Variables**: Replace hardcoded values with CSS custom properties
4. **Implement Build Process**: Use CSS preprocessing to manage imports and reduce duplication

### 4. Files to Refactor First

Focus on these files that have the most duplicate selectors:
- **pages/knowledge.css**: 61 duplicates (39.1% of selectors)
- **pages/practice.css**: 33 duplicates (29.2% of selectors)
- **pages/examples.css**: 31 duplicates (67.4% of selectors)
- **pages/patterns.css**: 27 duplicates (62.8% of selectors)
- **pages/practice-queue.css**: 26 duplicates (52.0% of selectors)

## Conclusion

With 14.2% duplication, there's moderate opportunity for CSS optimization. Focus on consolidating the 28 high-priority selectors and establish a clear CSS architecture to prevent future duplication.
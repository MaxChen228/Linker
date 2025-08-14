# Dynamic Styling System Guide

The Linker project now includes a comprehensive dynamic styling system that provides utilities for creating smooth, performant animations and dynamic UI elements using CSS custom properties and JavaScript utilities.

## Overview

The dynamic styling system consists of:

1. **CSS Utility Classes** - Pre-built classes that use CSS custom properties for dynamic values
2. **JavaScript Utilities** - Helper functions for manipulating styles programmatically
3. **Animation System** - Extended animation classes and keyframes

## CSS Utility Classes

### Progress Indicators

```css
/* Basic progress bar */
.progress-dynamic {
  width: var(--progress-width, 0%);
}

/* Vertical progress bar */
.progress-height-dynamic {
  height: var(--progress-height, 0%);
}

/* Circular progress (SVG) */
.progress-circle-dynamic {
  stroke-dashoffset: var(--progress-offset, 251.2);
}
```

### Mastery Level Indicators

```css
/* Width-based mastery indicator */
.mastery-indicator {
  width: var(--mastery-level, 0%);
}

/* Opacity-based mastery indicator */
.mastery-opacity {
  opacity: var(--mastery-opacity, 0);
}

/* Scale-based mastery indicator */
.mastery-scale {
  transform: scale(var(--mastery-scale, 1));
}
```

### Dynamic Dimensions

```css
.width-dynamic { width: var(--dynamic-width, auto); }
.height-dynamic { height: var(--dynamic-height, auto); }
.max-width-dynamic { max-width: var(--dynamic-max-width, none); }
.max-height-dynamic { max-height: var(--dynamic-max-height, none); }
```

### Animation Classes

```css
.animate-slide-out { animation: slideOutRight 0.3s ease forwards; }
.animate-slide-in { animation: slideInRight 0.3s ease forwards; }
.animate-fade-out { animation: fadeOut 0.3s ease forwards; }
.animate-bounce-in { animation: bounceIn 0.5s ease forwards; }
```

## JavaScript Utilities

### Basic Usage

```javascript
import { StyleUtils } from './web/static/js/style-utils.js';

// Set progress bar to 75%
const progressBar = document.querySelector('.progress-dynamic');
StyleUtils.setProgress(progressBar, 75);

// Set mastery level to 60%
const masteryIndicator = document.querySelector('.mastery-indicator');
StyleUtils.setMastery(masteryIndicator, 60);
```

### Progress Management

```javascript
// Basic progress
StyleUtils.setProgress(element, 50); // Sets --progress-width to 50%

// Height-based progress
StyleUtils.setProgressHeight(element, 75); // Sets --progress-height to 75%

// Circular progress (for SVG elements)
StyleUtils.setCircularProgress(element, 80, 251.2); // 80% with circumference 251.2
```

### Mastery Indicators

```javascript
// Set mastery level (0-100)
StyleUtils.setMastery(element, 85);

// Set mastery opacity (0-1)
StyleUtils.setMasteryOpacity(element, 0.8);

// Set mastery scale
StyleUtils.setMasteryScale(element, 1.2);
```

### Animation Management

```javascript
// Add animation with callback
StyleUtils.addAnimationClass(element, 'animate-slide-in', () => {
  console.log('Animation completed');
});

// Chain multiple animations
const animations = [
  { className: 'animate-fade-in', duration: '300ms', delay: 0 },
  { className: 'animate-scale-in', duration: '400ms', delay: 100 },
  { className: 'animate-bounce-in', duration: '500ms', delay: 200 }
];
StyleUtils.chainAnimations(element, animations);
```

### Dynamic Positioning

```javascript
// Set translation
StyleUtils.setTranslate(element, 50, 100); // 50px right, 100px down

// Set rotation
StyleUtils.setRotation(element, 45); // 45 degrees
```

### Dynamic Colors

```javascript
// Set dynamic text color
StyleUtils.setDynamicColor(element, 'var(--primary)');

// Set dynamic background
StyleUtils.setDynamicBackground(element, '#ff6b6b');

// Set dynamic border color
StyleUtils.setDynamicBorderColor(element, 'var(--success)');
```

## Advanced Features

### Batch Updates

```javascript
// Update multiple properties at once
StyleUtils.batchUpdate(element, {
  '--progress-width': '75%',
  '--mastery-level': '80%',
  '--dynamic-color': 'var(--success)'
});
```

### Animation Control

```javascript
// Pause all animations
StyleUtils.pauseAnimations(element);

// Resume animations
StyleUtils.resumeAnimations(element);

// Reset all dynamic properties
StyleUtils.resetDynamicProperties(element);
```

## HTML Examples

### Progress Bar

```html
<div class="progress-dynamic bg-primary" style="height: 8px; border-radius: 4px;">
</div>

<script>
// Animate progress to 75%
StyleUtils.setProgress(document.querySelector('.progress-dynamic'), 75);
</script>
```

### Mastery Indicator

```html
<div class="mastery-indicator bg-success" style="height: 4px; border-radius: 2px;">
</div>

<script>
// Set mastery level to 60%
StyleUtils.setMastery(document.querySelector('.mastery-indicator'), 60);
</script>
```

### Animated Card

```html
<div class="card animate-slide-in">
  <h3>Dynamic Card</h3>
  <p>This card will slide in with animation</p>
</div>
```

## Performance Considerations

1. **GPU Acceleration**: The system automatically adds GPU acceleration for better performance
2. **Reduced Motion**: Respects user's motion preferences
3. **Will-Change**: Optimizes for frequently changing properties
4. **Batch Updates**: Use `batchUpdate()` for multiple property changes

## Integration with Existing Design System

The dynamic styling system integrates seamlessly with the existing design system:

- Uses existing CSS custom properties for colors, spacing, and timing
- Follows the same naming conventions
- Respects accessibility preferences
- Works with existing component classes

## Demo

See `/web/static/js/style-utils-demo.js` for comprehensive usage examples and demonstrations of all features.

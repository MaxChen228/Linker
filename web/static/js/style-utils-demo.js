/**
 * Style Utils Demo
 * 動態樣式系統使用示例
 * 
 * This file demonstrates how to use the StyleUtils library
 * for dynamic styling in the Linker application.
 */

import { StyleUtils } from './style-utils.js';

/**
 * Demo: Progress Bar Animations
 * 示例：進度條動畫
 */
export function demoProgressBar() {
  // Find progress bar elements
  const progressBars = document.querySelectorAll('.progress-dynamic');
  
  progressBars.forEach((bar, index) => {
    // Animate to different progress values
    const targetProgress = (index + 1) * 25; // 25%, 50%, 75%, 100%
    
    // Set initial state
    StyleUtils.setProgress(bar, 0);
    
    // Animate to target after a delay
    setTimeout(() => {
      StyleUtils.setProgress(bar, targetProgress);
    }, index * 500);
  });
}

/**
 * Demo: Mastery Level Indicators
 * 示例：熟練度指示器
 */
export function demoMasteryIndicators() {
  const masteryElements = document.querySelectorAll('.mastery-indicator');
  
  masteryElements.forEach((element, index) => {
    const masteryLevel = Math.random() * 100; // Random mastery level
    
    // Start with 0 mastery
    StyleUtils.setMastery(element, 0);
    StyleUtils.setMasteryOpacity(element, 0.3);
    StyleUtils.setMasteryScale(element, 0.8);
    
    // Animate to target mastery
    setTimeout(() => {
      StyleUtils.setMastery(element, masteryLevel);
      StyleUtils.setMasteryOpacity(element, masteryLevel / 100);
      StyleUtils.setMasteryScale(element, 0.8 + (masteryLevel / 100) * 0.4);
    }, index * 200);
  });
}

/**
 * Demo: Animation Sequences
 * 示例：動畫序列
 */
export function demoAnimationSequences() {
  const cards = document.querySelectorAll('.card');
  
  cards.forEach((card, index) => {
    // Chain multiple animations
    const animations = [
      {
        className: 'animate-slide-in-left',
        duration: '300ms',
        delay: index * 100
      },
      {
        className: 'animate-bounce-in',
        duration: '500ms',
        delay: 200,
        callback: (element) => {
          console.log('Animation completed for card:', index);
        }
      }
    ];
    
    StyleUtils.chainAnimations(card, animations);
  });
}

/**
 * Demo: Dynamic Dimensions
 * 示例：動態尺寸
 */
export function demoDynamicDimensions() {
  const containers = document.querySelectorAll('.width-dynamic');
  
  containers.forEach((container, index) => {
    // Start with small width
    StyleUtils.setDynamicWidth(container, '50px');
    
    // Expand to full width
    setTimeout(() => {
      StyleUtils.setDynamicWidth(container, '100%');
    }, index * 300);
  });
}

/**
 * Demo: Interactive Animations
 * 示例：互動式動畫
 */
export function demoInteractiveAnimations() {
  const buttons = document.querySelectorAll('button');
  
  buttons.forEach(button => {
    button.addEventListener('click', (event) => {
      // Add click animation
      StyleUtils.addAnimationClass(
        event.target, 
        'animate-bounce-in',
        () => {
          console.log('Button animation completed');
        },
        { duration: '200ms' }
      );
      
      // Add a color change effect
      StyleUtils.setDynamicBackground(event.target, 'var(--primary)');
      
      // Reset color after animation
      setTimeout(() => {
        StyleUtils.setDynamicBackground(event.target, '');
      }, 200);
    });
    
    // Add hover effects
    button.addEventListener('mouseenter', (event) => {
      StyleUtils.setMasteryScale(event.target, 1.05);
    });
    
    button.addEventListener('mouseleave', (event) => {
      StyleUtils.setMasteryScale(event.target, 1);
    });
  });
}

/**
 * Demo: Circular Progress
 * 示例：圓形進度條
 */
export function demoCircularProgress() {
  const circularProgress = document.querySelectorAll('.progress-circle-dynamic');
  
  circularProgress.forEach((circle, index) => {
    const targetProgress = (index + 1) * 25;
    
    // Start at 0
    StyleUtils.setCircularProgress(circle, 0);
    
    // Animate to target
    setTimeout(() => {
      StyleUtils.setCircularProgress(circle, targetProgress);
    }, index * 400);
  });
}

/**
 * Demo: Dynamic Colors
 * 示例：動態顏色
 */
export function demoDynamicColors() {
  const elements = document.querySelectorAll('.color-dynamic');
  
  elements.forEach((element, index) => {
    const colors = [
      'var(--primary)',
      'var(--success)',
      'var(--warning)',
      'var(--error)',
      'var(--info)'
    ];
    
    let colorIndex = 0;
    
    // Cycle through colors
    setInterval(() => {
      StyleUtils.setDynamicColor(element, colors[colorIndex]);
      colorIndex = (colorIndex + 1) % colors.length;
    }, 1000 + index * 200);
  });
}

/**
 * Demo: Complete Animation Chain
 * 示例：完整動畫鏈
 */
export function demoCompleteChain() {
  const element = document.querySelector('#demo-element');
  if (!element) return;
  
  // Reset element
  StyleUtils.resetDynamicProperties(element);
  
  // Complex animation sequence
  const sequence = [
    {
      className: 'animate-fade-in',
      duration: '300ms',
      delay: 0
    },
    {
      className: 'animate-scale-in',
      duration: '400ms',
      delay: 100,
      callback: () => {
        StyleUtils.setProgress(element, 50);
      }
    },
    {
      className: 'animate-bounce-in',
      duration: '500ms',
      delay: 200,
      callback: () => {
        StyleUtils.setMastery(element, 80);
        StyleUtils.setDynamicColor(element, 'var(--success)');
      }
    }
  ];
  
  StyleUtils.chainAnimations(element, sequence);
}

/**
 * Initialize all demos
 * 初始化所有示例
 */
export function initializeStyleUtilsDemos() {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runDemos);
  } else {
    runDemos();
  }
}

function runDemos() {
  console.log('StyleUtils demos initialized');
  
  // Uncomment the demos you want to test
  // demoProgressBar();
  // demoMasteryIndicators();
  // demoAnimationSequences();
  // demoDynamicDimensions();
  // demoInteractiveAnimations();
  // demoCircularProgress();
  // demoDynamicColors();
  // demoCompleteChain();
}

// Auto-initialize if this script is loaded directly
if (typeof window !== 'undefined') {
  initializeStyleUtilsDemos();
}
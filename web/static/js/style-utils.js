/**
 * Style Manipulation Utilities
 * 動態樣式操作工具庫
 * 
 * Provides utilities for dynamic styling using CSS custom properties
 * and animation management for the Linker application.
 */

export const StyleUtils = {
  
  /**
   * Progress Management
   * 進度條管理
   */
  
  /**
   * Set progress bar width using CSS custom property
   * @param {HTMLElement} element - Target element
   * @param {number} value - Progress value (0-100)
   * @param {string} property - CSS property name (default: --progress-width)
   */
  setProgress(element, value, property = '--progress-width') {
    if (!element || typeof value !== 'number') {
      console.warn('StyleUtils.setProgress: Invalid element or value');
      return;
    }
    
    const clampedValue = Math.max(0, Math.min(100, value));
    element.style.setProperty(property, `${clampedValue}%`);
  },
  
  /**
   * Set progress bar height
   * @param {HTMLElement} element - Target element
   * @param {number} value - Progress value (0-100)
   */
  setProgressHeight(element, value) {
    this.setProgress(element, value, '--progress-height');
  },
  
  /**
   * Set circular progress indicator
   * @param {HTMLElement} element - Target SVG element
   * @param {number} value - Progress value (0-100)
   * @param {number} circumference - Circle circumference (default: 251.2)
   */
  setCircularProgress(element, value, circumference = 251.2) {
    if (!element || typeof value !== 'number') {
      console.warn('StyleUtils.setCircularProgress: Invalid element or value');
      return;
    }
    
    const clampedValue = Math.max(0, Math.min(100, value));
    const offset = circumference - (clampedValue / 100) * circumference;
    element.style.setProperty('--progress-offset', offset);
  },
  
  /**
   * Mastery Level Management
   * 熟練度管理
   */
  
  /**
   * Set mastery level indicator
   * @param {HTMLElement} element - Target element
   * @param {number} level - Mastery level (0-100)
   */
  setMastery(element, level) {
    if (!element || typeof level !== 'number') {
      console.warn('StyleUtils.setMastery: Invalid element or level');
      return;
    }
    
    const clampedLevel = Math.max(0, Math.min(100, level));
    element.style.setProperty('--mastery-level', `${clampedLevel}%`);
  },
  
  /**
   * Set mastery opacity
   * @param {HTMLElement} element - Target element
   * @param {number} opacity - Opacity value (0-1)
   */
  setMasteryOpacity(element, opacity) {
    if (!element || typeof opacity !== 'number') {
      console.warn('StyleUtils.setMasteryOpacity: Invalid element or opacity');
      return;
    }
    
    const clampedOpacity = Math.max(0, Math.min(1, opacity));
    element.style.setProperty('--mastery-opacity', clampedOpacity);
  },
  
  /**
   * Set mastery scale
   * @param {HTMLElement} element - Target element
   * @param {number} scale - Scale value
   */
  setMasteryScale(element, scale) {
    if (!element || typeof scale !== 'number') {
      console.warn('StyleUtils.setMasteryScale: Invalid element or scale');
      return;
    }
    
    element.style.setProperty('--mastery-scale', scale);
  },
  
  /**
   * Dynamic Dimensions
   * 動態尺寸
   */
  
  /**
   * Set dynamic width
   * @param {HTMLElement} element - Target element
   * @param {string|number} width - Width value
   */
  setDynamicWidth(element, width) {
    if (!element) {
      console.warn('StyleUtils.setDynamicWidth: Invalid element');
      return;
    }
    
    const widthValue = typeof width === 'number' ? `${width}px` : width;
    element.style.setProperty('--dynamic-width', widthValue);
  },
  
  /**
   * Set dynamic height
   * @param {HTMLElement} element - Target element
   * @param {string|number} height - Height value
   */
  setDynamicHeight(element, height) {
    if (!element) {
      console.warn('StyleUtils.setDynamicHeight: Invalid element');
      return;
    }
    
    const heightValue = typeof height === 'number' ? `${height}px` : height;
    element.style.setProperty('--dynamic-height', heightValue);
  },
  
  /**
   * Dynamic Positioning
   * 動態定位
   */
  
  /**
   * Set dynamic translation
   * @param {HTMLElement} element - Target element
   * @param {number|string} x - X translation
   * @param {number|string} y - Y translation
   */
  setTranslate(element, x, y = 0) {
    if (!element) {
      console.warn('StyleUtils.setTranslate: Invalid element');
      return;
    }
    
    const xValue = typeof x === 'number' ? `${x}px` : x;
    const yValue = typeof y === 'number' ? `${y}px` : y;
    
    element.style.setProperty('--translate-x', xValue);
    element.style.setProperty('--translate-y', yValue);
  },
  
  /**
   * Set rotation angle
   * @param {HTMLElement} element - Target element
   * @param {number} angle - Rotation angle in degrees
   */
  setRotation(element, angle) {
    if (!element || typeof angle !== 'number') {
      console.warn('StyleUtils.setRotation: Invalid element or angle');
      return;
    }
    
    element.style.setProperty('--rotation-angle', `${angle}deg`);
  },
  
  /**
   * Dynamic Colors
   * 動態顏色
   */
  
  /**
   * Set dynamic color
   * @param {HTMLElement} element - Target element
   * @param {string} color - Color value
   */
  setDynamicColor(element, color) {
    if (!element || !color) {
      console.warn('StyleUtils.setDynamicColor: Invalid element or color');
      return;
    }
    
    element.style.setProperty('--dynamic-color', color);
  },
  
  /**
   * Set dynamic background color
   * @param {HTMLElement} element - Target element
   * @param {string} color - Background color value
   */
  setDynamicBackground(element, color) {
    if (!element || !color) {
      console.warn('StyleUtils.setDynamicBackground: Invalid element or color');
      return;
    }
    
    element.style.setProperty('--dynamic-bg', color);
  },
  
  /**
   * Set dynamic border color
   * @param {HTMLElement} element - Target element
   * @param {string} color - Border color value
   */
  setDynamicBorderColor(element, color) {
    if (!element || !color) {
      console.warn('StyleUtils.setDynamicBorderColor: Invalid element or color');
      return;
    }
    
    element.style.setProperty('--dynamic-border-color', color);
  },
  
  /**
   * Animation Management
   * 動畫管理
   */
  
  /**
   * Add animation class with optional callback
   * @param {HTMLElement} element - Target element
   * @param {string} animationClass - Animation class name
   * @param {Function} callback - Optional callback when animation ends
   * @param {Object} options - Animation options
   */
  addAnimationClass(element, animationClass, callback = null, options = {}) {
    if (!element || !animationClass) {
      console.warn('StyleUtils.addAnimationClass: Invalid element or animation class');
      return;
    }
    
    const { 
      removeAfter = true, 
      once = true,
      duration = null 
    } = options;
    
    // Add GPU acceleration for better performance
    if (!element.classList.contains('gpu-accelerated')) {
      element.classList.add('gpu-accelerated');
    }
    
    element.classList.add(animationClass);
    
    if (duration) {
      element.style.setProperty('--animation-duration', duration);
    }
    
    if (removeAfter || callback) {
      const handleAnimationEnd = (event) => {
        if (event.target === element) {
          if (removeAfter) {
            element.classList.remove(animationClass);
          }
          
          if (callback) {
            callback(element, event);
          }
          
          if (once) {
            element.removeEventListener('animationend', handleAnimationEnd);
          }
        }
      };
      
      element.addEventListener('animationend', handleAnimationEnd, { once });
    }
  },
  
  /**
   * Remove animation class
   * @param {HTMLElement} element - Target element
   * @param {string} animationClass - Animation class name
   */
  removeAnimationClass(element, animationClass) {
    if (!element || !animationClass) {
      console.warn('StyleUtils.removeAnimationClass: Invalid element or animation class');
      return;
    }
    
    element.classList.remove(animationClass);
  },
  
  /**
   * Chain multiple animations
   * @param {HTMLElement} element - Target element
   * @param {Array} animations - Array of animation objects
   */
  chainAnimations(element, animations) {
    if (!element || !Array.isArray(animations) || animations.length === 0) {
      console.warn('StyleUtils.chainAnimations: Invalid element or animations array');
      return;
    }
    
    let currentIndex = 0;
    
    const runNextAnimation = () => {
      if (currentIndex >= animations.length) return;
      
      const animation = animations[currentIndex];
      const { 
        className, 
        duration, 
        delay = 0,
        callback 
      } = animation;
      
      setTimeout(() => {
        this.addAnimationClass(element, className, (el, event) => {
          if (callback) callback(el, event);
          currentIndex++;
          runNextAnimation();
        }, { duration });
      }, delay);
    };
    
    runNextAnimation();
  },
  
  /**
   * Utility Functions
   * 工具函數
   */
  
  /**
   * Reset all dynamic properties
   * @param {HTMLElement} element - Target element
   */
  resetDynamicProperties(element) {
    if (!element) {
      console.warn('StyleUtils.resetDynamicProperties: Invalid element');
      return;
    }
    
    const dynamicProperties = [
      '--progress-width',
      '--progress-height',
      '--progress-offset',
      '--mastery-level',
      '--mastery-opacity',
      '--mastery-scale',
      '--dynamic-width',
      '--dynamic-height',
      '--dynamic-max-width',
      '--dynamic-max-height',
      '--translate-x',
      '--translate-y',
      '--rotation-angle',
      '--dynamic-color',
      '--dynamic-bg',
      '--dynamic-border-color'
    ];
    
    dynamicProperties.forEach(property => {
      element.style.removeProperty(property);
    });
  },
  
  /**
   * Batch update multiple properties
   * @param {HTMLElement} element - Target element
   * @param {Object} properties - Object with property-value pairs
   */
  batchUpdate(element, properties) {
    if (!element || typeof properties !== 'object') {
      console.warn('StyleUtils.batchUpdate: Invalid element or properties');
      return;
    }
    
    Object.entries(properties).forEach(([property, value]) => {
      element.style.setProperty(property, value);
    });
  },
  
  /**
   * Get current value of a CSS custom property
   * @param {HTMLElement} element - Target element
   * @param {string} property - CSS property name
   * @returns {string} Current property value
   */
  getDynamicProperty(element, property) {
    if (!element || !property) {
      console.warn('StyleUtils.getDynamicProperty: Invalid element or property');
      return null;
    }
    
    return getComputedStyle(element).getPropertyValue(property).trim();
  },
  
  /**
   * Check if element has animation class
   * @param {HTMLElement} element - Target element
   * @param {string} animationClass - Animation class name
   * @returns {boolean} Whether element has the animation class
   */
  hasAnimationClass(element, animationClass) {
    if (!element || !animationClass) {
      return false;
    }
    
    return element.classList.contains(animationClass);
  },
  
  /**
   * Pause all animations on element
   * @param {HTMLElement} element - Target element
   */
  pauseAnimations(element) {
    if (!element) {
      console.warn('StyleUtils.pauseAnimations: Invalid element');
      return;
    }
    
    element.classList.add('animation-paused');
  },
  
  /**
   * Resume all animations on element
   * @param {HTMLElement} element - Target element
   */
  resumeAnimations(element) {
    if (!element) {
      console.warn('StyleUtils.resumeAnimations: Invalid element');
      return;
    }
    
    element.classList.remove('animation-paused');
    element.classList.add('animation-running');
  }
};

/**
 * Convenience aliases for common operations
 * 常用操作的便捷別名
 */
export const {
  setProgress,
  setMastery,
  addAnimationClass,
  setDynamicWidth,
  setDynamicHeight,
  setTranslate,
  setRotation
} = StyleUtils;

/**
 * Default export for ES6 modules
 */
export default StyleUtils;
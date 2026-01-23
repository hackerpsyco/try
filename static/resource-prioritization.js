/**
 * Resource Prioritization for CLAS PWA
 * 
 * Prioritizes loading of critical assets (HTML, core CSS, core JS)
 * before non-critical assets (images, fonts) on slow networks.
 * 
 * Requirements: 5.4
 * Property 10: Critical Asset Prioritization
 */

class ResourcePrioritizer {
  constructor() {
    this.criticalAssets = [
      '/static/css/tailwind.css',
      '/static/js/main.js'
    ];
    
    this.nonCriticalAssets = [
      /\.(png|jpg|jpeg|gif|svg|webp)$/i,
      /\.(woff|woff2|ttf|eot)$/i
    ];
    
    this.init();
  }

  /**
   * Initialize resource prioritization
   */
  init() {
    // Use Resource Hints for prioritization
    this.addResourceHints();
    
    // Monitor network speed
    this.monitorNetworkSpeed();
    
    console.log('[Resource Prioritization] Initialized');
  }

  /**
   * Add resource hints for critical assets
   */
  addResourceHints() {
    const head = document.head;
    
    // Preload critical assets (only if they exist)
    const criticalAssets = [
      { href: '/static/css/tailwind.css', as: 'style' },
      { href: '/static/js/main.js', as: 'script' }
    ];
    
    criticalAssets.forEach(asset => {
      // Check if asset exists before preloading
      fetch(asset.href, { method: 'HEAD' })
        .then(response => {
          if (response.ok) {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = asset.as;
            link.href = asset.href;
            link.crossOrigin = 'anonymous';
            head.appendChild(link);
          }
        })
        .catch(() => {
          // Asset doesn't exist, skip preloading
          console.log('[Resource Prioritization] Asset not found, skipping preload:', asset.href);
        });
    });
    
    // Prefetch non-critical assets
    const nonCriticalPrefetch = [
      '/static/images/icon-192.png',
      '/static/images/icon-512.png'
    ];
    
    nonCriticalPrefetch.forEach(asset => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = asset;
      link.crossOrigin = 'anonymous';
      head.appendChild(link);
    });
  }

  /**
   * Get asset type for resource hints
   */
  getAssetType(asset) {
    if (asset.endsWith('.css')) return 'style';
    if (asset.endsWith('.js')) return 'script';
    if (asset.match(/\.(png|jpg|jpeg|gif|svg|webp)$/i)) return 'image';
    if (asset.match(/\.(woff|woff2|ttf|eot)$/i)) return 'font';
    return 'fetch';
  }

  /**
   * Monitor network speed and adjust loading strategy
   */
  monitorNetworkSpeed() {
    if ('connection' in navigator) {
      const connection = navigator.connection;
      
      // Check effective type
      const effectiveType = connection.effectiveType;
      console.log('[Resource Prioritization] Network type:', effectiveType);
      
      // Adjust loading strategy based on network speed
      if (effectiveType === '4g') {
        this.setLoadingStrategy('fast');
      } else if (effectiveType === '3g') {
        this.setLoadingStrategy('moderate');
      } else {
        this.setLoadingStrategy('slow');
      }
      
      // Listen for network changes
      connection.addEventListener('change', () => {
        const newType = connection.effectiveType;
        console.log('[Resource Prioritization] Network type changed:', newType);
        this.setLoadingStrategy(newType === '4g' ? 'fast' : newType === '3g' ? 'moderate' : 'slow');
      });
    }
  }

  /**
   * Set loading strategy based on network speed
   */
  setLoadingStrategy(speed) {
    const strategy = {
      fast: {
        imageQuality: 'high',
        preloadImages: true,
        lazyLoadThreshold: 1000
      },
      moderate: {
        imageQuality: 'medium',
        preloadImages: false,
        lazyLoadThreshold: 500
      },
      slow: {
        imageQuality: 'low',
        preloadImages: false,
        lazyLoadThreshold: 100
      }
    };
    
    const config = strategy[speed] || strategy.moderate;
    
    // Store in window for use by other scripts
    window.resourceStrategy = config;
    
    // Apply lazy loading
    this.applyLazyLoading(config.lazyLoadThreshold);
    
    console.log('[Resource Prioritization] Loading strategy set:', speed, config);
  }

  /**
   * Apply lazy loading to images
   */
  applyLazyLoading(threshold) {
    if ('IntersectionObserver' in window) {
      const images = document.querySelectorAll('img[data-src]');
      
      const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            observer.unobserve(img);
          }
        });
      }, {
        rootMargin: `${threshold}px`
      });
      
      images.forEach(img => imageObserver.observe(img));
    }
  }

  /**
   * Check if asset is critical
   */
  isCriticalAsset(url) {
    return this.criticalAssets.some(asset => url.includes(asset));
  }

  /**
   * Check if asset is non-critical
   */
  isNonCriticalAsset(url) {
    return this.nonCriticalAssets.some(pattern => pattern.test(url));
  }

  /**
   * Get priority for asset
   */
  getPriority(url) {
    if (this.isCriticalAsset(url)) {
      return 'high';
    } else if (this.isNonCriticalAsset(url)) {
      return 'low';
    }
    return 'medium';
  }
}

// Initialize resource prioritizer when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.resourcePrioritizer = new ResourcePrioritizer();
  });
} else {
  window.resourcePrioritizer = new ResourcePrioritizer();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ResourcePrioritizer;
}

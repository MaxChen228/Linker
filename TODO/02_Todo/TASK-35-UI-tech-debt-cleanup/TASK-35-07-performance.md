# TASK-35-07: 性能優化 - CSS/JS載入和渲染優化

- **Priority**: 🟢 LOW
- **Estimated Time**: 12-16 hours
- **Related Components**: 全系統 CSS/JS 檔案、載入策略、渲染性能
- **Parent Task**: TASK-35-main.md

---

### 🎯 Task Objective

全面優化前端性能，包括CSS/JS載入策略、檔案大小優化、關鍵路徑優化、渲染性能提升，實現快速的用戶體驗和高效的資源利用。

### ✅ Acceptance Criteria

- [ ] **載入性能**: 首屏載入時間減少30%以上
- [ ] **檔案優化**: CSS/JS檔案大小優化，移除冗餘代碼
- [ ] **關鍵路徑**: 優化關鍵渲染路徑，提升FCP/LCP
- [ ] **快取策略**: 建立有效的瀏覽器快取機制
- [ ] **壓縮優化**: 實施gzip/brotli壓縮
- [ ] **懶載入**: 非關鍵資源實現懶載入
- [ ] **性能監控**: 建立性能監控和回歸檢測
- [ ] **Core Web Vitals**: 達到Good評級 (LCP<2.5s, FID<100ms, CLS<0.1)

### 📊 當前性能基準

**初始載入性能 (開發環境):**
```bash
# 使用Lighthouse測量基準數據
lighthouse http://localhost:8000 --only-categories=performance
```

**預期發現問題:**
- CSS檔案數量過多，串行載入
- JavaScript檔案未優化，全部載入
- 圖片未壓縮或未使用現代格式
- 缺乏資源預載入和優先級設定
- 字體載入策略需要改善

### 📋 具體執行步驟

#### Step 1: 性能基準測量和分析 (2-3小時)

1. **建立性能測量基準**
   ```bash
   # 安裝性能測試工具
   npm install -g lighthouse pagespeed-insights-cli web-vitals-cli
   
   # 測量各頁面基準性能
   lighthouse http://localhost:8000/ --output json --output-path baseline-home.json
   lighthouse http://localhost:8000/practice --output json --output-path baseline-practice.json
   lighthouse http://localhost:8000/patterns --output json --output-path baseline-patterns.json
   ```

2. **分析資源載入瀑布圖**
   ```bash
   # 使用Chrome DevTools或專用工具
   # 記錄各資源的載入時間和大小
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/
   ```

3. **識別性能瓶頸**
   ```markdown
   ## 預期發現的問題
   - CSS檔案: ~15個文件，總大小 ~200KB
   - JavaScript檔案: ~8個文件，總大小 ~150KB  
   - 字體檔案: 未優化載入策略
   - 圖片: 未壓縮，未使用WebP
   - 關鍵路徑: CSS阻塞渲染時間過長
   ```

#### Step 2: CSS載入策略優化 (3-4小時)

1. **CSS檔案合併和分離**
   ```html
   <!-- 改善前: 多個CSS檔案 -->
   <link rel="stylesheet" href="/static/css/design-system/index.css" />
   <link rel="stylesheet" href="/static/css/pages/practice.css" />
   <link rel="stylesheet" href="/static/css/components/batch-operations.css" />
   
   <!-- 改善後: 關鍵路徑優化 -->
   <!-- 內聯關鍵CSS -->
   <style>
     /* 關鍵的above-the-fold CSS內聯 */
     {% include 'critical.css' %}
   </style>
   
   <!-- 非關鍵CSS非阻塞載入 -->
   <link rel="preload" href="/static/css/design-system.min.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
   <noscript><link rel="stylesheet" href="/static/css/design-system.min.css"></noscript>
   ```

2. **建立CSS分層策略**
   ```css
   /* critical.css - 內聯的關鍵CSS */
   /* 包含: layout, typography, above-the-fold components */
   
   /* design-system.css - 主要設計系統 */
   /* 包含: tokens, components, utilities */
   
   /* page-specific.css - 頁面專用 */
   /* 按需載入的頁面專用樣式 */
   ```

3. **實施CSS壓縮和優化**
   ```bash
   # 安裝CSS優化工具
   npm install -g cssnano postcss-cli purgecss
   
   # CSS壓縮
   postcss web/static/css/design-system/index.css --use cssnano -o dist/design-system.min.css
   
   # 移除未使用的CSS
   purgecss --css dist/design-system.min.css --content 'web/templates/*.html' --output dist/
   ```

#### Step 3: JavaScript優化和分割 (3-4小時)

1. **JavaScript分割載入**
   ```html
   <!-- 關鍵JavaScript立即載入 -->
   <script src="/static/js/critical.min.js"></script>
   
   <!-- 非關鍵JavaScript非阻塞載入 -->
   <script defer src="/static/js/main.min.js"></script>
   <script defer src="/static/js/utils.min.js"></script>
   
   <!-- 頁面專用JavaScript按需載入 -->
   {% if active == 'practice' %}
   <script defer src="/static/js/practice-logic.min.js"></script>
   {% endif %}
   ```

2. **實施動態import**
   ```javascript
   // main.js - 使用動態import懶載入
   class AppCoordinator {
     async initPageSpecificManagers() {
       const path = window.location.pathname;
       
       if (path === '/patterns') {
         const { PatternsManager } = await import('./managers/PatternsManager.js');
         this.managers.patterns = new PatternsManager();
       }
       
       if (path === '/knowledge') {
         const { KnowledgeManager } = await import('./managers/KnowledgeManager.js');  
         this.managers.knowledge = new KnowledgeManager();
       }
     }
   }
   ```

3. **JavaScript壓縮和tree-shaking**
   ```bash
   # 安裝打包工具
   npm install -g esbuild terser
   
   # JavaScript壓縮
   esbuild web/static/js/main.js --bundle --minify --outfile=dist/main.min.js
   terser web/static/js/practice-logic.js -c -m -o dist/practice-logic.min.js
   ```

#### Step 4: 資源預載入和優先級 (2-3小時)

1. **實施資源提示**
   ```html
   <head>
     <!-- DNS預解析 -->
     <link rel="dns-prefetch" href="//fonts.googleapis.com">
     
     <!-- 關鍵資源預載入 -->
     <link rel="preload" href="/static/css/critical.css" as="style">
     <link rel="preload" href="/static/js/critical.js" as="script">
     
     <!-- 字體預載入 -->
     <link rel="preload" href="/static/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
     
     <!-- 下一頁面預載入 -->
     <link rel="prefetch" href="/static/js/practice-logic.js">
   </head>
   ```

2. **圖片懶載入和優化**
   ```html
   <!-- 使用現代圖片格式和懶載入 -->
   <picture>
     <source srcset="/static/images/hero.webp" type="image/webp">
     <source srcset="/static/images/hero.avif" type="image/avif">
     <img src="/static/images/hero.jpg" 
          alt="學習示意圖"
          loading="lazy"
          decoding="async"
          width="800" 
          height="400">
   </picture>
   
   <!-- SVG圖標內聯或雪碧圖 -->
   <svg class="icon" aria-hidden="true">
     <use href="#icon-check"></use>
   </svg>
   ```

3. **字體載入優化**
   ```css
   /* 字體載入策略 */
   @font-face {
     font-family: 'Inter';
     src: url('/static/fonts/inter-var.woff2') format('woff2-variations');
     font-display: swap; /* 字體交換策略 */
     font-weight: 100 900;
   }
   
   /* 字體預載入CSS */
   .font-loading {
     font-family: -apple-system, BlinkMacSystemFont, sans-serif;
   }
   
   .fonts-loaded {
     font-family: 'Inter', sans-serif;
   }
   ```

#### Step 5: 快取策略和CDN (2小時)

1. **設置瀏覽器快取**
   ```python
   # 在FastAPI中設置快取頭
   from fastapi.responses import FileResponse
   from fastapi.staticfiles import StaticFiles
   
   # 靜態檔案快取設置
   app.mount("/static", StaticFiles(
       directory="web/static",
       html=True,
       cache_control="public, max-age=31536000"  # 1年快取
   ), name="static")
   
   # HTML檔案快取設置
   @app.get("/")
   async def home():
       return templates.TemplateResponse(
           "index.html", 
           {"request": request},
           headers={"Cache-Control": "public, max-age=3600"}  # 1小時快取
       )
   ```

2. **實施檔案版本控制**
   ```bash
   # 生成檔案hash作為版本號
   #!/bin/bash
   for file in web/static/css/*.css; do
     hash=$(md5sum "$file" | cut -d' ' -f1 | cut -c1-8)
     mv "$file" "${file%.css}-${hash}.css"
   done
   ```

3. **壓縮設置**
   ```python
   # FastAPI gzip壓縮
   from fastapi.middleware.gzip import GZipMiddleware
   
   app.add_middleware(GZipMiddleware, minimum_size=500)
   
   # 或在nginx中設置
   # gzip on;
   # gzip_types text/css application/javascript application/json;
   # gzip_min_length 1000;
   ```

#### Step 6: 渲染性能優化 (2-3小時)

1. **CSS效能優化**
   ```css
   /* 避免複雜選擇器 */
   /* 改善前 */
   .container .card .header .title span:nth-child(2) { }
   
   /* 改善後 */
   .card-title-secondary { }
   
   /* 使用CSS containment */
   .card {
     contain: layout style paint;
   }
   
   /* 優化動畫性能 */
   .animated-element {
     will-change: transform;
     transform: translateZ(0); /* 觸發硬體加速 */
   }
   
   .animated-element:hover {
     transform: scale(1.05);
     transition: transform 0.2s ease;
   }
   ```

2. **JavaScript性能優化**
   ```javascript
   // 使用passive事件監聽器
   document.addEventListener('scroll', handleScroll, { passive: true });
   
   // 防抖和節流
   const debounce = (func, wait) => {
     let timeout;
     return (...args) => {
       clearTimeout(timeout);
       timeout = setTimeout(() => func.apply(this, args), wait);
     };
   };
   
   const throttle = (func, limit) => {
     let inThrottle;
     return (...args) => {
       if (!inThrottle) {
         func.apply(this, args);
         inThrottle = true;
         setTimeout(() => inThrottle = false, limit);
       }
     };
   };
   
   // 優化DOM操作
   const fragment = document.createDocumentFragment();
   for (let i = 0; i < items.length; i++) {
     const element = document.createElement('div');
     element.textContent = items[i];
     fragment.appendChild(element);
   }
   container.appendChild(fragment);
   ```

3. **關鍵渲染路徑優化**
   ```html
   <!-- 優化HTML結構 -->
   <!DOCTYPE html>
   <html lang="zh-Hant">
   <head>
     <meta charset="UTF-8">
     <meta name="viewport" content="width=device-width, initial-scale=1.0">
     
     <!-- 關鍵CSS內聯 -->
     <style>{% include 'critical.css' %}</style>
     
     <!-- 非關鍵CSS非阻塞載入 -->
     <link rel="preload" href="/static/css/main.min.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
   </head>
   <body>
     <!-- 內容結構 -->
     
     <!-- JavaScript放在body底部 -->
     <script defer src="/static/js/main.min.js"></script>
   </body>
   </html>
   ```

#### Step 7: 性能監控和測試 (1-2小時)

1. **自動化性能測試**
   ```bash
   #!/bin/bash
   # performance-test.sh
   
   echo "Running performance tests..."
   
   # Lighthouse測試
   lighthouse http://localhost:8000/ --output json --output-path reports/performance-home.json
   lighthouse http://localhost:8000/practice --output json --output-path reports/performance-practice.json
   
   # Web Vitals測試
   web-vitals http://localhost:8000/ > reports/web-vitals.txt
   
   # 載入時間測試
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/ > reports/load-time.txt
   ```

2. **性能監控指標**
   ```javascript
   // 添加性能監控代碼
   const observer = new PerformanceObserver((list) => {
     const entries = list.getEntries();
     entries.forEach((entry) => {
       if (entry.entryType === 'largest-contentful-paint') {
         console.log('LCP:', entry.startTime);
       }
       if (entry.entryType === 'first-input') {
         console.log('FID:', entry.processingStart - entry.startTime);
       }
     });
   });
   
   observer.observe({ type: 'largest-contentful-paint', buffered: true });
   observer.observe({ type: 'first-input', buffered: true });
   
   // 自定義性能標記
   performance.mark('app-init-start');
   // ... 應用初始化
   performance.mark('app-init-end');
   performance.measure('app-init', 'app-init-start', 'app-init-end');
   ```

3. **建立性能預算**
   ```json
   {
     "performance_budget": {
       "total_size": "500KB",
       "css_size": "100KB", 
       "js_size": "150KB",
       "image_size": "200KB",
       "font_size": "50KB",
       "lcp": "2.5s",
       "fid": "100ms",
       "cls": "0.1"
     }
   }
   ```

### 🎯 效能優化檢查清單

| 類別 | 優化項目 | 目標 | 狀態 |
|------|----------|------|------|
| **CSS** | 檔案合併和壓縮 | <100KB | ⭕ |
| **CSS** | 關鍵路徑優化 | 內聯關鍵CSS | ⭕ |
| **JS** | 代碼分割和懶載入 | <150KB初始載入 | ⭕ |
| **JS** | 壓縮和tree-shaking | 減少50%大小 | ⭕ |
| **圖片** | 現代格式和懶載入 | WebP/AVIF | ⭕ |
| **字體** | 預載入和font-display | swap策略 | ⭕ |
| **快取** | 瀏覽器快取策略 | 1年靜態資源 | ⭕ |
| **壓縮** | Gzip/Brotli | 減少70%傳輸 | ⭕ |

### 📊 預期性能改善

| 指標 | 優化前 | 優化後 | 改善幅度 |
|------|--------|--------|----------|
| **First Contentful Paint** | ~2.5s | ~1.2s | 52% |
| **Largest Contentful Paint** | ~4.0s | ~2.3s | 43% |
| **First Input Delay** | ~200ms | ~80ms | 60% |
| **Cumulative Layout Shift** | ~0.15 | ~0.08 | 47% |
| **Total Bundle Size** | ~400KB | ~200KB | 50% |
| **Time to Interactive** | ~5.5s | ~3.0s | 45% |

### 🔧 建置和部署優化

1. **建立自動化建置流程**
   ```bash
   #!/bin/bash
   # build.sh - 生產環境建置腳本
   
   echo "Building production assets..."
   
   # CSS處理
   postcss web/static/css/design-system/index.css --use cssnano -o dist/css/main.min.css
   purgecss --css dist/css/main.min.css --content 'web/templates/*.html' --output dist/css/
   
   # JavaScript處理
   esbuild web/static/js/main.js --bundle --minify --outfile=dist/js/main.min.js
   
   # 圖片優化
   imagemin web/static/images/* --out-dir=dist/images --plugin=webp --plugin=avif
   
   # 生成檔案hash
   find dist -name "*.css" -o -name "*.js" | while read file; do
     hash=$(md5sum "$file" | cut -c1-8)
     mv "$file" "${file%.*}-${hash}.${file##*.}"
   done
   
   echo "Build complete!"
   ```

2. **設定性能監控**
   ```javascript
   // 生產環境性能監控
   if ('performance' in window) {
     window.addEventListener('load', () => {
       setTimeout(() => {
         const perf = performance.getEntriesByType('navigation')[0];
         const metrics = {
           loadTime: perf.loadEventEnd - perf.fetchStart,
           domContentLoaded: perf.domContentLoadedEventEnd - perf.fetchStart,
           firstPaint: performance.getEntriesByType('paint')[0]?.startTime
         };
         
         // 發送到分析服務
         fetch('/api/performance', {
           method: 'POST',
           body: JSON.stringify(metrics)
         });
       }, 0);
     });
   }
   ```

### 📝 Execution Notes

**優化進度:**
- [ ] 性能基準測量完成
- [ ] CSS載入策略優化完成
- [ ] JavaScript分割和優化完成  
- [ ] 資源預載入設置完成
- [ ] 快取策略實施完成
- [ ] 渲染性能優化完成
- [ ] 性能監控建立完成

**性能測試:**
- [ ] Lighthouse分數 >90
- [ ] Core Web Vitals達到Good
- [ ] 載入時間減少30%+
- [ ] 檔案大小減少50%+

### 🔍 Review Comments (For Reviewer)

(審查者確認性能優化達到預期目標，所有指標符合要求，用戶體驗顯著改善)
# TASK-35-05: JavaScript重構 - main.js分離和模塊化

- **Priority**: 🟡 MEDIUM
- **Estimated Time**: 12-16 hours
- **Related Components**: web/static/js/main.js, web/static/js/*.js
- **Parent Task**: TASK-35-main.md

---

### 🎯 Task Objective

重構過度臃腫的main.js文件(987行)，將多個管理器類別分離為獨立模組，建立清晰的職責邊界，提高代碼可維護性和可測試性。

### ✅ Acceptance Criteria

- [ ] **main.js分離**: 將987行代碼分離為合理的模組
- [ ] **模組邊界清晰**: 每個管理器類別獨立文件，單一職責
- [ ] **依賴關係明確**: 建立清晰的模組import/export關係
- [ ] **功能完整性**: 所有現有功能正常運作
- [ ] **性能無退化**: JavaScript載入和執行效率維持或改善
- [ ] **事件管理簡化**: 移除過度設計的EventManager
- [ ] **代碼品質提升**: ESLint檢查通過，代碼更易維護
- [ ] **文檔更新**: 更新模組架構說明

### 📊 當前問題分析

**main.js結構問題:**
```javascript
// 單一文件包含過多職責 (987行)
class EventManager { /* 87行 - 過度設計 */ }
class DraftManager { /* 270行 - 草稿管理 */ }
class PracticeSync { /* 150行 - 練習同步 */ }
class PatternsManager { /* 210行 - 文法管理 */ }
class KnowledgeManager { /* 155行 - 知識管理 */ }
class LoadingManager { /* 45行 - 載入管理 */ }
// + 全域初始化代碼 70行
```

**架構問題:**
1. **單一職責違反**: 一個文件承擔多種功能
2. **模組耦合**: 類別間依賴關係不明確
3. **過度設計**: EventManager增加不必要複雜性
4. **測試困難**: 大文件難以進行單元測試
5. **載入問題**: 所有功能一次載入，影響性能

### 📋 具體執行步驟

#### Step 1: 分析現有代碼結構 (2-3小時)

1. **繪製依賴關係圖**
   ```bash
   # 分析各管理器的依賴關係
   grep -n "window\." web/static/js/main.js
   grep -n "globalEventManager" web/static/js/main.js
   grep -n "this\." web/static/js/main.js
   ```

2. **識別共同依賴**
   ```javascript
   // 分析哪些功能被多個類別使用
   // - logger 系統
   // - DOM 查詢工具
   // - 事件處理工具
   // - 存儲工具
   ```

3. **確定分離策略**
   ```markdown
   | 管理器類別 | 獨立性 | 依賴程度 | 分離優先級 |
   |-----------|--------|----------|-----------|
   | LoadingManager | 高 | 低 | 高 |
   | DraftManager | 高 | 中 | 高 |
   | EventManager | 低 | 高 | 低(重寫) |
   | PatternsManager | 中 | 中 | 中 |
   | KnowledgeManager | 中 | 中 | 中 |
   | PracticeSync | 低 | 高 | 低 |
   ```

#### Step 2: 建立共用工具模組 (3-4小時)

1. **創建核心工具模組**
   ```javascript
   // web/static/js/utils/dom.js
   export class DOMUtils {
     static query(selector) {
       return document.querySelector(selector);
     }
     
     static queryAll(selector) {
       return document.querySelectorAll(selector);
     }
     
     static createElement(tag, className, content) {
       const element = document.createElement(tag);
       if (className) element.className = className;
       if (content) element.textContent = content;
       return element;
     }
   }
   ```

2. **創建存儲工具模組**
   ```javascript
   // web/static/js/utils/storage.js
   export class StorageUtils {
     static get(key, defaultValue = null) {
       try {
         const value = localStorage.getItem(key);
         return value ? JSON.parse(value) : defaultValue;
       } catch (e) {
         console.error('Storage get error:', e);
         return defaultValue;
       }
     }
     
     static set(key, value) {
       try {
         localStorage.setItem(key, JSON.stringify(value));
         return true;
       } catch (e) {
         console.error('Storage set error:', e);
         return false;
       }
     }
   }
   ```

3. **簡化事件處理**
   ```javascript
   // web/static/js/utils/events.js
   export class EventUtils {
     // 替代過度設計的EventManager，使用簡單的事件處理
     static on(element, event, handler, options = {}) {
       element.addEventListener(event, handler, options);
       return () => element.removeEventListener(event, handler, options);
     }
     
     static once(element, event, handler) {
       element.addEventListener(event, handler, { once: true });
     }
     
     static emit(element, eventName, detail = {}) {
       const event = new CustomEvent(eventName, { detail });
       element.dispatchEvent(event);
     }
   }
   ```

#### Step 3: 分離獨立管理器 (4-5小時)

1. **LoadingManager 分離**
   ```javascript
   // web/static/js/managers/LoadingManager.js
   import { DOMUtils } from '../utils/dom.js';
   
   export class LoadingManager {
     constructor() {
       this.overlay = DOMUtils.query('#loading-overlay');
       this.title = DOMUtils.query('#loading-title');
       this.message = DOMUtils.query('#loading-message');
     }
     
     show(title = 'AI 正在處理中', message = '請稍候片刻...') {
       // 移動自 main.js 的實現
     }
     
     hide() {
       // 移動自 main.js 的實現  
     }
   }
   ```

2. **DraftManager 分離**
   ```javascript
   // web/static/js/managers/DraftManager.js
   import { StorageUtils } from '../utils/storage.js';
   import { EventUtils } from '../utils/events.js';
   import { DOMUtils } from '../utils/dom.js';
   
   export class DraftManager {
     constructor() {
       this.STORAGE_KEY = 'linker_practice_draft';
       this.AUTOSAVE_INTERVAL = 5000;
       // 移動其他屬性
     }
     
     init() {
       // 移動自 main.js 的實現，但簡化事件處理
     }
   }
   ```

3. **PatternsManager 分離**
   ```javascript
   // web/static/js/managers/PatternsManager.js
   import { DOMUtils } from '../utils/dom.js';
   import { StorageUtils } from '../utils/storage.js';
   
   export class PatternsManager {
     constructor() {
       // 移動屬性初始化
     }
     
     init() {
       // 移動並簡化初始化邏輯
     }
   }
   ```

#### Step 4: 重構main.js為協調器 (2-3小時)

1. **創建新的main.js**
   ```javascript
   // web/static/js/main.js (重構後)
   import { LoadingManager } from './managers/LoadingManager.js';
   import { DraftManager } from './managers/DraftManager.js';
   import { PatternsManager } from './managers/PatternsManager.js';
   import { KnowledgeManager } from './managers/KnowledgeManager.js';
   
   /**
    * 應用程式主協調器
    * 負責初始化各個管理器並協調它們的交互
    */
   class AppCoordinator {
     constructor() {
       this.managers = {};
       this.initLogger();
     }
     
     async init() {
       // 初始化載入管理器
       this.managers.loading = new LoadingManager();
       window.loadingManager = this.managers.loading;
       
       // 根據頁面類型初始化對應管理器
       this.initPageSpecificManagers();
       
       // 設置全域事件處理
       this.setupGlobalEvents();
     }
     
     initPageSpecificManagers() {
       const path = window.location.pathname;
       
       if (path === '/patterns') {
         this.managers.patterns = new PatternsManager();
         this.managers.patterns.init();
       }
       
       if (path === '/knowledge') {
         this.managers.knowledge = new KnowledgeManager();
         this.managers.knowledge.init();
       }
       
       // 練習頁面的管理器在 practice-logic.js 中處理
     }
   }
   
   // 初始化應用程式
   document.addEventListener('DOMContentLoaded', () => {
     const app = new AppCoordinator();
     app.init();
   });
   ```

2. **移除過度設計的EventManager**
   ```javascript
   // 將複雜的EventManager替換為簡單的工具函數
   // 減少987行中的87行不必要代碼
   ```

#### Step 5: 優化練習頁面邏輯 (2-3小時)

1. **檢查practice-logic.js與main.js的重疊**
   ```bash
   # 比較兩個文件的功能重疊
   diff -u web/static/js/main.js web/static/js/practice-logic.js
   ```

2. **清理重複功能**
   ```javascript
   // 確保練習頁面邏輯統一在practice-logic.js中
   // 移除main.js中與練習相關的重複代碼
   ```

3. **建立清晰的模組界面**
   ```javascript
   // practice-logic.js 應該獨立處理練習功能
   // main.js 只負責全域協調
   ```

#### Step 6: 測試和驗證 (2小時)

1. **功能測試**
   ```bash
   # 測試各頁面功能
   # - 首頁載入正常
   # - 文法句型頁面搜尋和篩選
   # - 知識點頁面管理
   # - 練習頁面完整功能
   ```

2. **性能測試**
   ```javascript
   // 測試JavaScript載入性能
   console.time('JS Load Time');
   // 測試各管理器初始化時間
   ```

3. **錯誤處理測試**
   ```javascript
   // 確保模組載入失敗時有適當的fallback
   // 測試各種錯誤情況
   ```

### 🎯 重構後的文件結構

```
web/static/js/
├── main.js                    # 120行 - 應用協調器
├── utils/
│   ├── dom.js                 # 30行 - DOM工具
│   ├── storage.js             # 40行 - 存儲工具  
│   └── events.js              # 25行 - 事件工具
├── managers/
│   ├── LoadingManager.js      # 50行 - 載入管理
│   ├── DraftManager.js        # 280行 - 草稿管理
│   ├── PatternsManager.js     # 220行 - 文法管理
│   └── KnowledgeManager.js    # 160行 - 知識管理
├── practice-logic.js          # 保持現有 - 練習邏輯
└── [其他現有文件保持不變]
```

### 📊 重構對比

| 方面 | 重構前 | 重構後 |
|------|--------|--------|
| main.js行數 | 987行 | ~120行 |
| 文件數量 | 1個主文件 | 8個模組化文件 |
| 職責分離 | 混亂 | 清晰 |
| 可測試性 | 困難 | 容易 |
| 維護性 | 低 | 高 |
| 載入策略 | 全部載入 | 按需載入 |

### ⚠️ 風險評估和緩解

**風險1: 模組載入順序問題**
- 緩解: 使用ES6 modules的import/export
- 測試: 確保依賴關係正確

**風險2: 功能破損**
- 緩解: 分步驟重構，每步驟都測試
- 備份: 保留原始main.js作為備份

**風險3: 性能退化**
- 緩解: 監控載入時間和內存使用
- 優化: 必要時使用動態import

### 🔧 工具和最佳實踐

1. **ESLint配置**
   ```json
   {
     "rules": {
       "max-lines": ["error", 200],
       "max-lines-per-function": ["error", 50],
       "complexity": ["error", 10]
     }
   }
   ```

2. **模組測試**
   ```javascript
   // 為每個管理器編寫單元測試
   import { LoadingManager } from '../managers/LoadingManager.js';
   
   describe('LoadingManager', () => {
     test('should show loading overlay', () => {
       // 測試載入功能
     });
   });
   ```

3. **性能監控**
   ```javascript
   // 添加性能監控點
   console.time('Manager Init');
   manager.init();
   console.timeEnd('Manager Init');
   ```

### 📝 Execution Notes

**分離進度:**
- [ ] 工具模組創建完成
- [ ] LoadingManager分離完成
- [ ] DraftManager分離完成  
- [ ] PatternsManager分離完成
- [ ] KnowledgeManager分離完成
- [ ] main.js重構完成
- [ ] 練習邏輯整理完成

**測試檢查點:**
- [ ] 首頁功能正常
- [ ] 文法句型頁面正常
- [ ] 知識點頁面正常
- [ ] 練習頁面功能完整
- [ ] 載入性能良好
- [ ] 錯誤處理正確

### 🔍 Review Comments (For Reviewer)

(審查者確認模組分離合理，代碼結構清晰，功能完整)
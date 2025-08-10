# 英文句型擴充計畫 TODO

## 🎯 專案目標
將現有的111個英文句型從簡單的「句型 + 說明 + 例句」擴充為完整的語法知識庫，提供深度、實用、結構化的學習資源。

---

## 📊 Phase 1: 批量 LLM API 處理架構

### 1.1 批量處理策略
```python
# core/pattern_enrichment.py

class PatternEnrichmentService:
    """句型擴充服務"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.batch_size = 5  # 每批處理5個句型
        self.retry_limit = 3
        self.delay_between_batches = 2  # 秒
        self.temperature = 0.7  # 平衡創意與一致性
        
    async def enrich_patterns_batch(self, patterns: list[dict]) -> list[dict]:
        """批量擴充句型"""
        enriched_patterns = []
        batches = [patterns[i:i+self.batch_size] 
                  for i in range(0, len(patterns), self.batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx+1}/{len(batches)}")
            
            # 並行處理批次內的句型
            tasks = [self.enrich_single_pattern(p) for p in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果與錯誤
            for pattern, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to enrich {pattern['id']}: {result}")
                    enriched_patterns.append(self.fallback_enrichment(pattern))
                else:
                    enriched_patterns.append(result)
            
            # 批次間延遲
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(self.delay_between_batches)
        
        return enriched_patterns
    
    async def enrich_single_pattern(self, pattern: dict) -> dict:
        """擴充單個句型（含重試機制）"""
        for attempt in range(self.retry_limit):
            try:
                response = await self.ai_service.enrich_pattern(
                    pattern=pattern,
                    temperature=self.temperature
                )
                validated = self.validate_response(response)
                if validated:
                    return validated
            except Exception as e:
                if attempt == self.retry_limit - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指數退避
        
    def validate_response(self, response: dict) -> dict:
        """驗證LLM回應結構"""
        required_fields = [
            'formula', 'structure_analysis', 'examples', 
            'variations', 'common_combinations'
        ]
        
        # 驗證必要欄位
        for field in required_fields:
            if field not in response:
                logger.warning(f"Missing field: {field}")
                return None
        
        # 驗證例句數量
        if len(response.get('examples', [])) < 5:
            logger.warning("Insufficient examples")
            return None
            
        return response
```

### 1.2 錯誤處理與恢復機制
```python
# 斷點續傳機制
class ProgressTracker:
    def __init__(self, checkpoint_file='data/enrichment_progress.json'):
        self.checkpoint_file = checkpoint_file
        self.progress = self.load_progress()
    
    def mark_completed(self, pattern_id: str):
        self.progress['completed'].append(pattern_id)
        self.save_progress()
    
    def get_remaining(self, all_patterns: list) -> list:
        completed_ids = set(self.progress['completed'])
        return [p for p in all_patterns if p['id'] not in completed_ids]
```

### 1.3 Rate Limiting 與配額管理
```python
class RateLimiter:
    def __init__(self, max_requests_per_minute=30):
        self.max_rpm = max_requests_per_minute
        self.request_times = deque(maxlen=max_requests_per_minute)
    
    async def acquire(self):
        now = time.time()
        if len(self.request_times) >= self.max_rpm:
            oldest = self.request_times[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        self.request_times.append(time.time())
```

---

## 🤖 Phase 2: 精準 Prompt 工程

### 2.1 主要 Prompt 模板
```python
PATTERN_ENRICHMENT_PROMPT = """
你是專業的英語語法專家，精通語言學理論與實際應用。請為以下句型生成完整、精準的語法資料。

【輸入句型】
Pattern: {pattern}
Category: {category}
Basic Explanation: {explanation}
Original Example: {example_zh} / {example_en}

【輸出要求】
請生成符合以下規範的JSON資料：

{
  "id": "{pattern_id}",
  "pattern": "{pattern}",
  "formula": "完整句法公式（使用標準語法符號：S, V, O, C, to-V, V-ing, that-clause等）",
  "category": "{category}",
  "difficulty": "1-5的整數（1=國中基礎, 2=高中核心, 3=大學入門, 4=進階應用, 5=專業學術）",
  "frequency": "high/medium/low（基於語料庫使用頻率）",
  
  "structure_analysis": {
    "components": "詳細說明每個成分的語法角色與功能",
    "word_order": "語序規則與變化可能",
    "required_elements": ["列出所有必要成分"],
    "optional_elements": ["列出所有可選成分"],
    "grammatical_features": "特殊語法特徵（如虛擬語氣、倒裝等）"
  },
  
  "usage_context": {
    "primary_function": "主要語言功能（表達目的、建議、強調等）",
    "register": "formal/neutral/informal",
    "domain": ["適用領域：academic/business/daily/literary"],
    "pragmatic_effect": "語用效果說明"
  },
  
  "examples": [
    {
      "zh": "中文句子（自然流暢的中文）",
      "en": "English sentence (natural and idiomatic)",
      "level": "basic/intermediate/advanced",
      "focus": "此例句重點展示的語法特徵",
      "vocabulary_level": "A1-C2",
      "context_note": "使用情境說明"
    }
    // 請提供10個例句，難度遞增，涵蓋不同時態和語境
  ],
  
  "variations": {
    "tense_forms": {
      "simple_present": "完整例句",
      "simple_past": "完整例句",
      "simple_future": "完整例句",
      "present_perfect": "完整例句",
      "past_perfect": "完整例句",
      "present_continuous": "完整例句（如適用）",
      "present_perfect_continuous": "完整例句（如適用）"
    },
    "voice": {
      "active": "主動語態例句",
      "passive": "被動語態例句（如適用）"
    },
    "polarity": {
      "affirmative": "肯定句",
      "negative": "否定句",
      "interrogative": "疑問句"
    },
    "modality": {
      "can/could": "例句",
      "may/might": "例句",
      "must/have to": "例句",
      "should/ought to": "例句"
    }
  },
  
  "collocations": {
    "high_frequency": {
      "verbs": ["最常用的10個動詞（按頻率排序）"],
      "nouns": ["最常用的10個名詞"],
      "adjectives": ["最常用的10個形容詞（如適用）"],
      "adverbs": ["最常用的10個副詞（如適用）"]
    },
    "fixed_phrases": [
      {
        "phrase": "固定搭配",
        "meaning": "意思",
        "example": "例句"
      }
    ],
    "common_chunks": ["常見詞塊：by the way, in order to等"]
  },
  
  "comparison": {
    "similar_patterns": [
      {
        "pattern": "相似句型",
        "similarity": "相同點",
        "difference": "關鍵差異",
        "usage_distinction": "使用場合區別"
      }
    ],
    "easily_confused": [
      {
        "pattern": "易混淆句型",
        "common_error": "常見錯誤",
        "distinction": "區分要點",
        "mnemonic": "記憶技巧"
      }
    ]
  },
  
  "common_errors": [
    {
      "error_pattern": "錯誤形式（標記錯誤處：*錯誤部分*）",
      "correction": "正確形式",
      "error_type": "grammar/word_order/agreement/tense",
      "explanation": "詳細解釋為什麼是錯誤",
      "l1_interference": true/false,
      "frequency": "very_common/common/occasional"
    }
    // 提供5個最常見的錯誤
  ],
  
  "advanced_notes": {
    "stylistic_variation": "文體變化說明",
    "regional_differences": {
      "american": "美式用法（如有差異）",
      "british": "英式用法（如有差異）"
    },
    "historical_development": "句型演變簡述（如相關）",
    "cross_linguistic": "與其他語言的對比（如相關）"
  },
  
  "practice_sentences": [
    "請將這個句子翻譯成英文：{中文句子1}",
    "請將這個句子翻譯成英文：{中文句子2}",
    "請將這個句子翻譯成英文：{中文句子3}",
    "請將這個句子翻譯成英文：{中文句子4}",
    "請將這個句子翻譯成英文：{中文句子5}"
  ],
  
  "corpus_frequency": {
    "bnc_rank": "估計在BNC語料庫中的頻率等級",
    "academic_frequency": "學術寫作中的使用頻率：high/medium/low",
    "spoken_frequency": "口語中的使用頻率：high/medium/low"
  }
}

【生成原則】
1. 所有例句必須自然、地道、符合該句型的典型用法
2. 例句難度要循序漸進，從簡單日常到複雜學術
3. 搭配詞必須按實際使用頻率排序（高頻優先）
4. 錯誤分析要基於實際的學習者常見錯誤
5. 變化形式要完整且實用
6. 不要包含過於罕見或過時的用法
7. 確保JSON格式正確，可直接解析

【重要提醒】
- 使用標準的語法術語和符號
- 例句要展示句型的不同面向和用法
- 中文翻譯要自然流暢，不要生硬直譯
- 提供的練習句要有代表性且實用
"""
```

### 2.2 Prompt 優化策略

#### 2.2.1 Few-shot Learning 範例
```python
FEW_SHOT_EXAMPLES = [
    {
        "input": {
            "pattern": "It is ~ that ~",
            "explanation": "分裂句，用於強調"
        },
        "output": {
            "formula": "It + be + 強調部分 + that + 句子其餘部分",
            "examples": [
                {
                    "zh": "就是昨天我遇見了她",
                    "en": "It was yesterday that I met her",
                    "focus": "強調時間"
                },
                {
                    "zh": "是約翰打破了窗戶",
                    "en": "It was John who broke the window",
                    "focus": "強調主詞"
                }
            ]
            # ... 完整結構
        }
    }
]
```

#### 2.2.2 Chain of Thought 引導
```python
COT_GUIDANCE = """
分析步驟：
1. 識別句型的核心結構 → 確定必要成分
2. 分析可能的變化形式 → 列出所有變體
3. 思考使用情境 → 確定語域和功能
4. 搜尋記憶中的例句 → 選擇典型用例
5. 考慮學習難點 → 識別常見錯誤
"""
```

### 2.3 Response 後處理
```python
class ResponsePostProcessor:
    """LLM回應後處理器"""
    
    def clean_response(self, raw_response: str) -> dict:
        """清理和標準化回應"""
        # 1. 提取JSON
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")
        
        # 2. 修復常見JSON錯誤
        json_str = json_match.group()
        json_str = self.fix_json_errors(json_str)
        
        # 3. 解析並驗證
        data = json.loads(json_str)
        
        # 4. 標準化欄位
        data = self.standardize_fields(data)
        
        # 5. 補充缺失欄位
        data = self.fill_missing_fields(data)
        
        return data
    
    def fix_json_errors(self, json_str: str) -> str:
        """修復常見的JSON格式錯誤"""
        # 移除尾隨逗號
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 修復布林值
        json_str = json_str.replace('true', 'true')
        json_str = json_str.replace('false', 'false')
        
        # 修復單引號
        json_str = json_str.replace("'", '"')
        
        return json_str
```

---

## 🎨 Phase 3: 使用者介面設計

### 3.1 句型列表頁面（簡潔版）

#### 3.1.1 資料結構
```python
# web/templates/patterns_list.html
"""
參考知識點列表的緊湊卡片設計：
- 每個句型顯示為一個緊湊的卡片
- 顯示關鍵資訊：句型、分類、難度、掌握度
- 支援篩選和搜尋
"""

class PatternListView:
    def get_pattern_summary(self, pattern_id: str) -> dict:
        """獲取句型摘要資訊"""
        return {
            "id": pattern_id,
            "pattern": "It is ~ that ~",
            "category": "強調用法",
            "difficulty": 3,
            "frequency": "high",
            "mastery": 0.65,  # 基於練習記錄計算
            "example_count": 10,
            "last_practiced": "2024-01-15",
            "error_count": 3
        }
```

#### 3.1.2 UI 元件設計
```html
<!-- 句型卡片（緊湊版） -->
<div class="pattern-card-compact" data-difficulty="3" data-mastery="65">
  <div class="pattern-header-compact">
    <h3 class="pattern-formula">It is ~ that ~</h3>
    <div class="pattern-badges">
      <span class="badge difficulty-badge" data-level="3">中級</span>
      <span class="badge frequency-badge">高頻</span>
    </div>
  </div>
  
  <div class="pattern-meta-compact">
    <span class="category-tag">強調用法</span>
    <div class="mastery-bar">
      <div class="mastery-fill" style="width: 65%"></div>
    </div>
  </div>
  
  <div class="pattern-stats-compact">
    <span class="stat-item">
      <svg class="icon">...</svg>
      10個例句
    </span>
    <span class="stat-item">
      <svg class="icon">...</svg>
      練習3次
    </span>
  </div>
  
  <a href="/patterns/GP001" class="pattern-link">查看詳情 →</a>
</div>
```

### 3.2 句型詳情頁面（豐富版）

#### 3.2.1 頁面結構
```html
<!-- 句型詳情頁面 -->
<div class="pattern-detail-container">
  <!-- 1. 頂部概覽 -->
  <section class="pattern-overview">
    <div class="overview-header">
      <h1 class="pattern-title">It is ~ that ~</h1>
      <div class="pattern-formula-box">
        <code>It + be + 強調部分 + that/who + 句子其餘部分</code>
      </div>
    </div>
    
    <div class="quick-info">
      <div class="info-card">
        <span class="label">分類</span>
        <span class="value">強調用法</span>
      </div>
      <div class="info-card">
        <span class="label">難度</span>
        <span class="value">⭐⭐⭐</span>
      </div>
      <div class="info-card">
        <span class="label">使用頻率</span>
        <span class="value">高</span>
      </div>
      <div class="info-card">
        <span class="label">掌握度</span>
        <div class="mastery-circle" data-percent="65">65%</div>
      </div>
    </div>
  </section>
  
  <!-- 2. 結構分析（可摺疊） -->
  <section class="pattern-structure collapsible">
    <h2 class="section-title">
      <svg class="icon">...</svg>
      結構分析
      <button class="toggle-btn">展開</button>
    </h2>
    <div class="section-content">
      <div class="structure-diagram">
        <!-- 視覺化句型結構圖 -->
        <div class="structure-tree">
          [It] → [be] → [強調部分] → [that/who] → [句子其餘]
        </div>
      </div>
      <div class="components-grid">
        <div class="component-card required">
          <h4>必要成分</h4>
          <ul>
            <li>It (形式主詞)</li>
            <li>be 動詞</li>
            <li>被強調的部分</li>
            <li>that/who (連接詞)</li>
          </ul>
        </div>
        <div class="component-card optional">
          <h4>可選成分</h4>
          <ul>
            <li>時間副詞</li>
            <li>情態動詞</li>
          </ul>
        </div>
      </div>
    </div>
  </section>
  
  <!-- 3. 例句展示（分級顯示） -->
  <section class="pattern-examples">
    <h2 class="section-title">
      <svg class="icon">...</svg>
      例句學習
    </h2>
    
    <!-- 難度篩選 -->
    <div class="level-filter">
      <button class="level-btn active" data-level="all">全部</button>
      <button class="level-btn" data-level="basic">基礎</button>
      <button class="level-btn" data-level="intermediate">中級</button>
      <button class="level-btn" data-level="advanced">進階</button>
    </div>
    
    <!-- 例句卡片 -->
    <div class="examples-grid">
      <div class="example-card" data-level="basic">
        <div class="example-header">
          <span class="level-badge basic">基礎</span>
          <span class="vocab-level">A2</span>
        </div>
        <div class="example-content">
          <p class="english">It was <mark>yesterday</mark> that I saw him.</p>
          <p class="chinese">就是昨天我看到他的。</p>
        </div>
        <div class="example-footer">
          <span class="focus-point">強調時間</span>
          <button class="btn-copy">複製</button>
          <button class="btn-practice">練習</button>
        </div>
      </div>
      <!-- 更多例句卡片... -->
    </div>
  </section>
  
  <!-- 4. 變化形式（標籤頁） -->
  <section class="pattern-variations">
    <h2 class="section-title">
      <svg class="icon">...</svg>
      變化形式
    </h2>
    
    <div class="variation-tabs">
      <button class="tab-btn active" data-tab="tense">時態</button>
      <button class="tab-btn" data-tab="voice">語態</button>
      <button class="tab-btn" data-tab="polarity">肯否疑</button>
      <button class="tab-btn" data-tab="modal">情態</button>
    </div>
    
    <div class="tab-content active" data-content="tense">
      <div class="variation-grid">
        <div class="variation-item">
          <h4>現在簡單式</h4>
          <p>It <mark>is</mark> John who helps me.</p>
        </div>
        <div class="variation-item">
          <h4>過去簡單式</h4>
          <p>It <mark>was</mark> John who helped me.</p>
        </div>
        <!-- 更多時態... -->
      </div>
    </div>
  </section>
  
  <!-- 5. 常用搭配（詞雲 + 列表） -->
  <section class="pattern-collocations">
    <h2 class="section-title">
      <svg class="icon">...</svg>
      常用搭配
    </h2>
    
    <div class="collocation-container">
      <!-- 視覺化詞雲 -->
      <div class="word-cloud">
        <span class="word-item high-freq">yesterday</span>
        <span class="word-item high-freq">important</span>
        <span class="word-item med-freq">reason</span>
        <!-- 更多詞彙... -->
      </div>
      
      <!-- 分類列表 -->
      <div class="collocation-lists">
        <div class="collocation-category">
          <h4>高頻動詞</h4>
          <ol class="freq-list">
            <li>was/is (be)</li>
            <li>made</li>
            <li>took</li>
          </ol>
        </div>
        <!-- 更多分類... -->
      </div>
    </div>
  </section>
  
  <!-- 6. 常見錯誤（警示卡片） -->
  <section class="pattern-errors">
    <h2 class="section-title">
      <svg class="icon">...</svg>
      常見錯誤
    </h2>
    
    <div class="errors-list">
      <div class="error-card">
        <div class="error-header">
          <span class="error-type">主謂一致</span>
          <span class="frequency-badge">極常見</span>
        </div>
        <div class="error-content">
          <div class="wrong">
            <span class="label">❌ 錯誤</span>
            <p>It <mark>were</mark> the students who came late.</p>
          </div>
          <div class="correct">
            <span class="label">✓ 正確</span>
            <p>It <mark>was</mark> the students who came late.</p>
          </div>
          <div class="explanation">
            <p>It 作為形式主詞，be 動詞永遠用單數形式，不受強調部分的單複數影響。</p>
          </div>
        </div>
      </div>
      <!-- 更多錯誤卡片... -->
    </div>
  </section>
  
  <!-- 7. 相關句型（連結卡片） -->
  <section class="related-patterns">
    <h2 class="section-title">
      <svg class="icon">...</svg>
      相關句型
    </h2>
    
    <div class="related-grid">
      <div class="related-card similar">
        <span class="relation-type">相似</span>
        <h4>What ... is ...</h4>
        <p>另一種強調句型，強調主詞或受詞</p>
        <a href="/patterns/GP002">查看 →</a>
      </div>
      <div class="related-card contrast">
        <span class="relation-type">對比</span>
        <h4>There is/are ...</h4>
        <p>存在句，不同於強調句</p>
        <a href="/patterns/GP015">查看 →</a>
      </div>
    </div>
  </section>
  
  <!-- 8. 練習區（互動式） -->
  <section class="pattern-practice">
    <h2 class="section-title">
      <svg class="icon">...</svg>
      即時練習
    </h2>
    
    <div class="practice-container">
      <div class="practice-question">
        <p class="instruction">請將以下句子改寫為強調句（強調劃線部分）：</p>
        <p class="original">I met Mary <u>in the park</u> yesterday.</p>
      </div>
      
      <div class="practice-input">
        <textarea placeholder="輸入你的答案..."></textarea>
        <button class="btn-check">檢查答案</button>
      </div>
      
      <div class="practice-feedback" style="display:none">
        <!-- 動態顯示回饋 -->
      </div>
    </div>
  </section>
</div>
```

#### 3.2.2 互動功能
```javascript
// 句型詳情頁互動功能
class PatternDetailPage {
  constructor() {
    this.initCollapsibles();
    this.initTabSwitching();
    this.initCopyButtons();
    this.initPracticeMode();
    this.initWordCloud();
  }
  
  initCollapsibles() {
    // 可摺疊區塊
    document.querySelectorAll('.collapsible').forEach(section => {
      const toggle = section.querySelector('.toggle-btn');
      toggle.addEventListener('click', () => {
        section.classList.toggle('expanded');
        toggle.textContent = section.classList.contains('expanded') 
          ? '收起' : '展開';
      });
    });
  }
  
  initTabSwitching() {
    // 標籤頁切換
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        // 切換標籤頁內容
        this.switchTab(tab);
      });
    });
  }
  
  initWordCloud() {
    // 詞雲視覺化
    const words = this.getCollocations();
    const cloud = new WordCloud('#word-cloud', {
      words: words,
      weightFactor: (size) => Math.pow(size, 1.5) * 10,
      color: (word, weight) => {
        return weight > 7 ? '#3b82f6' : 
               weight > 4 ? '#60a5fa' : '#93c5fd';
      }
    });
  }
  
  initPracticeMode() {
    // 即時練習功能
    const checkBtn = document.querySelector('.btn-check');
    checkBtn.addEventListener('click', async () => {
      const userAnswer = document.querySelector('textarea').value;
      const feedback = await this.checkAnswer(userAnswer);
      this.showFeedback(feedback);
    });
  }
}
```

### 3.3 CSS 設計規範
```css
/* 句型詳情頁樣式 */
.pattern-detail-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

/* 公式展示 */
.pattern-formula-box {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  font-family: 'Fira Code', monospace;
  font-size: 1.2rem;
  text-align: center;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

/* 例句卡片 */
.example-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s, box-shadow 0.3s;
}

.example-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.example-card mark {
  background: linear-gradient(120deg, #ffd670 0%, #ffab00 100%);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

/* 錯誤警示卡片 */
.error-card {
  background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
  border-left: 4px solid #f56565;
  padding: 1.5rem;
  border-radius: 8px;
}

.error-card .wrong {
  color: #c53030;
}

.error-card .correct {
  color: #22863a;
}

/* 詞雲效果 */
.word-cloud {
  position: relative;
  height: 300px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 1rem;
}

.word-item {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  transition: all 0.3s;
  cursor: pointer;
}

.word-item.high-freq {
  font-size: 1.5rem;
  font-weight: 600;
  background: rgba(59, 130, 246, 0.2);
}

.word-item:hover {
  transform: scale(1.1);
  background: #3b82f6;
  color: white;
}

/* 掌握度圓圈 */
.mastery-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: conic-gradient(
    #10b981 0deg,
    #10b981 calc(var(--percent) * 3.6deg),
    #e5e7eb calc(var(--percent) * 3.6deg)
  );
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  position: relative;
}

.mastery-circle::before {
  content: '';
  position: absolute;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: white;
}

.mastery-circle::after {
  content: attr(data-percent) '%';
  position: relative;
  z-index: 1;
}
```

---

## 📦 Phase 4: 資料存儲架構

### 4.1 資料庫結構設計
```python
# data/grammar_patterns_v2.json 結構
{
  "version": "2.0",
  "generated_at": "2024-01-20T10:00:00Z",
  "patterns": [
    {
      "id": "GP001",
      "pattern": "It is ~ that ~",
      "formula": "It + be + 強調部分 + that/who + 句子其餘部分",
      "category": "強調用法",
      "difficulty": 3,
      "frequency": "high",
      
      "structure": { /* 結構分析 */ },
      "examples": [ /* 例句陣列 */ ],
      "variations": { /* 變化形式 */ },
      "collocations": { /* 搭配詞彙 */ },
      "errors": [ /* 常見錯誤 */ ],
      "relations": { /* 相關句型 */ },
      
      "metadata": {
        "created_at": "2024-01-20T10:00:00Z",
        "updated_at": "2024-01-20T10:00:00Z",
        "enrichment_model": "gemini-2.5-pro",
        "review_status": "pending",
        "usage_stats": {
          "view_count": 0,
          "practice_count": 0,
          "error_rate": 0
        }
      }
    }
  ]
}
```

### 4.2 練習記錄整合
```python
# 擴充 practice_log.json
{
  "pattern_practice": [
    {
      "pattern_id": "GP001",
      "timestamp": "2024-01-20T10:00:00Z",
      "exercise_type": "translation",
      "user_answer": "It was yesterday that I met her",
      "correct_answer": "It was yesterday that I met her",
      "is_correct": true,
      "time_spent": 45,
      "hints_used": 0
    }
  ],
  
  "pattern_mastery": {
    "GP001": {
      "total_practices": 10,
      "correct_count": 7,
      "mastery_level": 0.7,
      "last_practiced": "2024-01-20",
      "error_patterns": ["tense_agreement"],
      "review_schedule": "2024-01-27"
    }
  }
}
```

---

## 🚀 Phase 5: 實施計畫

### 5.1 開發時程
- **Week 1**: 批量處理架構開發 + Prompt 優化
- **Week 2**: 執行批量擴充（分批進行，每日處理20個）
- **Week 3**: 前端介面開發（列表頁 + 詳情頁）
- **Week 4**: 整合測試 + 優化調整

### 5.2 品質控制
1. **自動驗證**：每個生成的句型資料都經過結構驗證
2. **人工抽檢**：每批次抽檢20%的內容品質
3. **使用者回饋**：上線後收集使用者回饋持續優化

### 5.3 風險管理
- **API 限制**：使用 rate limiting 和批次處理
- **品質不一致**：使用 few-shot examples 和嚴格的驗證
- **成本控制**：監控 token 使用量，優化 prompt 長度

### 5.4 成功指標
- 所有111個句型成功擴充
- 每個句型至少10個高品質例句
- 使用者滿意度 > 85%
- 頁面載入時間 < 2秒

---

## 📝 技術債務與未來優化

### 待優化項目
1. 建立句型之間的知識圖譜
2. 加入語音合成功能
3. 整合間隔重複演算法
4. 開發行動裝置 App
5. 加入社群分享功能

### 長期願景
- 建立完整的英語語法知識庫
- AI 個人化學習路徑
- 多語言支援（日語、韓語等）
- 整合更多語料庫資源
"""
英文句型批量擴充服務
使用 Gemini API 批量處理並擴充現有句型資料
"""

import asyncio
import json
import logging
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

from core.ai_service import AIService

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """API 速率限制器"""
    
    def __init__(self, max_requests_per_minute: int = 30):
        self.max_rpm = max_requests_per_minute
        self.request_times = deque(maxlen=max_requests_per_minute)
    
    async def acquire(self):
        """獲取執行權限，必要時等待"""
        now = time.time()
        if len(self.request_times) >= self.max_rpm:
            oldest = self.request_times[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
        self.request_times.append(time.time())


class ProgressTracker:
    """進度追蹤器，支援斷點續傳"""
    
    def __init__(self, checkpoint_file: str = 'data/enrichment_progress.json'):
        self.checkpoint_file = Path(checkpoint_file)
        self.progress = self.load_progress()
    
    def load_progress(self) -> Dict:
        """載入進度檔案"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'completed': [],
            'failed': [],
            'started_at': datetime.now().isoformat(),
            'last_updated': None
        }
    
    def save_progress(self):
        """儲存進度"""
        self.progress['last_updated'] = datetime.now().isoformat()
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def mark_completed(self, pattern_id: str):
        """標記完成"""
        if pattern_id not in self.progress['completed']:
            self.progress['completed'].append(pattern_id)
            self.save_progress()
    
    def mark_failed(self, pattern_id: str, error: str):
        """標記失敗"""
        self.progress['failed'].append({
            'id': pattern_id,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
        self.save_progress()
    
    def get_remaining(self, all_patterns: List[Dict]) -> List[Dict]:
        """獲取剩餘待處理的句型"""
        completed_ids = set(self.progress['completed'])
        return [p for p in all_patterns if p.get('id', p.get('pattern')) not in completed_ids]
    
    def reset(self):
        """重置進度"""
        self.progress = {
            'completed': [],
            'failed': [],
            'started_at': datetime.now().isoformat(),
            'last_updated': None
        }
        self.save_progress()


class ResponsePostProcessor:
    """LLM 回應後處理器"""
    
    def clean_response(self, raw_response: str) -> Dict:
        """清理和標準化回應"""
        try:
            # 1. 提取 JSON（處理可能的 markdown 包裹）
            json_match = re.search(r'```json\s*(.*?)\s*```', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 嘗試直接尋找 JSON 物件
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    raise ValueError("No JSON found in response")
            
            # 2. 修復常見 JSON 錯誤
            json_str = self.fix_json_errors(json_str)
            
            # 3. 解析 JSON
            data = json.loads(json_str)
            
            # 4. 標準化欄位
            data = self.standardize_fields(data)
            
            # 5. 補充缺失欄位
            data = self.fill_missing_fields(data)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to clean response: {e}")
            logger.debug(f"Raw response: {raw_response[:500]}...")
            raise
    
    def fix_json_errors(self, json_str: str) -> str:
        """修復常見的 JSON 格式錯誤"""
        # 移除尾隨逗號
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 確保布林值小寫
        json_str = json_str.replace('True', 'true')
        json_str = json_str.replace('False', 'false')
        json_str = json_str.replace('None', 'null')
        
        return json_str
    
    def standardize_fields(self, data: Dict) -> Dict:
        """標準化欄位名稱和格式"""
        # 確保必要欄位存在
        if 'examples' not in data:
            data['examples'] = []
        
        # 確保例句格式正確
        for i, example in enumerate(data.get('examples', [])):
            if isinstance(example, dict):
                # 確保有 zh 和 en 欄位
                if 'zh' not in example and 'chinese' in example:
                    example['zh'] = example.pop('chinese')
                if 'en' not in example and 'english' in example:
                    example['en'] = example.pop('english')
        
        return data
    
    def fill_missing_fields(self, data: Dict) -> Dict:
        """補充缺失的欄位"""
        defaults = {
            'difficulty': 3,
            'frequency': 'medium',
            'structure_analysis': {},
            'usage_context': {},
            'variations': {},
            'collocations': {},
            'comparison': {},
            'common_errors': [],
            'advanced_notes': {},
            'practice_sentences': [],
            'corpus_frequency': {}
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        return data


class PatternEnrichmentService:
    """句型擴充服務"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.batch_size = 5  # 每批處理5個句型
        self.retry_limit = 3
        self.delay_between_batches = 2  # 秒
        self.temperature = 0.7  # 平衡創意與一致性
        self.rate_limiter = RateLimiter(max_requests_per_minute=30)
        self.progress_tracker = ProgressTracker()
        self.post_processor = ResponsePostProcessor()
    
    def get_enrichment_prompt(self, pattern: Dict) -> str:
        """生成擴充 prompt"""
        prompt = f"""你是專業的英語語法專家，精通語言學理論與實際應用。請為以下句型生成完整、精準的語法資料。

【輸入句型】
Pattern: {pattern.get('pattern', '')}
Category: {pattern.get('category', '')}
Basic Explanation: {pattern.get('explanation', '')}
Original Example: {pattern.get('example_zh', '')} / {pattern.get('example_en', '')}

【輸出要求】
請生成符合以下規範的JSON資料：

{{
  "id": "{pattern.get('id', pattern.get('pattern', ''))}",
  "pattern": "{pattern.get('pattern', '')}",
  "formula": "完整句法公式（使用標準語法符號：S, V, O, C, to-V, V-ing, that-clause等）",
  "category": "{pattern.get('category', '')}",
  "difficulty": "1-5的整數（1=國中基礎, 2=高中核心, 3=大學入門, 4=進階應用, 5=專業學術）",
  "frequency": "high/medium/low（基於語料庫使用頻率）",
  
  "structure_analysis": {{
    "components": "詳細說明每個成分的語法角色與功能",
    "word_order": "語序規則與變化可能",
    "required_elements": ["列出所有必要成分"],
    "optional_elements": ["列出所有可選成分"],
    "grammatical_features": "特殊語法特徵（如虛擬語氣、倒裝等）"
  }},
  
  "usage_context": {{
    "primary_function": "主要語言功能（表達目的、建議、強調等）",
    "register": "formal/neutral/informal",
    "domain": ["適用領域：academic/business/daily/literary"],
    "pragmatic_effect": "語用效果說明"
  }},
  
  "examples": [
    {{
      "zh": "中文句子（自然流暢的中文）",
      "en": "English sentence (natural and idiomatic)",
      "level": "basic/intermediate/advanced",
      "focus": "此例句重點展示的語法特徵",
      "vocabulary_level": "A1-C2",
      "context_note": "使用情境說明"
    }}
    // 請提供10個例句，難度遞增，涵蓋不同時態和語境
  ],
  
  "variations": {{
    "tense_forms": {{
      "simple_present": "完整例句",
      "simple_past": "完整例句",
      "simple_future": "完整例句",
      "present_perfect": "完整例句（如適用）",
      "past_perfect": "完整例句（如適用）"
    }},
    "voice": {{
      "active": "主動語態例句",
      "passive": "被動語態例句（如適用）"
    }},
    "polarity": {{
      "affirmative": "肯定句",
      "negative": "否定句",
      "interrogative": "疑問句"
    }}
  }},
  
  "collocations": {{
    "high_frequency": {{
      "verbs": ["最常用的5個動詞"],
      "nouns": ["最常用的5個名詞"],
      "adjectives": ["最常用的5個形容詞（如適用）"]
    }},
    "fixed_phrases": [
      {{
        "phrase": "固定搭配",
        "meaning": "意思",
        "example": "例句"
      }}
    ]
  }},
  
  "common_errors": [
    {{
      "error_pattern": "錯誤形式",
      "correction": "正確形式",
      "error_type": "grammar/word_order/agreement/tense",
      "explanation": "詳細解釋為什麼是錯誤",
      "frequency": "very_common/common/occasional"
    }}
    // 提供3-5個最常見的錯誤
  ],
  
  "practice_sentences": [
    "請將這個句子翻譯成英文：（提供適合練習此句型的中文句子1）",
    "請將這個句子翻譯成英文：（提供適合練習此句型的中文句子2）",
    "請將這個句子翻譯成英文：（提供適合練習此句型的中文句子3）"
  ]
}}

【生成原則】
1. 所有例句必須自然、地道、符合該句型的典型用法
2. 例句難度要循序漸進，從簡單日常到複雜學術
3. 搭配詞必須按實際使用頻率排序（高頻優先）
4. 錯誤分析要基於實際的學習者常見錯誤
5. 變化形式要完整且實用
6. 確保JSON格式正確，可直接解析

請直接返回JSON資料，不需要額外說明。"""
        
        return prompt
    
    async def enrich_single_pattern(self, pattern: Dict) -> Dict:
        """擴充單個句型（含重試機制）"""
        pattern_id = pattern.get('id', pattern.get('pattern', 'unknown'))
        
        for attempt in range(self.retry_limit):
            try:
                # 速率限制
                await self.rate_limiter.acquire()
                
                # 生成 prompt
                prompt = self.get_enrichment_prompt(pattern)
                
                # 調用 AI
                logger.info(f"Enriching pattern: {pattern_id} (attempt {attempt + 1}/{self.retry_limit})")
                response = await self.ai_service.generate_async(
                    prompt=prompt,
                    temperature=self.temperature,
                    max_tokens=3000
                )
                
                # 處理回應
                enriched_data = self.post_processor.clean_response(response)
                
                # 驗證回應
                validated = self.validate_response(enriched_data)
                if validated:
                    # 合併原始資料
                    validated.update({
                        'original_pattern': pattern.get('pattern'),
                        'original_explanation': pattern.get('explanation'),
                        'enriched_at': datetime.now().isoformat(),
                        'enrichment_model': 'gemini-2.5-pro'
                    })
                    return validated
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {pattern_id}: {e}")
                if attempt == self.retry_limit - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指數退避
        
        raise Exception(f"Failed to enrich pattern {pattern_id} after {self.retry_limit} attempts")
    
    def validate_response(self, response: Dict) -> Optional[Dict]:
        """驗證 LLM 回應結構"""
        required_fields = [
            'pattern', 'formula', 'examples'
        ]
        
        # 驗證必要欄位
        for field in required_fields:
            if field not in response:
                logger.warning(f"Missing required field: {field}")
                return None
        
        # 驗證例句數量
        if len(response.get('examples', [])) < 3:
            logger.warning("Insufficient examples (minimum 3 required)")
            return None
        
        # 驗證例句格式
        for example in response.get('examples', []):
            if not isinstance(example, dict):
                logger.warning("Invalid example format")
                return None
            if 'zh' not in example or 'en' not in example:
                logger.warning("Example missing zh or en field")
                return None
        
        return response
    
    async def enrich_patterns_batch(self, patterns: List[Dict]) -> List[Dict]:
        """批量擴充句型"""
        enriched_patterns = []
        
        # 檢查剩餘待處理的句型
        remaining_patterns = self.progress_tracker.get_remaining(patterns)
        if not remaining_patterns:
            logger.info("All patterns have been processed")
            return enriched_patterns
        
        logger.info(f"Processing {len(remaining_patterns)} remaining patterns...")
        
        # 分批處理
        batches = [remaining_patterns[i:i+self.batch_size] 
                  for i in range(0, len(remaining_patterns), self.batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx+1}/{len(batches)}")
            
            # 並行處理批次內的句型
            tasks = []
            for pattern in batch:
                task = self.enrich_single_pattern(pattern)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果與錯誤
            for pattern, result in zip(batch, results):
                pattern_id = pattern.get('id', pattern.get('pattern', 'unknown'))
                
                if isinstance(result, Exception):
                    logger.error(f"Failed to enrich {pattern_id}: {result}")
                    self.progress_tracker.mark_failed(pattern_id, str(result))
                    # 使用原始資料作為後備
                    enriched_patterns.append(self.create_fallback_enrichment(pattern))
                else:
                    logger.info(f"Successfully enriched {pattern_id}")
                    self.progress_tracker.mark_completed(pattern_id)
                    enriched_patterns.append(result)
            
            # 批次間延遲
            if batch_idx < len(batches) - 1:
                logger.info(f"Waiting {self.delay_between_batches} seconds before next batch...")
                await asyncio.sleep(self.delay_between_batches)
        
        return enriched_patterns
    
    def create_fallback_enrichment(self, pattern: Dict) -> Dict:
        """創建後備擴充資料（當 AI 處理失敗時）"""
        return {
            'id': pattern.get('id', pattern.get('pattern', '')),
            'pattern': pattern.get('pattern', ''),
            'formula': pattern.get('pattern', ''),
            'category': pattern.get('category', ''),
            'difficulty': 3,
            'frequency': 'medium',
            'explanation': pattern.get('explanation', ''),
            'examples': [
                {
                    'zh': pattern.get('example_zh', ''),
                    'en': pattern.get('example_en', ''),
                    'level': 'intermediate',
                    'focus': 'basic usage'
                }
            ],
            'enrichment_status': 'fallback',
            'original_data': pattern
        }
    
    async def run_enrichment(self, input_file: str = 'data/grammar_patterns.json',
                           output_file: str = 'data/grammar_patterns_v2.json'):
        """執行完整的擴充流程"""
        try:
            # 載入原始資料
            logger.info(f"Loading patterns from {input_file}")
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            patterns = data if isinstance(data, list) else data.get('patterns', [])
            logger.info(f"Loaded {len(patterns)} patterns")
            
            # 執行批量擴充
            enriched_patterns = await self.enrich_patterns_batch(patterns)
            
            # 準備輸出資料
            output_data = {
                'version': '2.0',
                'generated_at': datetime.now().isoformat(),
                'total_patterns': len(enriched_patterns),
                'enrichment_summary': {
                    'completed': len(self.progress_tracker.progress['completed']),
                    'failed': len(self.progress_tracker.progress['failed']),
                    'model': 'gemini-2.5-pro',
                    'temperature': self.temperature
                },
                'patterns': enriched_patterns
            }
            
            # 儲存結果
            logger.info(f"Saving enriched data to {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info("Enrichment completed successfully!")
            logger.info(f"Completed: {len(self.progress_tracker.progress['completed'])}")
            logger.info(f"Failed: {len(self.progress_tracker.progress['failed'])}")
            
            return output_data
            
        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            raise


# 測試用的主程式
async def main():
    """測試批量擴充功能"""
    service = PatternEnrichmentService()
    
    # 可以選擇重置進度（從頭開始）或繼續上次的進度
    # service.progress_tracker.reset()  # 取消註解以重新開始
    
    # 執行擴充
    result = await service.run_enrichment()
    
    print(f"\n擴充完成！")
    print(f"總共處理: {result['total_patterns']} 個句型")
    print(f"成功: {result['enrichment_summary']['completed']} 個")
    print(f"失敗: {result['enrichment_summary']['failed']} 個")


if __name__ == "__main__":
    # 執行測試
    asyncio.run(main())
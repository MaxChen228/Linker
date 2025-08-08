"""
AI 服務模組 - 處理與 Gemini API 的互動
"""

import json
import os
import time
from typing import Any, Optional, List
from core.logger import get_logger


class AIService:
    """AI 服務類 - 封裝 Gemini API 調用"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # 模型名稱可由環境變數覆蓋
        self.generate_model_name = os.getenv("GEMINI_GENERATE_MODEL", "gemini-2.5-flash")
        self.grade_model_name = os.getenv("GEMINI_GRADE_MODEL", "gemini-2.5-pro")
        self.generate_model = None
        self.grade_model = None
        self.cache = {}
        self._init_gemini()
        self.logger = get_logger("ai")

    def _init_gemini(self):
        """初始化 Gemini"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            # 出題模型（快速）
            self.generate_model = genai.GenerativeModel(
                self.generate_model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.9,
                    top_p=0.95,
                ),
            )
            # 批改模型（高品質）
            self.grade_model = genai.GenerativeModel(
                self.grade_model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    top_p=0.9,
                ),
            )
            print("✅ Gemini API 初始化成功")
        except ImportError:
            print("❌ 請安裝 google-generativeai: pip install google-generativeai")
            raise
        except Exception as e:
            print(f"❌ Gemini 初始化失敗: {e}")
            raise

    def _call_model(self, model, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """調用指定模型的 LLM API"""
        # 檢查緩存
        cache_key = f"{system_prompt[:50]}_{user_prompt[:50]}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["time"] < 300:  # 5分鐘緩存
                return cached["data"]

        try:
            # 組合提示詞
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # 調用 API
            response = model.generate_content(full_prompt)

            # 解析 JSON 回應
            result = self._parse_response(response.text)

            # 儲存到緩存
            self.cache[cache_key] = {"data": result, "time": time.time()}

            try:
                self.logger.log_api_call(
                    api_name="gemini",
                    method="generate_content",
                    params={"prompt_preview": full_prompt[:200]},
                    response={k: result.get(k) for k in list(result.keys())[:3]} if isinstance(result, dict) else None,
                )
            except Exception:
                pass

            return result

        except Exception as e:
            self.logger.log_api_call(
                api_name="gemini",
                method="generate_content",
                params={"prompt_preview": (system_prompt + user_prompt)[:200]},
                error=e,
            )
            return self._get_fallback_response()

    def _parse_response(self, text: str) -> dict[str, Any]:
        """解析 AI 回應"""
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # 嘗試提取 JSON
            import re

            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError("無法解析 AI 回應") from e

    def _get_fallback_response(self) -> dict[str, Any]:
        """獲取備用回應"""
        return {
            "is_generally_correct": False,
            "overall_suggestion": "AI 服務暫時不可用，請稍後再試",
            "error_analysis": [],
        }

    def grade_translation(
        self, chinese: str, english: str, hint: Optional[str] = None
    ) -> dict[str, Any]:
        """批改翻譯 - 使用新的分類描述"""
        system_prompt = f"""
        你是一位專業的英文教師，請批改學生的翻譯。
        
        中文原句：{chinese}
        {"提示：" + hint if hint else ""}
        
        請以 JSON 格式回覆，包含以下欄位：
        
        1. is_generally_correct (boolean): 翻譯是否基本正確
        
        2. overall_suggestion (string): 建議的最佳翻譯（完整句子，使用英文）
        
        3. error_analysis (array): 錯誤分析列表，每個錯誤包含：
           - error_nature (string): 錯誤性質，必須是以下其中一種：
             * "系統性錯誤" - 涉及文法規則，學會規則後可避免同類錯誤（如時態、主謂一致、動詞變化）
             * "單一性錯誤" - 需要個別記憶的內容（如特定詞彙、搭配詞、介係詞、拼寫）
             * "可以更好" - 文法正確但表達可以更自然、更道地
             * "其他錯誤" - 不屬於上述類別的錯誤（如漏譯、理解錯誤）
           
           - key_point_summary (string): 錯誤重點的簡潔描述（使用繁體中文）
           
           - original_phrase (string): 學生寫錯的片語或句子部分
           
           - correction (string): 正確的寫法
           
           - explanation (string): 詳細解釋為什麼錯了，以及正確的用法（使用繁體中文）
           
           - severity (string): 嚴重程度，"major"（重要錯誤）或 "minor"（次要問題）
        
        分類原則：
        - 如果錯誤涉及可以通過學習規則解決的文法問題，歸類為"系統性錯誤"
        - 如果錯誤需要記憶特定用法或單字，歸類為"單一性錯誤"
        - 如果翻譯正確但可以更自然，歸類為"可以更好"（通常是 minor）
        - 其他情況歸類為"其他錯誤"
        
        重要：
        - 請確保 error_nature 欄位完全匹配上述四個選項之一
        - 每個錯誤都要有清楚的 explanation
        - overall_suggestion 必須是完整、正確的英文句子
        """

        user_prompt = f"學生的翻譯：「{english}」"

        if not self.grade_model:
            return self._get_fallback_response()
        return self._call_model(self.grade_model, system_prompt, user_prompt)

    def generate_practice_sentence(
        self,
        level: int = 1,
        length: str = "short",
        examples: Optional[List[str]] = None,
    ) -> dict[str, str]:
        """生成練習句子（使用出題模型）

        examples: 來自分級例句庫的代表例句（few-shot context），不會回傳給使用者。
        length: "short" | "medium" | "long" 影響目標字數/結構。
        """
        difficulty_map = {
            1: "國中基礎程度，簡單詞彙和基本句型",
            2: "高中程度，包含常見片語和複雜句型",
            3: "學測程度，包含進階詞彙和複雜語法",
        }
        length_hint = {
            "short": "字數約10-20，句子簡潔",
            "medium": "字數約20-35，結構完整",
            "long": "字數約35-60，包含從屬子句或分詞構句",
        }.get(length, "字數適中")

        examples_text = "\n".join(f"- {s}" for s in (examples or [])[:5])

        system_prompt = f"""
        你是一位專業的英文出題教師，
        請生成一個{difficulty_map.get(level, difficulty_map[1])}、且{length_hint}的中文句子，
        用於英文翻譯練習。
        
        要求：
        1. 句子要自然、實用、符合日常對話或寫作情境
        2. 長度適中（10-30字）
        3. 包含明確的語法重點或常見表達
        4. 避免過於文言或罕見的表達方式
        5. 請參考以下代表例句風格，但不要重複：
        {examples_text}
        
        請以 JSON 格式回覆：
        {{
            "sentence": "中文句子",
            "hint": "這個句子的翻譯重點或提示（例如：注意時態、注意介係詞等）",
            "difficulty_level": {level},
            "grammar_points": ["涉及的文法點1", "涉及的文法點2"]
        }}
        """

        # 加入變體 nonce，鼓勵模型產出不同結果，避免快取重複
        import time as _t
        user_prompt = f"請生成一個適合練習的中文句子\n[variant_nonce={int(_t.time()*1000)}]"

        if not self.generate_model:
            result = {}
        else:
            result = self._call_model(self.generate_model, system_prompt, user_prompt)

        # 處理可能的列表返回（API 有時返回列表）
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        elif not isinstance(result, dict):
            result = {}

        # 確保返回必要的欄位
        # 若 LLM 失敗則從 examples 隨機取一題退回
        import random as _r
        fallback_sentence = _r.choice(examples) if examples else "今天天氣很好。"
        return {
            "sentence": result.get("sentence", fallback_sentence),
            "hint": result.get("hint", "注意時態和主詞"),
            "difficulty_level": result.get("difficulty_level", level),
            "grammar_points": result.get("grammar_points", []),
        }

    def analyze_common_mistakes(self, practice_history: list) -> dict[str, Any]:
        """分析常見錯誤模式"""
        if not practice_history:
            return {"patterns": [], "suggestions": []}

        # 準備最近的錯誤摘要
        recent_mistakes = []
        for practice in practice_history[-self.settings.practice.RECENT_MISTAKES_COUNT :]:
            if not practice.get("is_correct", True):
                errors = practice.get("feedback", {}).get("error_analysis", [])
                for error in errors:
                    recent_mistakes.append(
                        {
                            "nature": error.get("error_nature", ""),
                            "key_point": error.get("key_point_summary", ""),
                        }
                    )

        if not recent_mistakes:
            return {"patterns": [], "suggestions": []}

        system_prompt = """
        你是一位英語教學專家，請分析學生的錯誤模式並提供學習建議。
        
        請以 JSON 格式回覆：
        {
            "common_patterns": [
                {
                    "pattern": "錯誤模式描述",
                    "frequency": "出現頻率（高/中/低）",
                    "examples": ["例子1", "例子2"]
                }
            ],
            "learning_suggestions": [
                {
                    "priority": "優先級（高/中/低）",
                    "focus_area": "需要加強的領域",
                    "specific_advice": "具體的學習建議",
                    "resources": ["建議的學習資源或方法"]
                }
            ],
            "overall_assessment": "整體評估和鼓勵的話"
        }
        """

        user_prompt = f"以下是學生最近的錯誤記錄：\n{json.dumps(recent_mistakes, ensure_ascii=False, indent=2)}"

        return self.call_llm(system_prompt, user_prompt)

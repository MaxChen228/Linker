"""
AI 服務模組

負責處理與 Google Gemini API 的所有互動，包括：
- 初始化 Gemini 模型
- 封裝模型調用邏輯
- 批改使用者翻譯
- 生成新的練習題
- 生成複習題
- 根據標籤生成題目
- 分析常見錯誤
"""

import asyncio
import contextlib
import json
import os
import time
from typing import Any, Optional

from core.log_config import get_module_logger


class AIService:
    """
    AI 服務類，封裝了對 Gemini API 的調用。

    提供兩種模型：
    - generate_model: 用於生成題目，設定較高的 temperature 以增加創意。
    - grade_model: 用於批改，設定較低的 temperature 以確保一致性和準確性。
    """

    def __init__(self):
        """初始化 AI 服務，載入 API 金鑰並設定模型。"""
        self.logger = get_module_logger(__name__)
        self.api_key = os.getenv("GEMINI_API_KEY")
        # 模型名稱可由環境變數覆蓋，提供靈活性
        self.generate_model_name = os.getenv("GEMINI_GENERATE_MODEL", "gemini-2.5-flash")
        self.grade_model_name = os.getenv("GEMINI_GRADE_MODEL", "gemini-2.5-pro")
        self.generate_model = None
        self.grade_model = None
        self._init_gemini()
        # 儲存最近的 LLM 互動記錄，方便調試
        self.last_llm_interaction = None

    def _init_gemini(self):
        """
        初始化 Gemini API。
        如果沒有 API 金鑰，將以 fallback 模式運行。
        """
        try:
            if not self.api_key:
                self.logger.warning(
                    "GEMINI_API_KEY 環境變數未設置，AI 服務將以 fallback 模式運行。"
                )
                return

            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            # 出題模型（快速且有創意）
            self.generate_model = genai.GenerativeModel(
                self.generate_model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=1.0,  # 提高溫度以增加創意和變化
                    top_p=0.95,
                    top_k=40,
                ),
            )
            # 批改模型（高品質且穩定）
            self.grade_model = genai.GenerativeModel(
                self.grade_model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2,  # 較低溫度確保批改一致性
                    top_p=0.9,
                ),
            )
            self.logger.info("Gemini API 初始化成功。")
        except ImportError:
            self.logger.error(
                "缺少 google-generativeai 套件，請執行: pip install google-generativeai"
            )
            raise
        except Exception as e:
            self.logger.error(f"Gemini 初始化失敗: {e}")
            raise

    def _call_model(
        self, model, system_prompt: str, user_prompt: str, use_cache: bool = True, timeout: int = 30
    ) -> dict[str, Any]:
        """
        內部方法，用於調用指定的 Gemini 模型。

        Args:
            model: 要調用的 Gemini 模型實例。
            system_prompt: 系統提示詞。
            user_prompt: 使用者提示詞。
            use_cache: 是否使用快取（目前已禁用）。
            timeout: API 調用超時時間（秒），預設 30 秒。

        Returns:
            一個包含模型回應的字典。
        """
        start_time = time.time()

        try:
            import google.generativeai as genai
            from google.api_core import retry
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            # 🔧 修復：安全地獲取模型配置信息
            model_config = {
                "model_name": getattr(model, "model_name", str(model)),
                "temperature": getattr(getattr(model, "generation_config", None), "temperature", None),
                "top_p": getattr(getattr(model, "generation_config", None), "top_p", None),
                "top_k": getattr(getattr(model, "generation_config", None), "top_k", None),
            }

            # 🔧 修復：添加超時和重試機制
            request_options = genai.types.RequestOptions(
                timeout=timeout,  # 設置超時時間
                retry=retry.Retry(
                    initial=1.0,        # 初始重試延遲 1 秒
                    maximum=3.0,        # 最大重試延遲 3 秒  
                    multiplier=1.5,     # 重試延遲倍增係數
                    deadline=timeout,   # 總體超時時間
                    predicate=retry.if_transient_error  # 只重試暫時性錯誤
                )
            )

            response = model.generate_content(full_prompt, request_options=request_options)
            duration_ms = int((time.time() - start_time) * 1000)
            result = self._parse_response(response.text)

            # 記錄詳細的互動資訊以供調試
            self.last_llm_interaction = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_ms": duration_ms,
                "model_config": model_config,
                "input": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "full_prompt": full_prompt,
                    "prompt_length": len(full_prompt),
                },
                "output": {
                    "raw_response": response.text,
                    "parsed_result": result,
                    "response_length": len(response.text),
                },
                "status": "success",
            }

            # 記錄 API 調用日誌
            with contextlib.suppress(Exception):
                self.logger.log_api_call(
                    api_name="gemini",
                    method="generate_content",
                    params={"prompt_preview": full_prompt[:200]},
                    response={k: result.get(k) for k in list(result.keys())[:3]}
                    if isinstance(result, dict)
                    else None,
                )

            return result

        except Exception as e:
            # 記錄失敗的互動資訊
            self.last_llm_interaction = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_ms": int((time.time() - start_time) * 1000),
                "model_config": locals().get("model_config", {}),
                "input": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "full_prompt": f"{system_prompt}\n\n{user_prompt}",
                    "prompt_length": len(f"{system_prompt}\n\n{user_prompt}"),
                },
                "output": {"error": str(e), "error_type": type(e).__name__},
                "status": "error",
            }
            self.logger.log_api_call(
                api_name="gemini",
                method="generate_content",
                params={"prompt_preview": (system_prompt + user_prompt)[:200]},
                error=e,
            )
            return self._get_fallback_response()

    def _parse_response(self, text: str) -> dict[str, Any]:
        """
        解析模型的 JSON 回應。
        如果直接解析失敗，會嘗試從文本中提取 JSON 結構。

        Args:
            text: 模型返回的原始文本。

        Returns:
            解析後的字典。

        Raises:
            ValueError: 如果無法解析 JSON。
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            import re

            match = re.search(r"\{{.*\}}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass  # 如果提取的部分仍然無法解析，則拋出原始錯誤
            raise ValueError("無法從 AI 回應中解析 JSON") from e

    def _get_fallback_response(self) -> dict[str, Any]:
        """
        在 AI 服務失敗時，提供一個統一的備用回應。

        Returns:
            一個包含錯誤標記的字典。
        """
        return {
            "is_generally_correct": False,
            "overall_suggestion": "AI 服務暫時不可用，請稍後再試。",
            "error_analysis": [],
            "service_error": True,  # 新增標記，方便後端識別服務錯誤
        }

    def health_check(self) -> dict[str, Any]:
        """
        🔥 透明化改造：AI 服務健康檢查
        
        真實檢測 AI 服務的可用性，不說謊！
        
        Returns:
            包含服務健康狀況的詳細報告
        """
        health_status = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "service_name": "AI Service (Gemini)",
            "status": "unknown",
            "details": {},
            "last_error": None,
            "recommendations": []
        }
        
        try:
            # 檢查模型是否已初始化
            if not self.generate_model:
                health_status.update({
                    "status": "unavailable",
                    "details": {"reason": "generate_model_not_initialized"},
                    "last_error": "Gemini API 未正確初始化",
                    "recommendations": ["檢查 GEMINI_API_KEY 環境變數", "重啟服務"]
                })
                return health_status
            
            # 進行實際的 API 測試調用
            test_prompt = "簡單測試：回答 'OK'"
            start_time = time.time()
            
            # 🔧 修復：健康檢查使用較短的超時時間
            import google.generativeai as genai
            from google.api_core import retry
            
            request_options = genai.types.RequestOptions(
                timeout=10,  # 健康檢查只給 10 秒超時
                retry=retry.Retry(
                    initial=0.5,
                    maximum=2.0,
                    multiplier=1.5,
                    deadline=10,
                    predicate=retry.if_transient_error
                )
            )
            
            response = self.generate_model.generate_content(test_prompt, request_options=request_options)
            duration_ms = int((time.time() - start_time) * 1000)
            
            if response and response.text:
                health_status.update({
                    "status": "healthy",
                    "details": {
                        "response_time_ms": duration_ms,
                        "model_accessible": True,
                        "api_responsive": True,
                        "test_response_length": len(response.text)
                    },
                    "recommendations": ["服務運行正常"] if duration_ms < 5000 else ["響應時間較慢，建議檢查網路連接"]
                })
            else:
                health_status.update({
                    "status": "degraded",
                    "details": {"reason": "empty_response"},
                    "last_error": "API 回應為空",
                    "recommendations": ["檢查 API 配額", "檢查網路連接"]
                })
                
        except Exception as e:
            health_status.update({
                "status": "failed",
                "details": {"reason": "api_call_failed", "error_type": type(e).__name__},
                "last_error": str(e),
                "recommendations": ["檢查 API Key 是否有效", "檢查網路連接", "檢查 API 配額"]
            })
            
        return health_status

    async def generate_async(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 3000,
        model: Optional[Any] = None,
    ) -> str:
        """
        異步生成內容。
        此方法使用執行緒池在背景執行同步的 `generate_content` 方法，以避免阻塞事件循環。

        Args:
            prompt: 完整的提示詞。
            temperature: 生成的溫度。
            max_tokens: 最大 token 數。
            model: 要使用的模型，如果未提供，則使用預設的生成模型。

        Returns:
            模型生成的文本內容。
        """
        loop = asyncio.get_event_loop()
        target_model = model or self.generate_model

        def _generate():
            try:
                import google.generativeai as genai

                target_model.generation_config = genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.95,
                    top_k=40,
                )
                response = target_model.generate_content(prompt)
                return response.text
            except Exception as e:
                self.logger.error(f"異步生成失敗: {e}")
                raise

        return await loop.run_in_executor(None, _generate)

    def grade_translation(
        self, chinese: str, english: str, hint: Optional[str] = None
    ) -> dict[str, Any]:
        """
        批改學生的翻譯。
        使用詳細的系統提示詞指導模型進行多維度分析，並以結構化的 JSON 格式回傳。

        Args:
            chinese: 中文原句。
            english: 學生的英文翻譯。
            hint: 翻譯提示。

        Returns:
            包含批改結果的字典。
        """
        system_prompt = f"""
        你是一位專業的英文教師，請批改學生的翻譯。

        中文原句：{chinese}
        {"提示：" + hint if hint else ""}

        請以 JSON 格式回覆，包含以下欄位：

        1. is_generally_correct (boolean): 翻譯是否基本正確。

        2. overall_suggestion (string): 建議的最佳翻譯（完整句子，使用英文）。

        3. error_analysis (array): 錯誤分析列表，每個錯誤包含：
           - category (string): 錯誤分類代碼，必須是以下其中一種：
             * \"systematic\" - 系統性錯誤：涉及文法規則，學會規則後可避免同類錯誤（如時態、主謂一致、動詞變化）。
             * \"isolated\" - 單一性錯誤：需要個別記憶的內容（如特定詞彙、搭配詞、介係詞、拼寫）。
             * \"enhancement\" - 可以更好：文法正確但表達可以更自然、更道地。
             * \"other\" - 其他錯誤：不屬於上述類別的錯誤（如漏譯、理解錯誤）。

           - key_point_summary (string): 錯誤重點的具體描述，格式為「錯誤類型: 具體錯誤內容」。
             例如：「單字拼寫錯誤: irrevertable」、「時態錯誤: have → has」、「介系詞搭配: in → on」。
             這樣可以區分不同的具體錯誤，避免把不相關的錯誤歸在一起（使用繁體中文）。

           - original_phrase (string): 學生寫錯的片語或句子部分。

           - correction (string): 正確的寫法。

           - explanation (string): 詳細解釋為什麼錯了，以及正確的用法（使用繁體中文）。

           - severity (string): 嚴重程度，"major"（重要錯誤）或 "minor"（次要問題）。

        分類原則：
        - 如果錯誤涉及可以通過學習規則解決的文法問題，使用 \"systematic\"。
        - 如果錯誤需要記憶特定用法或單字，使用 \"isolated\"。
        - 如果翻譯正確但可以更自然，使用 \"enhancement\"（通常是 minor）。
        - 其他情況使用 \"other\"。

        重要：
        - 請確保 category 欄位完全匹配上述四個代碼之一。
        - 每個錯誤都要有清楚的 explanation。
        - overall_suggestion 必須是完整、正確的英文句子。
        """
        user_prompt = f"學生的翻譯：「{english}」"

        if not self.grade_model:
            return self._get_fallback_response()

        result = self._call_model(self.grade_model, system_prompt, user_prompt, timeout=20)

        # 確保返回的結果是字典
        if not isinstance(result, dict):
            return self._get_fallback_response()

        return result

    def generate_practice_sentence(
        self,
        level: int = 1,
        length: str = "short",
        examples: Optional[list[str]] = None,
        shuffle: bool = False,
    ) -> dict[str, str]:
        """
        生成新的練習句子。
        使用 few-shot context（examples）和詳細的提示詞來引導模型生成高品質的題目。

        Args:
            level: 難度等級 (1-5)。
            length: 句子長度 ("short", "medium", "long")。
            examples: 用於 few-shot learning 的例句。
            shuffle: 是否強制生成新句子（目前預設強制）。

        Returns:
            包含中文句子、提示、難度等級等資訊的字典。
        """
        difficulty_map = {
            1: "國中基礎程度，簡單詞彙和基本句型",
            2: "高中程度，包含常見片語和複雜句型",
            3: "學測程度，包含進階詞彙和複雜語法",
            4: "指考程度，包含高階詞彙和複雜結構",
            5: "進階程度，包含學術或專業用語",
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
        1. 句子要自然、實用、符合日常對話或寫作情境。
        2. 長度適中（10-30字）。
        3. 包含明確的語法重點或常見表達。
        4. 避免過於文言或罕見的表達方式。
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
        import time as _t

        user_prompt = f"請生成一個適合練習的中文句子\n[variant_nonce={int(_t.time() * 1000)} ]"

        if not self.generate_model:
            result = {}
        else:
            result = self._call_model(
                self.generate_model, system_prompt, user_prompt, use_cache=False, timeout=25
            )

        if not isinstance(result, dict):
            result = {}

        # 🔥 透明化改造：不再隱藏服務錯誤！
        if result.get("service_error"):
            # AI 服務失敗，直接返回錯誤狀態，不要欺騙上層！
            return {
                "service_error": True,
                "error_message": "AI 服務不可用",
                "sentence": None,
                "hint": None,
            }

        # 只有真正成功時才返回內容
        import random as _r
        fallback_sentence = _r.choice(examples) if examples else "今天天氣很好。"
        return {
            "sentence": result.get("sentence", fallback_sentence),
            "hint": result.get("hint", "注意時態和主詞"),
            "difficulty_level": result.get("difficulty_level", level),
            "grammar_points": result.get("grammar_points", []),
            "service_error": False,  # 明確標記這是成功狀態
        }

    def generate_review_sentence(
        self,
        knowledge_points: list,
        level: int = 2,
        length: str = "medium",
    ) -> dict[str, Any]:
        """
        根據待複習的知識點生成複習句子。

        Args:
            knowledge_points: 待複習的知識點列表。
            level: 難度等級。
            length: 句子長度。

        Returns:
            包含複習句子、提示、目標知識點ID等資訊的字典。
        """
        import random

        if not knowledge_points:
            return self.generate_practice_sentence(level=level, length=length)

        num_points = 2 if length == "long" else 1
        length_hint = "較長句子（35-60字）" if length == "long" else "中等長度（20-35字）"

        candidates = knowledge_points[:5]
        selected_points = random.sample(candidates, min(len(candidates), num_points))

        points_info = [
            {
                "id": getattr(p, "id", p.get("id")),
                "key_point": getattr(p, "key_point", p.get("key_point")),
                "explanation": getattr(p, "explanation", p.get("explanation")),
                "original_phrase": getattr(p, "original_phrase", p.get("original_phrase")),
                "correction": getattr(p, "correction", p.get("correction")),
            }
            for p in selected_points
        ]

        self.logger.info(f"為複習環節選取了 {len(selected_points)} 個知識點。")

        system_prompt = f"""
        你是一位專業的英文教師，正在幫助學生複習。
        請使用以下知識點設計一個{length_hint}的中文句子讓學生翻譯：
        {json.dumps(points_info, ensure_ascii=False, indent=2)}

        要求：
        - 必須考察到所有提供的知識點。
        - 句子要自然、實用，不要生硬堆砌。
        - 確保錯誤點能在翻譯中被自然考察到。

        請以 JSON 格式回覆：
        {{
            "sentence": "要翻譯的中文句子",
            "hint": "給學生的提示（簡潔指出要注意什麼）",
            "target_point_ids": {[p["id"] for p in points_info]},
            "target_points_description": "本題考察：{", ".join([p["key_point"] for p in points_info])}",
            "difficulty_level": {level}
        }}
        """
        user_prompt = "請設計一個複習句子，要有創意且每次都不同。"

        if not self.generate_model:
            return {
                "sentence": "今天天氣很好。",
                "hint": "注意時態",
                "target_point_ids": [],
                "difficulty_level": level,
            }

        result = self._call_model(self.generate_model, system_prompt, user_prompt, use_cache=False, timeout=30)
        
        # 🔥 透明化改造：Review 模式的 AI 服務層也要檢查錯誤！
        if result.get("service_error"):
            return {
                "service_error": True,
                "error_message": "AI 服務不可用",
                "sentence": None,
                "hint": None,
                "target_point_ids": [],
                "target_points": [],
                "target_points_description": "",
            }
        
        if not isinstance(result, dict):
            result = {}

        target_points = [
            {
                "id": getattr(p, "id", p.get("id")),
                "key_point": getattr(p, "key_point", p.get("key_point")),
                "category": getattr(p, "category", {}).get("value", "other"),
                "mastery_level": round(getattr(p, "mastery_level", 0.0), 2),
            }
            for p in selected_points
        ]

        return {
            "sentence": result.get("sentence", "今天天氣很好。"),
            "hint": result.get("hint", "注意之前的錯誤"),
            "target_point_ids": [p["id"] for p in points_info],
            "target_points": target_points,
            "target_points_description": result.get("target_points_description", ""),
            "difficulty_level": result.get("difficulty_level", level),
            "is_review": True,
            "service_error": False,  # 明確標記成功狀態
        }

    def generate_tagged_sentence(
        self,
        tags: list[dict[str, str]],
        level: int = 2,
        length: str = "medium",
        combination_mode: str = "all",
    ) -> dict[str, Any]:
        """
        基於標籤生成練習題目。

        Args:
            tags: 標籤列表，例如 [{"type": "grammar", "id": "GP001", "name": "強調句"}]。
            level: 難度等級。
            length: 句子長度。
            combination_mode: 標籤組合模式 ("all", "any", "focus")。

        Returns:
            包含題目、提示、覆蓋點等資訊的字典。
        """
        import json

        from core.tag_system import tag_manager

        if not tags:
            return self.generate_practice_sentence(level=level, length=length)

        tag_details = []
        for tag_info in tags:
            tag_id = tag_info.get("id")
            if (
                tag_id
                and tag_manager.get_tag(tag_id)
                and (pattern := tag_manager.patterns_data.get(tag_id))
            ):
                tag_details.append(
                    {
                        "id": tag_id,
                        "pattern": pattern.get("pattern", ""),
                        "formula": pattern.get("formula", ""),
                        "core_concept": pattern.get("core_concept", ""),
                        "examples": pattern.get("examples", [])[:2],
                    }
                )

        if not tag_details:
            return self.generate_practice_sentence(level=level, length=length)

        length_hint = {
            "short": "簡短句子（10-20字）",
            "medium": "中等長度（20-35字）",
            "long": "較長句子（35-60字）",
        }.get(length, "中等長度")
        mode_instruction = {
            "all": "必須同時包含並正確展示所有列出的文法句型",
            "any": "選擇其中一個或多個文法句型來構建句子",
            "focus": "以第一個文法句型為主，其他可選擇性加入",
        }.get(combination_mode, "包含所有文法句型")

        system_prompt = f"""
        你是專業的英文教師，請設計一個翻譯練習題目。
        要求使用的文法句型：
        {json.dumps(tag_details, ensure_ascii=False, indent=2)}
        組合要求：{mode_instruction}
        題目要求：
        1. 設計一個{length_hint}的中文句子。
        2. 難度等級：{level}/5。
        3. 必須自然地融入指定的文法句型。
        4. 句子要實用、貼近生活或工作場景。
        5. 避免生硬堆砌，確保語意流暢。
        請以 JSON 格式回覆：
        {{
            "sentence": "要翻譯的中文句子",
            "hint": "給學生的提示（簡潔指出要注意的文法重點）",
            "covered_points": ["實際使用的文法點1", "實際使用的文法點2"],
            "expected_patterns": ["預期使用的句型結構"],
            "difficulty_level": {level}
        }}
        """
        user_prompt = "請設計一個包含指定文法句型的練習題目。"

        if not self.generate_model:
            return {
                "sentence": "今天天氣很好。",
                "hint": "注意句型結構",
                "covered_points": [],
                "difficulty_level": level,
            }

        result = self._call_model(self.generate_model, system_prompt, user_prompt, use_cache=False, timeout=35)
        if not isinstance(result, dict):
            result = {}

        return {
            "sentence": result.get("sentence", "今天天氣很好。"),
            "hint": result.get("hint", "注意文法句型的正確使用"),
            "covered_points": result.get("covered_points", []),
            "expected_patterns": result.get("expected_patterns", []),
            "tags": tags,
            "combination_mode": combination_mode,
            "difficulty_level": result.get("difficulty_level", level),
            "is_tagged": True,
        }

    def generate_tagged_preview(
        self,
        tags: list[str],
        combination_mode: str = "all",
    ) -> dict[str, Any]:
        """
        生成標籤組合的預覽題目，並評估其難度和變化性。

        Args:
            tags: 標籤ID列表。
            combination_mode: 組合模式。

        Returns:
            包含預覽題目和評估分數的字典。
        """
        tag_list = [{"type": "grammar", "id": tag_id} for tag_id in tags]
        result = self.generate_tagged_sentence(
            tags=tag_list, level=2, length="medium", combination_mode=combination_mode
        )

        from core.tag_system import tag_manager

        complexity_scores = [
            tag.complexity for tag_id in tags if (tag := tag_manager.get_tag(tag_id))
        ]
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 2
        variety_score = min(100, len(tags) * 30)

        if not isinstance(result, dict):
            result = {"sentence": "今天天氣很好。", "hint": "注意句型結構"}

        result["difficulty"] = min(5, max(1, round(avg_complexity)))
        result["variety_score"] = variety_score
        return result

    def get_last_interaction(self) -> dict[str, Any]:
        """
        獲取最近一次與 LLM 的互動記錄，用於調試。

        Returns:
            一個包含互動詳情的字典，如果沒有記錄則返回提示訊息。
        """
        return self.last_llm_interaction or {"status": "no_data", "message": "尚無 LLM 互動記錄"}

    def analyze_common_mistakes(self, practice_history: list) -> dict[str, Any]:
        """
        分析最近的練習歷史，找出常見的錯誤模式並提供學習建議。

        Args:
            practice_history: 練習歷史記錄列表。

        Returns:
            包含錯誤模式分析和學習建議的字典。
        """
        if not practice_history:
            return {"patterns": [], "suggestions": []}

        recent_mistakes = [
            {
                "nature": error.get("error_nature", ""),
                "key_point": error.get("key_point_summary", ""),
            }
            for practice in practice_history[-10:]
            if not practice.get("is_correct", True)
            for error in practice.get("feedback", {}).get("error_analysis", [])
        ]

        if not recent_mistakes:
            return {"patterns": [], "suggestions": []}

        system_prompt = """
        你是一位英語教學專家，請分析學生的錯誤模式並提供學習建議。
        請以 JSON 格式回覆：
        {
            "common_patterns": [{"pattern": "錯誤模式描述", "frequency": "出現頻率（高/中/低）", "examples": ["例子1", "例子2"]}],
            "learning_suggestions": [{"priority": "優先級（高/中/低）", "focus_area": "需要加強的領域", "specific_advice": "具體的學習建議", "resources": ["建議的學習資源或方法"]}],
            "overall_assessment": "整體評估和鼓勵的話"
        }
        """
        user_prompt = f"以下是學生最近的錯誤記錄：\n{json.dumps(recent_mistakes, ensure_ascii=False, indent=2)}"

        if not self.grade_model:
            return {"patterns": [], "suggestions": []}

        result = self._call_model(self.grade_model, system_prompt, user_prompt, timeout=25)
        if not isinstance(result, dict):
            return {"patterns": [], "suggestions": []}
        return result

    def generate_sentence_for_pattern(
        self,
        pattern_data: dict,
        level: int = 2,
        length: str = "medium",
    ) -> dict[str, Any]:
        """
        根據特定的文法句型生成練習題目。

        Args:
            pattern_data: 包含句型詳情的字典。
            level: 難度等級。
            length: 句子長度。

        Returns:
            包含題目、提示和預期結構的字典。
        """
        pattern_name = pattern_data.get("pattern", "")
        formula = pattern_data.get("formula", "")
        core_concept = pattern_data.get("core_concept", "")
        examples = pattern_data.get("examples", [])
        example_text = "\n".join(
            f"   例{i + 1}. {ex.get('zh', '')} → {ex.get('en', '')}"
            for i, ex in enumerate(examples[:3])
            if isinstance(ex, dict) and ex.get("zh") and ex.get("en")
        )

        length_hint = {
            "short": "簡短句子（10-20字）",
            "medium": "中等長度（20-35字）",
            "long": "較長句子（35-60字）",
        }.get(length, "中等長度")
        difficulty_hint = {
            1: "基礎程度",
            2: "中級程度",
            3: "中高級程度",
            4: "高級程度",
            5: "進階程度",
        }.get(level, "中級程度")

        system_prompt = f"""
        你是一位專業的英文教師，請根據指定的文法句型生成一個中文練習句子。
        目標句型：{pattern_name}
        句型公式：{formula}
        核心概念：{core_concept}
        參考例句：{example_text or "無"}
        要求：
        1. 生成一個{length_hint}的中文句子。
        2. 難度為{difficulty_hint}。
        3. 句子必須能夠自然地使用「{pattern_name}」句型來翻譯。
        4. 句子要實用、貼近生活或工作場景。
        5. 不要直接複製例句，要有創意。
        請以 JSON 格式回覆：
        {{
            "sentence": "要翻譯的中文句子",
            "hint": "給學生的提示（簡短說明這個句型的使用要點）",
            "expected_structure": "預期的英文句型結構（使用 ... 表示可填入的部分）"
        }}
        """
        user_prompt = "請生成一個適合練習此文法句型的中文句子。"

        if not self.generate_model:
            return {
                "sentence": "今天天氣很好。",
                "hint": f"注意使用 {pattern_name} 句型",
                "expected_structure": "",
            }

        result = self._call_model(self.generate_model, system_prompt, user_prompt, use_cache=False, timeout=30)
        
        # 🔥 透明化改造：Pattern 模式也要檢查服務錯誤！
        if result.get("service_error"):
            return {
                "service_error": True,
                "error_message": "AI 服務不可用",
                "sentence": None,
                "hint": None,
                "expected_structure": None,
            }
        
        if not isinstance(result, dict):
            result = {"sentence": "今天天氣很好。", "hint": f"注意使用 {pattern_name} 句型"}

        return {
            "sentence": result.get("sentence", "今天天氣很好。"),
            "hint": result.get("hint", f"注意使用 {pattern_name} 句型"),
            "expected_structure": result.get("expected_structure", formula),
            "service_error": False,  # 明確標記成功狀態
        }

"""
AI 服務模組 - 處理與 Gemini API 的互動
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional

from core.log_config import get_module_logger


class AIService:
    """AI 服務類 - 封裝 Gemini API 調用"""

    def __init__(self):
        self.logger = get_module_logger(__name__)  # 先初始化 logger
        self.api_key = os.getenv("GEMINI_API_KEY")
        # 模型名稱可由環境變數覆蓋
        self.generate_model_name = os.getenv("GEMINI_GENERATE_MODEL", "gemini-2.5-flash")
        self.grade_model_name = os.getenv("GEMINI_GRADE_MODEL", "gemini-2.5-pro")
        self.generate_model = None
        self.grade_model = None
        # self.cache = {}  # 完全禁用快取
        self._init_gemini()
        # 儲存最近的 LLM 互動記錄（用於調試）
        self.last_llm_interaction = None

    def _init_gemini(self):
        """初始化 Gemini"""
        try:
            if not self.api_key:
                self.logger.warning("GEMINI_API_KEY 環境變數未設置，AI 服務將使用 fallback 模式")
                return
            
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            # 出題模型（快速）- 提高溫度增加變化性
            self.generate_model = genai.GenerativeModel(
                self.generate_model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=1.0,  # 提高溫度以增加創意和變化
                    top_p=0.95,
                    top_k=40,  # 增加候選token數量
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
            self.logger.info("Gemini API 初始化成功")
        except ImportError:
            self.logger.error("請安裝 google-generativeai: pip install google-generativeai")
            raise
        except Exception as e:
            self.logger.error(f"Gemini 初始化失敗: {e}")
            raise

    def _call_model(self, model, system_prompt: str, user_prompt: str, use_cache: bool = True) -> dict[str, Any]:
        """調用指定模型的 LLM API"""
        start_time = time.time()

        try:
            # 組合提示詞
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # 取得模型配置
            model_config = {
                "model_name": model.model_name if hasattr(model, 'model_name') else str(model),
                "temperature": model.generation_config.temperature if hasattr(model, 'generation_config') else None,
                "top_p": model.generation_config.top_p if hasattr(model, 'generation_config') else None,
                "top_k": model.generation_config.top_k if hasattr(model, 'generation_config') else None,
            }

            # 調用 API
            response = model.generate_content(full_prompt)

            # 計算耗時
            duration_ms = int((time.time() - start_time) * 1000)

            # 解析 JSON 回應
            result = self._parse_response(response.text)

            # 儲存調試資料
            self.last_llm_interaction = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_ms": duration_ms,
                "model_config": model_config,
                "input": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "full_prompt": full_prompt,
                    "prompt_length": len(full_prompt)
                },
                "output": {
                    "raw_response": response.text,
                    "parsed_result": result,
                    "response_length": len(response.text)
                },
                "status": "success"
            }

            # 完全禁用快取儲存
            # if use_cache:
            #     self.cache[cache_key] = {"data": result, "time": time.time()}

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
            # 儲存錯誤調試資料
            self.last_llm_interaction = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_ms": int((time.time() - start_time) * 1000),
                "model_config": model_config if 'model_config' in locals() else {},
                "input": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "full_prompt": f"{system_prompt}\n\n{user_prompt}",
                    "prompt_length": len(f"{system_prompt}\n\n{user_prompt}")
                },
                "output": {
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                "status": "error"
            }

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

    async def generate_async(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 3000,
        model: Optional[Any] = None
    ) -> str:
        """異步生成內容"""
        # 使用 asyncio 在後台執行同步方法
        loop = asyncio.get_event_loop()

        # 準備完整的 prompt
        full_prompt = prompt

        # 使用指定的模型或預設生成模型
        if model is None:
            model = self.generate_model

        # 在執行緒池中執行同步方法
        def _generate():
            try:
                # 更新生成配置
                import google.generativeai as genai
                model.generation_config = genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.95,
                    top_k=40,
                )

                response = model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                self.logger.error(f"Async generation failed: {e}")
                raise

        # 在執行緒池中執行
        result = await loop.run_in_executor(None, _generate)
        return result

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
           - category (string): 錯誤分類代碼，必須是以下其中一種：
             * "systematic" - 系統性錯誤：涉及文法規則，學會規則後可避免同類錯誤（如時態、主謂一致、動詞變化）
             * "isolated" - 單一性錯誤：需要個別記憶的內容（如特定詞彙、搭配詞、介係詞、拼寫）
             * "enhancement" - 可以更好：文法正確但表達可以更自然、更道地
             * "other" - 其他錯誤：不屬於上述類別的錯誤（如漏譯、理解錯誤）
           
           - key_point_summary (string): 錯誤重點的簡潔描述（使用繁體中文）
           
           - original_phrase (string): 學生寫錯的片語或句子部分
           
           - correction (string): 正確的寫法
           
           - explanation (string): 詳細解釋為什麼錯了，以及正確的用法（使用繁體中文）
           
           - severity (string): 嚴重程度，"major"（重要錯誤）或 "minor"（次要問題）
        
        分類原則：
        - 如果錯誤涉及可以通過學習規則解決的文法問題，使用 "systematic"
        - 如果錯誤需要記憶特定用法或單字，使用 "isolated"
        - 如果翻譯正確但可以更自然，使用 "enhancement"（通常是 minor）
        - 其他情況使用 "other"
        
        重要：
        - 請確保 category 欄位完全匹配上述四個代碼之一（systematic, isolated, enhancement, other）
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
        shuffle: bool = False,
    ) -> dict[str, str]:
        """生成練習句子（使用出題模型）

        examples: 來自分級例句庫的代表例句（few-shot context），不會回傳給使用者。
        length: "short" | "medium" | "long" 影響目標字數/結構。
        shuffle: True 時禁用快取，強制生成新句子。
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
            # 永遠不使用快取，確保每次都獲得新結果
            result = self._call_model(self.generate_model, system_prompt, user_prompt, use_cache=False)

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

    def generate_review_sentence(
        self,
        knowledge_points: list,
        level: int = 2,
        length: str = "medium",
    ) -> dict[str, Any]:
        """生成複習句子（基於待複習知識點）
        
        Args:
            knowledge_points: 待複習的知識點列表
            level: 難度等級
            length: 句子長度
            
        Returns:
            包含句子、提示、考點ID等信息
        """
        import random

        if not knowledge_points:
            # 如果沒有待複習知識點，回退到普通出題
            return self.generate_practice_sentence(level=level, length=length)

        # 根據句子長度決定要選幾個知識點
        if length == "long":
            num_points = 2
            length_hint = "較長句子（35-60字）"
        else:  # short 或 medium
            num_points = 1
            length_hint = "簡短句子（10-20字）" if length == "short" else "中等長度（20-35字）"

        # 從候選知識點中隨機選擇
        candidates = knowledge_points[:5]  # 最多考慮前5個
        if len(candidates) <= num_points:
            selected_points = candidates
        else:
            selected_points = random.sample(candidates, num_points)

        # 只準備被選中的知識點信息給 AI
        points_info = []
        for point in selected_points:
            points_info.append({
                "id": getattr(point, 'id', point.get('id') if isinstance(point, dict) else None),
                "key_point": getattr(point, 'key_point', point.get('key_point') if isinstance(point, dict) else ''),
                "explanation": getattr(point, 'explanation', point.get('explanation') if isinstance(point, dict) else ''),
                "original_phrase": getattr(point, 'original_phrase', point.get('original_phrase') if isinstance(point, dict) else ''),
                "correction": getattr(point, 'correction', point.get('correction') if isinstance(point, dict) else ''),
            })

        # 記錄選中的知識點
        self.logger.info(f"Selected {len(selected_points)} knowledge points for review")

        system_prompt = f"""
        你是一位專業的英文教師，正在幫助學生複習。
        
        請使用以下知識點設計一個{length_hint}的中文句子讓學生翻譯：
        {json.dumps(points_info, ensure_ascii=False, indent=2)}
        
        要求：
        - 必須考察到所有提供的知識點
        - 句子要自然、實用，不要生硬堆砌
        - 確保錯誤點能在翻譯中被自然考察到
        
        請以 JSON 格式回覆：
        {{
            "sentence": "要翻譯的中文句子",
            "hint": "給學生的提示（簡潔指出要注意什麼）",
            "target_point_ids": {[point['id'] for point in points_info]},
            "target_points_description": "本題考察：{', '.join([p['key_point'] for p in points_info])}",
            "difficulty_level": {level}
        }}
        """

        user_prompt = "請設計一個複習句子，要有創意且每次都不同。"

        if not self.generate_model:
            # Fallback
            return {
                "sentence": "今天天氣很好。",
                "hint": "注意時態",
                "target_point_ids": [],
                "difficulty_level": level
            }

        result = self._call_model(self.generate_model, system_prompt, user_prompt, use_cache=False)

        # 處理返回結果
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        elif not isinstance(result, dict):
            result = {}

        # 使用已選中的知識點信息（不需要再從 AI 回應中找）
        target_points = []
        for point in selected_points:
            # 安全地獲取屬性
            point_id = getattr(point, 'id', point.get('id') if isinstance(point, dict) else None)
            key_point = getattr(point, 'key_point', point.get('key_point') if isinstance(point, dict) else '')
            mastery_level = getattr(point, 'mastery_level', point.get('mastery_level') if isinstance(point, dict) else 0.0)
            
            # 處理 category 屬性（可能是枚舉或字串）
            category = getattr(point, 'category', point.get('category') if isinstance(point, dict) else 'other')
            if hasattr(category, 'value'):
                category = category.value
            else:
                category = str(category)
            
            target_points.append({
                "id": point_id,
                "key_point": key_point,
                "category": category,
                "mastery_level": round(mastery_level, 2)
            })

        return {
            "sentence": result.get("sentence", "今天天氣很好。"),
            "hint": result.get("hint", "注意之前的錯誤"),
            "target_point_ids": [getattr(p, 'id', p.get('id') if isinstance(p, dict) else None) for p in selected_points],  # 使用實際選中的點
            "target_points": target_points,  # 完整知識點信息
            "target_points_description": result.get("target_points_description", ""),
            "difficulty_level": result.get("difficulty_level", level),
            "is_review": True  # 標記為複習題
        }

    def generate_tagged_sentence(
        self,
        tags: List[Dict[str, str]],
        level: int = 2,
        length: str = "medium",
        combination_mode: str = "all"
    ) -> dict[str, Any]:
        """基於標籤生成題目
        
        Args:
            tags: 標籤列表 [{"type": "grammar", "id": "GP001", "name": "強調句"}]
            level: 難度等級
            length: 句子長度
            combination_mode: 組合模式 (all/any/focus)
            
        Returns:
            包含句子、提示、覆蓋點等信息
        """
        import json
        from core.tag_system import tag_manager
        
        if not tags:
            return self.generate_practice_sentence(level=level, length=length)
        
        # 載入標籤詳細信息
        tag_details = []
        for tag_info in tags:
            tag_id = tag_info.get("id")
            tag = tag_manager.get_tag(tag_id)
            if tag and tag_id in tag_manager.patterns_data:
                pattern = tag_manager.patterns_data[tag_id]
                tag_details.append({
                    "id": tag_id,
                    "pattern": pattern.get("pattern", ""),
                    "formula": pattern.get("formula", ""),
                    "core_concept": pattern.get("core_concept", ""),
                    "examples": pattern.get("examples", [])[:2]  # 只取前2個例句
                })
        
        if not tag_details:
            return self.generate_practice_sentence(level=level, length=length)
        
        # 根據句子長度調整
        length_hint = {
            "short": "簡短句子（10-20字）",
            "medium": "中等長度（20-35字）",
            "long": "較長句子（35-60字）"
        }.get(length, "中等長度")
        
        # 構建智能 Prompt
        mode_instruction = {
            "all": "必須同時包含並正確展示所有列出的文法句型",
            "any": "選擇其中一個或多個文法句型來構建句子",
            "focus": "以第一個文法句型為主，其他可選擇性加入"
        }.get(combination_mode, "包含所有文法句型")
        
        system_prompt = f"""
        你是專業的英文教師，請設計一個翻譯練習題目。
        
        要求使用的文法句型：
        {json.dumps(tag_details, ensure_ascii=False, indent=2)}
        
        組合要求：{mode_instruction}
        
        題目要求：
        1. 設計一個{length_hint}的中文句子
        2. 難度等級：{level}/5
        3. 必須自然地融入指定的文法句型
        4. 句子要實用、貼近生活或工作場景
        5. 避免生硬堆砌，確保語意流暢
        
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
                "difficulty_level": level
            }
        
        result = self._call_model(self.generate_model, system_prompt, user_prompt, use_cache=False)
        
        # 處理結果
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        elif not isinstance(result, dict):
            result = {}
        
        return {
            "sentence": result.get("sentence", "今天天氣很好。"),
            "hint": result.get("hint", "注意文法句型的正確使用"),
            "covered_points": result.get("covered_points", []),
            "expected_patterns": result.get("expected_patterns", []),
            "tags": tags,
            "combination_mode": combination_mode,
            "difficulty_level": result.get("difficulty_level", level),
            "is_tagged": True
        }
    
    def generate_tagged_preview(
        self,
        tags: List[str],
        combination_mode: str = "all"
    ) -> dict[str, Any]:
        """生成標籤組合的預覽題目"""
        # 轉換標籤格式
        tag_list = [{"type": "grammar", "id": tag_id} for tag_id in tags]
        
        # 生成一個範例題目
        result = self.generate_tagged_sentence(
            tags=tag_list,
            level=2,
            length="medium",
            combination_mode=combination_mode
        )
        
        # 計算難度和變化性
        from core.tag_system import tag_manager
        complexity_scores = []
        for tag_id in tags:
            tag = tag_manager.get_tag(tag_id)
            if tag:
                complexity_scores.append(tag.complexity)
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 2
        variety_score = min(100, len(tags) * 30)  # 每個標籤增加30%變化性
        
        result["difficulty"] = min(5, max(1, round(avg_complexity)))
        result["variety_score"] = variety_score
        
        return result

    def get_last_interaction(self) -> dict[str, Any]:
        """獲取最近一次的 LLM 互動記錄"""
        return self.last_llm_interaction if self.last_llm_interaction else {
            "status": "no_data",
            "message": "尚無 LLM 互動記錄"
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

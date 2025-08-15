"""
嚴格的 API 輸入驗證模型

所有 API 端點都應使用這些模型進行輸入驗證，防止注入攻擊和資料損毀。
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class GradeAnswerRequest(BaseModel):
    """批改答案請求驗證模型"""

    chinese: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="中文句子",
        example="為了實現目標，她必須全力以赴。",
    )
    english: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="英文翻譯",
        example="To achieve her goal, she has to give it her all.",
    )
    mode: str = Field(default="new", pattern="^(new|review)$", description="練習模式")
    target_point_ids: List[int] = Field(
        default_factory=list, max_items=50, description="目標知識點ID列表"
    )

    @field_validator("target_point_ids")
    @classmethod
    def validate_point_ids(cls, v):
        """驗證知識點ID"""
        if v is None:
            return []

        # 檢查每個ID是否為正整數
        for point_id in v:
            if not isinstance(point_id, int) or point_id <= 0:
                raise ValueError(f"無效的知識點ID: {point_id}")

        return v

    @field_validator("chinese", "english")
    @classmethod
    def validate_text_content(cls, v):
        """驗證文本內容安全性"""
        if not v or not v.strip():
            raise ValueError("文本內容不能為空")

        # 防止基本的注入攻擊
        dangerous_patterns = ["<script", "javascript:", "data:", "vbscript:"]
        v_lower = v.lower()

        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"文本包含不安全內容: {pattern}")

        return v.strip()


class GenerateQuestionRequest(BaseModel):
    """生成問題請求驗證模型"""

    mode: str = Field(default="new", pattern="^(new|review|pattern)$", description="生成模式")
    length: str = Field(default="short", pattern="^(short|medium|long)$", description="句子長度")
    level: int = Field(default=1, ge=1, le=5, description="難度等級 (1-5)")
    pattern_id: Optional[int] = Field(None, ge=1, description="指定的語法模式ID")


class CompleteReviewRequest(BaseModel):
    """完成複習請求驗證模型"""

    chinese_sentence: str = Field(..., min_length=1, max_length=1000, description="複習的中文句子")
    user_answer: str = Field(..., min_length=1, max_length=2000, description="用戶答案")

    @field_validator("chinese_sentence", "user_answer")
    @classmethod
    def validate_review_content(cls, v):
        """驗證複習內容安全性"""
        if not v or not v.strip():
            raise ValueError("內容不能為空")

        # 基本安全檢查
        dangerous_patterns = ["<script", "javascript:", "data:", "vbscript:", "onclick", "onerror"]
        v_lower = v.lower()

        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"內容包含不安全字符: {pattern}")

        return v.strip()


class EnhancedEditKnowledgeRequest(BaseModel):
    """增強的編輯知識點請求驗證模型"""

    key_point: Optional[str] = Field(None, max_length=500, description="知識點標題")
    explanation: Optional[str] = Field(None, max_length=2000, description="解釋說明")
    original_phrase: Optional[str] = Field(None, max_length=500, description="原始短語")
    correction: Optional[str] = Field(None, max_length=500, description="修正版本")
    category: Optional[str] = Field(
        None, pattern="^(systematic|isolated|enhancement|other)$", description="錯誤分類"
    )
    subtype: Optional[str] = Field(None, max_length=100, description="子類型")
    tags: Optional[List[str]] = Field(None, max_items=20, description="標籤列表")
    custom_notes: Optional[str] = Field(None, max_length=1000, description="自定義筆記")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """驗證標籤"""
        if v is None:
            return None

        # 檢查每個標籤
        validated_tags = []
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("標籤必須是字符串")

            tag = tag.strip()
            if not tag:
                continue

            if len(tag) > 50:
                raise ValueError(f"標籤過長: {tag[:20]}...")

            # 基本安全檢查
            if any(char in tag.lower() for char in ["<", ">", '"', "'", "&"]):
                raise ValueError(f"標籤包含不安全字符: {tag}")

            validated_tags.append(tag)

        return validated_tags

    @field_validator(
        "key_point",
        "explanation",
        "original_phrase",
        "correction",
        "subtype",
        "custom_notes",
        mode="before",
    )
    @classmethod
    def validate_string_fields(cls, v):
        """對所有字符串字段進行基本安全檢查"""
        if isinstance(v, str) and v:
            # 基本 XSS 防護
            dangerous_patterns = [
                "<script",
                "</script>",
                "javascript:",
                "data:",
                "vbscript:",
                "onclick=",
                "onerror=",
                "onload=",
                "<iframe",
                "<object",
                "<embed",
            ]

            v_lower = v.lower()
            for pattern in dangerous_patterns:
                if pattern in v_lower:
                    raise ValueError("字段包含不安全內容")

        return v


class EnhancedDeleteKnowledgeRequest(BaseModel):
    """增強的刪除知識點請求驗證模型"""

    reason: str = Field(default="", max_length=500, description="刪除原因")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        """驗證刪除原因"""
        if v:
            # 基本安全檢查
            dangerous_patterns = ["<script", "javascript:", "data:"]
            v_lower = v.lower()

            for pattern in dangerous_patterns:
                if pattern in v_lower:
                    raise ValueError(f"刪除原因包含不安全內容: {pattern}")

        return v.strip() if v else ""


class EnhancedBatchRequest(BaseModel):
    """增強的批量操作請求驗證模型"""

    operation: str = Field(..., pattern="^(delete|update|restore)$", description="批量操作類型")
    ids: List[int] = Field(
        ...,
        min_items=1,
        max_items=100,  # 限制批量操作數量
        description="知識點ID列表",
    )
    data: Optional[dict] = Field(None, description="操作相關數據")

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v):
        """驗證ID列表"""
        if not v:
            raise ValueError("ID列表不能為空")

        # 檢查每個ID
        validated_ids = []
        for item_id in v:
            if not isinstance(item_id, int) or item_id <= 0:
                raise ValueError(f"無效的ID: {item_id}")
            validated_ids.append(item_id)

        # 移除重複的ID
        return list(set(validated_ids))

    @field_validator("data")
    @classmethod
    def validate_data(cls, v):
        """驗證操作數據"""
        if v is None:
            return None

        if not isinstance(v, dict):
            raise ValueError("數據必須是字典類型")

        # 限制數據大小
        if len(str(v)) > 10000:  # 10KB limit
            raise ValueError("操作數據過大")

        return v


class TagsRequest(BaseModel):
    """標籤請求驗證模型"""

    tags: List[str] = Field(..., max_items=20, description="標籤列表")

    @field_validator("tags")
    @classmethod
    def validate_tags_list(cls, v):
        """驗證標籤列表"""
        if not v:
            raise ValueError("標籤列表不能為空")

        validated_tags = []
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("標籤必須是字符串")

            tag = tag.strip()
            if not tag:
                continue

            if len(tag) > 50:
                raise ValueError(f"標籤過長: {tag[:20]}...")

            # 安全檢查
            if any(char in tag.lower() for char in ["<", ">", '"', "'", "&", "script"]):
                raise ValueError(f"標籤包含不安全字符: {tag}")

            validated_tags.append(tag)

        return validated_tags


class NotesRequest(BaseModel):
    """筆記請求驗證模型"""

    notes: str = Field(..., max_length=2000, description="筆記內容")

    @field_validator("notes")
    @classmethod
    def validate_notes_content(cls, v):
        """驗證筆記內容"""
        if not v or not v.strip():
            raise ValueError("筆記內容不能為空")

        # 安全檢查
        dangerous_patterns = [
            "<script",
            "</script>",
            "javascript:",
            "data:",
            "vbscript:",
            "onclick=",
            "onerror=",
            "onload=",
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"筆記包含不安全內容: {pattern}")

        return v.strip()


class DeleteOldPointsRequest(BaseModel):
    """刪除舊知識點請求驗證模型"""

    days_old: int = Field(
        default=30,
        ge=7,  # 至少7天
        le=365,  # 最多1年
        description="刪除多少天前的知識點",
    )
    dry_run: bool = Field(default=True, description="是否只是預覽")


# 路徑參數驗證
def validate_point_id(point_id: int) -> int:
    """驗證知識點ID路徑參數"""
    if not isinstance(point_id, int) or point_id <= 0:
        raise ValueError(f"無效的知識點ID: {point_id}")

    if point_id > 1000000:  # 合理的上限
        raise ValueError(f"知識點ID過大: {point_id}")

    return point_id


def validate_task_id(task_id: str) -> str:
    """驗證任務ID路徑參數"""
    if not task_id or not isinstance(task_id, str):
        raise ValueError("任務ID不能為空")

    task_id = task_id.strip()

    # 檢查格式 (UUID 或類似格式)
    if len(task_id) < 8 or len(task_id) > 100:
        raise ValueError("任務ID格式無效")

    # 安全字符檢查
    import re

    if not re.match(r"^[a-zA-Z0-9\-_]+$", task_id):
        raise ValueError("任務ID包含不安全字符")

    return task_id

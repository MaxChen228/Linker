# API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required. API keys for Gemini AI are configured server-side.

## Endpoints

### Practice Module

#### Generate Practice Sentence
```http
POST /api/generate
```

**Request Body:**
```json
{
  "difficulty": 1-5,
  "sentence_length": "short" | "medium" | "long",
  "mode": "new" | "review",
  "knowledge_ids": [1, 2, 3]  // Optional, for review mode
}
```

**Response:**
```json
{
  "sentence": "我今天很忙。",
  "hint": "注意時態的使用",
  "difficulty_level": 2,
  "is_review": false
}
```

#### Submit Translation
```http
POST /api/submit
```

**Request Body:**
```json
{
  "chinese_sentence": "我今天很忙。",
  "user_answer": "I am busy today.",
  "practice_mode": "new"
}
```

**Response:**
```json
{
  "is_generally_correct": true,
  "overall_suggestion": "I am very busy today.",
  "error_analysis": [
    {
      "category": "enhancement",
      "key_point_summary": "Missing intensity adverb",
      "original_phrase": "busy",
      "correction": "very busy",
      "explanation": "The Chinese '很' indicates 'very'",
      "severity": "minor"
    }
  ]
}
```

### Knowledge Management

#### Get Knowledge Points
```http
GET /api/knowledge
```

**Query Parameters:**
- `category`: Filter by error category (systematic/isolated/enhancement/other)
- `mastery_min`: Minimum mastery level (0.0-1.0)
- `mastery_max`: Maximum mastery level (0.0-1.0)
- `limit`: Number of results (default: 50)

**Response:**
```json
{
  "knowledge_points": [
    {
      "id": 1,
      "key_point": "時態錯誤: go → went",
      "category": "systematic",
      "mastery_level": 0.3,
      "mistake_count": 2,
      "correct_count": 1,
      "next_review": "2024-01-16T10:00:00"
    }
  ],
  "total": 25
}
```

#### Update Knowledge Mastery
```http
PUT /api/knowledge/{id}/mastery
```

**Request Body:**
```json
{
  "is_correct": true
}
```

**Response:**
```json
{
  "id": 1,
  "new_mastery_level": 0.45,
  "next_review": "2024-01-17T10:00:00"
}
```

### Review System

#### Get Review Queue
```http
GET /api/review/queue
```

**Response:**
```json
{
  "review_items": [
    {
      "id": 1,
      "key_point": "時態錯誤: go → went",
      "priority_score": 0.85,
      "days_overdue": 2
    }
  ],
  "total_due": 5
}
```

#### Generate Review Sentence
```http
POST /api/review/generate
```

**Request Body:**
```json
{
  "knowledge_ids": [1, 2],
  "difficulty": 3
}
```

**Response:**
```json
{
  "sentence": "他昨天去了圖書館。",
  "hint": "注意過去式動詞變化",
  "target_points": ["時態錯誤: go → went"],
  "is_review": true
}
```

### System Information

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.5.0",
  "ai_service": "connected",
  "data_version": "3.0"
}
```

#### Get LLM Interaction Log
```http
GET /api/debug/llm
```

**Response:**
```json
{
  "timestamp": "2024-01-15T12:00:00",
  "model": "gemini-2.5-flash",
  "prompt": "...",
  "response": "...",
  "duration_ms": 1500
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}  // Optional additional information
  }
}
```

Common error codes:
- `INVALID_REQUEST`: Malformed request data
- `AI_SERVICE_ERROR`: Gemini API failure
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Server error

## Rate Limiting

Currently no rate limiting implemented. For production deployment, consider adding rate limiting middleware.

## WebSocket Support

Not currently implemented. All communication is via REST API.
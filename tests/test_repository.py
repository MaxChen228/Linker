# tests/test_repository.py
from datetime import datetime

import asyncpg
import pytest

from core.database.repositories.knowledge_repository import KnowledgePointRepository
from core.knowledge import ErrorCategory, KnowledgePoint, OriginalError


@pytest.mark.asyncio
class TestKnowledgePointRepository:
    """Tests for the KnowledgePointRepository"""

    @pytest.fixture
    def repo(self, db_connection: asyncpg.Pool) -> KnowledgePointRepository:
        """Provides a repository instance for each test."""
        return KnowledgePointRepository(db_connection)

    @pytest.fixture
    def sample_point(self) -> KnowledgePoint:
        """Provides a sample KnowledgePoint object for testing."""
        return KnowledgePoint(
            id=0,  # ID will be assigned by the database
            key_point="Inversion with 'not only'",
            category=ErrorCategory.SYSTEMATIC,
            subtype="inversion",
            explanation="When 'Not only' starts a sentence, the subject and verb must be inverted.",
            original_phrase="Not only this is his duty",
            correction="Not only is this his duty",
            original_error=OriginalError(
                chinese_sentence="這不僅是他的責任，也是他的榮幸。",
                user_answer="Not only this is his duty, but also his honor.",
                correct_answer="Not only is this his duty, but it is also his honor.",
                timestamp=datetime.now().isoformat(),
            ),
            mastery_level=0.25,
            mistake_count=1,
            correct_count=0,
            tags=["grammar", "inversion"],
            next_review=datetime.now().isoformat(),
        )

    async def test_create_and_find_by_id(
        self, repo: KnowledgePointRepository, sample_point: KnowledgePoint
    ):
        """Test creating a knowledge point and retrieving it by ID."""
        # 1. Create the knowledge point
        created_point = await repo.create(sample_point)

        assert created_point is not None
        assert created_point.id > 0
        assert created_point.key_point == sample_point.key_point

        # 2. Find the knowledge point by its new ID
        found_point = await repo.find_by_id(created_point.id)

        assert found_point is not None
        assert found_point.id == created_point.id
        assert found_point.key_point == "Inversion with 'not only'"
        assert found_point.category == ErrorCategory.SYSTEMATIC
        assert found_point.mastery_level == 0.25

        # 3. Check if tags were created (this part is simplified)
        # A more complete test would query the tags table directly
        # For now, we assume the create method handles it.
        # Note: The simplified _row_to_knowledge_point in the repo doesn't fetch tags on find_by_id yet.
        # We will test this properly after implementing the full find_by_id query.

    async def test_update(self, repo: KnowledgePointRepository, sample_point: KnowledgePoint):
        """Test updating an existing knowledge point."""
        # 1. Create a point first
        created_point = await repo.create(sample_point)
        assert created_point.mastery_level == 0.25

        # 2. Update its mastery level and notes
        created_point.mastery_level = 0.50
        created_point.custom_notes = "Practiced this twice."
        updated_point = await repo.update(created_point)

        assert updated_point is not None
        assert updated_point.mastery_level == 0.50

        # 3. Retrieve from DB to confirm the change
        found_point = await repo.find_by_id(created_point.id)
        assert found_point is not None
        assert found_point.mastery_level == 0.50
        assert found_point.custom_notes == "Practiced this twice."

    async def test_soft_delete(self, repo: KnowledgePointRepository, sample_point: KnowledgePoint):
        """Test soft-deleting a knowledge point."""
        # 1. Create a point
        created_point = await repo.create(sample_point)
        point_id = created_point.id

        # 2. Soft delete it
        delete_success = await repo.delete(point_id, reason="mastered")
        assert delete_success is True

        # 3. Verify it cannot be found by normal find_by_id
        found_point = await repo.find_by_id(point_id)
        assert found_point is None

        # 4. Verify it exists in the database with is_deleted = true
        async with repo.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM knowledge_points WHERE id = $1", point_id)

        assert row is not None
        assert row["is_deleted"] is True
        assert row["deleted_reason"] == "mastered"

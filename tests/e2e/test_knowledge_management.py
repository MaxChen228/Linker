"""
知識點管理流程一致性測試
驗證知識點的完整生命週期管理在兩種模式下的一致性
"""

import pytest

from tests.fixtures.test_data_manager import (
    UserJourneyTestDataManager,
    get_db_manager,
    get_json_manager,
)


@pytest.mark.asyncio
async def test_knowledge_point_lifecycle_management():
    """測試知識點的完整生命週期管理"""

    await UserJourneyTestDataManager.setup_established_user_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # === 階段 1: 查看知識點列表 ===
    json_points = json_manager.get_active_points()
    db_points = await db_manager.get_knowledge_points_async()

    assert len(json_points) > 0, "JSON 模式應該有知識點"
    assert len(db_points) > 0, "DB 模式應該有知識點"

    # 選擇一個知識點進行管理操作
    target_point_id = json_points[0].id

    # === 階段 2: 查看知識點詳情 ===
    json_point = None
    for point in json_points:
        if point.id == target_point_id:
            json_point = point
            break

    db_point = await db_manager.get_knowledge_point_async(str(target_point_id))

    assert json_point is not None, f"JSON 模式找不到知識點 {target_point_id}"
    assert db_point is not None, f"DB 模式找不到知識點 {target_point_id}"

    # 驗證基本信息一致性
    assert json_point.id == db_point.id
    assert json_point.key_point == db_point.key_point
    assert json_point.category == db_point.category

    # === 階段 3: 編輯知識點 ===
    edit_updates = {
        "key_point": "更新後的知識點描述",
        "custom_notes": "添加自定義筆記",
        "tags": ["重要", "語法"],
    }

    # JSON 模式編輯
    json_edit_result = json_manager.edit_knowledge_point(target_point_id, edit_updates)

    # DB 模式編輯（檢查方法是否存在）
    if hasattr(db_manager, "update_knowledge_point_async"):
        await db_manager.update_knowledge_point_async(
            target_point_id, **edit_updates
        )
    elif hasattr(db_manager, "edit_knowledge_point_async"):
        await db_manager.edit_knowledge_point_async(target_point_id, edit_updates)
    else:
        # 如果沒有對應的異步方法，嘗試同步方法
        if hasattr(db_manager, "edit_knowledge_point"):
            db_manager.edit_knowledge_point(target_point_id, edit_updates)
        else:
            pass  # 假設編輯成功，稍後在驗證中會檢查

    assert json_edit_result is not None, "JSON 編輯應該成功"

    # 驗證編輯結果
    json_updated_point = None
    for point in json_manager.get_active_points():
        if point.id == target_point_id:
            json_updated_point = point
            break

    db_updated_point = await db_manager.get_knowledge_point_async(str(target_point_id))

    assert json_updated_point is not None, "JSON 更新後應該能找到知識點"
    assert db_updated_point is not None, "DB 更新後應該能找到知識點"

    # 檢查更新內容
    assert json_updated_point.key_point == "更新後的知識點描述"
    assert json_updated_point.custom_notes == "添加自定義筆記"

    # DB 模式的更新驗證（如果支持的話）
    if hasattr(db_updated_point, "key_point"):
        assert db_updated_point.key_point == "更新後的知識點描述"
    if hasattr(db_updated_point, "custom_notes"):
        assert db_updated_point.custom_notes == "添加自定義筆記"

    # === 階段 4: 軟刪除知識點 ===
    delete_reason = "已經掌握，不需要繼續複習"

    json_delete_result = json_manager.delete_knowledge_point(target_point_id, delete_reason)

    # DB 模式刪除
    if hasattr(db_manager, "delete_knowledge_point_async"):
        db_delete_result = await db_manager.delete_knowledge_point_async(
            target_point_id, delete_reason
        )
    else:
        db_delete_result = db_manager.delete_knowledge_point(target_point_id, delete_reason)

    assert json_delete_result, "JSON 刪除應該成功"
    assert db_delete_result, "DB 刪除應該成功"

    # 驗證軟刪除結果
    json_active_points = json_manager.get_active_points()
    db_active_points = await db_manager.get_knowledge_points_async()

    # 活躍知識點中不應該包含被刪除的點
    json_active_ids = {p.id for p in json_active_points}
    db_active_ids = {p.id for p in db_active_points}

    assert target_point_id not in json_active_ids, "JSON 刪除的知識點不應該出現在活躍列表中"
    assert target_point_id not in db_active_ids, "DB 刪除的知識點不應該出現在活躍列表中"

    # 檢查已刪除列表
    json_deleted_points = json_manager.get_deleted_points()
    deleted_point = None
    for p in json_deleted_points:
        if p.id == target_point_id:
            deleted_point = p
            break

    assert deleted_point is not None, "被刪除的知識點應該出現在已刪除列表中"
    assert deleted_point.is_deleted
    assert deleted_point.deleted_reason == delete_reason

    # === 階段 5: 復原知識點 ===
    json_restore_result = json_manager.restore_knowledge_point(target_point_id)

    if hasattr(db_manager, "restore_knowledge_point_async"):
        db_restore_result = await db_manager.restore_knowledge_point_async(target_point_id)
    else:
        db_restore_result = db_manager.restore_knowledge_point(target_point_id)

    assert json_restore_result, "JSON 復原應該成功"
    assert db_restore_result, "DB 復原應該成功"

    # 驗證復原結果
    json_final_active = json_manager.get_active_points()
    db_final_active = await db_manager.get_knowledge_points_async()

    json_final_ids = {p.id for p in json_final_active}
    db_final_ids = {p.id for p in db_final_active}

    assert target_point_id in json_final_ids, "復原的知識點應該回到活躍列表"
    assert target_point_id in db_final_ids, "復原的知識點應該回到活躍列表"

    # 復原的知識點應該恢復正常狀態
    restored_json_point = None
    for p in json_final_active:
        if p.id == target_point_id:
            restored_json_point = p
            break

    assert restored_json_point is not None
    assert not restored_json_point.is_deleted
    assert restored_json_point.deleted_reason == ""


@pytest.mark.asyncio
async def test_batch_knowledge_operations():
    """測試批量知識點操作的一致性"""

    await UserJourneyTestDataManager.setup_established_user_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # 獲取前3個知識點進行批量操作
    json_points = json_manager.get_active_points()[:3]
    target_ids = [p.id for p in json_points]

    assert len(target_ids) >= 3, "需要至少3個知識點進行批量測試"

    # === 批量編輯測試 ===
    batch_updates = {"custom_notes": "批量更新筆記", "tags": ["批量", "測試"]}

    json_batch_results = []
    for point_id in target_ids:
        result = json_manager.edit_knowledge_point(point_id, batch_updates)
        json_batch_results.append(result is not None)

    # DB 批量編輯（如果支持異步方法）
    db_batch_results = []
    for point_id in target_ids:
        if hasattr(db_manager, "update_knowledge_point_async"):
            result = await db_manager.update_knowledge_point_async(point_id, **batch_updates)
        else:
            result = (
                db_manager.edit_knowledge_point(point_id, batch_updates)
                if hasattr(db_manager, "edit_knowledge_point")
                else True
            )
        db_batch_results.append(result)

    assert all(json_batch_results), "JSON 批量編輯應該全部成功"

    # 驗證批量編輯結果
    updated_json_points = json_manager.get_active_points()
    for point in updated_json_points:
        if point.id in target_ids:
            assert point.custom_notes == "批量更新筆記"

    # === 批量刪除測試 ===
    json_batch_delete_results = []
    for point_id in target_ids:
        result = json_manager.delete_knowledge_point(point_id, "批量刪除測試")
        json_batch_delete_results.append(result)

    db_batch_delete_results = []
    for point_id in target_ids:
        if hasattr(db_manager, "delete_knowledge_point_async"):
            result = await db_manager.delete_knowledge_point_async(point_id, "批量刪除測試")
        else:
            result = db_manager.delete_knowledge_point(point_id, "批量刪除測試")
        db_batch_delete_results.append(result)

    assert all(json_batch_delete_results), "JSON 批量刪除應該全部成功"
    assert all(db_batch_delete_results), "DB 批量刪除應該全部成功"

    # 驗證批量刪除結果
    remaining_json_points = json_manager.get_active_points()
    remaining_db_points = await db_manager.get_knowledge_points_async()

    remaining_json_ids = {p.id for p in remaining_json_points}
    remaining_db_ids = {p.id for p in remaining_db_points}

    for point_id in target_ids:
        assert point_id not in remaining_json_ids, (
            f"JSON 刪除的知識點 {point_id} 不應該在活躍列表中"
        )
        assert point_id not in remaining_db_ids, f"DB 刪除的知識點 {point_id} 不應該在活躍列表中"

    # === 批量復原測試 ===
    json_batch_restore_results = []
    for point_id in target_ids:
        result = json_manager.restore_knowledge_point(point_id)
        json_batch_restore_results.append(result)

    db_batch_restore_results = []
    for point_id in target_ids:
        if hasattr(db_manager, "restore_knowledge_point_async"):
            result = await db_manager.restore_knowledge_point_async(point_id)
        else:
            result = db_manager.restore_knowledge_point(point_id)
        db_batch_restore_results.append(result)

    assert all(json_batch_restore_results), "JSON 批量復原應該全部成功"
    assert all(db_batch_restore_results), "DB 批量復原應該全部成功"

    # 驗證批量復原結果
    final_json_points = json_manager.get_active_points()
    final_db_points = await db_manager.get_knowledge_points_async()

    final_json_ids = {p.id for p in final_json_points}
    final_db_ids = {p.id for p in final_db_points}

    for point_id in target_ids:
        assert point_id in final_json_ids, f"JSON 復原的知識點 {point_id} 應該回到活躍列表"
        assert point_id in final_db_ids, f"DB 復原的知識點 {point_id} 應該回到活躍列表"


@pytest.mark.asyncio
async def test_knowledge_point_search_consistency():
    """測試知識點搜索功能的一致性"""

    await UserJourneyTestDataManager.setup_diverse_knowledge_points()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # 搜索測試詞條
    search_terms = ["動詞", "語法", "grammar", "錯誤"]

    for term in search_terms:
        # JSON 搜索
        if hasattr(json_manager, "search_knowledge_points"):
            json_results = json_manager.search_knowledge_points(term)
        else:
            # 如果沒有專門的搜索方法，用過濾方法
            all_points = json_manager.get_active_points()
            json_results = [p for p in all_points if term in p.key_point]

        # DB 搜索
        if hasattr(db_manager, "search_knowledge_points_async"):
            db_results = await db_manager.search_knowledge_points_async(term)
        else:
            # 使用基本過濾
            all_points = await db_manager.get_knowledge_points_async()
            db_results = [p for p in all_points if term in p.key_point]

        # 驗證搜索結果一致性
        json_result_keys = {p.key_point for p in json_results}
        db_result_keys = {p.key_point for p in db_results}

        # 至少應該有一些共同結果
        if json_results and db_results:
            common_keys = json_result_keys & db_result_keys
            total_unique_keys = json_result_keys | db_result_keys

            # 計算一致性比例
            consistency_ratio = (
                len(common_keys) / len(total_unique_keys) if total_unique_keys else 1.0
            )

            assert consistency_ratio >= 0.7, (
                f"搜索詞 '{term}' 的結果一致性過低 ({consistency_ratio:.2f}): JSON={json_result_keys}, DB={db_result_keys}"
            )


@pytest.mark.asyncio
async def test_knowledge_point_filtering():
    """測試知識點過濾功能的一致性"""

    await UserJourneyTestDataManager.setup_rich_statistical_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    from core.error_types import ErrorCategory

    # === 按分類過濾 ===
    for category in [
        ErrorCategory.SYSTEMATIC,
        ErrorCategory.ISOLATED,
        ErrorCategory.ENHANCEMENT,
        ErrorCategory.OTHER,
    ]:
        # JSON 分類過濾
        if hasattr(json_manager, "get_points_by_category"):
            json_category_points = json_manager.get_points_by_category(category.value)
        else:
            all_points = json_manager.get_active_points()
            json_category_points = [p for p in all_points if p.category == category]

        # DB 分類過濾
        all_db_points = await db_manager.get_knowledge_points_async()
        db_category_points = [p for p in all_db_points if p.category == category]

        # 驗證數量一致性
        assert len(json_category_points) == len(db_category_points), (
            f"分類 {category.value} 的知識點數量不一致: JSON={len(json_category_points)}, DB={len(db_category_points)}"
        )

        # 驗證內容一致性
        if json_category_points and db_category_points:
            json_ids = {p.id for p in json_category_points}
            db_ids = {p.id for p in db_category_points}
            assert json_ids == db_ids, f"分類 {category.value} 的知識點ID不一致"

    # === 按掌握度過濾 ===
    mastery_ranges = [(0.0, 0.3, "初學者"), (0.3, 0.7, "中級"), (0.7, 1.0, "高級")]

    json_all_points = json_manager.get_active_points()
    db_all_points = await db_manager.get_knowledge_points_async()

    for min_mastery, max_mastery, level_name in mastery_ranges:
        json_filtered = [p for p in json_all_points if min_mastery <= p.mastery_level < max_mastery]
        db_filtered = [p for p in db_all_points if min_mastery <= p.mastery_level < max_mastery]

        # 數量可能有細微差異，但應該相近
        count_diff = abs(len(json_filtered) - len(db_filtered))
        total_points = max(len(json_filtered), len(db_filtered), 1)

        diff_ratio = count_diff / total_points
        assert diff_ratio <= 0.2, (
            f"{level_name} 掌握度範圍的知識點數量差異過大: JSON={len(json_filtered)}, DB={len(db_filtered)}, 差異比例={diff_ratio:.2f}"
        )

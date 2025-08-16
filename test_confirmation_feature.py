#!/usr/bin/env python3
"""Test script to verify the knowledge point confirmation feature"""


import requests

# Test data with intentional errors
test_data = {
    "chinese": "我昨天去了圖書館",
    "english": "I go to library yesterday",  # Intentional errors: tense and article
    "mode": "new"
}

print("Testing Knowledge Point Confirmation Feature")
print("=" * 50)
print("\n1. Sending grading request with errors...")
print(f"Chinese: {test_data['chinese']}")
print(f"English: {test_data['english']}")

# Send grading request
response = requests.post(
    "http://localhost:8000/api/grade-answer",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    print("\n2. Grading Response:")
    print(f"   Success: {result.get('success')}")
    print(f"   Score: {result.get('score')}")
    print(f"   Auto Save: {result.get('auto_save', 'NOT SET')}")

    # Check for pending knowledge points
    if 'pending_knowledge_points' in result:
        pending_points = result['pending_knowledge_points']
        print(f"\n3. Pending Knowledge Points: {len(pending_points)} found")

        for i, point in enumerate(pending_points, 1):
            print(f"\n   Point {i}:")
            print(f"   - ID: {point.get('id')}")
            print(f"   - Error: {point.get('error', {}).get('key_point_summary')}")
            print(f"   - Category: {point.get('error', {}).get('category')}")

        # Test confirmation API
        if pending_points:
            print("\n4. Testing Confirmation API...")
            confirm_data = {
                "confirmed_points": pending_points[:1]  # Confirm first point only
            }

            confirm_response = requests.post(
                "http://localhost:8000/api/confirm-knowledge-points",
                json=confirm_data,
                headers={"Content-Type": "application/json"}
            )

            if confirm_response.status_code == 200:
                confirm_result = confirm_response.json()
                print(f"   Confirmation Success: {confirm_result.get('success')}")
                print(f"   Confirmed Count: {confirm_result.get('confirmed_count')}")
                print(f"   Point IDs: {confirm_result.get('point_ids')}")
            else:
                print(f"   Confirmation Failed: {confirm_response.status_code}")
                print(f"   Error: {confirm_response.text}")
    else:
        print("\n3. WARNING: No pending_knowledge_points field in response!")
        print("   This means the confirmation UI won't be shown.")
        print("\n   Full response keys:", list(result.keys()))

        # Check configuration
        print("\n5. Checking server configuration...")
        import os
        print(f"   AUTO_SAVE_KNOWLEDGE_POINTS env: {os.getenv('AUTO_SAVE_KNOWLEDGE_POINTS', 'not set')}")
        print(f"   SHOW_CONFIRMATION_UI env: {os.getenv('SHOW_CONFIRMATION_UI', 'not set')}")

else:
    print(f"\nError: Failed to grade answer - Status {response.status_code}")
    print(response.text)

print("\n" + "=" * 50)
print("Test Complete")

from src.storage.storage_handler import save_member, update_member
from src.storage.storage_handler_extended import delete_member, get_members


def test_update_member_changes_field():
    sample = {"name": "TempUser", "email": "tempuser@example.com", "student_id": "9999", "major": "CS"}
    # Ensure clean state
    try:
        delete_member(sample["email"])
    except Exception:
        pass

    res = save_member(sample)
    assert res == "success"

    # Update major
    res2 = update_member(sample["email"], {"major": "Math"})
    assert res2 == "success"

    # Verify
    members = get_members()
    found = [m for m in members if m.get("email") == sample["email"]]
    assert len(found) == 1
    assert found[0].get("major") == "Math"

    # Cleanup
    delete_member(sample["email"])

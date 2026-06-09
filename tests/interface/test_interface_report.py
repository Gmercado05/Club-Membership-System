from src.interface.cli import format_response


def test_format_report_dict_shows_counts():
    result = {"status": "success", "message": "Report generated.", "data": {"CS": 3, "EE": 1}}
    output = format_response(result)
    assert "Report generated" in output
    assert "CS: 3" in output
    assert "EE: 1" in output

import pytest

from scripts.review_delivery import python_summary


def test_junit_summary_separates_success_failure_and_skip(tmp_path):
    path = tmp_path / "result.xml"
    path.write_text('<testsuites><testsuite time="2.5"><testcase classname="test_a"/><testcase classname="test_a"><failure/></testcase><testcase classname="test_b"><skipped/></testcase></testsuite></testsuites>', encoding="utf-8")
    result = python_summary(path)
    assert (result["passed"], result["failed"], result["skipped"]) == (1, 1, 1)
    assert result["seconds"] == 2.5
    assert result["modules"][0] == {"name": "test_a", "passed": 1, "failed": 1, "skipped": 0}


def test_empty_report_cannot_be_presented_as_a_success(tmp_path):
    path = tmp_path / "empty.xml"
    path.write_text('<testsuites/>', encoding="utf-8")
    with pytest.raises(ValueError, match="no contiene pruebas"):
        python_summary(path)

import pytest
from pathlib import Path
from app.ml.text_extractor import text_extractor

def test_file_not_found():
    res = text_extractor.extract("non_existent_file.pdf")
    assert res["success"] is False
    assert "File not found" in res["error"]

def test_text_cleaner():
    raw_text = "This   is   a   dirty   text   with\n\n\n\n\nnewlines   and   specials."
    cleaned = text_extractor._clean_text(raw_text)
    assert "   " not in cleaned  # no 3 or more spaces
    assert "  " in cleaned       # collapses to exactly 2 spaces
    assert "\n\n\n\n" not in cleaned  # collapsed multiple newlines
    assert cleaned == "This  is  a  dirty  text  with\n\n\nnewlines  and  specials."

def test_ext_to_mime():
    assert text_extractor._ext_to_mime(".pdf") == "application/pdf"
    assert text_extractor._ext_to_mime(".docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert text_extractor._ext_to_mime(".png") == "image/png"
    assert text_extractor._ext_to_mime(".random") == "application/octet-stream"

def test_extract_txt_format(tmp_path):
    # Create a temp txt file
    test_file = tmp_path / "resume.txt"
    test_file.write_text("Hello this is some plain text resume content.", encoding="utf-8")
    
    res = text_extractor.extract(str(test_file), mime_type="text/plain")
    assert res["success"] is True
    assert res["method_used"] == "plaintext"
    assert "plain text resume" in res["text"]
    assert res["char_count"] > 0

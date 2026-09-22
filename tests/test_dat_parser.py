import pytest
import os
from services.dat_parser import DatParser

def test_dat_line_parser_valid():
    parser = DatParser()
    # 000 = controle, 0012 = matricula (deve virar '12'), 1 = tipo, ABCDEABCDE = respostas
    line = "00000121ABCDEABCDE"
    parsed = parser.parse_line(line, line_number=1)

    assert parsed["control"] == "000"
    assert parsed["control_ok"] is True
    assert parsed["matricula"] == "12"
    assert parsed["tipo"] == "1"
    assert parsed["respostas"] == "ABCDEABCDE"
    assert parsed["error_msg"] is None

def test_dat_line_parser_discard_control():
    parser = DatParser()
    # aluno[0..2] = "001" (controle descartado), aluno[3..6] = "0234" (matricula '234')
    line = "00102341ABCDEABCDE"
    parsed = parser.parse_line(line, line_number=2)

    assert parsed["control"] == "001"
    assert parsed["control_ok"] is True
    assert parsed["matricula"] == "234"
    assert parsed["tipo"] == "1"
    assert parsed["error_msg"] is None

def test_dat_file_parser(tmp_path):
    filepath = os.path.join(tmp_path, "teste.dat")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("00012341ABCDEABCDE\n")
        f.write("00599992EDCBAEDCBA\n")

    parser = DatParser()
    results = parser.parse_file(filepath)

    assert len(results) == 2
    assert results[0]["control_ok"] is True
    assert results[0]["matricula"] == "1234"
    
    assert results[1]["control_ok"] is True
    assert results[1]["control"] == "005"
    assert results[1]["matricula"] == "9999"

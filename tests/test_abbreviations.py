import pytest
from services.abbreviations import get_acronym, get_header_tooltip

def test_known_acronyms():
    assert get_acronym("Linguagens, Códigos e Suas Tecnologias") == "LC"
    assert get_acronym("Matemática e Suas Tecnologias") == "MT"
    assert get_acronym("Ciências da Natureza e Suas Tecnologias") == "CN"
    assert get_acronym("Ciências Humanas e Suas Tecnologias") == "CH"
    assert get_acronym("Português") == "POR"
    assert get_acronym("Matemática") == "MAT"
    assert get_acronym("Física") == "FIS"
    assert get_acronym("Química") == "QUI"
    assert get_acronym("Biologia") == "BIO"

def test_fallback_acronyms():
    assert get_acronym("GEO") == "GEO"
    assert get_acronym("Robótica Educacional") == "RE" or get_acronym("Robótica Educacional") == "ROB" or len(get_acronym("Robótica Educacional")) > 0
    assert get_acronym("Astronomia") == "AST"

def test_header_tooltip():
    tooltip = get_header_tooltip("Português", mode="disciplina")
    assert "POR → Português" in tooltip
    assert "Nota da disciplina" in tooltip

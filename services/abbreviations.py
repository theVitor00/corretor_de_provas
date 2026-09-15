"""
Utilitário para padronização e gerenciamento de siglas (abreviações) de blocos e disciplinas,
além da geração de tooltips explicativos para os cabeçalhos de relatórios.
"""

from typing import Tuple, Dict

# Dicionário de mapeamento direto de nomes completos para siglas padronizadas
ACRONYM_MAP: Dict[str, str] = {
    # Blocos Padrão (ENEM / Matriz de Referência)
    "linguagens, códigos e suas tecnologias": "LC",
    "linguagens, códigos e suas tecnologias ": "LC",
    "linguagens e códigos": "LC",
    "linguagens": "LC",
    "matemática e suas tecnologias": "MT",
    "matemática e suas tecnologias ": "MT",
    "ciências da natureza e suas tecnologias": "CN",
    "ciências da natureza e suas tecnologias ": "CN",
    "ciências da natureza": "CN",
    "ciências humanas e suas tecnologias": "CH",
    "ciências humanas e suas tecnologias ": "CH",
    "ciências humanas": "CH",

    # Disciplinas Padrão
    "língua portuguesa": "POR",
    "português": "POR",
    "portugues": "POR",
    "matemática": "MAT",
    "matematica": "MAT",
    "física": "FIS",
    "fisica": "FIS",
    "química": "QUI",
    "quimica": "QUI",
    "biologia": "BIO",
    "história": "HIS",
    "historia": "HIS",
    "geografia": "GEO",
    "filosofia": "FIL",
    "sociologia": "SOC",
    "língua inglesa": "ING",
    "inglês": "ING",
    "ingles": "ING",
    "língua espanhola": "ESP",
    "espanhol": "ESP",
    "redação": "RED",
    "redacao": "RED",
    "arte": "ART",
    "artes": "ART",
    "educação física": "EDF",
    "educacao fisica": "EDF",
    "literatura": "LIT"
}


def get_acronym(full_name: str) -> str:
    """
    Retorna a sigla padronizada para um bloco ou disciplina.
    Caso o nome não esteja no dicionário padrão:
    - Se tiver 4 caracteres ou menos, retorna em maiúsculo.
    - Se for um nome composto (ex: "Robótica Avançada"), pega as iniciais maiúsculas.
    - Caso contrário, pega as primeiras 3 letras em maiúsculo.
    """
    if not full_name:
        return ""
    
    clean_name = str(full_name).strip()
    key = clean_name.lower()
    
    if key in ACRONYM_MAP:
        return ACRONYM_MAP[key]
    
    if len(clean_name) <= 4:
        return clean_name.upper()
    
    words = [w for w in clean_name.split() if len(w) > 2 and w.lower() not in ["de", "da", "do", "dos", "das", "e", "suas"]]
    if len(words) >= 2:
        acronym = "".join([w[0].upper() for w in words[:4]])
        return acronym
    
    return clean_name[:3].upper()


def get_header_tooltip(full_name: str, mode: str = "geral") -> str:
    """
    Retorna o texto explicativo (tooltip) para o cabeçalho de uma coluna na tabela de relatórios.
    
    :param full_name: Nome completo do bloco ou disciplina (ex: 'Linguagens, Códigos e Suas Tecnologias')
    :param mode: 'geral', 'bloco' ou 'disciplina'
    """
    sigla = get_acronym(full_name)
    if mode == "geral":
        desc = "Total de acertos do aluno neste bloco"
    elif mode == "bloco":
        desc = "Nota do bloco calculada proporcionalmente na escala de 0,00 a 10,00"
    else: # disciplina
        desc = "Nota da disciplina calculada proporcionalmente na escala de 0,00 a 10,00"
    
    return f"{sigla} → {full_name}\n({desc})"

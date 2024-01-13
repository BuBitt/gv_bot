import re
import difflib
from beautifultable import BeautifulTable


def id_converter(raw_id: str):
    """### Converte uma menção para um formato de id"""
    return int(raw_id[2:-1])


def is_valid_regex(message, regex_pattern):
    """### Validação de padrão regex"""
    match = re.match(regex_pattern, message)
    return bool(match)


def search_or_similar(termo_de_pesquisa, all_items, limiar=0.5):
    """
    Busca pelo termo fornecido na lista de strings do modelo Peewee.
    Retorna uma lista de strings similares usando o difflib.
    """
    # Percorre os itens no modelo Peewee
    for item in all_items:
        # Verifica se o termo de pesquisa está no item ou se o item é similar
        if termo_de_pesquisa.lower() == item:
            return (True, 1)
    # Usa o difflib para obter correspondências próximas
    correspondencias = difflib.get_close_matches(
        termo_de_pesquisa, all_items, n=10, cutoff=limiar
    )
    if correspondencias:
        return (False, correspondencias)
    return (False, 0)


def constroi_tabela(list, header=None):
    table = BeautifulTable()
    table.set_style(BeautifulTable.STYLE_COMPACT)
    table.columns.append(list, header)
    table.columns.alignment = BeautifulTable.ALIGN_LEFT
    return table

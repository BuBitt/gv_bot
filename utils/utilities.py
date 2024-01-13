import re
import difflib
from beautifultable import BeautifulTable


def id_converter(raw_id: str):
    """### Converte uma menção para um formato de id"""
    return int(raw_id[2:-1])


def mention_by_id(id):
    return f"<@{id}>"


def is_valid_regex(message, regex_pattern):
    """### Validação de padrão regex"""
    match = re.match(pattern=regex_pattern, string=message)
    return bool(match)


def search_or_similar(termo_de_pesquisa, all_items, limiar=0.5, n=10):
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
        termo_de_pesquisa, all_items, n=n, cutoff=limiar
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

def search_offer_table_construct(offers, header=None):
    table = BeautifulTable(maxwidth=1024)
    table.set_style(BeautifulTable.STYLE_COMPACT)
    table.columns.append(
        offers, header=header, alignment=BeautifulTable.ALIGN_LEFT, padding_left=0
    )
    return table
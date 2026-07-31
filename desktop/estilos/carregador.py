from pathlib import Path
from typing import Union

from PySide6.QtWidgets import QApplication, QWidget


PASTA_ESTILOS = Path(__file__).resolve().parent


def carregar_qss(*nomes_arquivos: str) -> str:
    """
    Lê um ou mais arquivos QSS e retorna os estilos
    unidos em uma única string.
    """

    estilos = []

    for nome_arquivo in nomes_arquivos:
        caminho = PASTA_ESTILOS / nome_arquivo

        if not caminho.exists():
            raise FileNotFoundError(
                f"Arquivo de estilo não encontrado: {caminho}"
            )

        conteudo = caminho.read_text(
            encoding="utf-8"
        )

        estilos.append(conteudo)

    return "\n\n".join(estilos)


def aplicar_estilo(
    elemento: Union[QApplication, QWidget],
    *nomes_arquivos: str,
) -> None:
    """
    Aplica um ou mais arquivos QSS em uma aplicação,
    janela ou tela.
    """

    estilo = carregar_qss(
        *nomes_arquivos
    )

    elemento.setStyleSheet(estilo)
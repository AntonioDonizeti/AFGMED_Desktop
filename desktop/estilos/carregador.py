from pathlib import Path
from typing import Union

from PySide6.QtWidgets import QApplication, QWidget


PASTA_ESTILOS = Path(__file__).resolve().parent


def carregar_qss(*nomes_arquivos: str) -> str:
    """Lê um ou mais arquivos QSS e devolve um único texto."""
    estilos: list[str] = []

    for nome_arquivo in nomes_arquivos:
        caminho = PASTA_ESTILOS / nome_arquivo

        if not caminho.exists():
            raise FileNotFoundError(
                f"Arquivo de estilo não encontrado: {caminho}"
            )

        estilos.append(caminho.read_text(encoding="utf-8"))

    return "\n\n".join(estilos)


def aplicar_estilo(
    elemento: Union[QApplication, QWidget],
    *nomes_arquivos: str,
) -> None:
    """Aplica arquivos QSS a uma aplicação, janela ou tela."""
    elemento.setStyleSheet(carregar_qss(*nomes_arquivos))

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from PySide6.QtWidgets import QApplication

from projetoafgmed import app
from desktop.estilos import (
    aplicar_estilo,
    aplicar_tema_claro,
)
from desktop.telas.tela_inicio import abrir_tela_inicio


def main():
    print(
        "BANCO USADO:",
        app.config["SQLALCHEMY_DATABASE_URI"],
    )

    # Evita que o tema dos widgets seja herdado
    # diretamente do modo escuro do Windows.
    QApplication.setStyle("Fusion")

    app_qt = QApplication(sys.argv)

    app_qt.setApplicationName("AFGMED")
    app_qt.setOrganizationName("AFGMED")

    # Primeiro força a paleta clara.
    aplicar_tema_claro(app_qt)

    # Depois aplica o QSS personalizado.
    aplicar_estilo(
        app_qt,
        "global.qss",
    )

    abrir_tela_inicio()

    sys.exit(app_qt.exec())


if __name__ == "__main__":
    main()
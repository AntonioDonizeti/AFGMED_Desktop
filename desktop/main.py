import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from PySide6.QtWidgets import QApplication

from desktop.estilos import aplicar_estilo, aplicar_tema_claro
from desktop.telas.tela_inicio import abrir_tela_inicio
from projetoafgmed import app


def main():
    print(
        "BANCO USADO:",
        app.config["SQLALCHEMY_DATABASE_URI"],
    )

    app_qt = QApplication(sys.argv)
    app_qt.setApplicationName("AFGMED")
    app_qt.setOrganizationName("AFGMED")

    aplicar_tema_claro(app_qt)
    aplicar_estilo(app_qt, "global.qss")

    abrir_tela_inicio()
    sys.exit(app_qt.exec())


if __name__ == "__main__":
    main()

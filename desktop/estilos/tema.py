from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def aplicar_tema_claro(app: QApplication) -> None:
    """
    Força toda a aplicação AFGMED a utilizar uma
    paleta clara, mesmo que o Windows esteja no modo escuro.
    """

    paleta = QPalette()

    # Fundo principal das janelas.
    paleta.setColor(
        QPalette.ColorRole.Window,
        QColor("#F2F7FA"),
    )

    # Texto geral.
    paleta.setColor(
        QPalette.ColorRole.WindowText,
        QColor("#082B45"),
    )

    # Fundo de campos como QLineEdit e QDateEdit.
    paleta.setColor(
        QPalette.ColorRole.Base,
        QColor("#FFFFFF"),
    )

    # Fundo alternativo de listas e tabelas.
    paleta.setColor(
        QPalette.ColorRole.AlternateBase,
        QColor("#EAF2F6"),
    )

    # Texto dentro dos campos.
    paleta.setColor(
        QPalette.ColorRole.Text,
        QColor("#082B45"),
    )

    # Fundo padrão dos botões.
    paleta.setColor(
        QPalette.ColorRole.Button,
        QColor("#FFFFFF"),
    )

    # Texto dos botões.
    paleta.setColor(
        QPalette.ColorRole.ButtonText,
        QColor("#0B6071"),
    )

    # Destaques e seleções.
    paleta.setColor(
        QPalette.ColorRole.Highlight,
        QColor("#18AA9B"),
    )

    paleta.setColor(
        QPalette.ColorRole.HighlightedText,
        QColor("#FFFFFF"),
    )

    # Links.
    paleta.setColor(
        QPalette.ColorRole.Link,
        QColor("#078A91"),
    )

    paleta.setColor(
        QPalette.ColorRole.LinkVisited,
        QColor("#075F73"),
    )

    # Tooltips.
    paleta.setColor(
        QPalette.ColorRole.ToolTipBase,
        QColor("#082B45"),
    )

    paleta.setColor(
        QPalette.ColorRole.ToolTipText,
        QColor("#FFFFFF"),
    )

    # Texto mais destacado.
    paleta.setColor(
        QPalette.ColorRole.BrightText,
        QColor("#FFFFFF"),
    )

    # Texto de placeholder.
    paleta.setColor(
        QPalette.ColorRole.PlaceholderText,
        QColor("#8297A2"),
    )

    # Componentes desativados.
    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor("#879AA4"),
    )

    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor("#879AA4"),
    )

    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor("#879AA4"),
    )

    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Button,
        QColor("#DCE4E8"),
    )

    app.setPalette(paleta)
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def aplicar_tema_claro(app: QApplication) -> None:
    """Força a aplicação a permanecer clara, mesmo no Windows escuro."""
    app.setStyle("Fusion")

    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor("#F4F6F8"))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor("#2C3946"))
    paleta.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor("#EDF1F4"))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor("#10263B"))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.Text, QColor("#2C3946"))
    paleta.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor("#17344F"))
    paleta.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.Link, QColor("#176F6A"))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor("#1C817A"))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor("#7B8794"))

    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor("#7B8794"),
    )
    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor("#7B8794"),
    )
    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor("#7B8794"),
    )
    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Button,
        QColor("#DDE3E8"),
    )

    app.setPalette(paleta)

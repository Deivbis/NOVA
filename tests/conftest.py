"""Configuración compartida de pytest para NOVA."""

import pytest


@pytest.fixture
def qapp():
    """Aplicación Qt compartida para las pruebas de interfaz.

    PySide6 se importa aquí dentro para que las pruebas del Core no
    dependan de la interfaz (DOC-022: Core ejecutable sin UI).
    """
    from PySide6.QtCore import QCoreApplication

    application = QCoreApplication.instance()

    if application is None:
        application = QCoreApplication([])

    return application
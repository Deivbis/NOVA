"""Configuración compartida de pytest para NOVA."""

# Archivos en cuarentena: lanzan un QThread real sin cerrarlo y hacen
# caer el proceso completo de pytest (código 0xC0000409 en Windows).
# Pertenecen a la capa de UI, fuera del alcance de la v0.1 (DOC-023).
# TODO (fase UI): añadir bridge.shutdown() que espere al hilo activo,
# actualizar estas pruebas al modelo QThread y quitar esta lista.
collect_ignore = [
    "integration/test_conversation_persistence.py",
    "unit/test_ui_qml_bridge.py",
]
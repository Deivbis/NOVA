
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QML_DIR = PROJECT_ROOT / "src" / "nova" / "ui" / "qml"
COMPONENTS_DIR = QML_DIR / "components"


def test_main_window_has_expected_dimensions():
    main_qml = (QML_DIR / "Main.qml").read_text(encoding="utf-8")

    assert re.search(r"\bwidth:\s*1280\b", main_qml)
    assert re.search(r"\bheight:\s*800\b", main_qml)
    assert re.search(r"\bminimumWidth:\s*980\b", main_qml)
    assert re.search(r"\bminimumHeight:\s*700\b", main_qml)


def test_main_window_has_expected_title():
    main_qml = (QML_DIR / "Main.qml").read_text(encoding="utf-8")

    assert 'title: "NOVA"' in main_qml


def test_main_window_starts_on_home_section():
    main_qml = (QML_DIR / "Main.qml").read_text(encoding="utf-8")
    sidebar = (COMPONENTS_DIR / "Sidebar.qml").read_text(
        encoding="utf-8"
    )

    assert re.search(r"property\s+int\s+current:\s*0", sidebar)
    assert "currentIndex: sidebar.current" in main_qml


def test_sidebar_has_six_navigation_items():
    sidebar = (COMPONENTS_DIR / "Sidebar.qml").read_text(
        encoding="utf-8"
    )

    labels = re.findall(r'label:\s*"([^"]+)"', sidebar)

    assert labels == [
        "Inicio",
        "Conversación",
        "Memoria",
        "Proyectos",
        "Dashboard",
        "Configuración",
    ]


def test_main_window_contains_all_six_pages():
    main_qml = (QML_DIR / "Main.qml").read_text(encoding="utf-8")

    pages = [
        "HomePage",
        "ConversationPage",
        "MemoryPage",
        "ProjectsPage",
        "DashboardPage",
        "SettingsPage",
    ]

    for page in pages:
        assert re.search(rf"\b{page}\s*\{{", main_qml)


def test_sidebar_selection_updates_bridge_page():
    main_qml = (QML_DIR / "Main.qml").read_text(encoding="utf-8")

    assert "onCurrentChanged: novaBridge.set_current_page(current)" in main_qml


def test_voice_navigation_selects_conversation_page():
    main_qml = (QML_DIR / "Main.qml").read_text(encoding="utf-8")

    assert "function onNavigateRequested(page) { sidebar.current = page }" in main_qml

import tkinter as tk
from tkinter import ttk

from nova.core import ConnectivityState, NovaState
from nova.ui import UIState


class MainWindow:
    """Main NOVA application window."""

    DEFAULT_WIDTH = 1100
    DEFAULT_HEIGHT = 700

    MIN_WIDTH = 900
    MIN_HEIGHT = 600

    NAVIGATION_ITEMS = (
        "Inicio",
        "Chat",
        "Memoria",
        "Proyectos",
        "Sistema",
        "Configuración",
    )

    def __init__(
        self,
        root: tk.Tk | None = None,
        ui_state: UIState | None = None,
    ) -> None:
        self.root = root or tk.Tk()

        self.ui_state = ui_state or UIState.from_core(
            NovaState.IDLE,
            ConnectivityState.UNKNOWN,
        )

        self.current_section = "Inicio"

        self._configure_window()
        self._build_ui()

    def _configure_window(self) -> None:
        """Configure the main application window."""
        self.root.title("NOVA")

        self.root.geometry(
            f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}"
        )

        self.root.minsize(
            self.MIN_WIDTH,
            self.MIN_HEIGHT,
        )

    def _build_ui(self) -> None:
        """Build the complete main window structure."""
        self._create_header()
        self._create_body()
        self._create_footer()

    def _create_header(self) -> None:
        """Create the application header."""
        self.header = ttk.Frame(self.root)
        self.header.pack(
            fill="x",
            padx=16,
            pady=(16, 8),
        )

        self.logo_label = ttk.Label(
            self.header,
            text="NOVA",
            font=("Segoe UI", 18, "bold"),
        )
        self.logo_label.pack(side="left")

        self.status_label = ttk.Label(
            self.header,
            text=self._status_text(),
        )
        self.status_label.pack(side="right")

    def _create_body(self) -> None:
        """Create the main body with navigation and content."""
        self.body = ttk.Frame(self.root)
        self.body.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=8,
        )

        self._create_sidebar()
        self._create_content()

    def _create_sidebar(self) -> None:
        """Create the navigation sidebar."""
        self.sidebar = ttk.Frame(self.body)
        self.sidebar.pack(
            side="left",
            fill="y",
            padx=(0, 16),
        )

        self.navigation_buttons: dict[str, ttk.Button] = {}

        for section in self.NAVIGATION_ITEMS:
            button = ttk.Button(
                self.sidebar,
                text=section,
                command=lambda item=section: self.show_section(item),
            )

            button.pack(
                fill="x",
                pady=4,
            )

            self.navigation_buttons[section] = button

    def _create_content(self) -> None:
        """Create the main content area."""
        self.content = ttk.Frame(self.body)
        self.content.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.section_title = ttk.Label(
            self.content,
            text=self.current_section,
            font=("Segoe UI", 20, "bold"),
        )
        self.section_title.pack(
            anchor="w",
            padx=20,
            pady=(20, 10),
        )

        self.content_message = ttk.Label(
            self.content,
            text="Espacio de contenido de NOVA.",
        )
        self.content_message.pack(
            anchor="w",
            padx=20,
            pady=10,
        )

    def _create_footer(self) -> None:
        """Create the application footer."""
        self.footer = ttk.Frame(self.root)
        self.footer.pack(
            fill="x",
            padx=16,
            pady=(8, 16),
        )

        self.version_label = ttk.Label(
            self.footer,
            text="NOVA 0.1.0",
        )
        self.version_label.pack(side="left")

        self.state_label = ttk.Label(
            self.footer,
            text=self._state_text(),
        )
        self.state_label.pack(side="right")

    def _status_text(self) -> str:
        """Return the current connectivity status text."""
        return (
            f"Conectividad: "
            f"{self.ui_state.connectivity.value}"
        )

    def _state_text(self) -> str:
        """Return the current NOVA state text."""
        return (
            f"Estado: "
            f"{self.ui_state.nova_state.value}"
        )

    def show_section(self, section: str) -> None:
        """Display the selected application section."""
        if section not in self.NAVIGATION_ITEMS:
            raise ValueError(
                f"Sección de NOVA no válida: {section}"
            )

        self.current_section = section
        self.section_title.configure(
            text=section,
        )

        self.content_message.configure(
            text=f"Sección {section} preparada para implementación.",
        )

    def run(self) -> None:
        """Start the Tk event loop."""
        self.root.mainloop()

    def close(self) -> None:
        """Close the main window."""
        self.root.destroy()
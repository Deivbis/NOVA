import tkinter as tk

from nova.core import OrbState
from nova.ui.orb.windows import WindowsWindowStyle


class NovaOrb:
    """Floating NOVA orb window."""

    DEFAULT_SIZE = 90
    DEFAULT_MARGIN = 24

    IDLE_ALPHA = 0.82
    ACTIVE_ALPHA = 1.0

    def __init__(
        self,
        root: tk.Tk,
        state: OrbState = OrbState.IDLE,
    ) -> None:
        self.root = root
        self.state = state

        self.window = tk.Toplevel(root)

        self.window.update_idletasks()

        # Important:
        # Use Tkinter's own top-level HWND directly.
        self.window_style = WindowsWindowStyle(
            self.window.winfo_id()
        )

        self._configure_window()
        self._build_ui()
        self._position_window()
        self.set_state(state)

    def _configure_window(self) -> None:
        """Configure the floating orb window."""
        self.window.title("NOVA Orbe")

        self.window.overrideredirect(True)

        self.window.attributes(
            "-topmost",
            True,
        )

        self.window.attributes(
            "-alpha",
            self.IDLE_ALPHA,
        )

        self.window.resizable(
            False,
            False,
        )

    def _build_ui(self) -> None:
        """Build the orb interface."""
        self.canvas = tk.Canvas(
            self.window,
            width=self.DEFAULT_SIZE,
            height=self.DEFAULT_SIZE,
            highlightthickness=0,
            bd=0,
        )

        self.canvas.pack()

        center = self.DEFAULT_SIZE // 2
        radius = 30

        self.orb = self.canvas.create_oval(
            center - radius,
            center - radius,
            center + radius,
            center + radius,
            fill="#4F46E5",
            outline="",
        )

        self.label = self.canvas.create_text(
            center,
            center,
            text="N",
            fill="white",
            font=("Segoe UI", 20, "bold"),
        )

    def _position_window(self) -> None:
        """Position the orb in the lower-right corner."""
        self.window.update_idletasks()

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        x = (
            screen_width
            - self.DEFAULT_SIZE
            - self.DEFAULT_MARGIN
        )

        y = (
            screen_height
            - self.DEFAULT_SIZE
            - self.DEFAULT_MARGIN
            - 48
        )

        self.window.geometry(
            f"{self.DEFAULT_SIZE}x{self.DEFAULT_SIZE}"
            f"+{x}+{y}"
        )

    def set_state(self, state: OrbState) -> None:
        """Update the orb visual state."""
        self.state = state

        if state == OrbState.IDLE:
            self._set_idle_state()
            self.enable_click_through()

        elif state == OrbState.LISTENING:
            self._set_listening_state()
            self.disable_click_through()

        elif state == OrbState.PROCESSING:
            self._set_processing_state()
            self.disable_click_through()

        elif state == OrbState.RESPONDING:
            self._set_responding_state()
            self.disable_click_through()

        elif state == OrbState.ERROR:
            self._set_error_state()
            self.disable_click_through()

    def _set_idle_state(self) -> None:
        """Set the idle visual state."""
        self.canvas.itemconfigure(
            self.orb,
            fill="#4F46E5",
        )

        self.canvas.itemconfigure(
            self.label,
            text="N",
        )

        self.window.attributes(
            "-alpha",
            self.IDLE_ALPHA,
        )

    def _set_listening_state(self) -> None:
        """Set the listening visual state."""
        self.canvas.itemconfigure(
            self.orb,
            fill="#10B981",
        )

        self.canvas.itemconfigure(
            self.label,
            text="●",
        )

        self.window.attributes(
            "-alpha",
            self.ACTIVE_ALPHA,
        )

    def _set_processing_state(self) -> None:
        """Set the processing visual state."""
        self.canvas.itemconfigure(
            self.orb,
            fill="#F59E0B",
        )

        self.canvas.itemconfigure(
            self.label,
            text="⋯",
        )

        self.window.attributes(
            "-alpha",
            self.ACTIVE_ALPHA,
        )

    def _set_responding_state(self) -> None:
        """Set the responding visual state."""
        self.canvas.itemconfigure(
            self.orb,
            fill="#3B82F6",
        )

        self.canvas.itemconfigure(
            self.label,
            text="N",
        )

        self.window.attributes(
            "-alpha",
            self.ACTIVE_ALPHA,
        )

    def _set_error_state(self) -> None:
        """Set the error visual state."""
        self.canvas.itemconfigure(
            self.orb,
            fill="#EF4444",
        )

        self.canvas.itemconfigure(
            self.label,
            text="!",
        )

        self.window.attributes(
            "-alpha",
            self.ACTIVE_ALPHA,
        )

    def show(self) -> None:
        """Show the orb."""
        self.window.deiconify()

    def hide(self) -> None:
        """Hide the orb."""
        self.window.withdraw()

    def enable_click_through(self) -> None:
        """Make the orb ignore mouse input."""
        self.window_style.set_click_through(True)

    def disable_click_through(self) -> None:
        """Allow the orb to receive mouse input."""
        self.window_style.set_click_through(False)

    def is_click_through(self) -> bool:
        """Return whether the orb ignores mouse input."""
        return self.window_style.is_click_through()

    def close(self) -> None:
        """Close the orb."""
        self.window.destroy()
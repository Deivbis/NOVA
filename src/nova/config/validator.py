from .exceptions import ConfigurationValidationError


class ConfigValidator:
    """Validates the semantic values of NOVA configuration."""

    VALID_ENVIRONMENTS = {"development", "production", "testing"}
    VALID_EXECUTION_MODES = {"normal", "debug"}
    VALID_LANGUAGES = {"es", "en"}
    VALID_ORB_POSITIONS = {
        "bottom_right",
        "bottom_left",
        "top_right",
        "top_left",
    }
    VALID_ORB_SIZES = {"small", "medium", "large"}
    VALID_THEMES = {"dark", "light"}

    def validate(self, data: dict) -> None:
        self._validate_nova(data)
        self._validate_execution(data)
        self._validate_connectivity(data)
        self._validate_ui(data)
        self._validate_voice(data)
        self._validate_paths(data)

    def _validate_nova(self, data: dict) -> None:
        nova = self._section(data, "nova")

        self._require_type(nova, "name", str)
        self._require_type(nova, "version", str)
        self._require_type(nova, "environment", str)
        self._require_type(nova, "language", str)

        if nova["environment"] not in self.VALID_ENVIRONMENTS:
            raise ConfigurationValidationError(
                f"Invalid environment: {nova['environment']}"
            )

        if nova["language"] not in self.VALID_LANGUAGES:
            raise ConfigurationValidationError(
                f"Invalid language: {nova['language']}"
            )

    def _validate_execution(self, data: dict) -> None:
        execution = self._section(data, "execution")

        self._require_type(execution, "mode", str)
        self._require_type(execution, "debug", bool)

        if execution["mode"] not in self.VALID_EXECUTION_MODES:
            raise ConfigurationValidationError(
                f"Invalid execution mode: {execution['mode']}"
            )

    def _validate_connectivity(self, data: dict) -> None:
        connectivity = self._section(data, "connectivity")

        self._require_type(connectivity, "internet_enabled", bool)
        self._require_type(connectivity, "offline_mode_allowed", bool)

    def _validate_ui(self, data: dict) -> None:
        ui = self._section(data, "ui")
        orb = self._section(ui, "orb")

        self._require_type(ui, "theme", str)
        self._require_type(orb, "enabled", bool)
        self._require_type(orb, "position", str)
        self._require_type(orb, "size", str)
        self._require_type(orb, "opacity", (int, float))
        self._require_type(orb, "click_through", bool)
        self._require_type(orb, "gaming_mode", bool)

        if ui["theme"] not in self.VALID_THEMES:
            raise ConfigurationValidationError(
                f"Invalid UI theme: {ui['theme']}"
            )

        if orb["position"] not in self.VALID_ORB_POSITIONS:
            raise ConfigurationValidationError(
                f"Invalid Orb position: {orb['position']}"
            )

        if orb["size"] not in self.VALID_ORB_SIZES:
            raise ConfigurationValidationError(
                f"Invalid Orb size: {orb['size']}"
            )

        if not 0.0 <= float(orb["opacity"]) <= 1.0:
            raise ConfigurationValidationError(
                "Orb opacity must be between 0.0 and 1.0."
            )

    def _validate_voice(self, data: dict) -> None:
        voice = self._section(data, "voice")

        for key in (
            "enabled",
            "wake_word_enabled",
            "stt_enabled",
            "tts_enabled",
        ):
            self._require_type(voice, key, bool)

    def _validate_paths(self, data: dict) -> None:
        paths = self._section(data, "paths")

        for key in (
            "data",
            "database",
            "cache",
            "backups",
            "logs",
            "models",
        ):
            self._require_type(paths, key, str)

    @staticmethod
    def _section(data: dict, name: str) -> dict:
        value = data.get(name)

        if not isinstance(value, dict):
            raise ConfigurationValidationError(
                f"Missing or invalid configuration section: {name}"
            )

        return value

    @staticmethod
    def _require_type(
        section: dict,
        key: str,
        expected_type: type | tuple[type, ...],
    ) -> None:
        if key not in section:
            raise ConfigurationValidationError(
                f"Missing configuration value: {key}"
            )

        if not isinstance(section[key], expected_type):
            raise ConfigurationValidationError(
                f"Invalid type for configuration value: {key}"
            )
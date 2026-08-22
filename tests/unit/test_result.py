from nova.core.result import Result


def test_success_result():
    result = Result.ok("respuesta")

    assert result.success is True
    assert result.value == "respuesta"
    assert result.error is None


def test_failure_result():
    result = Result.fail(
        code="TEST_ERROR",
        message="Error de prueba",
    )

    assert result.success is False
    assert result.value is None
    assert result.error is not None
    assert result.error.code == "TEST_ERROR"
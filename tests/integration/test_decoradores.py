import logging

from app.decoradores import medir_duracion


def test_conserva_resultado_y_nombre():
    @medir_duracion
    def suma(a, b):
        """doc"""
        return a + b

    assert suma(2, 3) == 5
    assert suma.__name__ == "suma" and suma.__doc__ == "doc"


def test_registra_duracion(caplog):
    @medir_duracion
    def nada():
        return None

    with caplog.at_level(logging.INFO, logger="gestor"):
        nada()
    assert "nada tardó" in caplog.text


def test_registra_aunque_falle(caplog):
    @medir_duracion
    def falla():
        raise ValueError("x")

    with caplog.at_level(logging.INFO, logger="gestor"):
        try:
            falla()
        except ValueError:
            pass
    assert "falla tardó" in caplog.text

import pytest

from src.common.estado import EstadoBrazo, EstadoTrafico
from src.vision.escala_maqueta import EscaladorMaqueta, capacidad_zona_sumo


def brazo(presentes, detenidos):
    return EstadoBrazo(vehiculos=presentes, detenidos=detenidos, cola_relativa=0.0,
                       vehiculos_zona=presentes, detenidos_zona=detenidos)


def test_capacidad_zona_sumo():
    config = {"carriles_zona_camara": 2, "zona_camara_m": 100, "espacio_por_vehiculo_m": 7.5}
    assert capacidad_zona_sumo(config) == pytest.approx(26.67, abs=0.01)


def test_brazo_lleno_equivale_a_zona_llena():
    escalador = EscaladorMaqueta({"norte": 5}, 26.67)
    assert escalador.equivalentes("norte", 5) == 27
    assert escalador.equivalentes("norte", 0) == 0


def test_mas_carros_que_capacidad_se_satura():
    escalador = EscaladorMaqueta({"este": 3}, 26.67)
    assert escalador.equivalentes("este", 7) == escalador.equivalentes("este", 3)


def test_brazos_cortos_pesan_mas_por_carro():
    escalador = EscaladorMaqueta({"norte": 5, "este": 3}, 26.67)
    assert escalador.equivalentes("este", 1) > escalador.equivalentes("norte", 1)


def test_escalar_estado_completo():
    escalador = EscaladorMaqueta({"norte": 5, "sur": 5, "este": 3, "oeste": 3}, 26.67)
    estado = EstadoTrafico(tiempo=10.0, brazos={"norte": brazo(5, 4), "sur": brazo(0, 0),
                                                "este": brazo(3, 3), "oeste": brazo(1, 0)})
    escalado = escalador.escalar(estado)
    assert escalado.tiempo == 10.0
    assert escalado.brazos["norte"].vehiculos_zona == 27
    assert escalado.brazos["norte"].detenidos_zona == 21
    assert escalado.brazos["este"].detenidos_zona == 27
    assert escalado.brazos["oeste"].vehiculos_zona == 9
    assert escalado.brazos["norte"].cola_relativa == pytest.approx(0.8)


def test_capacidad_invalida():
    with pytest.raises(ValueError):
        EscaladorMaqueta({"norte": 0}, 26.67)

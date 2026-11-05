import pytest

from src.common.configuracion import cargar_interseccion
from src.common.estado import EstadoBrazo, EstadoTrafico
from src.vision.escala_maqueta import EscaladorMaqueta, capacidades_zona_sumo

SUMO = {"norte": 18.7, "sur": 26.67, "este": 26.67, "oeste": 26.67}


def brazo(presentes, detenidos):
    return EstadoBrazo(vehiculos=presentes, detenidos=detenidos, cola_relativa=0.0,
                       vehiculos_zona=presentes, detenidos_zona=detenidos)


def test_capacidades_de_la_red_real():
    capacidades = capacidades_zona_sumo(cargar_interseccion())
    # norte: 41.1 m x 2 carriles + 58.1 m x 1 carril (puente) dentro de los 100 m
    assert capacidades["norte"] == pytest.approx((41.1 * 2 + 58.1) / 7.5, abs=0.2)
    for nombre in ("sur", "este", "oeste"):   # 2 carriles en toda la zona
        assert capacidades[nombre] == pytest.approx(2 * 100 / 7.5, abs=0.01)


def test_brazo_lleno_equivale_a_zona_llena():
    escalador = EscaladorMaqueta({"norte": 4, "sur": 8}, SUMO)
    assert escalador.equivalentes("norte", 4) == 19
    assert escalador.equivalentes("sur", 8) == 27
    assert escalador.equivalentes("norte", 0) == 0


def test_mas_carros_que_capacidad_se_satura():
    escalador = EscaladorMaqueta({"este": 3}, 26.67)
    assert escalador.equivalentes("este", 7) == escalador.equivalentes("este", 3)


def test_brazos_cortos_pesan_mas_por_carro():
    escalador = EscaladorMaqueta({"norte": 5, "este": 3}, 26.67)
    assert escalador.equivalentes("este", 1) > escalador.equivalentes("norte", 1)


def test_escalar_estado_completo():
    escalador = EscaladorMaqueta({"norte": 4, "sur": 8, "este": 4, "oeste": 4}, SUMO)
    estado = EstadoTrafico(tiempo=10.0, brazos={"norte": brazo(4, 2), "sur": brazo(0, 0),
                                                "este": brazo(4, 4), "oeste": brazo(1, 0)})
    escalado = escalador.escalar(estado)
    assert escalado.tiempo == 10.0
    assert escalado.brazos["norte"].vehiculos_zona == 19
    assert escalado.brazos["norte"].detenidos_zona == 9
    assert escalado.brazos["este"].detenidos_zona == 27
    assert escalado.brazos["oeste"].vehiculos_zona == 7
    assert escalado.brazos["norte"].cola_relativa == pytest.approx(0.5)


def test_capacidad_invalida():
    with pytest.raises(ValueError):
        EscaladorMaqueta({"norte": 0}, 26.67)
    with pytest.raises(ValueError):
        EscaladorMaqueta({"norte": 4}, {"sur": 26.67})

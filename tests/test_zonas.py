"""Pruebas de src/vision/zonas.py (no necesitan camara ni YOLO)."""
import pytest

from src.vision.zonas import ContadorZonas, VehiculoSeguido, punto_en_poligono

CUADRADO = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)]
ZONAS = {"norte": CUADRADO, "sur": [(0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0)]}
ANCHO, ALTO = 1000, 1000


def caja(id_, cx, cy, lado=40):
    return VehiculoSeguido(id_, cx - lado / 2, cy - lado / 2, cx + lado / 2, cy + lado / 2)


def test_punto_en_poligono():
    assert punto_en_poligono(0.25, 0.25, CUADRADO)
    assert not punto_en_poligono(0.75, 0.25, CUADRADO)
    triangulo = [(0, 0), (1, 0), (0, 1)]
    assert punto_en_poligono(0.2, 0.2, triangulo)
    assert not punto_en_poligono(0.8, 0.8, triangulo)


def test_cuenta_presentes_por_zona_y_fuera():
    contador = ContadorZonas(ZONAS)
    estado = contador.actualizar(0.0, [caja(1, 250, 250), caja(2, 100, 100), caja(3, 750, 750), caja(4, 750, 250)],
                                 ANCHO, ALTO)
    assert estado.brazos["norte"].vehiculos_zona == 2
    assert estado.brazos["sur"].vehiculos_zona == 1   # el 4 esta fuera de ambas zonas


def test_quieto_cuenta_como_detenido_solo_despues_de_la_ventana():
    contador = ContadorZonas(ZONAS, ventana_detenido_s=1.0, umbral_movimiento=0.01)
    for paso in range(6):
        t = paso * 0.2   # 5 cuadros por segundo
        estado = contador.actualizar(t, [caja(1, 250 + (paso % 2) * 2, 250)], ANCHO, ALTO)   # tiembla 2 px
        if t < 1.0:
            assert estado.brazos["norte"].detenidos_zona == 0
    assert estado.brazos["norte"].detenidos_zona == 1


def test_en_movimiento_no_es_detenido():
    contador = ContadorZonas(ZONAS, ventana_detenido_s=1.0, umbral_movimiento=0.01)
    for paso in range(10):
        estado = contador.actualizar(paso * 0.2, [caja(1, 100 + paso * 20, 250)], ANCHO, ALTO)   # 100 px/s
    assert estado.brazos["norte"].vehiculos_zona == 1
    assert estado.brazos["norte"].detenidos_zona == 0


def test_arranca_y_deja_de_estar_detenido():
    contador = ContadorZonas(ZONAS, ventana_detenido_s=1.0, umbral_movimiento=0.01)
    for paso in range(8):
        estado = contador.actualizar(paso * 0.2, [caja(1, 200, 250)], ANCHO, ALTO)
    assert estado.brazos["norte"].detenidos_zona == 1
    estado = contador.actualizar(1.6, [caja(1, 260, 250)], ANCHO, ALTO)   # se movio 60 px (6 %)
    assert estado.brazos["norte"].detenidos_zona == 0


def test_imagen_no_cuadrada_usa_el_lado_mayor():
    contador = ContadorZonas({"norte": [(0, 0), (1, 0), (1, 1), (0, 1)]}, ventana_detenido_s=0.4,
                             umbral_movimiento=0.01)
    # 1920x1080: 15 px en y = 15/1920 = 0.8 % del lado mayor -> sigue "quieto"
    for paso in range(4):
        estado = contador.actualizar(paso * 0.2, [caja(1, 500, 500 + paso * 5)], 1920, 1080)
    assert estado.brazos["norte"].detenidos_zona == 1


def test_olvida_ids_que_desaparecen():
    contador = ContadorZonas(ZONAS, olvidar_tras_s=1.0)
    contador.actualizar(0.0, [caja(7, 250, 250)], ANCHO, ALTO)
    contador.actualizar(5.0, [], ANCHO, ALTO)
    assert 7 not in contador._historiales


@pytest.mark.parametrize("zonas", [{}, {"norte": [(0, 0), (1, 1)]}, {"norte": [(0, 0), (2, 0), (0, 1)]}])
def test_zonas_invalidas(zonas):
    with pytest.raises(ValueError):
        ContadorZonas(zonas)

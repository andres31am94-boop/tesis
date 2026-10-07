"""Pruebas de src/metrics/metricas.py con un tripinfo pequeno hecho a mano (valores de prueba)."""
import tempfile
import unittest
from pathlib import Path

from src.metrics.metricas import leer_tripinfo, resumir_colas, resumir_verdes, resumir_viajes

TRIPINFO_PRUEBA = """<tripinfos>
  <tripinfo id="a" vType="carro" depart="100.00" departDelay="0.00" arrival="130.00" duration="30.00" routeLength="300.00" waitingTime="10.00" timeLoss="12.00"/>
  <tripinfo id="b" vType="moto"  depart="420.00" departDelay="20.00" arrival="460.00" duration="40.00" routeLength="400.00" waitingTime="5.00" timeLoss="8.00"/>
  <tripinfo id="c" vType="bus"   depart="500.00" departDelay="0.00" arrival="560.00" duration="60.00" routeLength="300.00" waitingTime="25.00" timeLoss="30.00"/>
</tripinfos>
"""


class TestMetricas(unittest.TestCase):
    def setUp(self):
        carpeta = tempfile.mkdtemp()
        self.ruta = Path(carpeta) / "tripinfo.xml"
        self.ruta.write_text(TRIPINFO_PRUEBA, encoding="utf-8")

    def test_ventana_usa_hora_programada_e_incluye_retraso_de_entrada(self):
        viajes = leer_tripinfo(self.ruta)
        # ventana [300, 600): entra "b" (programado 400) y "c" (500); "a" (100) queda fuera
        r = resumir_viajes(viajes, 300, 600)
        self.assertEqual(r["vehiculos_medidos"], 2)
        self.assertAlmostEqual(r["espera_en_red_promedio_s"], (5 + 25) / 2)
        self.assertAlmostEqual(r["retraso_entrada_promedio_s"], (20 + 0) / 2)
        self.assertAlmostEqual(r["espera_total_promedio_s"], ((5 + 20) + 25) / 2)
        self.assertAlmostEqual(r["tiempo_viaje_promedio_s"], (40 + 60) / 2)
        self.assertAlmostEqual(r["velocidad_promedio_kmh"], ((400 / 40) + (300 / 60)) / 2 * 3.6)
        # salidas dentro de [300, 600): b (460) y c (560) -> 2 vehiculos en 300 s = 24 veh/h
        self.assertAlmostEqual(r["throughput_veh_h"], 24.0)

    def test_ventana_vacia_da_error(self):
        with self.assertRaises(ValueError):
            resumir_viajes(leer_tripinfo(self.ruta), 2000, 3000)

    def test_colas(self):
        filas = [
            {"tiempo": 0, "detenidos_norte": 9, "detenidos_sur": 9},   # fuera de la ventana
            {"tiempo": 10, "detenidos_norte": 2, "detenidos_sur": 0},
            {"tiempo": 11, "detenidos_norte": 4, "detenidos_sur": 6},
        ]
        r = resumir_colas(filas, ["norte", "sur"], 10, 20)
        self.assertAlmostEqual(r["cola_promedio_norte"], 3)
        self.assertEqual(r["cola_maxima_sur"], 6)
        self.assertAlmostEqual(r["detenidos_promedio_total"], (2 + 10) / 2)

    def test_verdes(self):
        historial = [("dg15", 0, 42), ("cra23", 47, 42), ("dg15", 94, 30), ("cra23", 129, 20)]
        r = resumir_verdes(historial, 40, 200)
        self.assertAlmostEqual(r["verde_promedio_dg15_s"], 30)
        self.assertAlmostEqual(r["verde_promedio_cra23_s"], (42 + 20) / 2)
        self.assertEqual(r["verdes_cra23"], 2)


if __name__ == "__main__":
    unittest.main()

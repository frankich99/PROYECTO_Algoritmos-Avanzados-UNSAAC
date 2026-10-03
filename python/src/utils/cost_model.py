"""
Modelo de costo para ruteo urbano en Cusco. Calcula impedancia considerando
longitud, pendiente topográfica (alpha=2.5) y tipo de vía.
"""
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class RoadSegment:
    """Representa un tramo vial dirigido con atributos físicos y operacionales de Cusco."""
    origin: str
    destination: str
    length_m: float           # Longitud métrica en metros
    street_type: str          # 'avenida', 'calle_centro', 'calle_residencial', 'peatonal'
    gradient_pct: float       # Pendiente en porcentaje (e.g., 8.0 para 8% de subida)
    street_name: str          # Nombre de la vía cusqueña

class CuscoCostModel:
    """
    C(u,v) = T_base * (1 + alpha * max(0, pendiente/100))
    T_base = longitud / velocidad_nominal
    """
    # Velocidades promedio efectivas según tipo de vía en km/h
    NOMINAL_SPEED_KMH = {
        'avenida': 35.0,            # Av. El Sol, Av. Tullumayo, Av. de la Cultura
        'calle_residencial': 25.0,  # Calles fuera del casco monumental
        'calle_centro': 15.0,       # Calles coloniales estrechas (Santa Clara, Marqués, Espaderos)
        'peatonal': 8.0             # Tramos como Portal de Panes o Loreto con paso restringido
    }

    ALPHA_SLOPE = 2.5  # Sensibilidad a la pendiente (fuerte penalización para vehículos de emergencia en subidas)

    @classmethod
    def calculate_cost(cls, segment: RoadSegment, metric: str = 'time') -> float:
        """
        Calcula el costo del tramo según la métrica elegida:
        - 'distance': Retorna la distancia física pura en metros.
        - 'time': Retorna el tiempo de viaje estimado en segundos (impedancia de emergencia).
        """
        if metric == 'distance':
            return segment.length_m

        speed_kmh = cls.NOMINAL_SPEED_KMH.get(segment.street_type, 20.0)
        speed_ms = speed_kmh / 3.6  # Conversión a m/s

        t_base_sec = segment.length_m / speed_ms

        # Penalización por pendiente positiva (cuesta arriba en la topografía cusqueña)
        slope_penalty = 1.0 + cls.ALPHA_SLOPE * max(0.0, segment.gradient_pct / 100.0)

        total_time_sec = t_base_sec * slope_penalty
        return round(total_time_sec, 2)

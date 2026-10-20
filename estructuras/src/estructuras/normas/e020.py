"""Norma Técnica E.020 Cargas (D.S. N° 011-2006-VIVIENDA).

Valores en tonf/m² y tonf/m³. La norma los da en kPa y kN/m³ con su equivalente en kgf.
"""

# Tabla 1: cargas vivas mínimas repartidas (tonf/m²).
CARGAS_VIVAS = {
    "vivienda": (0.20, "Viviendas"),
    "vivienda_corredores_escaleras": (0.20, "Viviendas – corredores y escaleras"),
    "oficinas": (0.25, "Oficinas – ambientes de trabajo"),
    "oficinas_corredores_escaleras": (0.40, "Oficinas – corredores y escaleras"),
    "educacion_aulas": (0.25, "Centros de educación – aulas"),
    "educacion_talleres": (0.35, "Centros de educación – talleres"),
    "educacion_corredores_escaleras": (0.40, "Centros de educación – corredores y escaleras"),
    "hospital_cuartos": (0.20, "Hospitales – cuartos"),
    "hospital_salas_operacion": (0.30, "Hospitales – salas de operación y laboratorios"),
    "hospital_corredores_escaleras": (0.40, "Hospitales – corredores y escaleras"),
    "hotel_cuartos": (0.20, "Hoteles – cuartos"),
    "hotel_corredores_escaleras": (0.40, "Hoteles – corredores y escaleras"),
    "tiendas": (0.50, "Tiendas"),
    "garaje_autos": (0.25, "Garajes – vehículos de pasajeros"),
    "biblioteca_lectura": (0.30, "Bibliotecas – salas de lectura"),
    "biblioteca_almacenaje": (0.75, "Bibliotecas – almacenaje"),
    "asamblea_asientos_fijos": (0.30, "Lugares de asamblea – con asientos fijos"),
    "asamblea_sin_asientos_fijos": (0.40, "Lugares de asamblea – sin asientos fijos"),
    "techo": (0.10, "Techos con inclinación hasta 3° (art. 7.1)"),
}

# Anexo 1: pesos unitarios (tonf/m³).
PESOS_UNITARIOS = {
    "concreto_armado": 2.40,
    "concreto_simple": 2.30,
    "albanileria_solida": 1.80,
    "albanileria_hueca": 1.35,
    "mortero_cemento": 2.00,
    "agua": 1.00,
}

# Anexo 1: losas aligeradas en una dirección con viguetas de 0,10 m cada 0,40 m (tonf/m²).
PESO_ALIGERADO = {0.17: 0.28, 0.20: 0.30, 0.25: 0.35, 0.30: 0.42}


def carga_viva(uso: str) -> float:
    try:
        return CARGAS_VIVAS[uso][0]
    except KeyError:
        raise ValueError(f"Uso {uso!r} no existe; use uno de {', '.join(CARGAS_VIVAS)}.") from None


def peso_aligerado(espesor: float) -> float:
    for h, peso in PESO_ALIGERADO.items():
        if abs(h - espesor) < 1e-6:
            return peso
    raise ValueError(f"Aligerado de {espesor} m no tabulado; espesores: {', '.join(map(str, PESO_ALIGERADO))}.")

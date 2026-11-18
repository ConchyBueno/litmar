"""Pruebas sin red con una respuesta core sintética guardada en disco."""

import json
from pathlib import Path

import httpx
import pytest

from litmar import Articulo
from litmar.fuentes import EuropePMC, Fuente

RESPUESTA = json.loads(
    (Path(__file__).parent / "datos" / "europepmc_search_sintetica.json").read_text(
        encoding="utf-8"
    )
)


def test_convierte_respuesta_guardada_y_pagina():
    peticiones = []

    def responder(peticion):
        peticiones.append(peticion)
        datos = RESPUESTA if len(peticiones) == 1 else {"resultList": {"result": []}}
        return httpx.Response(200, json=datos)

    with httpx.Client(transport=httpx.MockTransport(responder)) as client:
        fuente = EuropePMC(client=client)
        assert isinstance(fuente, Fuente)
        articulos = fuente.buscar("biomedical", n=2)

    assert articulos == [
        Articulo(
            title="Example biomedical study",
            authors=("Garcia A", "Study Group"),
            year=2024,
            doi="10.1000/epmc",
            journal="Example Journal",
            abstract="An example abstract.",
            citations=12,
        )
    ]
    assert peticiones[0].url.path == "/europepmc/webservices/rest/search"
    assert dict(peticiones[0].url.params) == {
        "query": "biomedical",
        "format": "json",
        "resultType": "core",
        "pageSize": "25",
        "cursorMark": "*",
    }
    assert peticiones[1].url.params["cursorMark"] == "pagina-2"


def test_limita_resultados_y_hereda_reintentos():
    esperas = []
    llamadas = []

    def responder(peticion):
        llamadas.append(peticion)
        return httpx.Response(503) if len(llamadas) == 1 else httpx.Response(200, json=RESPUESTA)

    with httpx.Client(transport=httpx.MockTransport(responder)) as client:
        assert len(EuropePMC(client=client, sleep=esperas.append).buscar("x", n=1)) == 1
    assert esperas == [1.0]


def test_rechaza_n_invalido():
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: pytest.fail("petición inesperada"))
    ) as client:
        with pytest.raises(ValueError):
            EuropePMC(client=client).buscar("x", n=0)


def test_cursor_repetido_no_crea_bucle():
    datos = {**RESPUESTA, "nextCursorMark": "*"}
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=datos))
    ) as client:
        assert len(EuropePMC(client=client).buscar("x", n=1001)) == 1

"""Fuente Europe PMC: https://europepmc.org/RestfulWebService."""

from __future__ import annotations

from typing import Any

from litmar.articulo import Articulo
from litmar.fuentes.base import Fuente


class EuropePMC(Fuente):
    """Busca metadatos públicos sin clave; hereda los reintentos de Fuente."""

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    MAX_PER_PAGE = 1000

    def buscar(self, consulta: str, n: int = 10) -> list[Articulo]:
        if n < 1:
            raise ValueError("n debe ser al menos 1")
        articulos: list[Articulo] = []
        cursor = "*"
        visitados: set[str] = set()
        while cursor not in visitados:
            visitados.add(cursor)
            datos = self._get_json(
                self.BASE_URL,
                params={
                    "query": consulta,
                    "format": "json",
                    "resultType": "core",
                    "pageSize": min(n, self.MAX_PER_PAGE),
                    "cursorMark": cursor,
                },
            )
            resultados = (datos.get("resultList") or {}).get("result") or []
            for obra in resultados:
                articulo = a_articulo(obra)
                if articulo is not None:
                    articulos.append(articulo)
                    if len(articulos) == n:
                        return articulos
            cursor = datos.get("nextCursorMark")
            if not resultados or not cursor:
                break
        return articulos


def a_articulo(obra: dict[str, Any]) -> Articulo | None:
    """Convierte metadatos core; descarta registros sin campos obligatorios."""
    autores = [
        nombre
        for autor in (obra.get("authorList") or {}).get("author") or []
        if (nombre := autor.get("fullName") or autor.get("collectiveName"))
    ]
    doi, titulo, anio = obra.get("doi"), obra.get("title"), obra.get("pubYear")
    if not (doi and titulo and anio and autores):
        return None
    revista = ((obra.get("journalInfo") or {}).get("journal") or {}).get("title")
    try:
        return Articulo(
            title=titulo,
            authors=autores,
            year=int(anio),
            doi=doi,
            journal=revista or "",
            abstract=obra.get("abstractText") or "",
            citations=int(obra.get("citedByCount") or 0),
        )
    except (TypeError, ValueError):
        return None

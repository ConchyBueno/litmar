# litmar

## Buscar artículos con OpenAlex

`Fuente` es una clase abstracta con `buscar(consulta, n=10) -> list[Articulo]`.
`OpenAlex` la implementa y devuelve como máximo `n` artículos válidos. Descarta
obras sin DOI, título, año o autores y reconstruye los resúmenes desde su índice
invertido. La paginación básica se detiene a los 10.000 resultados consultados.

```python
from litmar.fuentes import OpenAlex

with OpenAlex() as fuente:
    articulos = fuente.buscar("bibliometrics", n=10)
```

Para usar una clave, pasa `api_key` al constructor; se envía mediante
`Authorization: Bearer`, sin incluirla en la URL.

Documentación oficial consultada el 17 de noviembre de 2026:

- Endpoint: `GET https://api.openalex.org/works`.
- Parámetros utilizados: `search` (consulta), `per_page` (hasta 100), `page`
  (página desde 1) y `select` (campos necesarios para construir `Articulo`).
- Clave opcional para consultas básicas. La clave gratuita amplía diez veces el
  presupuesto diario y permite continuar la paginación por cursor.
- Límites: 10 peticiones/s sin clave, 30 con clave gratuita o saldo prepago y 50
  con plan anual. Las consultas con más de cinco operadores booleanos tienen
  límites menores: 1, 5 y 25 peticiones/s, respectivamente.
- La paginación básica exige `page × per_page <= 10.000`. Esta implementación
  usa paginación básica, sin cursores.
- Un exceso de frecuencia o presupuesto devuelve HTTP 429. Las cuentas gratuitas
  nuevas también tienen un límite inicial de gasto de 0,10 USD cada cinco minutos
  durante su primer dólar de uso.

Fuentes: [búsqueda](https://help.openalex.org/api/searching/),
[autenticación y límites](https://help.openalex.org/api/authentication/) y
[paginación](https://help.openalex.org/api/paging/).

Los reintentos residen en `Fuente`: errores de transporte, HTTP 429 y errores
500/502/503/504, con espera exponencial y soporte para `Retry-After`. Por defecto
se hacen tres reintentos. Si `Retry-After` supera `max_wait`, se propaga el error.

## Pruebas sin red

```sh
uv run pytest
```

`tests/test_fuentes.py` utiliza `httpx.MockTransport` y la respuesta guardada en
`tests/datos/openalex_works.json`, sin consultar OpenAlex ni necesitar una clave.
Comprueba conversión, parámetros, paginación, autenticación y reintentos.

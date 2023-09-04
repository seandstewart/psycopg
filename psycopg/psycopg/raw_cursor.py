"""
psycopg raw queries cursors
"""

# Copyright (C) 2023 The Psycopg Team

from typing import Optional, List, Tuple, TYPE_CHECKING
from functools import lru_cache

from .abc import ConnectionType, Query, Params
from .sql import Composable
from .rows import Row
from ._enums import PyFormat
from .cursor import BaseCursor, Cursor
from .cursor_async import AsyncCursor
from ._queries import PostgresQuery, QueryPart

if TYPE_CHECKING:
    from typing import Any  # noqa: F401
    from .connection import Connection  # noqa: F401
    from .connection_async import AsyncConnection  # noqa: F401


class PostgresRawQuery(PostgresQuery):
    def convert(self, query: Query, vars: Optional[Params]) -> None:
        if isinstance(query, str):
            bquery = query.encode(self._encoding)
        elif isinstance(query, Composable):
            bquery = query.as_bytes(self._tx)
        else:
            bquery = query

        self.query = bquery
        self._want_formats = self._order = None
        self.dump(vars)

    def dump(self, vars: Optional[Params]) -> None:
        if vars is not None:
            if not PostgresQuery.is_params_sequence(vars):
                raise TypeError("raw queries require a sequence of parameters")
            self._want_formats = [PyFormat.AUTO] * len(vars)

            self.params = self._tx.dump_sequence(vars, self._want_formats)
            self.types = self._tx.types or ()
            self.formats = self._tx.formats
        else:
            self.params = None
            self.types = ()
            self.formats = None

    @staticmethod
    def query2pg_nocache(
        query: bytes, encoding: str
    ) -> Tuple[bytes, Optional[List[PyFormat]], Optional[List[str]], List[QueryPart]]:
        raise NotImplementedError()

    query2pg = lru_cache()(query2pg_nocache)


class RawCursorMixin(BaseCursor[ConnectionType, Row]):
    _query_cls = PostgresRawQuery


class RawCursor(RawCursorMixin["Connection[Any]", Row], Cursor[Row]):
    __module__ = "psycopg"


class AsyncRawCursor(RawCursorMixin["AsyncConnection[Any]", Row], AsyncCursor[Row]):
    __module__ = "psycopg"

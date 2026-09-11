"""Infrastructure layer: External data loaders, file parsing, and hardware adapters.

Implements protocols defined in the domain layer.
"""

from infrastructure.aggregate_loader import (
    AGGREGATE_FILENAMES,
    AggregateLoader,
    load_aggregates,
)
from infrastructure.alias_resolver import (
    COMMON_PLAYER_ID_COLUMNS,
    AliasResolver,
    get_alias_resolver,
    resolve,
)
from infrastructure.event_loader import (
    EVENT_TABLE_NAMES,
    EventLoader,
    load_events,
)
from infrastructure.graph_builder import (
    GraphBuilder,
    GraphData,
    build_chance_graph,
)
from infrastructure.tracking_loader import (
    TRACKING_SCHEMA,
    TrackingLoader,
    load_tracking,
)

__all__ = [
    # Alias Resolver
    "AliasResolver",
    "resolve",
    "get_alias_resolver",
    "COMMON_PLAYER_ID_COLUMNS",
    # Event Loader
    "EventLoader",
    "load_events",
    "EVENT_TABLE_NAMES",
    # Tracking Loader
    "TrackingLoader",
    "load_tracking",
    "TRACKING_SCHEMA",
    # Aggregate Loader
    "AggregateLoader",
    "load_aggregates",
    "AGGREGATE_FILENAMES",
    # Graph Builder
    "GraphBuilder",
    "GraphData",
    "build_chance_graph",
]

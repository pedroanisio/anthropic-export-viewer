"""
API response contracts for the Anthropic Data Manager (drift-risk Finding #1).

These Pydantic models are the single source of truth for the JSON shapes that
the frontend templates (``src/templates/*.html``) consume. The template
JavaScript reads response fields by bare key (e.g. ``data.summary.total_conversations``,
``data.pagination.has_next``, ``data.account_distribution``). Nothing in the
language links those reads to the ad-hoc ``dict`` literals that ``app.py``
passes to ``jsonify(...)`` — so a renamed or dropped backend field silently
breaks the UI with no build, type, or test error.

⚠ ARCHITECTURAL CONTRACT (PALS's LAW) — LLM/handwritten output is unverified by
default. These models exist so that the response shape is verified explicitly:

* Every model sets ``extra="forbid"``. A response that gains an undeclared key,
  loses a declared one, or changes a type fails validation loudly.
* ``tests/test_response_contracts.py`` validates the live output of each
  endpoint against the matching model. A backend shape change now fails a test
  instead of silently emptying a chart.

These contracts mirror the returns in ``app.py`` as of the drift-risk map. When
``app.py`` becomes editable (it is currently lock-held by another agent under
the coordination protocol), the endpoints should construct and ``model_dump()``
these models directly, which additionally surfaces drift at the construction
site under ``mypy``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# --- Shared envelope pieces ---------------------------------------------------


class Pagination(BaseModel):
    """Pagination envelope shared by search and recent-items responses."""

    model_config = ConfigDict(extra="forbid")

    page: int
    per_page: int
    total_count: int
    total_pages: int
    has_prev: bool
    has_next: bool


# --- /api/stats/timeseries ----------------------------------------------------


class TimeseriesSummary(BaseModel):
    """``summary`` block of the timeseries response."""

    model_config = ConfigDict(extra="forbid")

    total_conversations: int
    total_messages: int
    avg_per_day: float
    data_span_days: int
    conversation_trend: int


class TimeseriesPoint(BaseModel):
    """A single day/week/month bucket inside ``time_series``."""

    model_config = ConfigDict(extra="forbid")

    date: str
    label: str
    conversations: int
    human_messages: int
    assistant_messages: int


class TimeseriesBuckets(BaseModel):
    """The ``time_series`` object with its three grouping granularities."""

    model_config = ConfigDict(extra="forbid")

    day: list[TimeseriesPoint]
    week: list[TimeseriesPoint]
    month: list[TimeseriesPoint]


class MessageDistribution(BaseModel):
    """``message_distribution`` block: human vs. assistant message counts."""

    model_config = ConfigDict(extra="forbid")

    human: int
    assistant: int


class AccountCount(BaseModel):
    """One entry of ``account_distribution``."""

    model_config = ConfigDict(extra="forbid")

    account: str
    count: int


class DayOfWeekCount(BaseModel):
    """One entry of ``day_of_week_distribution`` (0 = Sunday)."""

    model_config = ConfigDict(extra="forbid")

    day: int
    count: int


class HourCount(BaseModel):
    """One entry of ``hour_of_day_distribution`` (0-23)."""

    model_config = ConfigDict(extra="forbid")

    hour: int
    count: int


class LengthBucket(BaseModel):
    """One entry of ``length_distribution`` (conversation length buckets)."""

    model_config = ConfigDict(extra="forbid")

    bucket: str
    count: int


class TimeseriesResponse(BaseModel):
    """Full contract for ``GET /api/stats/timeseries``."""

    model_config = ConfigDict(extra="forbid")

    summary: TimeseriesSummary
    time_series: TimeseriesBuckets
    message_distribution: MessageDistribution
    account_distribution: list[AccountCount]
    day_of_week_distribution: list[DayOfWeekCount]
    hour_of_day_distribution: list[HourCount]
    length_distribution: list[LengthBucket]


# --- /api/stats/heatmap -------------------------------------------------------


class HeatmapStats(BaseModel):
    """``stats`` block of the heatmap response."""

    model_config = ConfigDict(extra="forbid")

    total_conversations: int
    active_days: int
    avg_per_day: float
    max_in_day: int


class HeatmapResponse(BaseModel):
    """Full contract for ``GET /api/stats/heatmap``."""

    model_config = ConfigDict(extra="forbid")

    year: int
    daily_counts: dict[str, int]
    stats: HeatmapStats
    available_years: list[int]


# --- /api/search/conversations ------------------------------------------------


class ConversationSearchItem(BaseModel):
    """
    One projected conversation in the search response.

    The ``$project`` stage in ``search_conversations`` emits exactly these
    fields. ``_id`` and ``_account_name`` keep their Mongo-style names (the
    templates read them verbatim), so they are declared via aliases. Optional
    fields tolerate documents that lack a value for the projected key.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mongo_id: str = Field(alias="_id")
    uuid: str | None = None
    name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    account_name: str | None = Field(default=None, alias="_account_name")
    message_count: int
    attachment_count: int
    artifact_count: int
    user_message_count: int
    assistant_message_count: int


class SortInfo(BaseModel):
    """``sort_info`` echo block of the search response."""

    model_config = ConfigDict(extra="forbid")

    sort_by: str
    sort_order: str


class SearchConversationsResponse(BaseModel):
    """Full contract for ``POST /api/search/conversations``."""

    model_config = ConfigDict(extra="forbid")

    conversations: list[ConversationSearchItem]
    pagination: Pagination
    sort_info: SortInfo

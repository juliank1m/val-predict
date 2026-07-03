from unittest.mock import MagicMock

from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Integer, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.models import PlayerMapStat
from app.services import scraper
from app.services.scraper import _extract_players, _insert_match_data


def _stats_html(player_href: str | None) -> BeautifulSoup:
    link = f'<a href="{player_href}"><span class="text-of">player</span></a>' if player_href else (
        '<span class="text-of">player</span>'
    )
    return BeautifulSoup(
        f"""
        <div class="vm-stats-game" data-game-id="456">
          <div class="vm-stats-game-header">
            <span class="team-name">Team One</span>
            <span class="team-name">Team Two</span>
          </div>
          <table class="wf-table-inset mod-overview"><tbody><tr>
            <td class="mod-player">{link}</td>
            <td class="mod-agents"><img title="Yoru"></td>
          </tr></tbody></table>
        </div>
        """,
        "html.parser",
    )


def test_extract_players_accepts_player_url_without_trailing_slash():
    rows = _extract_players(
        _stats_html("/player/12345"),
        {"team1": "Team One", "team2": "Team Two"},
        [{"game_id": 456, "match_id": 789}],
    )

    assert rows[0]["player_id"] == 12345


def test_insert_match_data_skips_stats_without_player_id(caplog):
    session = MagicMock()
    match = {
        "match_id": 789,
        "team1": "Team One",
        "team2": "Team Two",
        "team1_score": 2,
        "team2_score": 0,
        "winner": None,
        "date": None,
        "time": None,
        "event": None,
        "stage": None,
        "match_url": None,
    }
    players = [{
        "match_id": 789,
        "game_id": 456,
        "team_name": "Team One",
        "player_id": None,
        "player_name": "player",
    }]

    _insert_match_data(
        session,
        match,
        [],
        players,
        {"Team One": 1, "Team Two": 2},
        {},
    )

    added_stats = [
        call.args[0]
        for call in session.add.call_args_list
        if isinstance(call.args[0], PlayerMapStat)
    ]
    assert added_stats == []
    assert "Skipping player stats without a VLR player ID" in caplog.text


def test_recent_scrape_recovers_after_one_match_fails(monkeypatch):
    class TestBase(DeclarativeBase):
        pass

    class Write(TestBase):
        __tablename__ = "writes"

        id: Mapped[int] = mapped_column(primary_key=True)
        match_id: Mapped[int] = mapped_column(Integer, nullable=False)

    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE matches (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT)"))
        connection.execute(text("CREATE TABLE players (id INTEGER PRIMARY KEY)"))

    session_factory = sessionmaker(bind=engine)
    matches = [
        {
            "match_id": 1,
            "team1": "One",
            "team2": "Two",
            "match_url": "https://example.test/1",
        },
        {
            "match_id": 2,
            "team1": "Three",
            "team2": "Four",
            "match_url": "https://example.test/2",
        },
    ]

    monkeypatch.setattr(scraper, "SyncSessionLocal", session_factory)
    monkeypatch.setattr(scraper, "_fetch", lambda *_args: BeautifulSoup("", "html.parser"))
    monkeypatch.setattr(scraper, "_parse_results_page", lambda _soup: matches)
    monkeypatch.setattr(scraper, "_extract_games", lambda *_args: [])
    monkeypatch.setattr(scraper, "_extract_players", lambda *_args: [])
    monkeypatch.setattr(scraper.time, "sleep", lambda _seconds: None)

    def insert_match(session, match, *_args):
        session.add(Write(match_id=None if match["match_id"] == 1 else match["match_id"]))

    monkeypatch.setattr(scraper, "_insert_match_data", insert_match)

    assert scraper.scrape_recent_matches(pages=1) == 1
    with engine.connect() as connection:
        assert connection.execute(text("SELECT match_id FROM writes")).scalars().all() == [2]

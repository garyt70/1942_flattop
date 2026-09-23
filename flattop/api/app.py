"""
HTTP application API for the 1942 Flat Top web client.

This is a functional-prototype implementation of the command/projection
boundary described in docs/design/WEB_ARCHITECTURE.md: an in-memory game
store stands in for the PostgreSQL runtime store, and there is no
WebSocket/event stream yet. Game rules remain in the ``flattop`` domain
package; this module only adapts HTTP requests to domain commands and
side-filtered projections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from flattop.scenarios import ScenarioError, get_scenario, load_all_scenarios, scenario_catalog_summary
from flattop.web_session import CommandError, GameSession

app = FastAPI(title="1942 Flat Top API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GAMES: dict[str, GameSession] = {}


class NewGameRequest(BaseModel):
    scenario_id: str
    player_side: Literal["Allied", "Japanese", "allied", "japanese"]
    opponent: Literal["human", "computer"] = "computer"


class MoveRequest(BaseModel):
    side: str
    piece_id: str
    q: int
    r: int


class ReadinessMoveRequest(BaseModel):
    side: str
    base_id: str
    aircraft_type: str
    from_status: str
    to_status: str
    count: int


class FormationAircraft(BaseModel):
    type: str
    count: int


class CreateFormationRequest(BaseModel):
    side: str
    base_id: str
    formation_number: int
    aircraft: list[FormationAircraft]


def _get_session(game_id: str) -> GameSession:
    session = GAMES.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown game_id")
    return session


def _command_error_response(error: CommandError) -> dict[str, Any]:
    return {
        "accepted": False,
        "error": {"code": error.code, "message": error.message, "details": error.details},
    }


@app.get("/api/scenarios")
def list_scenarios():
    try:
        return [scenario_catalog_summary(s) for s in load_all_scenarios()]
    except ScenarioError as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/api/scenarios/{scenario_id}")
def get_scenario_detail(scenario_id: str):
    try:
        return scenario_catalog_summary(get_scenario(scenario_id))
    except ScenarioError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.post("/api/games")
def create_game(request: NewGameRequest):
    try:
        scenario = get_scenario(request.scenario_id)
    except ScenarioError as error:
        raise HTTPException(status_code=404, detail=str(error))

    session = GameSession(scenario, request.player_side, request.opponent)
    GAMES[session.id] = session
    return session.to_projection(request.player_side)


@app.get("/api/games/{game_id}")
def get_game(game_id: str, side: str):
    session = _get_session(game_id)
    return session.to_projection(side)


@app.post("/api/games/{game_id}/advance-phase")
def advance_phase(game_id: str, side: str):
    session = _get_session(game_id)
    session.advance_phase()
    return session.to_projection(side)


@app.post("/api/games/{game_id}/move")
def move_piece(game_id: str, request: MoveRequest):
    session = _get_session(game_id)
    try:
        session.move_piece(request.piece_id, request.q, request.r)
    except CommandError as error:
        return _command_error_response(error)
    return {"accepted": True, "projection": session.to_projection(request.side)}


@app.get("/api/games/{game_id}/units/{piece_id}/reachable")
def get_reachable_hexes(game_id: str, piece_id: str):
    session = _get_session(game_id)
    try:
        return {"hexes": session.reachable_hexes(piece_id)}
    except CommandError as error:
        raise HTTPException(status_code=404, detail=error.message)


@app.post("/api/games/{game_id}/air-ops/readiness")
def readiness_move(game_id: str, request: ReadinessMoveRequest):
    session = _get_session(game_id)
    try:
        session.readiness_move(
            request.base_id, request.aircraft_type, request.from_status, request.to_status, request.count
        )
    except CommandError as error:
        return _command_error_response(error)
    return {"accepted": True, "projection": session.to_projection(request.side)}


@app.post("/api/games/{game_id}/air-ops/formation")
def create_formation(game_id: str, request: CreateFormationRequest):
    session = _get_session(game_id)
    try:
        session.create_air_formation(
            request.base_id, request.formation_number, [entry.model_dump() for entry in request.aircraft]
        )
    except CommandError as error:
        return _command_error_response(error)
    return {"accepted": True, "projection": session.to_projection(request.side)}


_WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"
if _WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")

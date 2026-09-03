from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.application.usecases.search_games import SearchGames
from app.infrastructure.external.steam.steam_game_repository import (
    SteamGameRepository
)

app = FastAPI(title="DRIFT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = SteamGameRepository()
search_games = SearchGames(repository)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/games/search")
def search_games_endpoint(
    q: str = Query(..., min_length=1)
):
    games = search_games.execute(q)

    return [
        {
            "id": game.id,
            "name": game.name,
            "prices": game.prices
        }
        for game in games
    ]
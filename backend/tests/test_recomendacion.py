"""
Recomendación de compra: precio, compatibilidad y rendimiento juntos
(ADR-0019). Ninguna prueba usa la red.
"""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.application.usecases.recommend_purchase import RecommendPurchase
from app.domain.model.account import Device, PcSpecs
from app.domain.services.recommendation import (
    BETTER_EXPERIENCE,
    CHEAPEST,
    CONSOLE,
    INSUFFICIENT,
    MINIMUM,
    NOT_SOLD,
    ONLY_OPTION,
    RECOMMENDED,
    UNVERIFIED,
    DeviceVerdict,
    recommend,
)

client = TestClient(main.app)

PRICES = {"Steam": 100_000, "GOG": 90_000, "PlayStation": 120_000, "Xbox": 95_000}


def pc(experience, name="Mi PC"):
    return DeviceVerdict(name, name, "pc", experience)


PS5 = DeviceVerdict("ps5", "PS5", "playstation", CONSOLE)
SERIES = DeviceVerdict("xbox", "Series S", "xbox", CONSOLE)


# --- La regla ------------------------------------------------------------------


def test_without_devices_the_cheapest_store_wins():
    answer = recommend(PRICES, {"GOG": 10})

    assert answer.uses_devices is False
    assert (answer.best.store, answer.best.price, answer.best.discount) == (
        "GOG",
        90_000,
        10,
    )
    assert answer.reason == CHEAPEST
    assert answer.price_difference == 5_000
    # Después, la mejor tienda de cada otra plataforma.
    assert [option.store for option in answer.alternatives] == [
        "Xbox",
        "PlayStation",
    ]


def test_each_device_gets_the_cheapest_store_of_its_platform():
    answer = recommend(PRICES, devices=[pc(RECOMMENDED), PS5])

    assert answer.uses_devices is True
    assert answer.best.store == "GOG"
    assert answer.best.device.name == "Mi PC"
    assert answer.reason == CHEAPEST
    assert answer.price_difference == 30_000
    assert [option.store for option in answer.alternatives] == ["PlayStation"]


def test_a_pc_below_the_minimum_is_left_out_even_if_it_is_cheaper():
    answer = recommend(PRICES, devices=[pc(INSUFFICIENT), PS5])

    assert answer.best.store == "PlayStation"
    assert answer.reason == ONLY_OPTION
    assert [(item.device.name, item.reason) for item in answer.excluded] == [
        ("Mi PC", INSUFFICIENT)
    ]


def test_a_better_experience_wins_when_it_costs_a_little_more():
    # Xbox cuesta 5,6 % más que el PC, que solo alcanza los mínimos.
    answer = recommend(PRICES, devices=[pc(MINIMUM), SERIES])

    assert answer.best.store == "Xbox"
    assert answer.reason == BETTER_EXPERIENCE
    assert answer.price_difference == 5_000
    assert [option.store for option in answer.alternatives] == ["GOG"]


def test_a_better_experience_does_not_win_when_it_costs_much_more():
    # PlayStation cuesta 33 % más.
    answer = recommend(PRICES, devices=[pc(MINIMUM), PS5])

    assert answer.best.store == "GOG"
    assert answer.reason == CHEAPEST


def test_between_two_pcs_the_one_that_runs_it_better_is_recommended():
    answer = recommend(
        PRICES,
        devices=[pc(MINIMUM, "Portátil"), pc(RECOMMENDED, "Torre")],
    )

    assert answer.best.device.name == "Torre"
    assert answer.best.store == "GOG"


def test_a_device_whose_store_does_not_sell_the_game_is_left_out():
    answer = recommend({"Steam": 50_000}, devices=[PS5, pc(UNVERIFIED)])

    assert answer.best.store == "Steam"
    assert answer.best.experience == UNVERIFIED
    assert [(item.device.name, item.reason) for item in answer.excluded] == [
        ("PS5", NOT_SOLD)
    ]


def test_when_no_device_can_play_it_nothing_is_recommended():
    answer = recommend({"Steam": 50_000}, devices=[pc(INSUFFICIENT), PS5])

    assert answer.best is None
    assert len(answer.excluded) == 2


def test_two_consoles_of_the_same_kind_are_one_option():
    other = DeviceVerdict("ps4", "PS4", "playstation", CONSOLE)

    answer = recommend(PRICES, devices=[PS5, other])

    assert answer.reason == ONLY_OPTION
    assert answer.alternatives == []


def test_no_prices_no_recommendation():
    assert recommend({}).best is None
    assert recommend({}, devices=[PS5]).best is None


# --- El caso de uso ------------------------------------------------------------


class Compatibility:
    def __init__(self, status=None, levels=("recommended",), error=None):
        self.status = status
        self.levels = levels
        self.error = error
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)

        if self.error:
            raise self.error

        return {
            "status": self.status,
            "checks": [{"level": level} for level in self.levels],
        }


def my_pc():
    return Device(
        id="d1",
        user_id="u1",
        name="Torre",
        kind="pc",
        specs=PcSpecs(ram_gb=16, gpu_score=3, gpu_name="RTX 3060"),
    )


@pytest.mark.parametrize(
    "status, expected",
    [
        ("Compatible", RECOMMENDED),
        ("Compatible con limitaciones", MINIMUM),
        ("Requisitos no disponibles", UNVERIFIED),
    ],
)
def test_the_pc_experience_comes_from_the_compatibility_estimate(status, expected):
    compatibility = Compatibility(status)

    answer = RecommendPurchase(compatibility).execute(
        "620", {"Steam": 40_000}, devices=[my_pc()]
    )

    assert answer.best.experience == expected
    assert compatibility.calls[0]["game_id"] == 620
    assert compatibility.calls[0]["gpu_name"] == "RTX 3060"


def test_a_pc_that_does_not_reach_the_minimum_gets_no_recommendation():
    answer = RecommendPurchase(Compatibility("No compatible")).execute(
        "620", {"Steam": 40_000}, devices=[my_pc()]
    )

    assert answer.best is None
    assert answer.excluded[0].reason == INSUFFICIENT


def test_a_pc_is_unverified_when_nothing_could_be_compared():
    # Sin ningún componente comparado, «Compatible» no significa nada.
    compatibility = Compatibility("Compatible", levels=("unknown", "unknown"))

    answer = RecommendPurchase(compatibility).execute(
        "620", {"Steam": 40_000}, devices=[my_pc()]
    )

    assert answer.best.experience == UNVERIFIED


def test_when_the_requirements_source_fails_the_price_still_decides():
    compatibility = Compatibility(error=ConnectionError("Steam caído"))

    answer = RecommendPurchase(compatibility).execute(
        "620", {"Steam": 40_000}, devices=[my_pc()]
    )

    assert answer.best.store == "Steam"
    assert answer.best.experience == UNVERIFIED


def test_a_game_without_steam_id_is_not_checked_against_the_pc():
    compatibility = Compatibility("Compatible")

    answer = RecommendPurchase(compatibility).execute(
        "EP0001-ABC", {"GOG": 40_000}, devices=[my_pc()]
    )

    assert answer.best.experience == UNVERIFIED
    assert compatibility.calls == []


# --- La ruta -------------------------------------------------------------------


def test_recommendation_endpoint(monkeypatch):
    monkeypatch.setattr(
        main.recommend_purchase,
        "estimate_compatibility",
        Compatibility("Compatible con limitaciones", levels=("minimum",)),
    )

    response = client.post(
        "/games/620/recommendation",
        json={
            "prices": PRICES,
            "discounts": {"Xbox": 50},
            "devices": [
                {
                    "id": "d1",
                    "name": "Torre",
                    "kind": "pc",
                    "specs": {"ram_gb": 16, "gpu_score": 3},
                },
                {"name": "Series S", "kind": "xbox"},
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["uses_devices"] is True
    assert data["reason"] == "better_experience"
    assert data["price_difference"] == 5_000
    assert data["recommended"] == {
        "store": "Xbox",
        "platform": "Xbox",
        "price": 95_000,
        "discount": 50,
        "experience": "console",
        "device": {"id": "local-1", "name": "Series S", "kind": "xbox"},
    }
    assert data["alternatives"][0]["device"]["id"] == "d1"
    assert data["excluded"] == []


def test_recommendation_endpoint_without_devices():
    data = client.post(
        "/games/620/recommendation", json={"prices": {"Steam": 40_000}}
    ).json()

    assert data["uses_devices"] is False
    assert data["recommended"]["store"] == "Steam"
    assert data["recommended"]["device"] is None
    assert data["reason"] == "only_option"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"prices": {"Steam": -1}},
        {"prices": {" ": 10}},
        {"prices": {"Steam": 10}, "devices": [{"name": "X", "kind": "switch"}]},
        # Un PC sin su equipo y una consola con componentes de PC.
        {"prices": {"Steam": 10}, "devices": [{"name": "X", "kind": "pc"}]},
        {
            "prices": {"Steam": 10},
            "devices": [
                {
                    "name": "X",
                    "kind": "xbox",
                    "specs": {"ram_gb": 8, "gpu_score": 2},
                }
            ],
        },
        {
            "prices": {"Steam": 10},
            "devices": [{"name": "X", "kind": "xbox"}] * 11,
        },
    ],
)
def test_recommendation_endpoint_rejects_invalid_bodies(body):
    assert client.post("/games/620/recommendation", json=body).status_code == 422

import httpx
import pytest

import ai_filter
from ai_filter import AIFilter

YES = {"choices": [{"message": {"content": " yes"}}]}
NO = {"choices": [{"message": {"content": "NO"}}]}


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    async def instant(_):
        pass

    monkeypatch.setattr(ai_filter.asyncio, "sleep", instant)


def _respond(status, body):
    return httpx.Response(status, json=body)


async def classify(responses):
    it = iter(responses)
    f = AIFilter()
    f.client = httpx.AsyncClient(transport=httpx.MockTransport(lambda req: _respond(*next(it))))
    try:
        return await f.is_important("python developer kerak")
    finally:
        await f.close()


@pytest.mark.parametrize(
    "responses, expected",
    [
        ([(200, YES)], True),
        ([(200, NO)], False),
        ([(503, {}), (429, {}), (200, YES)], True),  # qayta urinish
        ([(401, {"error": "bad token"})], None),  # qayta urinilmaydi
        ([(200, {"unexpected": 1})], None),
        ([(503, {})] * 4, None),
    ],
)
async def test_is_important(responses, expected):
    assert await classify(responses) is expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Python dasturchi kerak, masofaviy", True),
        ("Salom hammaga, bugun havo zo'r ekan", False),
        ("ish", False),  # juda qisqa
    ],
)
def test_prefilter(text, expected):
    assert AIFilter.passes_prefilter(text) is expected

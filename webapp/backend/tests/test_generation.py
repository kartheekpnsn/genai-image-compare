from webapp.backend import generation


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    def generate(self, prompt):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_generate_all_returns_one_result_per_client():
    clients = {
        "GPT-Image": _FakeClient(b"\x89PNG-gpt"),
        "MAI-Image-2e": _FakeClient(b"\x89PNG-mai"),
    }
    results = generation.generate_all("a cat", clients)
    by_model = {r["model"]: r for r in results}
    assert set(by_model) == {"GPT-Image", "MAI-Image-2e"}
    assert by_model["GPT-Image"]["error"] is None
    assert by_model["GPT-Image"]["image_b64"]  # base64 string
    assert by_model["GPT-Image"]["seconds"] >= 0


def test_generate_all_isolates_failures():
    clients = {
        "GPT-Image": _FakeClient(b"\x89PNG"),
        "MAI-Image-2e": _FakeClient(RuntimeError("boom")),
    }
    by_model = {r["model"]: r for r in generation.generate_all("x", clients)}
    assert by_model["GPT-Image"]["error"] is None
    assert by_model["MAI-Image-2e"]["image_b64"] is None
    assert "boom" in by_model["MAI-Image-2e"]["error"]

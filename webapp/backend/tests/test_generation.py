from webapp.backend import generation


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    def generate(self, prompt):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_generate_stream_returns_one_result_per_client():
    clients = {
        "GPT-Image": _FakeClient(b"\x89PNG-gpt"),
        "MAI-Image-2e": _FakeClient(b"\x89PNG-mai"),
    }
    results = list(generation.generate_stream("a cat", clients))
    by_model = {r["model"]: r for r in results}
    assert set(by_model) == {"GPT-Image", "MAI-Image-2e"}
    assert by_model["GPT-Image"]["error"] is None
    assert by_model["GPT-Image"]["image_b64"]
    assert by_model["GPT-Image"]["seconds"] >= 0


def test_generate_stream_isolates_failures():
    clients = {
        "GPT-Image": _FakeClient(b"\x89PNG"),
        "MAI-Image-2e": _FakeClient(RuntimeError("boom")),
    }
    by_model = {r["model"]: r for r in generation.generate_stream("x", clients)}
    assert by_model["GPT-Image"]["error"] is None
    assert by_model["MAI-Image-2e"]["image_b64"] is None
    assert "boom" in by_model["MAI-Image-2e"]["error"]


def test_generate_stream_is_a_generator():
    clients = {"M1": _FakeClient(b"\x89PNG")}
    result = generation.generate_stream("x", clients)
    # Must be a generator, not a list
    import types
    assert isinstance(result, types.GeneratorType)

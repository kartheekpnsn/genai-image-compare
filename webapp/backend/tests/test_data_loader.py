from webapp.backend import data_loader


def test_load_prompts_returns_all_twelve():
    prompts = data_loader.load_prompts()
    assert len(prompts) == 12
    first = prompts["prompt-1"]
    assert first["category"] == "Text Rendering"
    assert "latte" in first["prompt"].lower()


def test_discover_models_finds_four():
    models = data_loader.discover_models()
    assert set(models) == {
        "GPT-Image",
        "MAI-Image-2.5",
        "MAI-Image-2.5-Flash",
        "MAI-Image-2e",
    }


def test_image_path_points_at_png():
    p = data_loader.image_path("GPT-Image", "prompt-1")
    assert p.name == "prompt-1.png"
    assert p.parent.name == "GPT-Image"
    assert p.exists()

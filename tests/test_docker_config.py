"""
Tests for the Docker config generation (docker/generate_config.sh + docker/template_config.yml).
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, meta

DOCKER_DIR = Path(__file__).parent.parent / "docker"
VENV_BIN = Path(sys.executable).parent

# Environment variable -> where it ends up in config.yml
STRING_VARS = {
    "INPUT_PATH": ("gallery", "input_path"),
    "OUTPUT_PATH": ("gallery", "output_path"),
    "RECURSIVE_NAME_PATTERN": ("gallery", "albums", "recursive_name_pattern"),
    "WATERMARK_PATH": ("gallery", "watermark", "path"),
    "SITE_ROOT": ("site", "http_root"),
    "SITE_TITLE": ("site", "title"),
}

DEFAULTS = {
    "OUTPUT_PATH": "site/",
    "RECURSIVE_NAME_PATTERN": "{parent_album} > {album}",
    "WATERMARK_PATH": "web/src/images/fussel-watermark.png",
    "SITE_ROOT": "/",
    "SITE_TITLE": "Fussel Gallery",
}

AWKWARD_STRINGS = [
    "{parent_album} > {album}",
    '"{parent_album} > {album}"',  # what docker compose passes for a quoted default
    'Dad\'s "best" photos',
    "back\\slash",
    "key: value # not a comment",
    "null",
    "Ünïcödé 日本 🎉",
]


def render(**env):
    """Run generate_config.sh with only the given environment variables and return the parsed config."""
    if not (VENV_BIN / "jinja2").exists():
        pytest.skip("jinja2-cli is not installed")

    result = subprocess.run(
        [str(DOCKER_DIR / "generate_config.sh"), str(DOCKER_DIR / "template_config.yml")],
        env={"PATH": f"{VENV_BIN}:/usr/bin:/bin", "INPUT_PATH": "/input", **env},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return yaml.safe_load(result.stdout)


def lookup(config, path):
    for key in path:
        config = config[key]
    return config


def test_defaults_when_nothing_is_set():
    config = render()

    assert config["gallery"]["input_path"] == "/input"
    for var, expected in DEFAULTS.items():
        assert lookup(config, STRING_VARS[var]) == expected, var
    assert config["gallery"]["overwrite"] is False
    assert config["gallery"]["exif_transpose"] is False
    assert config["gallery"]["parallel_tasks"] == 1
    assert config["gallery"]["albums"]["recursive"] is True
    assert config["gallery"]["people"]["enable"] is True
    assert config["gallery"]["watermark"]["enable"] is True
    assert config["gallery"]["watermark"]["size_ratio"] == 0.3


def test_non_string_values_keep_their_type():
    config = render(
        OVERWRITE="True",
        EXIF_TRANSPOSE="True",
        ALLOW_DOWNLOAD="False",
        RECURSIVE="False",
        FACE_TAG_ENABLE="False",
        WATERMARK_ENABLE="False",
        WATERMARK_SIZE_RATIO="0.5",
        PARALLEL_TASKS="4",
    )

    assert config["gallery"]["overwrite"] is True
    assert config["gallery"]["exif_transpose"] is True
    assert config["gallery"]["allow_download"] is False
    assert config["gallery"]["albums"]["recursive"] is False
    assert config["gallery"]["people"]["enable"] is False
    assert config["gallery"]["watermark"]["enable"] is False
    assert config["gallery"]["watermark"]["size_ratio"] == 0.5
    assert config["gallery"]["parallel_tasks"] == 4


@pytest.mark.parametrize("value", AWKWARD_STRINGS)
def test_string_values_round_trip_unchanged(value):
    config = render(SITE_TITLE=value)

    assert config["site"]["title"] == value


@pytest.mark.parametrize("var", sorted(STRING_VARS))
def test_every_string_variable_is_escaped(var):
    value = 'Dad\'s "best" \\ {photos}'

    assert lookup(render(**{var: value}), STRING_VARS[var]) == value


@pytest.mark.parametrize("var", sorted(DEFAULTS))
def test_empty_string_values_fall_back_to_the_default(var):
    config = render(**{var: ""})

    assert lookup(config, STRING_VARS[var]) == DEFAULTS[var]


def test_every_template_variable_is_wired_through_script_and_compose():
    template = (DOCKER_DIR / "template_config.yml").read_text()
    script = (DOCKER_DIR / "generate_config.sh").read_text()
    compose = (DOCKER_DIR.parent / "docker-compose.yml").read_text()

    used = meta.find_undeclared_variables(Environment().parse(template))

    assert [var for var in sorted(used) if f"-D {var}=" not in script] == []
    assert [var for var in sorted(used) if f"- {var}=" not in compose] == []

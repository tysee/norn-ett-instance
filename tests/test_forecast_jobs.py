import re
from pathlib import Path

import yaml


def test_forecast_jobs_shape():
    for name in ["ot_baseline.yml", "ot_timesfm.yml", "ot_timesfm_xreg.yml"]:
        job = yaml.safe_load(Path("forecasts", name).read_text())
        assert job["metric"] == "ot"
        assert job["source"] == "fct_ot"
        assert job["grain"] == "hourly"
        assert job["dimensions"] == ["dataset", "feature"]


def test_model_variants():
    base = yaml.safe_load(Path("forecasts/ot_baseline.yml").read_text())
    assert base["model"] == "baseline-seasonal-naive"
    assert base["horizon"] == 24
    assert base["seasonality"] == 24

    tfm = yaml.safe_load(Path("forecasts/ot_timesfm.yml").read_text())
    assert tfm["model"] == "timesfm-2.5"

    xreg = yaml.safe_load(Path("forecasts/ot_timesfm_xreg.yml").read_text())
    assert xreg["use_dependencies"] is True


def test_deps_shape():
    seg_re = re.compile(r"^dataset=ETT(h1|h2)\|feature=.+$")
    deps = sorted(Path("forecasts/deps").glob("*.yml"))
    assert deps, "expected at least one dependency spec"
    for path in deps:
        dep = yaml.safe_load(path.read_text())
        assert dep["metric"] == "reading"
        assert dep["mart"] == "mart_metric"
        assert seg_re.match(dep["source_segment"])
        assert seg_re.match(dep["target_segment"])
        assert dep["target_segment"].endswith("|feature=ot")
        assert dep["max_lag"] == 48

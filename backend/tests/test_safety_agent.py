from app.agents.safety_agent import SafetyStaticResult, run_safety_static
from app.config import settings
from app.services.classifier import SpeciesResult
from app.services.safety_data import load_safety_data

load_safety_data(settings)


def make_predictions(top_confidence: float, runner_up: float = 0.01) -> list[SpeciesResult]:
    return [
        SpeciesResult(species="test_species", confidence=top_confidence),
        SpeciesResult(species="other_species", confidence=runner_up),
    ]


def test_below_floor_danger():
    """Confidence below floor returns 'danger' verdict immediately."""
    predictions = make_predictions(0.10)
    result = run_safety_static(species_class_name="goldenrod", predictions=predictions, state_abbr=None)
    assert result.safety_verdict == "danger"
    assert "Couldn't identify" in result.warning_message


def test_low_confidence_uncertain():
    """Confidence below uncertain threshold returns 'caution' verdict."""
    predictions = make_predictions(0.35, runner_up=0.30)
    result = run_safety_static(species_class_name="goldenrod", predictions=predictions, state_abbr=None)
    assert result.confidence_tier == "uncertain"
    assert result.safety_verdict == "caution"
    assert "Low confidence" in result.warning_message


def test_high_confidence_returns_verdict_from_data():
    """High confidence returns the safety verdict from the curated data."""
    predictions = make_predictions(0.78, runner_up=0.01)
    result = run_safety_static(species_class_name="goldenrod", predictions=predictions, state_abbr=None)
    assert result.safety_verdict in ("safe", "caution", "danger")


def test_ramps_lookalike_findings():
    """Ramps has danger-level lookalike findings."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="ramps", predictions=predictions, state_abbr=None)
    assert len(result.lookalike_findings) > 0
    assert result.lookalike_findings[0]["danger_level"] == "danger"


def test_ramps_safety_info_includes_sources():
    """Safety info includes edibility, preparation, and sources."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="ramps", predictions=predictions, state_abbr=None)
    assert result.safety_info["edibility"] is not None
    assert len(result.safety_info["sources"]) > 0


def test_ramps_protected_in_nc():
    """Ramps in NC triggers protection findings."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="ramps", predictions=predictions, state_abbr="NC")
    assert len(result.protection_findings) > 0


def test_ramps_not_protected_in_ohio():
    """Ramps in OH triggers no protection findings."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="ramps", predictions=predictions, state_abbr="OH")
    assert result.protection_findings == []


def test_toxic_species_danger():
    """Toxic species returns danger verdict."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="poison_hemlock", predictions=predictions, state_abbr=None)
    assert result.safety_verdict == "danger"


def test_no_location_runs_successfully():
    """Static checks complete when state_abbr is None."""
    predictions = make_predictions(0.98)
    result = run_safety_static(species_class_name="goldenrod", predictions=predictions, state_abbr=None)
    assert isinstance(result, SafetyStaticResult)


def test_edibility_is_list():
    """Edibility field is returned as a list."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="dandelion", predictions=predictions, state_abbr=None)
    assert isinstance(result.safety_info["edibility"], list)
    assert "edible" in result.safety_info["edibility"]


def test_dual_category_edibility():
    """Dual-category species returns both edible and medicinal."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="dandelion", predictions=predictions, state_abbr=None)
    assert "edible" in result.safety_info["edibility"]
    assert "medicinal" in result.safety_info["edibility"]


def test_preparation_is_dict():
    """Preparation field is returned as a dict with category keys."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="dandelion", predictions=predictions, state_abbr=None)
    prep = result.safety_info["preparation"]
    assert isinstance(prep, dict)
    assert "edible" in prep


def test_medicinal_only_species():
    """Medicinal-only species has medicinal prep but no edible prep."""
    predictions = make_predictions(0.90)
    result = run_safety_static(species_class_name="turkey_tail", predictions=predictions, state_abbr=None)
    assert result.safety_info["edibility"] == ["medicinal"]
    prep = result.safety_info["preparation"]
    assert "medicinal" in prep
    assert "edible" not in prep

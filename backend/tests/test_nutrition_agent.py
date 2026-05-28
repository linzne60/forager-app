from app.config import settings
from app.services.nutrition_data import get_nutrition, load_nutrition_data

load_nutrition_data(settings)


def test_nutrition_found():
    result = get_nutrition("watercress")
    assert result is not None
    assert result["species"] == "watercress"
    assert "calories_per_100g" in result


def test_nutrition_not_found():
    result = get_nutrition("not_a_real_species")
    assert result is None

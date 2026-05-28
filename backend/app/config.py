from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # app
    app_name: str = "Forager"
    debug: bool = False

    # database
    database_url: str = ""

    # redis
    redis_url: str = ""

    # auth
    secret_key: str = ""
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    # Ollama
    ollama_base_url: str = ""
    ollama_model: str = "gemma3:4b"

    # llm provider
    llm_provider: str = "google"
    llm_api_key: str = ""
    llm_api_model: str = "gemini-2.0-flash"

    # safety data
    safety_lookalikes_path: Path = Path(__file__).resolve().parent / "data" / "safety" / "lookalikes.json"
    safety_protected_path: Path = Path(__file__).resolve().parent / "data" / "safety" / "protected_species.json"
    safety_knowledge_base_path: Path = Path(__file__).resolve().parent / "data" / "safety" / "knowledge_base.json"

    # knowledge model
    knowledge_model: str = "all-MiniLM-L6-v2"

    # urls — override in .env for production
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # cors
    # default to localhost for development, can be overridden in .env for production
    cors_origins: list[str] = ["http://localhost:5173"]

    # cv model
    cv_model_onnx_path: Path = Path(__file__).resolve().parents[2] / "ml" / "models" / "plant_classifier.onnx"
    cv_class_map_path: Path = Path(__file__).resolve().parents[2] / "ml" / "data" / "splits" / "class_map.json"
    cv_classifier_weights_path: Path = Path(__file__).resolve().parents[2] / "ml" / "models" / "classifier_weights.json"
    
    cv_confidence_floor: float = 0.25
    cv_confidence_uncertain: float = 0.40
    cv_confidence_strong: float = 0.60
    cv_ratio_strong: float = 5.0
    cv_ratio_possible: float = 2.0

    cv_img_size: int = 600
    media_dir: Path = Path(__file__).resolve().parents[2] / "media"

    # USDA FoodData Central
    usda_api_key: str = ""
    usda_api_base_url: str = "https://api.nal.usda.gov/fdc/v1"

    # nutrition data
    nutrition_data_path: Path = Path(__file__).resolve().parent / "data" / "nutrition" / "nutrition_data.json"

settings = Settings()

from __future__ import annotations

import os
import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_user_data_dir() -> Path:
    """Default Playwright persistent profile dir (OS layout similar to Chrome, separate from real Chrome)."""
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/xautomation/ChromiumProfile"
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / "xautomation" / "ChromiumProfile"
        return home / "AppData" / "Local" / "xautomation" / "ChromiumProfile"
    return home / ".local/share/xautomation/chromium-profile"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    x_user_data_dir: Path = Field(
        default=Path("./automation-chrome"),
        validation_alias="X_USER_DATA_DIR",
    )
    playwright_channel: str = Field(default="", validation_alias="PLAYWRIGHT_CHANNEL")

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_BASE_URL")
    llm_model: str = Field(default="gpt-4o-mini", validation_alias="LLM_MODEL")
    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8765, validation_alias="API_PORT")
    api_token: str = Field(default="", validation_alias="API_TOKEN")

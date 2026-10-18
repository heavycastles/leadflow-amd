import os

# Keep the suite hermetic: never hit a live endpoint even if a real key / .env is loaded in the shell.
for _var in (
    "AMD_TOKEN_FACTORY_API_KEY", "RADEON_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL",
    "AMD_TOKEN_FACTORY_BASE_URL", "TOKEN_FACTORY_BASE_URL", "AMD_TOKEN_FACTORY_MODEL", "LLM_TIMEOUT",
):
    os.environ.pop(_var, None)
os.environ["LLM_BACKEND"] = "mock"

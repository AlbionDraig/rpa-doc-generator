from pydantic import BaseModel


class RootResponse(BaseModel):
    message: str
    version: str
    docs: str
    redoc: str
    health: str


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    timestamp: str


class ArtifactGenerationResponse(BaseModel):
    status: str
    session_id: str
    proyecto: str
    archivos_salida: dict[str, str]
    output_directory: str


class ApiErrorResponse(BaseModel):
    error: str
    code: str

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TipoActivo(str, Enum):
    hardware = "hardware"
    software = "software"
    datos = "datos"
    servicio = "servicio"
    personal = "personal"


class Activo(BaseModel):
    id: str
    nombre: str
    tipo: TipoActivo
    propietario: str
    valor_confidencialidad: int = Field(ge=0, le=10)
    valor_integridad: int = Field(ge=0, le=10)
    valor_disponibilidad: int = Field(ge=0, le=10)


class Amenaza(BaseModel):
    id: str
    nombre: str
    categoria: str  # natural, industrial, errores_humanos, ataques_deliberados
    probabilidad_base: float = Field(ge=0, le=1)


class Vulnerabilidad(BaseModel):
    id: str
    activo_id: str
    descripcion: str
    facilidad_explotacion: str  # baja, media, alta


class NivelRiesgo(str, Enum):
    bajo = "bajo"
    medio = "medio"
    alto = "alto"
    critico = "critico"


class Riesgo(BaseModel):
    id: str
    activo_id: str
    amenaza_id: str
    vulnerabilidad_id: str
    probabilidad: float = Field(ge=0, le=1)
    impacto: float = Field(ge=0, le=10)
    valor_riesgo: float  # se calcula: probabilidad * impacto
    nivel: NivelRiesgo


class Salvaguarda(BaseModel):
    id: str
    nombre: str
    tipo: str
    eficacia: float = Field(ge=0, le=1)
    riesgos_mitigados: list[str] = []  # ids de Riesgo


class Hallazgo(BaseModel):
    id: str
    riesgo_id: str
    fuente_ia: str  # ej. "claude-sonnet-5", "gpt-5"
    confianza_ia: float = Field(ge=0, le=1)
    prioridad: str  # baja, media, alta, deal_breaker (para M&A)
    estado: str = "pendiente"  # pendiente, revisado, resuelto
    creado_en: datetime = Field(default_factory=datetime.now)
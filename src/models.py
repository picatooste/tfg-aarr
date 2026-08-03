from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# GRUPO 1 — VOCABULARIOS CONTROLADOS
# =============================================================================

class Ocurrencia(str, Enum):
    """Frecuencia con la que se estima que ocurre una amenaza."""
    no_aplica = "N/A"
    anual = "Anual"
    mensual = "Mensual"
    semanal = "Semanal"


class NivelImpacto(str, Enum):
    """Nivel cualitativo de impacto economico u operacional."""
    no_aplica = "N/A"
    limitado = "Limitado"
    medio = "Medio"
    relevante = "Relevante"


class TipoAmenaza(str, Enum):
    """Categorias del catalogo de amenazas."""
    ataques_intencionados = "Ataques intencionados"
    errores_no_intencionados = "Errores y fallos no intencionados"
    desastres_naturales = "Desastres naturales"
    fallos_tecnicos = "Fallos tecnicos"


class GradoDependencia(str, Enum):
    """Nivel de acoplamiento con un servicio o aplicacion externa."""
    no_aplica = "N/A"
    parcial = "Parcial"
    total = "Total"


class NivelPermisos(str, Enum):
    sin_admin = "sin admin"
    admin_restringido = "admin restringido"
    admin_total = "admin a todos los roles"


class ModeloServicio(str, Enum):
    iaas = "IaaS"
    paas = "PaaS"
    saas = "SaaS"


class TipoHost(str, Enum):
    on_prem = "OnPrem"
    cloud = "Cloud"
    hibrido = "Hibrido"


class NivelRiesgo(str, Enum):
    bajo = "bajo"
    medio = "medio"
    alto = "alto"
    critico = "critico"


class TipoUsuario(str, Enum):
    interno = "Interno"
    externo = "Externo"


# =============================================================================
# GRUPO 2 — FICHA DE APLICACION (INPUT)
# =============================================================================

class GrupoUsuarios(BaseModel):
    """Un grupo de usuarios de la aplicacion con sus permisos."""
    nombre: str
    tipo: TipoUsuario
    numero_usuarios: int = Field(ge=0)
    permisos: NivelPermisos


class ServicioIT(BaseModel):
    """
    Servicio corporativo (ej. WAS) que la aplicacion usa o no.
    Los servicios y su lista son fijos por compania.
    """
    nombre: str
    utiliza: bool
    dependencia: GradoDependencia = GradoDependencia.no_aplica


class DependenciaApp(BaseModel):
    """Dependencia con otra aplicacion del catalogo interno."""
    nombre_app: str
    grado: GradoDependencia


class EstadoTecnico(BaseModel):
    """Indicadores tecnicos objetivos que informan el analisis de riesgo."""
    amenazas_dast_identificadas: int = Field(ge=0, default=0)
    amenazas_dast_corregidas: int = Field(ge=0, default=0)
    amenazas_sast_identificadas: int = Field(ge=0, default=0)
    amenazas_sast_corregidas: int = Field(ge=0, default=0)
    porcentaje_obsolescencia: float = Field(ge=0, le=100, default=0)
    uso_cpu: float = Field(ge=0, default=0)  # unidades libres (nucleos, MHz, etc)
    uso_memoria_porcentaje: float = Field(ge=0, le=100, default=0)
    uso_almacenamiento_porcentaje: float = Field(ge=0, le=100, default=0)


class FichaAplicacion(BaseModel):
    """
    Ficha completa de una aplicacion. Es la entrada al proceso de AARR.
    Se rellena una vez con el Service Manager y se actualiza
    periodicamente.
    """
    # Identificacion
    nombre: str
    descripcion: str
    area_responsable: str
    service_manager: str
    arquitecto: str

    # Modelo de despliegue
    modelo_servicio: ModeloServicio
    proveedor: str
    host: TipoHost

    # Arquitectura
    servicios_it: list[ServicioIT] = []

    # Usuarios
    tiene_usuarios_internos: bool
    tiene_usuarios_proveedores: bool
    tiene_usuarios_clientes: bool
    grupos_usuarios: list[GrupoUsuarios] = []

    # Dependencias con otras apps
    dependencias: list[DependenciaApp] = []

    # Estado tecnico actual
    estado_tecnico: EstadoTecnico = Field(default_factory=EstadoTecnico)

    # Metadatos
    fecha_actualizacion: datetime = Field(default_factory=datetime.now)


# =============================================================================
# GRUPO 3 — CATALOGOS FIJOS
# =============================================================================

class Amenaza(BaseModel):
    """Una amenaza del catalogo corporativo. Los ids son estables."""
    id: str  # ej. AME-001
    nombre: str  # ej. "Manipulacion de programas"
    tipo: TipoAmenaza
    descripcion: str = ""


class Salvaguarda(BaseModel):
    """Una salvaguarda del catalogo corporativo."""
    id: str  # ej. SAL-001
    nombre: str  # ej. "Cifrado de datos en reposo"
    descripcion: str = ""


class MitigacionAmenaza(BaseModel):
    """
    Fila de la matriz de mitigacion: que grado de mitigacion aporta
    una salvaguarda sobre una amenaza concreta. Si una salvaguarda no
    mitiga una amenaza dada, simplemente no existe la fila.
    """
    salvaguarda_id: str
    amenaza_id: str
    grado_mitigacion: float = Field(ge=0, le=1)  # 0 = no mitiga; 1 = mitiga totalmente


# =============================================================================
# GRUPO 4 — VALORACIONES Y RESULTADOS
# =============================================================================

class ValoracionAmenaza(BaseModel):
    """
    Valoracion de una amenaza aplicada a una aplicacion concreta.
    La produce el LLM y/o valida el analista humano.
    """
    amenaza_id: str
    ocurrencia: Ocurrencia
    impacto_economico: NivelImpacto
    impacto_operacional: NivelImpacto
    justificacion: str
    fuente: str = "llm"  # "llm" o "humano" o "llm_ajustado_humano"


class SalvaguardaImplantada(BaseModel):
    """Salvaguarda del catalogo que esta implantada para una app."""
    salvaguarda_id: str
    implantada: bool = True
    comentario: str = ""


class RiesgoInherente(BaseModel):
    """Riesgo antes de aplicar salvaguardas. Uno por amenaza analizada."""
    amenaza_id: str
    peso_ocurrencia: float
    peso_impacto_promedio: float  # promedio de imp. economico y operacional
    valor: float
    nivel: NivelRiesgo


class RiesgoResidual(BaseModel):
    """
    Riesgo tras aplicar el efecto conjunto de las salvaguardas
    implantadas que mitigan la amenaza.
    """
    amenaza_id: str
    valor_inherente: float
    reduccion_total: float = Field(ge=0, le=1)
    valor_residual: float
    nivel: NivelRiesgo
    salvaguardas_aplicadas: list[str] = []  # ids


class HallazgoLLM_Valoracion(BaseModel):
    """
    Esquema simplificado que el LLM debe generar cuando se le pide
    valorar UNA amenaza contra UNA ficha. Se construye ValoracionAmenaza
    a partir de este objeto anadiendo la fuente.
    """
    ocurrencia: Ocurrencia
    impacto_economico: NivelImpacto
    impacto_operacional: NivelImpacto
    justificacion: str


class InformeAARR(BaseModel):
    """
    Resultado completo de analizar una aplicacion. Contiene todas las
    valoraciones, los riesgos calculados y la trazabilidad de la fuente
    (que modelo produjo cada valoracion).
    """
    aplicacion: str
    fecha_analisis: datetime = Field(default_factory=datetime.now)
    modelo_ia: str  # ej. "claude-sonnet-5"
    valoraciones: list[ValoracionAmenaza] = []
    riesgos_inherentes: list[RiesgoInherente] = []
    salvaguardas_implantadas: list[SalvaguardaImplantada] = []
    riesgos_residuales: list[RiesgoResidual] = []
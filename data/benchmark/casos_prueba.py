"""
Dataset de casos de prueba para benchmark del clasificador de riesgos.

Cada caso incluye una descripcion sintetica de un escenario de riesgo
y metadatos para poder analizar los resultados por categoria.
"""

CASOS_PRUEBA = [
    # === DATOS ===
    {
        "id": "C01",
        "categoria_activo": "datos",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "media",
        "descripcion": "Fallo de cifrado en base de datos de clientes que contiene datos personales sensibles.",
    },
    {
        "id": "C02",
        "categoria_activo": "datos",
        "categoria_amenaza": "errores_humanos",
        "complejidad": "baja",
        "descripcion": "Un empleado envia por error un fichero con datos de nomina a una lista de distribucion externa.",
    },
    {
        "id": "C03",
        "categoria_activo": "datos",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "alta",
        "descripcion": "Fuga de credenciales de administrador en un repositorio publico de GitHub, expuestas durante 48 horas.",
    },
    # === SOFTWARE ===
    {
        "id": "C04",
        "categoria_activo": "software",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "media",
        "descripcion": "Sistema ERP corporativo sin parche aplicado para vulnerabilidad critica (CVE con exploit publico).",
    },
    {
        "id": "C05",
        "categoria_activo": "software",
        "categoria_amenaza": "errores_humanos",
        "complejidad": "baja",
        "descripcion": "Aplicacion web en produccion desplegada con la configuracion de depuracion activada.",
    },
    {
        "id": "C06",
        "categoria_activo": "software",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "alta",
        "descripcion": "Ataque de cadena de suministro: libreria de terceros usada en produccion incluye codigo malicioso en su ultima version.",
    },
    # === HARDWARE ===
    {
        "id": "C07",
        "categoria_activo": "hardware",
        "categoria_amenaza": "naturales",
        "complejidad": "baja",
        "descripcion": "El CPD principal esta ubicado en una zona con riesgo de inundacion documentado.",
    },
    {
        "id": "C08",
        "categoria_activo": "hardware",
        "categoria_amenaza": "industriales",
        "complejidad": "media",
        "descripcion": "Corte de suministro electrico prolongado sin SAI dimensionado para mantener servicios criticos.",
    },
    {
        "id": "C09",
        "categoria_activo": "hardware",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "alta",
        "descripcion": "Robo fisico de un portatil sin cifrado de disco que contiene informacion de clientes.",
    },
    # === SERVICIO ===
    {
        "id": "C10",
        "categoria_activo": "servicio",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "media",
        "descripcion": "Ataque de denegacion de servicio distribuido (DDoS) contra la web corporativa en periodo de campana de ventas.",
    },
    {
        "id": "C11",
        "categoria_activo": "servicio",
        "categoria_amenaza": "errores_humanos",
        "complejidad": "media",
        "descripcion": "Un administrador borra por error la instancia de produccion de un servicio cloud en horario laboral.",
    },
    {
        "id": "C12",
        "categoria_activo": "servicio",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "alta",
        "descripcion": "Compromiso del proveedor de identidad SSO externo, afectando a todos los servicios corporativos autenticados con el.",
    },
    # === PERSONAL ===
    {
        "id": "C13",
        "categoria_activo": "personal",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "media",
        "descripcion": "Campana de phishing dirigida (spear phishing) contra directivos financieros de la organizacion.",
    },
    {
        "id": "C14",
        "categoria_activo": "personal",
        "categoria_amenaza": "errores_humanos",
        "complejidad": "baja",
        "descripcion": "Personal no tecnico sin formacion en concienciacion de seguridad, con acceso a sistemas criticos.",
    },
    {
        "id": "C15",
        "categoria_activo": "personal",
        "categoria_amenaza": "ataques_deliberados",
        "complejidad": "alta",
        "descripcion": "Insider threat: empleado con acceso privilegiado en periodo de despido, con indicios de descarga masiva de datos.",
    },
]
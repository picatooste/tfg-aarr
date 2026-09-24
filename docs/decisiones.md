# Bitácora de decisiones — TFG AARR

Registro de decisiones técnicas y metodológicas tomadas durante el
desarrollo. Cada entrada sirve como material de referencia para la memoria.

---

## Primer benchmark comparativo Claude vs GPT-5

**Fecha:** 2026-07-23
**Tarea evaluada:** Clasificación de riesgo según MAGERIT
**Prompt:** "Clasifica este riesgo según MAGERIT: fallo de cifrado en base
de datos de clientes."

### Resultados cuantitativos

| Métrica | Claude Sonnet 5 | GPT-5 |
|---|---|---|
| Tiempo de respuesta | 15,02 s | 54,08 s |
| Longitud de salida | 2.978 caracteres | 2.140 caracteres |
| Códigos MAGERIT específicos | 5 (E.24, E.19, A.5, A.11, A.18) | 0 |
| Formato de salida | Tablas Markdown con emojis | Listas planas anidadas |
| Cita RGPD/LOPDGDD | Sí, con plazo de 72 h | Sí, sin detalle |

### Observaciones cualitativas

- Claude Sonnet 5 devuelve mayor granularidad MAGERIT (códigos del
  catálogo E/A) y detalle regulatorio; se acerca a un entregable de
  consultoría.
- GPT-5 usa lenguaje más cauto ("valoración orientativa") y estructura
  más plana, potencialmente más fácil de convertir a JSON.
- GPT-5 fue 3,6 veces más lento en este caso concreto.

### Hipótesis de trabajo

A validar con más casos de prueba (mínimo 10-15):

- Claude podría ser más adecuado para tareas de clasificación técnica
  detallada y redacción de informes destinados a stakeholders.
- GPT-5 podría ser más adecuado para tareas de normalización o
  extracción estructurada.

### Limitaciones de esta prueba

Un único caso de prueba no permite conclusiones estadísticas; sirve
únicamente como punto de partida para el diseño del benchmark.
---

## Método de cálculo de riesgo: cualitativo escalado (MAGERIT)

**Fecha:** 2026-07-23

### Fórmula
valor_riesgo = probabilidad_efectiva × impacto
probabilidad_efectiva = probabilidad_base_amenaza × factor_explotacion
impacto = max(valor_C, valor_I, valor_D) del activo
### Justificación

- **Método cualitativo escalado** en lugar de puramente cuantitativo
  (ej. modelos actuariales, FAIR): no se dispone de datos históricos
  de incidentes reales para calibrar distribuciones de probabilidad.
  El método cualitativo escalado es el que MAGERIT recomienda para
  organizaciones sin histórico consolidado.
- **Impacto = máximo de las dimensiones CIAT** en lugar de media o suma:
  criterio conservador de MAGERIT — el peor efecto sobre cualquier
  dimensión define el impacto global del activo.
- **Factor de explotación** (0.3 / 0.6 / 1.0) como modulador: una
  vulnerabilidad de fácil explotación no cambia la amenaza en sí, pero
  aumenta la probabilidad de que la amenaza se materialice.

### Umbrales de nivel

| Rango valor_riesgo | Nivel |
|---|---|
| [0.0, 2.0) | bajo |
| [2.0, 4.0) | medio |
| [4.0, 7.0) | alto |
| [7.0, 10.0] | crítico |

### Ventaja arquitectónica

El cálculo es **determinístico y trazable**: dados los mismos inputs, el
motor produce siempre el mismo output. Los LLMs se emplean para tareas
interpretativas (extracción, clasificación, redacción) pero el cálculo
cuantitativo se aísla en un módulo Python con reglas explícitas, lo que
permite auditar cualquier valor de riesgo hasta su fórmula de origen.

### Prueba de validación

Caso: fallo de cifrado en BD de clientes (C=9, I=7, D=5), amenaza acceso
no autorizado (p=0.6), vulnerabilidad de facilidad alta.

Resultado: probabilidad=0.6, impacto=9.0, valor_riesgo=5.4, nivel=alto.

---

## Benchmark comparativo de 3 modelos (15 casos × 3 modelos)

**Fecha:** 2026-07-29
**Casos evaluados:** 15 escenarios sintéticos cubriendo 5 tipos de
activo (datos, software, hardware, servicio, personal) × 4 categorías
de amenaza × 3 niveles de complejidad.
**Modelos:** Claude Sonnet 5, GPT-5, Llama 3.3 70B (via Groq).

### Resultados agregados

| Modelo | N OK | Tiempo (s) | Longitud | Cód. MAGERIT | RGPD | ENS | Coste |
|---|---|---|---|---|---|---|---|
| Claude Sonnet 5 | 13 | 15,77 ± 1,44 | 3.046 | 15,2 | 38% | 23% | ~$0,15 |
| GPT-5 | 15 | 34,37 ± 6,30 | 2.098 | 0 | 20% | 0% | ~$0,08 |
| Llama 3.3 70B | 15 | 1,96 ± 0,31 | 1.831 | 0 | 0% | 0% | $0 |

### Hallazgos y decisiones

1. **Codigos MAGERIT específicos:** Claude es el único que emite
   códigos del catálogo (E.x, A.x). GPT-5 y Llama devuelven texto
   descriptivo sin códigos. Diferenciador definitivo para
   clasificación MAGERIT rigurosa.

2. **Velocidad:** Llama es 17× más rápido que GPT-5 y 8× más rápido
   que Claude. Candidato natural para tareas de alto volumen.

3. **Consistencia temporal:** GPT-5 muestra alta varianza (σ=6,3 s),
   Groq y Claude son estables. Relevante para diseñar timeouts en
   producción.

4. **Reconocimiento normativo (RGPD, ENS):** Claude es el que más
   contexto regulatorio incorpora. Groq no cita ninguna norma en
   ningún caso.

### Asignación tentativa de modelo por tarea

Basado en los hallazgos, la asignación actual queda:

| Tarea | Modelo | Justificación |
|---|---|---|
| Clasificación MAGERIT profunda | Claude Sonnet 5 | Único que emite códigos del catálogo y reconoce normativa española |
| Extracción de datos estructurados | Pendiente | A validar con benchmark específico de extracción JSON |
| Generación de informe | Claude Sonnet 5 | Riqueza narrativa y estructura Markdown |
| Tareas de alto volumen / prefiltrado | Llama 3.3 70B | 17× más rápido, coste 0 |

### Limitación de este benchmark

Se evalúa solo la tarea de clasificación. Extracción y generación de
informe requieren datasets y métricas propias, pendientes de definir.

### Bug detectado en la capa adaptadora

Claude Sonnet 5 devuelve `ThinkingBlock + TextBlock` en casos
complejos. El adaptador inicial asumía primer bloque = texto, causando
2 errores. Corregido iterando hasta encontrar el primer bloque con
atributo `text`.

---

## Benchmark de generación de JSON estructurado (3 modelos)

**Fecha:** 2026-07-29

### Hallazgos

- **Claude Sonnet 5**: JSON válido a la primera, códigos MAGERIT reales y
  verificables, formato limpio compatible con enums de Pydantic.
- **GPT-5**: JSON válido, rigor legal (cita RD, año, número de norma),
  pero incrusta descripciones dentro de campos que deberían ser etiquetas
  cortas. Sin códigos MAGERIT.
- **Llama 3.3 70B**: JSON válido, pero **inventó un código MAGERIT
  inexistente ("DF6")**. Alucinación crítica en contexto de AARR.
  Descartado para clasificación con códigos.

### Consecuencia arquitectónica

1. `HallazgoLLM` se endurece con Enums (facilidad_explotacion,
   categoria_amenaza, dimension_principal) para forzar valores del
   catálogo y activar el self-repair de call_structured.
2. Se añade instrucción "epistemic humility" al system prompt para
   reducir alucinación de códigos MAGERIT.

### Asignación de modelo por tarea (actualizada)

| Tarea | Modelo | Motivo |
|---|---|---|
| Clasificación MAGERIT con códigos | Claude Sonnet 5 | Confirmado por dos benchmarks |
| Extracción/estructuración a JSON | Claude Sonnet 5 | Formato limpio, compatible con Pydantic |
| Cita normativa con referencia legal | GPT-5 | Ganador en precisión legal |
| Prefiltrado/triaje rápido | Llama 3.3 70B | Solo cuando no requiera códigos MAGERIT |

---

## Iteración 2 de call_structured: schema endurecido + epistemic humility

**Fecha:** 2026-07-29

### Cambios aplicados

1. `HallazgoLLM` migrado de strings libres a Enums en tres campos
   críticos (facilidad_explotacion, categoria_amenaza, dimension_principal).
2. System prompt añade instrucción explícita de dejar lista vacía si no
   se conocen códigos MAGERIT reales ("epistemic humility").

### Resultados observados

- Los 3 modelos validan JSON a la primera (sin uso del self-repair).
- Llama dejó de inventar códigos MAGERIT (antes: DF6 inexistente;
  ahora: E.2 y E.19 reales), aunque con incoherencia entre código y
  categoría de amenaza.
- Claude mejora de 3 a 4 códigos MAGERIT reales.
- GPT-5 mantiene 0 códigos pero adapta enums correctamente.

### Hallazgo metodológico

Con vocabularios controlados (Enums), los tres modelos convergen en la
mayoría de campos categóricos. Con schemas libres, divergen. Argumento
a favor del diseño con listas cerradas para asegurar consistencia
entre distintos LLMs.

### Discrepancia numérica remanente

probabilidad_base: Claude=0.7, Llama=0.7, GPT-5=0.5. GPT-5 es
sistemáticamente más conservador (~30% menor). En un motor de riesgo
determinístico, esto se propaga al valor final del riesgo. Requiere
discusión en la memoria: ¿usar consenso de N modelos? ¿ajustar por
prior de conservadurismo?

---

## Formula del motor de riesgo

**Fecha:** 2026-07-30

### Formulas

- Riesgo inherente = peso(Ocurrencia) x promedio(peso(Imp. Economico), peso(Imp. Operacional))
- Reduccion combinada = 1 - Π(1 - grado_mitigacion_i)   [acumulacion probabilistica]
- Riesgo residual = riesgo_inherente x (1 - reduccion_total)

### Justificacion de la acumulacion probabilistica

Sumar los grados de mitigacion produce valores absurdos (dos salvaguardas
al 50% + 50% = 100% no elimina el riesgo). La acumulacion probabilistica
modela la probabilidad de que "al menos una salvaguarda actue"
correctamente: 50% + 50% -> 75% combinado.

### Parametrizacion

Pesos ordinales y umbrales de nivel estan externalizados como constantes
(PESOS_ORDINALES, UMBRALES_NIVEL) para permitir alinear el sistema con
distintas configuraciones empresariales sin modificar la logica.

---

## Externalización de catálogos en JSON

**Fecha:** 2026-07-30

### Decisión

Los catálogos (amenazas, salvaguardas, matriz de mitigación) se
almacenan en ficheros JSON en `data/catalogos/`, no en constantes
Python.

### Justificación

- **Auditoría**: cada cambio queda en el historial de Git como un diff
  legible, no como un cambio de código.
- **Editabilidad**: personal no técnico (analista de seguridad) puede
  actualizar el catálogo sin tocar código Python.
- **Reutilización**: los mismos JSON se podrían consumir desde otras
  herramientas (Excel, dashboards) si fuera necesario.
- **Separación entre lógica y datos**: el motor y el pipeline no
  cambian si se añaden nuevas amenazas o salvaguardas.

### Fail-fast

La carga y validación (contra los modelos Pydantic) se realiza en
tiempo de import del módulo `src.catalogos`. Un JSON mal formado o con
tipos incorrectos hace fallar el arranque, no una petición en
producción.

### Descubrimiento colateral

Al analizar la matriz se detectan huecos de cobertura (amenazas sin
salvaguarda aplicable). Este análisis es útil para el propio proceso
de gobierno de riesgos y se genera automáticamente.
---

## Primer AARR end-to-end funcional

**Fecha:** 2026-08-03
**Aplicación:** AppEjemplo (ficha genérica)
**Modelo:** claude-sonnet-5

### Resultados agregados

- 10/10 amenazas valoradas sin errores
- 3 salvaguardas implantadas aplicadas
- Riesgos residuales: 1 alto, 3 medios, 6 bajos

### Hallazgos cualitativos

- El LLM identificó automáticamente un hueco de cobertura:
  "Errores del administrador" quedó como riesgo alto residual porque
  ninguna salvaguarda implantada lo mitigaba. La herramienta detecta
  problemas de gobierno de riesgos sin instrucción explícita.
- El modelo asignó N/A a "Desastre natural" correctamente al
  interpretar que una app PaaS transfiere esa responsabilidad al
  proveedor cloud.
- Las justificaciones citan datos concretos de la ficha (%
  obsolescencia, DAST/SAST, dependencias, tipos de usuario), no
  razonamiento genérico. Evidencia de grounding en la entrada.

### Validación de la acumulación probabilística

Caso "Destrucción de información" (AME-005):
- Inherente: 2.5
- Salvaguardas activas: SAL-002 (cifrado, 0.7) + SAL-005 (backup, 0.9)
- Reducción combinada: 1 - (1-0.7)(1-0.9) = 0.97
- Residual: 2.5 × (1 - 0.97) = 0.075 ✓

---

## Interfaz Streamlit v1

**Fecha:** 2026-08-03

### Alcance decidido

- Una sola página con tres secciones (Ficha, Análisis, Resultados)
- Ficha cargable como ejemplo predefinido (carga desde Excel queda
  como trabajo futuro / iteración siguiente)
- Selección de salvaguardas mediante checkboxes
- Visualización de resultados con tabla coloreada, gráfico y top 3

### Fuera de alcance en esta iteración

- Ajuste manual de las valoraciones propuestas por el LLM
  (human-in-the-loop pendiente para v2)
- Persistencia de análisis previos (historial)
- Exportación a PDF/Excel
- Login o multi-usuario

### Justificación del alcance

Iteración mínima viable que permite demostrar el pipeline end-to-end
visualmente. Suficiente para revisión con tutor y para el capítulo
de validación. Las funciones descartadas se documentan como líneas
de mejora futura en la memoria.
### Deprecación de pandas.Styler.applymap

Detectada al probar la UI: pandas eliminó `Styler.applymap` en su
versión reciente, sustituido por `Styler.map`. Corrección de una
palabra. Refuerza la necesidad de fijar versiones en `requirements.txt`
para reproducibilidad, cosa que se aborda en la fase de empaquetado.
### Métricas reales de una ejecución completa vía UI

- Aplicación: AppEjemplo (10 amenazas, 3 salvaguardas)
- Tiempo total: 74,8 s
- Latencia media por amenaza: ~7,5 s
- Coste estimado: <$0,10
- Resultado: 1 alto, 4 medios, 5 bajos
- Riesgo destacado: AME-008 (Errores del administrador) queda como
  único "alto" residual por ausencia de salvaguarda implantada. La
  herramienta detecta autónomamente huecos de gobernanza.

  ---

## Ingesta desde Excel: formato propio

**Fecha:** 2026-08-03

### Decisión

Se define un formato Excel propio con 5 hojas (Ficha, Servicios_IT,
Grupos_Usuarios, Dependencias, Estado_Tecnico) en lugar de intentar
consumir directamente el formato del Excel corporativo.

### Justificación

- El Excel corporativo tiene macros, formato visual, bloques y celdas
  combinadas que dificultan la extracción programática robusta.
- Un formato propio, simple y estable, mapea 1:1 al modelo de datos
  (Pydantic) y falla temprano si un valor no cumple.
- En producción se implementaría un adaptador que convierta el Excel
  corporativo a este formato estándar, aislando la lógica de negocio
  de la fuente de datos.

### Beneficios colaterales

- Se genera automáticamente una plantilla vacía para el usuario final.
- La misma estructura sirve para intercambio entre sistemas si en el
  futuro se conecta un CMDB u otra fuente.

  ### Determinismo limitado con temperature=0

Detectada varianza en la valoración del LLM (Claude Sonnet 5) entre
ejecuciones sobre la misma ficha aun con temperature=0. Esto se debe
al carácter no determinístico de los modelos con razonamiento
extendido. Implicación práctica: la herramienta debe utilizarse como
apoyo al analista, no como sustituto — el "human-in-the-loop" no es
opcional, es metodológicamente necesario.

### Idempotencia en Streamlit: bug de reset al editar valoraciones

Detectado durante pruebas de la fase de human-in-the-loop: al editar
un valor en la tabla, Streamlit re-ejecuta el script completo,
provocando que el bloque del file_uploader re-procesara el mismo
archivo y reseteara el estado (informe = None). Corregido añadiendo
un centinela (`excel_procesado`) que evita procesar dos veces el
mismo archivo. Aprendizaje: en apps reactivas, todo side effect debe
ser idempotente por diseño.

---

## Edición de justificaciones antes del PDF

**Fecha:** 24/09

### Motivación

Feedback de la reunión con el tutor: el analista debería poder ajustar
no solo las valoraciones cuantitativas sino también la redacción de
las justificaciones del LLM antes de generar el informe final.

### Diseño

Cada justificación se muestra en un `st.text_area` editable dentro del
expander del Top 3. Si el analista modifica el texto, la valoración se
marca automáticamente como `fuente="llm_ajustado_humano"` (mismo campo
que se usaba para valoraciones cuantitativas ajustadas).

### Consecuencia

El human-in-the-loop es ahora completo: tanto la parte numérica del
análisis como la parte narrativa quedan bajo control del analista antes
del informe final. La trazabilidad "quién dijo qué" (LLM vs humano) se
mantiene en un único campo del modelo.

---

## Envio de correos con adjuntos

**Fecha:** [fecha actual]

### Motivacion

Feedback del tutor: convertir la herramienta en un ciclo completo del
proceso empresarial. Dos correos automatizados:
- Al Service Manager: se envia al inicio con la plantilla Excel vacia
- Al cliente: se envia al final con el informe PDF generado

### Decisiones de diseno

**Modo sandbox por defecto.** Si no hay SMTP configurado en `.env`, el
sistema simula el envio en lugar de mandar el correo. Esto evita
envios accidentales durante desarrollo o defensa.

**Confirmacion explicita antes de enviar.** El boton primero muestra
el correo completo (destinatario, asunto, cuerpo, adjunto) y pide
confirmacion. No hay envio directo por click involuntario.

**Plantillas externas.** Los cuerpos de los correos viven en
`templates/emails/*.txt` con variables `{nombre_app}` etc. Se pueden
editar sin tocar codigo Python.

**Gmail SMTP con App Password.** Se descarta OAuth2 por complejidad
para un TFG; App Password es estandar, simple y seguro (contrasenna
especifica revocable, aislada de la principal).

### Consecuencia

La herramienta cubre ahora el flujo completo:
1. Correo al Service Manager con plantilla
2. Service Manager rellena y devuelve el Excel
3. Analista sube el Excel a la herramienta y ejecuta AARR
4. Analista revisa y ajusta valoraciones + justificaciones
5. Herramienta envia el informe al cliente por correo

### Consideraciones eticas

- Credenciales (App Password) fuera del repositorio, solo en `.env`
- En demos y video de defensa se usa la propia direccion del autor
- El sistema NUNCA envia sin confirmacion humana explicita
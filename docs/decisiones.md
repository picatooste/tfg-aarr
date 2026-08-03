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
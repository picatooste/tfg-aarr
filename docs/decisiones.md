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
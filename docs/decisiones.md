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
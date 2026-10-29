
# Proyecto 10 · RAG de seguros de automóvil

## Master en Ingeniería de IA

Sistema de generación aumentada por recuperación (RAG) que responde preguntas sobre documentación de seguros de automóvil. El sistema recupera fragmentos relevantes de documentos PDF, utiliza un modelo local para generar respuestas y cita las fuentes consultadas.

La respuesta debe basarse exclusivamente en la información recuperada. Cuando los documentos no contienen información suficiente, el sistema responde exactamente `No lo sé.`.

## 1. Tecnologías

- Python.
- PostgreSQL y pgvector, alojados en Neon.
- Ollama para generar embeddings locales con `nomic-embed-text`.
- Ollama con `llama3.1:8b` para generar respuestas.
- LangChain para el procesamiento y la integración con los modelos.
- LangGraph para coordinar el flujo conversacional.
- Recuperación semántica y textual.
- Aislamiento de datos mediante `tenant_id`.

## 2. Documentación utilizada

La carpeta `docs/` contiene los tres documentos PDF indexados:

1. `gesauto_condiciones_modelo_2020.pdf`: condiciones generales del modelo GesAuto 2020.
2. `linea_directa_coberturas_complementarias.pdf`: coberturas complementarias de Línea Directa, marzo de 2025.
3. `linea_directa_condiciones_generales.pdf`: condiciones generales de Línea Directa, edición de enero de 2026.

Se trata de ediciones concretas de los documentos. Su inclusión en el proyecto no implica que todas sus condiciones sigan vigentes actualmente.

## 3. Arquitectura del sistema

El flujo de trabajo es el siguiente:

1. **Ingesta:** extracción del texto de los documentos PDF y división en fragmentos.
2. **Embeddings:** conversión de los fragmentos en vectores mediante `nomic-embed-text`.
3. **Almacenamiento:** persistencia del texto, el nombre del documento, la página, el vector y el identificador del tenant en PostgreSQL.
4. **Recuperación:** búsqueda de fragmentos relevantes mediante similitud vectorial y coincidencias textuales.
5. **Generación:** envío de la pregunta y del contexto recuperado al modelo local `llama3.1:8b`.
6. **Respuesta:** presentación de una respuesta breve con referencias al documento y la página, o abstención cuando no existe información suficiente.

## 4. Configuración del entorno

### Requisitos

- Python.
- Git.
- Ollama instalado y funcionando.
- PostgreSQL con la extensión pgvector; este proyecto utiliza Neon.
- Una variable de entorno `DATABASE_URL` configurada con las credenciales de la base de datos.

### Variables de entorno

Crea un archivo `.env` a partir de `.env.example` y configura `DATABASE_URL` con la cadena de conexión de tu propia base de datos.

No publiques el archivo `.env` ni compartas sus credenciales. El repositorio contiene únicamente una plantilla sin secretos.

### Modelos locales

Descarga los modelos necesarios mediante Ollama:

```powershell
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

Comprueba que Ollama está funcionando antes de ejecutar los scripts.

### Instalación de dependencias

Desde la carpeta raíz del repositorio, crea y activa un entorno virtual e instala las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si ya dispones del entorno virtual preparado, no necesitas crearlo de nuevo.

## 5. Ejecución del proyecto

Los principales archivos de procesamiento son:

| Archivo | Función |
|---|---|
| `ingesta.py` | Extracción del texto de los PDF y división en fragmentos. |
| `db.py` | Conexión con PostgreSQL y funciones de acceso a la base de datos y embeddings. |
| `02_indexar.py` | Generación y almacenamiento de los embeddings y los fragmentos. |
| `03_recuperar.py` | Recuperación de fragmentos relevantes para una pregunta. |
| `04_generar.py` | Generación de respuestas basadas en el contexto recuperado. |
| `rag.py` | Lógica de recuperación, construcción del contexto y generación de respuestas. |
| `05_chatbot_grafo.py` | Chatbot conversacional con LangGraph, memoria y reformulación de preguntas. |
| `06_aislamiento_tenant.py` | Migración para incorporar el aislamiento por tenant cuando sea necesaria. |
| `buscar_lunas.py` | Script auxiliar de búsqueda de información sobre la garantía de lunas. |
| `comprobar_tabla.py` | Script auxiliar para comprobar la tabla de la base de datos. |

Para iniciar una conversación interactiva:

```powershell
python .\05_chatbot_grafo.py --chat
```

Para consultar una pregunta de forma individual:

```powershell
python .\04_generar.py "¿Qué cubre la garantía de lunas?"
```

Para ejecutar estos comandos, sitúate en la carpeta raíz del proyecto y asegúrate de tener configurados la base de datos y Ollama.

**Importante:** los scripts de preparación y migración no deben ejecutarse de nuevo sin comprobar antes su efecto. En particular, `02_indexar.py` puede vaciar y reconstruir la tabla vectorial. La tabla ya está indexada, por lo que no es necesario repetir este proceso para utilizar el chatbot.

## 6. Configuración de embeddings e indexación

El proyecto utiliza el modelo local `nomic-embed-text` mediante Ollama.

- Dimensión de los embeddings: 768.
- Tamaño de fragmento: 500 caracteres.
- Solapamiento: 75 caracteres.
- Fragmentos indexados en la ejecución registrada: 1.139.
- Tabla vectorial: `fragmentos_rag10`.
- Índice vectorial: HNSW con distancia coseno.

La pregunta se transforma en un embedding mediante el mismo modelo empleado para indexar los documentos. PostgreSQL y pgvector permiten ordenar los fragmentos según su similitud con la consulta.

La recuperación semántica puede devolver fragmentos que no respondan directamente a una pregunta. Por ello, el sistema combina búsqueda vectorial y textual y permite que el modelo se abstenga cuando el contexto no aporta información suficiente.

## 7. Aislamiento por tenant

La tabla `fragmentos_rag10` contiene la columna `tenant_id`. Las consultas de recuperación filtran los resultados por el tenant solicitado para evitar que una búsqueda acceda a fragmentos de otro ámbito.

El tenant de demostración es:

`seguros_auto_demo`

En la comprobación realizada se obtuvieron los siguientes resultados:

- Fragmentos asignados a `seguros_auto_demo`: 1.139.
- Fragmentos visibles para otro tenant mediante la consulta de prueba: 0.

El filtro por `tenant_id` debe mantenerse en todas las consultas de recuperación. Este requisito forma parte del diseño de seguridad del sistema y no debe depender únicamente de las instrucciones del modelo.

## 8. Respuestas y fuentes

El prompt del sistema establece que el asistente debe:

- Responder en español y de forma breve.
- Utilizar exclusivamente la información disponible en el contexto recuperado.
- Citar el documento y la página utilizados.
- No inventar coberturas, condiciones ni importes.
- Responder exactamente `No lo sé.` cuando no dispone de información suficiente.

Las respuestas deben contrastarse con los fragmentos recuperados y las fuentes citadas. La similitud vectorial por sí sola no garantiza que una respuesta sea correcta.

## 9. Pruebas funcionales realizadas

### Prueba 1. Pregunta con respuesta disponible

**Pregunta:** ¿Qué cubre la garantía de lunas?

**Respuesta obtenida:**

La garantía de lunas cubre la reparación, la reposición y los gastos de colocación de las lunas del vehículo, siempre que su inclusión aparezca expresamente pactada en las condiciones particulares.

**Fuente:** `gesauto_condiciones_modelo_2020.pdf`, página 41.

### Prueba 2. Pregunta sin respuesta disponible

**Pregunta:** ¿Cuál es el precio exacto de mi póliza personal?

**Respuesta obtenida:**

`No lo sé.`

El sistema no dispone de los datos particulares de la póliza y no inventa un importe.

### Evidencias

Las capturas de las pruebas y de la comprobación del aislamiento por tenant se encuentran en `documentacion/`:

- [Respuesta sobre la garantía de lunas](documentacion/01_respuesta_garantia_lunas.png)
- [Respuesta de abstención: No lo sé](documentacion/02_respuesta_no_lo_se.png)
- [Comprobación del aislamiento por tenant](documentacion/03_aislamiento_tenant.png)

## 10. Estructura del repositorio

- `docs/`: documentos PDF utilizados en la indexación.
- `documentacion/`: capturas de evidencias de las pruebas.
- `db.py`: conexión y operaciones con PostgreSQL y embeddings.
- `ingesta.py`: extracción y división del texto.
- `rag.py`: lógica de recuperación y generación.
- `02_indexar.py` a `06_aislamiento_tenant.py`: scripts de indexación, consulta, generación, conversación y aislamiento.
- `buscar_lunas.py` y `comprobar_tabla.py`: scripts auxiliares.
- `requirements.txt`: dependencias de Python.
- `.env.example`: plantilla de configuración sin credenciales.
- `.gitignore`: exclusión de archivos locales, credenciales y otros elementos que no forman parte de la entrega.

## 11. Seguridad y limitaciones

- No publicar `.env`, contraseñas, claves ni otros secretos.
- No subir el entorno virtual `.venv`.
- Mantener el repositorio privado mientras no se haya confirmado que se dispone de autorización para compartir los documentos PDF.
- No considerar las condiciones históricas como necesariamente vigentes.
- La recuperación puede incluir fragmentos poco relevantes; las fuentes deben comprobarse.
- El modelo no debe responder con información que no esté respaldada por el contexto.
- El aislamiento por tenant debe aplicarse en todas las consultas de recuperación.

## 12. Resultado

El proyecto implementa un flujo RAG funcional sobre documentación de seguros de automóvil, con embeddings locales, almacenamiento vectorial en PostgreSQL y pgvector, generación local de respuestas, referencias a las fuentes y aislamiento por tenant.

Las pruebas registradas demuestran tanto la generación de una respuesta basada en la documentación como la abstención ante una pregunta para la que no se dispone de información suficiente.




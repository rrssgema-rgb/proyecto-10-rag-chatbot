
# rag-chatbot · Master AI Engineer · Proyecto 10

## RAG de seguros de automóvil con PostgreSQL y pgvector

Este proyecto implementa un sistema RAG (Retrieval-Augmented Generation) que responde preguntas sobre documentación de seguros de automóvil. Recupera fragmentos de los documentos, genera una respuesta con un modelo local y cita el documento y la página utilizados.

La respuesta debe basarse exclusivamente en el contexto recuperado. Si los documentos no contienen información suficiente, el sistema responde `No lo sé.`.

### Tecnologías

- Python.
- PostgreSQL y pgvector, alojados en Neon.
- Ollama para generar embeddings locales con `nomic-embed-text`.
- Ollama con `llama3.1:8b` para generar respuestas.
- LangChain y LangGraph para el procesamiento y la conversación.
- Filtro por `tenant_id` en las consultas de recuperación.

## Documentos utilizados

La carpeta `docs/` contiene los tres PDF indexados:

1. `gesauto_condiciones_modelo_2020.pdf`: condiciones generales del modelo GesAuto 2020.
2. `linea_directa_coberturas_complementarias.pdf`: coberturas complementarias de Línea Directa, marzo de 2025.
3. `linea_directa_condiciones_generales.pdf`: condiciones generales de Línea Directa, edición de enero de 2026.

Los documentos corresponden a ediciones concretas y son reales. 

## Puesta en marcha

### 1. Requisitos

- Python instalado.
- Ollama instalado y funcionando.
- PostgreSQL con la extensión pgvector; en este proyecto se utiliza Neon.
- Una base de datos configurada mediante la variable `DATABASE_URL`.

### 2. Configurar las variables de entorno

Copia `.env.example` como `.env` y configura `DATABASE_URL` con la cadena de conexión de tu propia base de datos.

No se publica el archivo `.env`, ya que contiene credenciales.

### 3. Preparar Ollama

Descarga los modelos utilizados por el proyecto:

```powershell
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

Comprueba que Ollama está funcionando antes de ejecutar los scripts.

### 4. Instalar las dependencias

Desde la carpeta raíz del repositorio, crea y activa un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 5. Ejecutar el proyecto

Los scripts numerados permiten realizar las distintas etapas:

- `01_cargar_trocear.py`: preparar los documentos y sus fragmentos.
- `02_indexar.py`: crear y poblar el índice vectorial en PostgreSQL.
- `03_recuperar.py`: buscar fragmentos relevantes.
- `04_generar.py`: generar una respuesta basada en el contexto recuperado.
- `05_chatbot_grafo.py`: ejecutar el chatbot con memoria y reformulación de preguntas.
- `06_aislamiento_tenant.py`: aplicar la migración de aislamiento por tenant, si es necesario.

La ingesta y la indexación son operaciones de preparación. **No ejecutes `02_indexar.py` innecesariamente**, ya que el script puede vaciar y reconstruir la tabla.

Para iniciar una conversación interactiva:

```powershell
python .\05_chatbot_grafo.py --chat
```

Para consultar una pregunta de forma individual:

```powershell
python .\03_recuperar.py "¿Qué cubre la garantía de lunas?"
python .\04_generar.py "¿Qué cubre la garantía de lunas?"
```

Las rutas y los nombres de los scripts deben ejecutarse desde la carpeta raíz del proyecto.

## Pipeline RAG

| Etapa | Archivo | Función |
|---|---|---|
| Ingesta | `ingesta.py` | Extraer texto de los PDF y dividirlo en fragmentos. |
| Indexación | `02_indexar.py`, `db.py` | Generar embeddings y almacenar texto, documento, página y vector. |
| Recuperación | `03_recuperar.py`, `rag.py` | Buscar fragmentos por similitud vectorial y coincidencias textuales. |
| Generación | `04_generar.py`, `rag.py` | Enviar al modelo la pregunta y el contexto recuperado. |
| Conversación | `05_chatbot_grafo.py` | Coordinar reformulación, recuperación y generación con LangGraph. |

## Configuración de embeddings

El proyecto utiliza el modelo local `nomic-embed-text` mediante Ollama.

- Dimensión de los embeddings: 768.
- Tamaño de fragmento: 500 caracteres.
- Solapamiento configurado: 75 caracteres.
- Número de fragmentos indexados: 1.139 en la ejecución registrada.
- Tabla vectorial: `fragmentos_rag10`.

La pregunta se transforma en un embedding con el mismo modelo utilizado para indexar los documentos. PostgreSQL y pgvector permiten ordenar los fragmentos por distancia coseno.

Los resultados de recuperación pueden incluir fragmentos poco relevantes. Por ello, el sistema combina recuperación semántica y textual y debe permitir que el modelo se abstenga cuando no encuentra información suficiente.

## Aislamiento por tenant

La tabla incluye la columna `tenant_id`. Las consultas de recuperación deben filtrar por el tenant solicitado para impedir que una búsqueda acceda a fragmentos de otro ámbito.

En la configuración de demostración se utiliza el tenant `seguros_auto_demo`.

La comprobación realizada mostró 1.139 fragmentos para `seguros_auto_demo` y cero fragmentos visibles para otro tenant mediante la consulta de prueba.


## Respuestas y citas

El prompt del sistema establece que el asistente:

- Responda en español y de forma breve.
- Utilice exclusivamente la información del contexto.
- Cite el documento y la página de la fuente.
- No invente coberturas, condiciones ni importes.
- Responda exactamente `No lo sé.` cuando no disponga de información suficiente.


## Pruebas funcionales realizadas

### Pregunta con respuesta disponible

**Pregunta:** ¿Qué cubre la garantía de lunas?

**Respuesta obtenida:** La garantía de lunas cubre la reparación, la reposición y los gastos de colocación de las lunas del vehículo.

**Fuente citada:** `gesauto_condiciones_modelo_2020.pdf`, página 41.

### Pregunta sin respuesta disponible

**Pregunta:** ¿Cuál es el precio exacto de mi póliza personal?

**Respuesta obtenida:** `No lo sé.`

Estas pruebas muestran el comportamiento esperado en los dos casos. 

## Estructura del proyecto

- `docs/`: documentos PDF que se indexan.
- `db.py`: conexión a PostgreSQL y generación de embeddings.
- `ingesta.py`: extracción y división del texto.
- `rag.py`: recuperación y generación de respuestas.
- `01_cargar_trocear.py` a `06_aislamiento_tenant.py`: scripts de procesamiento, consulta y configuración.
- `requirements.txt`: dependencias del proyecto.
- `.env.example`: plantilla de configuración sin credenciales.

## Seguridad y limitaciones

- No publicar `.env`, credenciales ni otros secretos.
- No subir el entorno virtual `.venv`.
- No considerar los documentos históricos como condiciones necesariamente vigentes.
- La similitud vectorial no garantiza que un fragmento responda correctamente a la pregunta.
- El aislamiento por tenant debe mantenerse en todas las consultas de recuperación.



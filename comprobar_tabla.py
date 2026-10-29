from db import conectar

conn = conectar()
try:
    print("COLUMNAS DE fragmentos_rag10:")
    filas = conn.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'fragmentos_rag10'
        ORDER BY ordinal_position
    """).fetchall()

    for fila in filas:
        print(fila)

    print("\nNUMERO DE FRAGMENTOS:")
    print(conn.execute(
        "SELECT COUNT(*) FROM fragmentos_rag10"
    ).fetchone()[0])

finally:
    conn.close()

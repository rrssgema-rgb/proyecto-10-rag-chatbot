from db import conectar

conn = conectar()

try:
    filas = conn.execute("""
        SELECT documento, pagina, texto
        FROM fragmentos_rag10
        WHERE tenant_id = %s
          AND texto ILIKE %s
        ORDER BY documento, pagina
        LIMIT 12
    """, ("seguros_auto_demo", "%lunas%")).fetchall()

    if not filas:
        print("No se encontraron fragmentos que contengan la palabra 'lunas'.")

    for documento, pagina, texto in filas:
        print("=" * 80)
        print(f"DOCUMENTO: {documento} | PAGINA: {pagina}")
        print(texto[:1200])
        print()

finally:
    conn.close()

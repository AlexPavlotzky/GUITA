import sqlite3
import uuid
from datetime import datetime

DB_FILE = "guita.sqlite"

def format_date(raw_date: str) -> str:
    try:
        ts = int(raw_date)
        if ts > 1e12:
            ts //= 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except:
        return raw_date

def to_timestamp(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return str(int(dt.timestamp() * 1000))
    except:
        return date_str

def get_categories():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT uid, NAME, TYPE FROM ZCATEGORY")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_accounts():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT uid, NIC_NAME FROM ASSETS")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_account_balances():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            A.NIC_NAME,
            SUM(
                CASE 
                    WHEN I.DO_TYPE IN (0, 4)
                        THEN CAST(I.ZMONEY AS REAL)
                    WHEN I.DO_TYPE IN (1, 3) 
                        THEN -CAST(I.ZMONEY AS REAL)
                    ELSE 0
                END
            ) AS balance
        FROM ASSETS A
        LEFT JOIN INOUTCOME I ON A.uid = I.assetUid
        GROUP BY A.uid;
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def insert_transaction(date_uid, amount_uid, desc_uid, tipo, category_uid, account_uid, to_account_uid):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    ts = to_timestamp(date_uid)

    if tipo in (0, 1):  # Ganancia o Gasto
        cur.execute("""
            INSERT INTO INOUTCOME (ZDATE, ZMONEY, ZCONTENT, ctgUid, assetUid, DO_TYPE, uid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ts, str(amount_uid), desc_uid, category_uid, account_uid, tipo, str(uuid.uuid4())))
    elif tipo == 3:  # Transferencia
        # Crearemos dos registros: salida de la cuenta origen (tipo 3) y entrada en cuenta destino (tipo 4)
        # Salida
        cur.execute("""
            INSERT INTO INOUTCOME (ZDATE, ZMONEY, ZCONTENT, ctgUid, assetUid, toAssetUid, DO_TYPE, uid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts, str(abs(amount_uid)), desc_uid, None, account_uid, to_account_uid, 3, str(uuid.uuid4())))
        # Entrada
        cur.execute("""
            INSERT INTO INOUTCOME (ZDATE, ZMONEY, ZCONTENT, ctgUid, assetUid, DO_TYPE, uid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ts, str(abs(amount_uid)), desc_uid, None, to_account_uid, 4, str(uuid.uuid4())))

    conn.commit()
    conn.close()

def get_transactions(limit=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    query = """
    SELECT I.uid,
           I.ZDATE,
           I.ZMONEY,
           I.DO_TYPE,
           C.NAME as category,
           I.ZCONTENT,
           A.NIC_NAME as account, 
           I.ctgUid
    FROM INOUTCOME I
    LEFT JOIN ZCATEGORY C ON I.ctgUid = C.uid
    LEFT JOIN ASSETS A ON I.assetUid = A.uid
    
    ORDER BY I.ZDATE DESC
    """
    # WHERE I.IS_DEL IS NULL OR I.IS_DEL != 1
    if limit:
        query += " LIMIT ?"
        cur.execute(query, (limit,))
    else:
        cur.execute(query)

    rows = cur.fetchall()
    conn.close()

    formatted = []
    for r in rows:
        formatted.append((
            r[0],                                   # uid
            format_date(r[1]),                      # fecha
            r[2],                                   # monto
            int(r[3]) if r[3] is not None else 0,   # tipo
            r[4],                                   # categoría nombre
            r[5],                                   # descripcion
            r[6],                                   # cuenta
            r[7]                                    # categoria uid
        ))
    return formatted
    
def delete_transaction(uid):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM INOUTCOME  WHERE uid = ?", (uid,))
    conn.commit()
    conn.close()

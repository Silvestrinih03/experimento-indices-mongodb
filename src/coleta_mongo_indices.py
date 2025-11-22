import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import csv

# ================= CONFIGURAÇÕES =================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
N_REPETICOES_POR_TRATAMENTO = int(os.getenv("N_REPETICOES", 30))
INTERVALO_DIAS = int(os.getenv("INTERVALO_DIAS", 30))

CSV_OUTPUT = "resultados/resultados_mongo_indices.csv"

DATA_INICIO_GLOBAL = datetime(2013, 1, 1)
DATA_FIM_GLOBAL = datetime(2017, 12, 31)


# ================= FUNÇÕES =================

def conectar():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]
    return client, col


def gerar_periodo_aleatorio():
    delta_total = (DATA_FIM_GLOBAL - DATA_INICIO_GLOBAL).days - INTERVALO_DIAS
    dia_inicial = random.randint(0, delta_total)
    inicio = DATA_INICIO_GLOBAL + timedelta(days=dia_inicial)
    fim = inicio + timedelta(days=INTERVALO_DIAS)
    return inicio, fim


def executar_consulta(col, tratamento, usar_indice):
    inicio, fim = gerar_periodo_aleatorio()
    filtro = {"saleDate": {"$gte": inicio, "$lt": fim}}

    consulta = col.find(filtro).sort("saleDate", 1).limit(1000)

    if usar_indice:
        consulta = consulta.hint([("saleDate", 1)])
    else:
        consulta = consulta.hint([("$natural", 1)])

    plano = consulta.explain()
    stats = plano.get("executionStats", {})

    return {
        "tratamento": tratamento,
        "latencia_ms": stats.get("executionTimeMillis"),
        "docs_examinados": stats.get("totalDocsExamined"),
        "chaves_examinadas": stats.get("totalKeysExamined"),
        "n_retornados": stats.get("nReturned"),
        "data_inicio": inicio.isoformat(),
        "data_fim": fim.isoformat()
    }

def preparar_indice(col):
    try:
        col.drop_index("saleDate_1")
    except:
        pass
    col.create_index("saleDate")


# ================= MAIN =================

def main():
    print("INICIANDO EXPERIMENTO")

    os.makedirs("resultados", exist_ok=True)

    client, col = conectar()

    total_docs = col.count_documents({})
    print(f"Documentos na coleção: {total_docs}")

    if total_docs == 0:
        print("ERRO: A coleção está vazia. Importe o dataset antes.")
        return

    preparar_indice(col)

    resultados = []

    print("Warm-up...")
    executar_consulta(col, "warmup", False)
    executar_consulta(col, "warmup", True)

    print("Coletando SEM índice...")
    for i in range(N_REPETICOES_POR_TRATAMENTO):
        res = executar_consulta(col, "sem_indice", False)
        resultados.append(res)
        print(f"[SEM] Exec {i+1} → {res['latencia_ms']} ms")

    print("Coletando COM índice...")
    for i in range(N_REPETICOES_POR_TRATAMENTO):
        res = executar_consulta(col, "com_indice", True)
        resultados.append(res)
        print(f"[COM] Exec {i+1} → {res['latencia_ms']} ms")

    print("Salvando CSV...")
    with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        campos = [
            "tratamento",
            "latencia_ms",
            "docs_examinados",
            "chaves_examinadas",
            "n_retornados",
            "data_inicio",
            "data_fim"
        ]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    client.close()
    print("EXPERIMENTO FINALIZADO COM SUCESSO!")


if __name__ == "__main__":
    main()
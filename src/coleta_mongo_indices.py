import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import csv
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu


# ================= CONFIGURAÇÕES =================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
N_REPETICOES_POR_TRATAMENTO = int(os.getenv("N_REPETICOES", 30))
INTERVALO_DIAS = int(os.getenv("INTERVALO_DIAS", 30))
SEED = int(os.getenv("SEED", 0))

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

    # explica no servidor (executionStats) para obter métricas do servidor
    consulta_explain = col.find(filtro).sort("saleDate", 1).limit(1000)
    if usar_indice:
        consulta_explain = consulta_explain.hint([("saleDate", 1)])
    else:
        consulta_explain = consulta_explain.hint([("$natural", 1)])

    try:
        plano = consulta_explain.explain("executionStats")
    except Exception:
        plano = consulta_explain.explain()

    stats = plano.get("executionStats", {})
    server_latency = stats.get("executionTimeMillis")
    docs_examined = stats.get("totalDocsExamined")
    keys_examined = stats.get("totalKeysExamined")

    # medir tempo do cliente (inclui rede + desserialização)
    consulta_exec = col.find(filtro).sort("saleDate", 1).limit(1000)
    if usar_indice:
        consulta_exec = consulta_exec.hint([("saleDate", 1)])
    else:
        consulta_exec = consulta_exec.hint([("$natural", 1)])

    t0 = time.perf_counter()
    docs = list(consulta_exec)
    t1 = time.perf_counter()
    client_latency_ms = int((t1 - t0) * 1000)

    return {
        "tratamento": tratamento,
        "latencia_ms_server": server_latency,
        "latencia_ms_client": client_latency_ms,
        "docs_examinados": docs_examined,
        "chaves_examinadas": keys_examined,
        "n_retornados": len(docs),
        "data_inicio": inicio.isoformat(),
        "data_fim": fim.isoformat()
    }

def gerar_graficos():
    print("Gerando gráficos comparativos...")

    os.makedirs("graphs", exist_ok=True)

    df = pd.read_csv(CSV_OUTPUT)

    # Converter colunas de latência
    df["latencia_ms_server"] = pd.to_numeric(df.get("latencia_ms_server"), errors="coerce")
    df["latencia_ms_client"] = pd.to_numeric(df.get("latencia_ms_client"), errors="coerce")

    sem_client = df[df["tratamento"] == "sem_indice"]["latencia_ms_client"].dropna()
    com_client = df[df["tratamento"] == "com_indice"]["latencia_ms_client"].dropna()

    if sem_client.empty or com_client.empty:
        print("⚠️ Dados insuficientes para gerar gráficos.")
        return

    # HISTOGRAMA COMPARATIVO (CLIENT)
    plt.figure(figsize=(8, 5))
    plt.hist(sem_client, bins=20, alpha=0.6, label="Sem Índice")
    plt.hist(com_client, bins=20, alpha=0.6, label="Com Índice")
    plt.title("Histograma Comparativo (cliente) - Latência das Consultas")
    plt.xlabel("Latência (ms)")
    plt.ylabel("Frequência")
    plt.legend()
    plt.tight_layout()
    plt.savefig("graphs/histograma_comparativo_client.png")
    plt.close()

    # ECDF (CLIENT)
    def ecdf(data):
        x = np.sort(data)
        y = np.arange(1, len(x) + 1) / len(x)
        return x, y

    x_sem, y_sem = ecdf(sem_client.values)
    x_com, y_com = ecdf(com_client.values)

    plt.figure(figsize=(8, 5))
    plt.step(x_sem, y_sem, where='post', label='Sem Índice')
    plt.step(x_com, y_com, where='post', label='Com Índice')
    plt.title('ECDF - Latência (cliente)')
    plt.xlabel('Latência (ms)')
    plt.ylabel('Proporção')
    plt.legend()
    plt.tight_layout()
    plt.savefig('graphs/ecdf_client.png')
    plt.close()

    # BOXPLOT (CLIENT)
    plt.figure(figsize=(6, 5))
    plt.boxplot([sem_client.values, com_client.values], labels=["Sem Índice", "Com Índice"], showmeans=True)
    plt.title("Boxplot Comparativo (cliente)")
    plt.ylabel("Latência (ms)")
    plt.tight_layout()
    plt.savefig("graphs/boxplot_comparativo_client.png")
    plt.close()

    # Estatística (Mann-Whitney)
    try:
        stat, pvalue = mannwhitneyu(sem_client, com_client, alternative='two-sided')
        print(f"Mann-Whitney U test (cliente): stat={stat:.2f}, p-value={pvalue:.4g}")
    except Exception as e:
        print("Erro ao rodar Mann-Whitney:", e)

    print("✅ Gráficos comparativos gerados com sucesso na pasta graphs/")

def preparar_indice(col):
    try:
        col.drop_index("saleDate_1")
    except:
        pass
    col.create_index("saleDate")


# ================= MAIN =================

def main():
    print("INICIANDO EXPERIMENTO")

    if SEED and SEED > 0:
        random.seed(SEED)
        np.random.seed(SEED)

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
        print(f"[SEM] Exec {i+1} → cliente={res.get('latencia_ms_client')} ms | servidor={res.get('latencia_ms_server')} ms")

    print("Coletando COM índice...")
    for i in range(N_REPETICOES_POR_TRATAMENTO):
        res = executar_consulta(col, "com_indice", True)
        resultados.append(res)
        print(f"[COM] Exec {i+1} → cliente={res.get('latencia_ms_client')} ms | servidor={res.get('latencia_ms_server')} ms")

    print("Salvando CSV...")
    with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        campos = [
            "tratamento",
            "latencia_ms_server",
            "latencia_ms_client",
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
    gerar_graficos()
    print("EXPERIMENTO FINALIZADO COM SUCESSO!")


if __name__ == "__main__":
    main()
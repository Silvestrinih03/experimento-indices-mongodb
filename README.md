
# Experimento: Índices no MongoDB

Este repositório contém um experimento acadêmico que avalia o impacto da criação de índices no desempenho de consultas por intervalo de datas no MongoDB. O objetivo é comparar latências e comportamento entre cenários com e sem indexação, e apresentar análises estatísticas dos resultados.

## Dependências
- Python 3.8 ou superior  
- MongoDB em execução  
- Bibliotecas Python:
  - pymongo  
  - pandas  
  - numpy  
  - matplotlib  
  - scipy  
  - python-dotenv  

Instalação rápida das dependências:

```powershell
pip install -r requirements.txt
```

## Configuração
Antes de executar o experimento, configure as variáveis de ambiente no arquivo .env conforme .env.example

## Como executar

1. Crie e ative um ambiente virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Rode o script:

```powershell
python src\coleta_mongo_indices.py
```

## Saídas Geradas
Após a execução, serão criados automaticamente:
- resultados/resultados_mongo_indices.csv
- gráficos na pasta graphs/, como:
    - Histogramas comparativos
    - Boxplots comparativos
    - ECDF (função de distribuição acumulada empírica)

## Estrutura do CSV

O CSV contém uma linha por execução com, entre outros campos:
- `tratamento`: `sem_indice` ou `com_indice`
- `latencia_ms_server`: tempo registrado pelo servidor (executionStats)
- `latencia_ms_client`: tempo medido no cliente (wall-clock)
- `docs_examinados`, `chaves_examinadas`, `n_retornados`, `data_inicio`, `data_fim`

Use `latencia_ms_client` para comparações que incluem rede/serialização; `latencia_ms_server` mostra custo puro no servidor.

## Análises Estatísticas
O script também realiza automaticamente:

- Geração de gráficos comparativos
- Teste estatístico de Mann–Whitney U para verificar diferença significativa entre os tratamentos

O p-value obtido indica se há evidência estatística para rejeitar a hipótese nula de igualdade entre as latências.

## Observações Importantes

- Certifique-se de que a coleção contenha dados suficientes.
- O script executa um warm-up inicial para estabilização de cache.
- O índice utilizado é criado automaticamente no campo saleDate.
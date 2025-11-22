 # Experimento: Índices no MongoDB

Este repositório contém um experimento acadêmico que avalia o impacto da criação de índices no desempenho de consultas por intervalo de datas no MongoDB. O objetivo é comparar latências e comportamento entre cenários com e sem indexação, e apresentar análises estatísticas dos resultados.

## Visão geral

O script principal realiza operações de leitura/escrita no MongoDB simulando consultas por intervalos de data. Em seguida coleta métricas de latência e salva em CSV para análise (gráficos e testes estatísticos).

## Pré-requisitos

- Python 3.8+ instalado
- Uma instância do MongoDB acessível (local ou remota)
- Permissão para criar índices na coleção usada pelo experimento

## Instalação (Windows / PowerShell)

1. Criar ambiente virtual e ativar:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Instalar dependências:

```powershell
pip install -r requirements.txt
```

> Observação: ajuste a instalação conforme seu gerenciador de pacotes e políticas de ambiente.

## Uso

1. Ajuste as configurações de conexão com o MongoDB no arquivo de configuração ou diretamente no script (`coleta_mongo_indices.py`) — por exemplo, `MONGO_URI`, `DATABASE`, `COLLECTION`.

2. Ative o ambiente e execute:

```powershell
.\venv\Scripts\Activate.ps1
python coleta_mongo_indices.py
```

3. Saída esperada:

- Um arquivo `resultados_mongo_indices.csv` com as medições de latência.
- Possivelmente gráficos e relatórios gerados pelos scripts de análise (se houver).

## Scripts principais

- `coleta_mongo_indices.py`: coleta as medições com/sem índice.
- `analisa_resultados.py` (opcional): realiza análise estatística e plota gráficos.
- `resultados_mongo_indices.csv`: saída gerada após execução.

> Se algum desses arquivos não existir ainda, ajuste o README conforme o conteúdo atual do repositório.

## Reproduzir o experimento

1. Garanta um dataset com timestamps compatíveis (campo usado nas queries).
2. Execute a coleta sem índices e salve os resultados.
3. Crie o índice (por ex.: `db.collection.createIndex({data: 1})`).
4. Execute a coleta com índice e salve os resultados.
5. Compare médias, medianas e distribuições; aplique testes estatísticos para verificar significância.

## Estrutura do repositório

- `coleta_mongo_indices.py` — script de coleta
- `analisa_resultados.py` — scripts de análise (se presentes)
- `resultados_mongo_indices.csv` — arquivo de saída
- `README.md` — este arquivo

Atualize a lista acima se os nomes reais dos arquivos forem diferentes.

## Como interpretar os resultados

- Procure diferenças nas métricas de latência (média, mediana, percentis).
- Verifique variação e presença de outliers.
- Use testes como t-test ou Mann–Whitney conforme a distribuição dos dados.

## Próximos passos e melhorias

- Adicionar badges (build, python version)
- Incluir exemplos de gráficos no README (imagens)
- Automatizar geração de relatórios (notebook ou script)

## Licença

Coloque aqui a licença do projeto (ex.: MIT) ou remova esta seção se não for aplicável.

## Contato

Para dúvidas ou contribuições, abra uma issue ou entre em contato com o mantenedor.


# Trabalho Murano

Sistema de controle e gestao para a Murano - automatiza o calculo, organizacao e exportacao de dados do dia a dia do negocio (lavanderia e oficina), com armazenamento em banco de dados na nuvem.

## Funcionalidades

- Registro e calculo de dados operacionais (lavanderia e oficina)
- Historico de movimentacoes
- Exportacao de relatorios para Excel
- Persistencia dos dados no Supabase

## Estrutura

- `app.py` - ponto de entrada da aplicacao
- `utils/calculo.py` - regras de calculo
- `utils/excel.py` - geracao de planilhas
- `utils/supabase_db.py` - integracao com o banco (Supabase)
- `data/` - historico, lavanderia e oficina (CSV)

## Tecnologias

Python, Supabase, pandas/openpyxl

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

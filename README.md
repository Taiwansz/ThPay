# ThPay // Motor de Folha de Pagamento e Conformidade Trabalhista

> Sistema de processamento de folha de pagamento corporativo brasileiro (CLT / eSocial / RFB / MTE), fundamentado em arquitetura bitemporal, resolucao por grafo aciclico dirigido (DAG) e determinismo fiscal centavo a centavo.

---

## 1. Visao Geral

O **ThPay** e um motor de calculo e conformidade trabalhista projetado para atender com precisao matematica irrestrita as exigencias da legislacao brasileira, integrando-se aos ecossistemas do **eSocial**, **DCTFWeb**, **FGTS Digital** e **EFD-Reinf**.

Diferente de sistemas legados acoplados a bancos relacionais com processamento procedural imperativo, o ThPay adota:
1. **Resolucao Topologica em Grafo (DAG):** Cada verba, adicional, desconto ou encargo e um no de dependencia matematica, garantindo ordem de execucao estrita e deteccao preventiva de ciclos.
2. **Arquitetura Bitemporal:** Diferenciacao categorica entre *Valid Time* (momento em que o fato trabalhista ocorreu na realidade) e *Transaction Time* (momento em que o fato foi escriturado no sistema), permitindo retroatividade e apuracao de dissidios sem corromper fechamentos historicos.
3. **Imutabilidade e Version Lock:** Fechamentos mensais geram hashes criptograficos imutaveis (SHA-256), assegurando integridade contabil e paridade com os totalizadores oficiais do governo (S-5001, S-5002, S-5003, S-5011, S-5012).
4. **Zero Emojis e Densidade Maxima:** Documentacao, logs e commits estritamente tecnicos e normativos.

---

## 2. Documentacao Normativa Principal

O mapeamento exaustivo de todas as regras trabalhistas, previdenciarias e fiscais esta formalizado no documento:
- **[SPECIFICATION.md](SPECIFICATION.md):** Especificacao mestre com tabelas, algoritmos de fatiamento marginal de INSS, comparador automatico de IRRF tradicional vs simplificado, DCTFWeb, FGTS Digital via Pix, modalidades de rescisao (Artigos 477 a 484-A CLT), calculo de ferias e 13o salario, e matriz de casos extremos (*edge cases*).

---

## 3. Estrutura do Repositorio

```
ThPay/
├── README.md                      # Apresentacao executiva e guia operacional
├── SPECIFICATION.md               # Mapeamento integral e exaustivo de regras e calculos
├── pyproject.toml                 # Metadados e dependencias do projeto
├── .gitignore                     # Filtros de exclusao para controle de versao
├── thpay/                         # Pacote principal do motor
│   ├── __init__.py                # Exportacoes do modulo
│   ├── domain/                    # Modelos de dominio tipados (Empresa, Contrato, Rubrica)
│   │   ├── __init__.py
│   │   ├── entities.py            # Entidades centrais do negocio
│   │   └── rubrics.py             # Dicionario canonico e naturezas eSocial
│   ├── engine/                    # Motor de calculo e resolucao
│   │   ├── __init__.py
│   │   ├── dag.py                 # Grafo Aciclico Dirigido e ordenacao topologica
│   │   └── context.py             # Contexto de avaliacao e variaveis de ponto
│   ├── tax/                       # Modulos tributarios e previdenciarios
│   │   ├── __init__.py
│   │   ├── inss.py                # Calculo progressivo marginal EC 103/2019
│   │   ├── irrf.py                # IRRF tradicional vs desconto simplificado
│   │   └── fgts.py                # FGTS mensal, jovem aprendiz e rescisorio
│   └── pipelines/                 # Orquestradores de processamento
│       ├── __init__.py
│       └── monthly.py             # Pipeline de folha de pagamento mensal
├── tests/                         # Suite de testes automatizados e regressao
│   ├── __init__.py
│   ├── test_inss.py               # Validacao de faixas marginais de INSS
│   ├── test_irrf.py               # Validacao de comparador de IRRF
│   └── test_dag.py                # Validacao de ordenacao e resolucao de dependencias
└── demo.py                        # Script demonstrativo executavel
```

---

## 4. Como Executar e Validar

### 4.1 Requisitos
- Python 3.10+
- Ambiente com suporte a tipos nativos `decimal.Decimal`

### 4.2 Executar Demonstracao de Calculo
```bash
python3 demo.py
```

### 4.3 Executar Testes Unitarios
```bash
python3 -m unittest discover tests/
```

---

## 5. Resumo do Ciclo Operacional

```
[Cadastro e Contratos] ──> [Espelho de Ponto] ──> [Motor DAG ThPay]
                                                         │
         ┌───────────────────────────────────────────────┴────────────────────────────────────────┐
         ▼                                               ▼                                        ▼
[Demonstrativo / Holerite]                      [Eventos eSocial]                               [DCTFWeb / FGTS Digital]
- Proventos e Adicionais                        - S-1200 (Remuneracao)                          - DARF Previdenciario Unico
- Descontos e Pensao                            - S-1210 (Pagamentos IRRF)                      - Guia GFD (Pix)
- Salario Liquido Garantido                     - S-1299 (Fechamento)                           - Conciliacao centavo a centavo
```

---
*ThPay Core Team // Arquitetura Sagital de Sistemas Críticos*

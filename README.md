# ThPay // Motor de Folha de Pagamento e Conformidade Trabalhista

> Sistema de processamento de folha de pagamento corporativo brasileiro (CLT / eSocial / RFB / MTE), fundamentado em arquitetura poliglota especializada, bitemporalidade, resolucao por grafo aciclico dirigido (DAG) e determinismo fiscal centavo a centavo.

---

## 1. Visao Geral

O **ThPay** e uma plataforma de calculo e conformidade trabalhista projetada para atender com precisao matematica irrestrita as exigencias da legislacao brasileira, integrando-se aos ecossistemas do **eSocial**, **DCTFWeb**, **FGTS Digital** e **EFD-Reinf**.

Em vez de forcar uma unica linguagem para dominios fundamentalmente distintos, o ThPay adota uma **Arquitetura Poliglota Especializada**, selecionando para cada camada a tecnologia que oferece a maxima solidez tecnica:
1. **Calculo e Conformidade eSocial:** **Java 21 (LTS)** com Virtual Threads, Records e XMLDSig nativo.
2. **Interface do DP e Portal do Colaborador:** **TypeScript / Next.js 15** com React Server Components.
3. **Simulador em Tempo Real (In-Browser):** **Rust (Wasm)** para calculos instantaneos no cliente.
4. **Data Analytics, ETL e Auditoria Salarial:** **Python 3.12+** com Polars para conformidade da Lei 14.611/2023.

---

## 2. Matriz Arquitetural de Decisao Tecnologica

```
+-----------------------------------------------------------------------------------------+
|                    PORTAL WEB / DP / COLABORADOR (TypeScript & Next.js 15)              |
|        Painel de Fechamento | Espelho de Ponto | Visualizador de Holerites              |
+--------------------------------------------+--------------------------------------------+
                                             |
                      +----------------------+----------------------+
                      | (REST / OpenAPI / gRPC)                     | (Execucao Local Wasm)
                      v                                             v
+--------------------------------------------+  +-----------------------------------------+
|   CORE ENGINE & ESOCIAL (Java 21 LTS)      |  |  SIMULADOR CLIENT-SIDE (Rust / Wasm)    |
| - Motor DAG com BigDecimal nativo          |  | - Pre-visualizacao de ferias/rescisao   |
| - Virtual Threads (Loom) para 50k vidas    |  | - Resposta sub-milissegundo no browser  |
| - Assinatura XMLDSig A1/A3 (JCA/JCE)       |  +-----------------------------------------+
| - Conectividade Bancaria CNAB 240/400      |
+---------------------+----------------------+
                      |
        (Eventos e Fechamentos Consolidados)
                      v
+-----------------------------------------------------------------------------------------+
|               ANALYTICS, COMPLIANCE & MIGRACAO (Python 3.12 / Polars)                   |
|   Relatorio Lei 14.611 (Equidade Salarial) | Deteccao de Anomalias | Ingestao Legada    |
+-----------------------------------------------------------------------------------------+
```

### 2.1 Justificativa Tecnica por Camada

| Camada do Sistema | Tecnologia Escolhida | Justificativa de Engenharia |
|---|---|---|
| **Core de Calculo & eSocial Gateway** | **Java 21 (LTS)** (Spring Boot 3 / Quarkus) | `BigDecimal` nativo para calculo financeiro estrito; Virtual Threads (Loom) para paralelismo massivo em batch; JCA/JCE nativo para XMLDSig e certificados A1/A3; Caelum Stella e geradores CNAB 240/400 maduros. |
| **Frontend DP & Self-Service** | **TypeScript** (Next.js 15, Tailwind, React 19) | Produtividade maxima em UI, tipagem de contratos sincronizada via OpenAPI, Server Components para paineis analiticos e acessibilidade. |
| **Simulador de Borda (Live Preview)** | **Rust -> WebAssembly (Wasm)** | Calculo deterministico sem latencia de rede rodando no navegador do operador enquanto ele digita horas extras ou simula rescisao. |
| **Auditoria, Relatorios & ETL** | **Python 3.12+** (Polars, DuckDB, FastAPI) | Ecossistema de dados imativel para gerar o Relatorio de Transparencia Salarial (Lei 14.611/2023), auditorias de compliance e migracao de bancos legados. |
| **Mensageria e Filas eSocial** | **RabbitMQ / Redis Streams** | Garantia de entrega, idempotencia e retry com backoff exponencial para transmissao de lotes XML ao governo. |
| **Persistencia e Auditoria** | **PostgreSQL 16+** | Suporte a particionamento por competencia, dados bitemporais e trilha de auditoria append-only. |

---

## 3. Documentacao Normativa Principal

O mapeamento exaustivo de todas as regras trabalhistas, previdenciarias, fiscais e de produto esta formalizado nos documentos:
- **[SPECIFICATION.md](SPECIFICATION.md):** Especificacao mestre com tabelas, algoritmos de fatiamento marginal de INSS, comparador automatico de IRRF tradicional vs simplificado, DCTFWeb, FGTS Digital via Pix, modalidades de rescisao (Artigos 477 a 484-A CLT), calculo de ferias e 13o salario, e arquitetura poliglota.
- **[docs/TAKO_PARADIGM_UI_UX.md](docs/TAKO_PARADIGM_UI_UX.md):** Especificacao de produto no padrao Tako (tako.ai), detalhando o calculo continuo (Continuous Payroll), unificacao CLT + PJ, design system de alta densidade e Agente Analista com IA.

---

## 4. Estrutura do Repositorio

```
ThPay/
├── README.md                      # Apresentacao executiva e matriz arquitetural
├── SPECIFICATION.md               # Mapeamento integral e exaustivo de regras e calculos
├── pyproject.toml                 # Metadados e dependencias do prototipo analitico
├── .gitignore                     # Filtros de exclusao para controle de versao
├── docs/                          # Documentos de arquitetura e design
│   └── TAKO_PARADIGM_UI_UX.md     # Paradigma de produto e design system estilo Tako
├── ui/                            # Prototipo visual e funcional interativo
│   └── index.html                 # Interface SPA estilo Tako com Live Payslip Drawer e IA
├── thpay/                         # Prototipo funcional das regras de negocio em Python
│   ├── domain/                    # Modelos de dominio tipados (Empresa, Contrato, Rubrica)
│   ├── engine/                    # Motor DAG e ordenacao topologica
│   ├── tax/                       # Algoritmos fiscais (INSS progressivo, IRRF comparado, FGTS)
│   └── pipelines/                 # Pipeline de folha mensal com protecao anti-negativo
├── tests/                         # Suite de testes automatizados e regressao (11 testes)
└── demo.py                        # Script demonstrativo executavel no terminal
```

---

## 5. Como Executar e Validar

### 5.1 Visualizar o Prototipo Visual Interativo (Estilo Tako)
Abra diretamente o arquivo `ui/index.html` em qualquer navegador web ou sirva via HTTP local:
```bash
python3 -m http.server 3000 --directory ui
# Acesse: http://localhost:3000
```
Recursos incluidos no prototipo web:
- Dashboard de fechamento continuo com readiness bar.
- Diretorio unificado CLT + PJ com badges semanticos.
- Live Payslip Inspector lateral (deslizante) com fatiamento de INSS e comparador IRRF.
- Interface conversacional simulada com o Agente Analista ThPay.
- Central de eventos eSocial e guias Pix (GFD).

### 5.2 Executar Demonstracao de Calculo no Terminal
```bash
python3 demo.py
```

### 5.3 Executar Testes Unitarios
```bash
python3 -m unittest discover tests/
```


---
*ThPay Core Team // Arquitetura Sagital de Sistemas Críticos*

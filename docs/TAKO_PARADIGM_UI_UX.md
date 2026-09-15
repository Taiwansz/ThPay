# ThPay // Especificacao do Paradigma Funcional e Visual (Estilo Tako)
Versao: 1.0.0-PROD-UX | Status: Normativo e Canônico | Referencia: Tako (tako.ai)

---

## 1. O Paradigma Tako Aplicado ao ThPay

A **Tako** (tako.ai) redefiniu o padrao da industria de software de Recursos Humanos e Departamento Pessoal no Brasil ao romper com os dois grandes males dos sistemas legados (TOTVS, Senior, Folhamatic):
1. **O Pesadelo do "Batch" de Fim de Mes:** Softwares tradicionais acumulam dados o mes inteiro e rodam um processamento monolitico no dia 28 que demora horas, gera centenas de inconsistencias crípticas e estressa a equipe do DP.
2. **A Interface Arcaica dos Anos 90:** Menus cinzas labirinticos, tabelas estaticas ilegiveis e fragmentacao extrema (um sistema para ponto, outro para beneficios, outro para folha e planilhas paralelas para PJs).

O ThPay incorpora a mesma filosofia de produto de classe mundial:
- **Continuous Payroll (Calculo Continuo em Tempo Real):** A folha nunca dorme. Qualquer entrada (atestado, admissao, ajuste salarial, hora extra) recalcula instantaneamente os tributos, o custo empresa e o holerite.
- **Unificacao Rigorosa CLT + PJ:** Uma unica esteira operacional para gerenciar o headcount total da companhia, mantendo estrita segregacao tributaria no motor fiscal.
- **Codigo Deterministico + Agentes de IA:** O calculo financeiro e fiscal e 100% deterministico e imutavel em codigo (Java/DAG). A Inteligencia Artificial opera como uma camada de supervisao, analise preditiva e interface em linguagem natural ("Agente Analista").
- **Estetica Contemporanea de Alta Densidade:** Inspirada nos melhores produtos de tecnologia global (Linear, Ramp, Tako), priorizando clareza visual, tipografia refinada e ausencia de ruido grafico.

---

## 2. Design System e Identidade Visual

### 2.1 Paleta de Cores e Hierarquia de Contraste
O ThPay adota uma paleta sobria, de alta precisao e elegancia editorial, evitando cliches visuais:

- **Superficies e Fundos:**
  - `bg-canvas`: `#090A0F` (Dark) / `#F9FAFB` (Light)
  - `bg-surface`: `#11131A` (Dark) / `#FFFFFF` (Light)
  - `bg-subtle`: `#181B26` (Dark) / `#F3F4F6` (Light)
  - `border-subtle`: `#262B3D` (Dark) / `#E5E7EB` (Light)
- **Tipografia:**
  - `text-primary`: `#F8FAFC` (Dark) / `#0F172A` (Light)
  - `text-secondary`: `#94A3B8` (Dark) / `#475569` (Light)
  - `text-muted`: `#64748B` (Dark) / `#94A3B8` (Light)
- **Cores Semanticas de Alta Precisao:**
  - `accent-compliance` (Verde Esmeralda): `#10B981` (eSocial sincronizado, guias quitadas, sem divergencias)
  - `accent-attention` (Ambar Tecnico): `#F59E0B` (Atestado pendente, pendencia cadastral, lote aguardando transmissao)
  - `accent-critical` (Rubi): `#EF4444` (Divergencia fiscal com totalizador, risco de perda de prazo)
  - `accent-agent` (Indigo Profundo): `#6366F1` (Agente Analista, simulacoes e insights inteligentes)
  - `badge-clt`: Background `#1E293B`, Texto `#38BDF8`
  - `badge-pj`: Background `#312E81`, Texto `#A5B4FC`

### 2.2 Tipografia e Escala Espacial
- **Familia Tipografica:** Inter ou Geist Sans para interface, e JetBrains Mono para valores monetarios, codigos de rubrica e hashes SHA-256.
- **Escala de Dados:**
  - Numeros e metricas financeiras em formato tabular (`font-mono tracking-tight`), garantindo alinhamento decimal perfeito em tabelas.

---

## 3. Modulos Funcionais Centrais

### 3.1 Painel de Fechamento Continuo (Continuous Live Dashboard)
- **Healthcheck em Tempo Real:** Barra de status indicando o nivel de prontidao da folha (ex: `Folha Setembro/2026: 98,4% Pronta | 2 inconsistencias para revisar`).
- **Cards de Resumo Executivo:**
  - Custo Total de Folha (Salarios Brutos + Beneficios + Encargos Patronais).
  - Cota Previdenciaria e Fiscal (DARF DCTFWeb consolidado).
  - FGTS Digital Previsto (recolhimento via Pix no dia 20).
  - Headcount Ativo segregado por modelo de contratacao (CLT, PJ, Estagio, Jovem Aprendiz).
- **Feed de Eventos em Tempo Real:** Registro visual cronologico de alteracoes que impactaram a folha nas ultimas 24 horas.

### 3.2 Tabela Unificada de Pessoas (Directory & People Ops)
- Visualizacao hibrida de colaboradores CLT e prestadores PJ.
- Colunas essenciais: Colaborador (Avatar, Nome, Cargo, CBO), Modalidade (Badge CLT / PJ), Salario Base / Fixo Mensal, Custo Empresa Projetado, Status de Ponto e Acoes.
- Busca instantanea e filtros por departamento, regime tributario e sindicato.

### 3.3 Drawer Lateral de Live Payslip Inspector (O "Raio-X do Holerite")
Ao clicar em qualquer colaborador na tabela, um painel deslizante se abre na lateral direita sem que o operador perca o contexto da lista:
- **Resumo do Holerite:** Total de Proventos, Total de Descontos e Liquido a Pagar.
- **Desdobramento Visual dos Impostos:**
  - Barra interativa mostrando as fatias marginais do INSS (Faixa 1 a 7,5%, Faixa 2 a 9%, etc.).
  - Demonstracao do comparativo de IRRF: demonstrando exatamente por que o motor escolheu as Deducoes Legais ou o Desconto Simplificado.
- **Calculo de Custo Empresa:** Demonstracao transparente de quanto aquele colaborador realmente custa (Salario + Encargos Patronais 20% + RAT x FAP + Terceiros + FGTS + Provisao de Ferias e 13o).
- **Assinatura SHA-256 e Auditoria:** Hash de validacao do lote.

### 3.4 O Agente Analista (Copiloto Conversacional de DP)
Inspirado nos agentes de IA da Tako (como o Otto e a Nara):
- Campo de comando com atalho rapido (`Cmd + K` ou barra de chat) para consultas em linguagem natural:
  - *"Qual sera o custo total se promovermos 3 engenheiros de Pleno para Senior neste mes?"*
  - *"Mostre todos os colaboradores que ultrapassaram 15 horas extras na semana passada."*
  - *"Qual e a previsao de DARF Previdenciario para este mes em comparacao com o mes anterior?"*
- O Agente Analista traduz a pergunta em consultas tipadas no banco de dados e executa o motor de calculo deterministico para trazer numeros exatos, nunca alucinados.

### 3.5 Central de Automacao eSocial e Guias Fiscais
- Visualizacao em kanban ou esteira do ciclo de vida dos eventos:
  - Eventos de Admissao e Ponto (S-2190, S-2200, S-2206).
  - Eventos de Remuneracao (S-1200) e Pagamentos (S-1210).
  - Conciliacao automatica com totalizadores de retorno (S-5001, S-5002, S-5003).
- Emissao de guias com 1 clique:
  - GFD do FGTS Digital com QR Code Pix dinamico.
  - DARF Previdenciario Numerado da DCTFWeb.

---

## 4. Arquitetura de Componentes Frontend (Next.js 15 / React 19)

```
ui/
├── app/
│   ├── layout.tsx                 # Shell do aplicativo, sidebar e topbar global
│   ├── page.tsx                   # Dashboard principal da folha continua
│   ├── pessoas/                   # Diretorio unificado CLT + PJ
│   ├── holerite/                  # Visualizador e simulador de holerites
│   └── esocial/                   # Central de eventos governamentais
├── components/
│   ├── ui/                        # Botoes, dialogs, drawers, badges, inputs
│   ├── dashboard/
│   │   ├── MetricCards.tsx        # Resumo de folha, encargos e headcount
│   │   ├── ContinuousFeed.tsx     # Feed de eventos de recalculo continuo
│   │   └── ReadinessBar.tsx       # Barra de conformidade e fechamento
│   ├── people/
│   │   ├── PeopleTable.tsx        # Tabela densa com filtros rapidos
│   │   └── EmployeeDrawer.tsx     # Drawer lateral de Raio-X do colaborador
│   ├── payslip/
│   │   ├── LivePayslipView.tsx    # Visualizacao de proventos e descontos
│   │   └── TaxBracketVisual.tsx   # Grafico de fatias de INSS e IRRF
│   └── agent/
│       └── AnalystChat.tsx        # Interface conversacional com o Agente Analista
```

---
*ThPay Core Team // Padrao de Excelencia e Experiencia do Usuario*

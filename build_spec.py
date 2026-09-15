# -*- coding: utf-8 -*-
"""
Script de geracao do documento mestre de especificacao ThPay.
Produz SPECIFICATION.md com profundidade industrial, formulas matematicas,
regras de compliance eSocial, legislacao trabalhista e arquitetura de software.
"""

sections = []

sections.append("""# ThPay // Especificacao Mestre e Mapeamento Integral de Folha de Pagamento
Versao: 1.0.0-PROD-SPEC | Status: Canonico e Normativo | Ambito: Brasil (CLT / eSocial / RFB / MTE)

---

## Sumario Executivo

O processamento de folha de pagamento no ecossistema juridico e tributario brasileiro e amplamente reconhecido como um dos dominios de software de maior complexidade do mundo. A convergencia da CLT (Consolidacao das Leis do Trabalho), de legislacoes esparsas, de acordos e convencoes coletivas de trabalho (CCT/ACT) com o eSocial, a DCTFWeb, o FGTS Digital e a EFD-Reinf exige determinismo absoluto, rastreabilidade bitemporal e modelagem matematica exata centavo a centavo.

O ThPay foi concebido para ser um motor de calculo e conformidade (Payroll Engine & Compliance Core) de alta performance, projetado sob os principios de imutabilidade, resolucao por grafo aciclico dirigido (DAG) e desacoplamento total entre as regras fiscais vigentes e a persistencia historica.

Este documento estabelece o mapeamento formal e exaustivo de todos os modulos, entidades, formulas, incidencias, tabelas e fluxos operacionais necessarios para a construcao de um sistema de folha de pagamento de classe empresarial.

---

## 1. Principios Arquiteturais e Fundamentos de Engenharia

### 1.1 Modelo de Dados Bitemporal (Valid-Time vs Transaction-Time)
Sistemas legados frequentemente falham ao sobrescrever registros historicos quando ocorrem convencoes coletivas retroativas (dissidios) ou retificacoes trabalhistas. O ThPay opera estritamente sob arquitetura bitemporal:
1. **Valid Time (Tempo da Realidade Juridica):** O periodo no qual o fato juridico-trabalhista efetivamente ocorreu (ex: o colaborador teve aumento salarial com vigencia retroativa a 01/05/2025).
2. **Transaction Time (Tempo do Registro no Sistema):** O momento exato em que o fato foi gravado no banco de dados do sistema (ex: a Convencao Coletiva foi homologada e digitada no sistema em 20/09/2025).

Qualquer consulta ou recalculo pode ser executado em duas dimensoes:
- "Qual era o valor da folha de maio de 2025 com o conhecimento que tinhamos em 31 de maio de 2025?" (Visao Contabil Original / Fechamento Oficial)
- "Qual e o valor da folha de maio de 2025 com o conhecimento que temos hoje?" (Visao Retroativa para Apuracao de Diferencas e Folha Complementar)

### 1.2 Imutabilidade Criptografica e Version Lock
- Apos o envio do evento de fechamento periodico ao eSocial (S-1299) e a aprovacao financeira, o lote da folha e lacrado (Locked State).
- E gerado um hash SHA-256 consolidando o estado de todos os colaboradores, proventos, descontos, bases e encargos da competencia.
- Uma folha fechada nunca pode sofrer UPDATE direto no banco de dados. Qualquer alteracao requer a emissao de uma Folha Complementar ou de uma Folha Retificadora (que reabre a competencia mediante evento S-1298 do eSocial).

### 1.3 Motor de Calculo Baseado em Grafo Aciclico Dirigido (DAG)
O calculo de uma folha de pagamento nao e linear. Rubricas dependem de outras rubricas, que geram bases de calculo acumuladoras, que por sua vez alimentam tributos e deducoes em cadeia.
- Cada rubrica, base ou tributo e representado como um vertice em um Grafo Aciclico Dirigido (DAG).
- As dependencias funcionais sao as arestas direcionadas.
- O motor resolve a ordem de avaliacao via Ordenacao Topologica (Topological Sort).
- Ciclos de dependencia sao detectados estaticamente durante a validacao do grafo antes da execucao, impedindo condicoes de corrida ou recursao infinita.

### 1.4 Precisao Monetaria e Arredondamento
- Operacoes financeiras de folha de pagamento nao podem sofrer distorcoes de ponto flutuante binario (`float`).
- Todo o calculo financeiro deve utilizar tipos decimais de precisao arbitraria (como `Decimal` com precisao minima de 28 digitos e escala de 4 a 6 casas decimais intermediarias).
- Arredondamento final de cada rubrica: `ROUND_HALF_EVEN` (Banqueiro) ou `ROUND_HALF_UP` (conforme exigencia estrita da RFB e eSocial, onde 0.005 arredonda para cima para 0.01).
- Totalizadores sao calculados somando-se os valores previamente arredondados de cada rubrica individual para manter paridade absoluta com os eventos S-5001, S-5002 e S-5003 do eSocial.
""")

sections.append("""## 2. Modelo de Entidades e Cadastro Estrutural

```
+----------------------------------------------------------+
|                   Empregador (Empresa)                   |
|   CNPJ Raiz | CNAE | FAP | Grau Risco | Regime Tributario|
+-----------------------------+----------------------------+
                              | 1..n
+-----------------------------v----------------------------+
|                 Estabelecimentos / Filiais               |
|       CNPJ Filial / CNO / CAEPF | FPAS | Terceiros       |
+-----------------------------+----------------------------+
                              | 1..n
+-----------------------------v----------------------------+
|                   Lotacoes Tributarias                   |
|     Codigo eSocial Tabela 10 | Tomadores de Servico      |
+-----------------------------+----------------------------+
                              | 1..n
+-----------------------------v----------------------------+
|               Contratos de Trabalho / Vinculos           |
|  Matricula | Categoria eSocial | Salario | Tipo Contrato |
+-----------------------------+----------------------------+
                              | 1..n
+-----------------------------v----------------------------+
|             Demonstrativo Mensal da Folha (Holerite)     |
|   Rubricas | Bases | Descontos | Encargos | Liquido      |
+----------------------------------------------------------+
```

### 2.1 Empregador e Estabelecimentos
- **Identificadores:** CNPJ Raiz (14 digitos), CAEPF (Pessoa Fisica equiparada a empresa - 14 digitos), CNO (Cadastro Nacional de Obras de Construcao Civil).
- **Regime Tributario:**
  - `SIMPLES_NACIONAL_ANEXO_I_II_III_V`: Isento de Contribuicao Patronal Previdenciaria (CPP 20%), RAT e Terceiros na guia de folha (recolhidos no DAS unificado).
  - `SIMPLES_NACIONAL_ANEXO_IV`: Recolhe CPP patronal de 20% e RAT x FAP diretamente sobre a folha de pagamento, porem isento de Terceiros/Outras Entidades.
  - `LUCRO_PRESUMIDO` / `LUCRO_REAL`: Recolhimento integral de CPP 20%, RAT ajustado pelo FAP e Terceiros (FPAS).
  - `DESONERACAO_CPRB`: Empresas contempladas pela Lei 12.546/2011 e regras de transicao 2024-2027 que substituem a CPP de 20% pela aliquota sobre a Receita Bruta.
  - `ENTIDADE_BENEFICENTE`: Imune/Isenta de cota patronal e terceiros (Lei Complementar 187/2021).
- **Parametros Previdenciarios e de Seguranca:**
  - CNAE Preponderante (Classificacao Nacional de Atividades Economicas).
  - Grau de Risco de Acidente de Trabalho: 1 (Leve), 2 (Medio), 3 (Grave), 4 (Gravissimo).
  - Aliquota RAT Basica: 1,0%, 2,0% ou 3,0%.
  - FAP (Fator Acidentario de Prevencao): Indice multiplicador anual publicado pela Previdencia, variando de 0,5000 a 2,0000 com 4 casas decimais.
  - Aliquota RAT Ajustada: Calculada pela expressao:
    $$\\text{RAT\\_Ajustado} = \\text{RAT\\_Basico} \\times \\text{FAP}$$
  - Codigo FPAS (Fundo de Previdencia e Assistencia Social): Determina o enquadramento de recolhimento de terceiros (ex: 507 para Industria, 515 para Comercio/Servicos, 523 para Sindicatos, 582 para Construcao Civil).
  - Codigo de Terceiros / Outras Entidades: Codigo numerico de 4 digitos que define as aliquotas para SENAI, SESI, SENAC, SESC, SEBRAE, INCRA, Salario-Educacao, etc.

### 2.2 Convencoes e Acordos Coletivos (CCT / ACT)
- Sindicato Patronal e Sindicato Laboral conveniados.
- Data-Base da categoria (mes oficial de renovacao do dissidio coletivo: ex: Maio, Setembro).
- Pisos Salariais por funcao / CBO (Classificacao Brasileira de Ocupacoes).
- Percentuais de Adicionais Convencionais:
  - Horas Extras em dias uteis: minimo legal CLT de 50%, comumente elevado para 60%, 70% ou 80% em CCT.
  - Horas Extras em domingos e feriados: minimo legal CLT de 100%.
  - Adicional Noturno: minimo legal de 20% para trabalhadores urbanos, frequentemente elevado por convencoes.
- Clausulas Sociais Especificas:
  - Quebra de Caixa (para operadores de caixa, tesoureiros).
  - Auxilio Creche (valor e prazo de concessao para colaboradoras maes).
  - Estabilidades Provisorias (pos-retorno de ferias, retorno de afastamento, pre-aposentadoria nos 12 ou 24 meses anteriores ao direito).

### 2.3 Contratos de Trabalho e Categorias de Trabalhadores
O sistema deve suportar todas as categorias canonicas mapeadas pelo eSocial:
1. `101`: Empregado Geral (vinculo CLT por prazo indeterminado).
2. `102`: Empregado - Trabalhador Rural por prazo indeterminado.
3. `103`: Aprendiz (Lei 10.097/2000 - aliquota FGTS diferenciada de 2%).
4. `104`: Empregado Domestico (recolhimento via DAE com FGTS 8% + reserva rescisoria 3,2%).
5. `105`: Empregado - Contrato de Trabalho Intermitente (Art. 452-A CLT).
6. `106`: Empregado - Contrato por Prazo Determinado / Temporario (Lei 6.019/1974).
7. `111`: Empregado - Contrato de Experiencia (Art. 443 CLT, maximo 90 dias com prorrogacao unica).
8. `701`: Dirigente Sindical.
9. `721`: Diretor Nao Empregado com FGTS (pro-labore com FGTS facultativo).
10. `722`: Diretor Nao Empregado sem FGTS (pro-labore padrao).
11. `723`: Cooperado que presta servicos por meio de cooperativa de trabalho.
12. `731`: Contribuinte Individual / Autonomo contratado por empresa.
13. `901`: Estagiario (Lei 11.788/2008 - bolsa auxilio isenta de encargos trabalhistas e previdenciarios, com retencao exclusiva de IRRF quando aplicavel).

### 2.4 Dependentes e Beneficiarios
- Dependentes para fins de IRRF:
  - Conjuge ou companheiro(a) com uniao estavel.
  - Filhos ou enteados ate 21 anos, ou ate 24 anos se cursando ensino superior ou escola tecnica de segundo grau.
  - Filhos ou enteados com incapacidade fisica ou mental permanente para o trabalho (sem limite de idade).
  - Pais, avos e bisavos sem rendimentos ou com rendimentos inferiores ao limite de isencao.
- Dependentes para fins de Salario-Familia:
  - Filhos ou equiparados ate 14 anos de idade, ou invalidos de qualquer idade.
  - Requisito legal: Remuneracao mensal bruta do colaborador dentro do teto de baixa renda fixado anualmente pelo Ministerio da Previdencia.
- Beneficiarios de Pensao Alimenticia:
  - Cadastro judicial individualizado com conta bancaria especifica.
  - Modalidade de calculo determinada pelo oficio judicial:
    - Percentual sobre Rendimento Bruto.
    - Percentual sobre Rendimento Liquido (Bruto deduzido de INSS e IRRF).
    - Valor Monetario Fixo corrigido por indice oficial (ex: IPCA, Salario Minimo).
  - Incidencia expressa sobre verbas: Ferias, Terco Constitucional, 13o Salario, PLR (Participacao nos Lucros e Resultados), Verbas Rescisorias.
""")

sections.append("""## 3. Arquitetura do Motor de Calculo e Grafo de Rubricas (DAG)

### 3.1 Resolucao de Dependencias Topologicas
Em vez de scripts procedurais repletos de `if/else` e ordens rigidas de codigo, o ThPay modela cada conceito como um no de um grafo aciclico direcionado.

```
[Dias Trabalhados] ---> [Salario Proporcional]
                              |
[Horas Extras 50%] ----------+---> [Base INSS] ---> [INSS Empregado]
                              |          |                 |
[Adicional Noturno] ----------+          +---> [FGTS]      |
                              |                            v
[DSR s/ HE e Noturno] --------+---------------------> [Base IRRF] ---> [IRRF Empregado]
                                                           |
[Desconto VT 6%] -----------------------------------------+
                                                           |
[Desconto VR/VA] -----------------------------------------+
                                                           v
                                                  [Salario Liquido]
```

### 3.2 Pipeline Padrao de Avaliacao
1. **Fase 0 - Ingestao Contratual e Parametrica:**
   - Carga do contrato, salario base, regime de jornada (mensalista/horista), dependentes e historico de afastamentos/ferias no mes.
   - Carga das tabelas fiscais vigentes da competencia (INSS, IRRF, Salario-Familia, FAP, CCT).
2. **Fase 1 - Processamento de Ponto e Variaveis Temporais:**
   - Ingestao do espelho de ponto apurado.
   - Calculo de horas normais, horas de falta/atraso, horas extras segregadas por percentual (50%, 60%, 100%), horas noturnas e hora ficta reduzida.
3. **Fase 2 - Avaliacao de Proventos Primarios e Adicionais:**
   - Salario Base ou Horas Normais proporcionais aos dias de direito.
   - Adicionais de Insalubridade (10%, 20% ou 40% sobre Salario Minimo ou Piso da CCT) e Periculosidade (30% sobre Salario Base contratual).
   - Comissoes, premios e gratificacoes.
4. **Fase 3 - Calculo dos Reflexos de DSR (Descanso Semanal Remunerado):**
   - Aplicacao da formula legal da Lei 605/1949 e Sumula 172 do TST:
     $$\\text{DSR} = \\left( \\frac{\\sum \\text{Variaveis do Mes}}{\\text{Dias Uteis}} \\right) \\times \\text{Domingos e Feriados}$$
5. **Fase 4 - Consolidacao das Bases de Encargos Sociais:**
   - Apuracao da Base de INSS (soma de todas as rubricas com `codIncCP = 11`).
   - Apuracao da Base de FGTS (soma de todas as rubricas com `codIncFGTS = 11`).
   - Apuracao da Base de Salario-Familia e verificacao de elegibilidade.
6. **Fase 5 - Calculo dos Encargos do Colaborador:**
   - Calculo progressivo do INSS Empregado (fatiamento por faixas da EC 103/2019 com teto maximo).
   - Concessao do Salario-Familia (credito compensatorio).
7. **Fase 6 - Calculo do Imposto de Renda Retido na Fonte (IRRF):**
   - Apuracao da Base de IRRF Bruta (rubricas com `codIncIRRF = 11`).
   - Deducoes Legais Tradicionais: INSS recolhido + Dependentes (R$ 189,59 cada) + Pensao Alimenticia + Previdencia Privada PGBL.
   - Avaliacao automatica do Desconto Simplificado Mensal (Regra mais favoravel ao contribuinte).
   - Aplicacao da Tabela Progressiva sobre a Base Liquida de IRRF.
8. **Fase 7 - Calculo de Beneficios e Descontos Voluntarios/Legais:**
   - Vale-Transporte: menor valor entre 6% do salario base contratual e o custo real do beneficio fornecido.
   - Vale-Refeição/Alimentacao (PAT): desconto contratual limitado a 20% do custo do beneficio.
   - Plano de Saude e Odontologico: mensalidade fixa + coparticipacao em exames e consultas.
   - Desconto de Emprestimo Consignado: validacao rigorosa da Margem Consignavel da Lei 10.820/2003.
   - Desconto de Adiantamento Salarial ja quitado na quinzena anterior.
   - Pensao Alimenticia sobre proventos ou liquido conforme oficio.
9. **Fase 8 - Consolidacao do Liquido e Checagem de Consistencia:**
   - Calculo: `Total_Proventos - Total_Descontos = Salario_Liquido`.
   - **Regra Anti-Liquido Negativo:** A legislacao trabalhista brasileira veda que o colaborador fique com saldo negativo no holerite. Caso os descontos superem os proventos, o sistema gera a rubrica automatica de `Insuficiencia de Saldo` (provento compensatorio que zera o liquido e vira desconto no mes seguinte).
10. **Fase 9 - Apuracao dos Encargos Patronais (Custo Empresa):**
    - INSS Patronal (20%), RAT Ajustado (RAT x FAP) e Terceiros/FPAS.
    - FGTS Patronal (8% ou 2% aprendiz).
""")

sections.append("""## 4. Dicionario Canonico de Rubricas e Incidencias Tributarias

### 4.1 Tipologia de Rubricas
Conforme classificacao oficial do eSocial (Evento S-1010):
- **Tipo 1 - Vencimento / Provento:** Aumenta o valor a receber pelo trabalhador.
- **Tipo 2 - Desconto:** Reduz o valor liquido a receber pelo trabalhador.
- **Tipo 3 - Informativa:** Nao afeta o liquido, mas compoe bases tributarias ou informacoes estatisticas (ex: FGTS depositado, base de calculo de tributos).
- **Tipo 4 - Informativa Dedutora:** Utilizada para compensacoes e reducoes de bases sem impactar diretamente o liquido financeiro.

### 4.2 Tabela Mestre de Parametrizacao de Rubricas Canônicas

| Codigo | Nome da Rubrica | Tipo | Incid. INSS (codIncCP) | Incid. FGTS (codIncFGTS) | Incid. IRRF (codIncIRRF) | Natureza eSocial |
|---|---|---|---|---|---|---|
| **1000** | Salario Base / Vencimento Normal | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1000 (Salario) |
| **1005** | DSR Mensalista (Ja incluso no Salario) | 3 (Informativa) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao tributavel) | 1000 (Salario) |
| **1010** | Horas Extras 50% | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1003 (Horas Extras) |
| **1015** | Horas Extras 100% | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1003 (Horas Extras) |
| **1020** | DSR sobre Horas Extras | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1010 (DSR) |
| **1030** | Adicional Noturno 20% | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1201 (Adic. Noturno) |
| **1035** | DSR sobre Adicional Noturno | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1010 (DSR) |
| **1040** | Adicional de Insalubridade | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1202 (Insalubridade) |
| **1050** | Adicional de Periculosidade | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1203 (Periculosidade) |
| **1060** | Comissoes / Percentagens | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1005 (Comissoes) |
| **1065** | DSR sobre Comissoes | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 1010 (DSR) |
| **1070** | Salario-Familia | 1 (Provento) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao tributavel) | 1409 (Salario-Familia) |
| **1080** | Salario-Maternidade | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 4001 (Sal. Maternidade) |
| **1090** | Auxilio Doenca (15 primeiros dias empresa) | 1 (Provento) | 11 (Mensal) | 11 (Mensal) | 11 (Remun. Mensal) | 4002 (Aux. Doenca) |
| **1100** | Adiantamento Salarial Concedido (Provento no Vale) | 1 (Provento) | 00 (No Vale) | 00 (No Vale) | 00 (Se nao cruzar mes) | 1020 (Adiantamento) |
| **2000** | Ferias Gozadas no Mes | 1 (Provento) | 13 (Ferias) | 11 (Mensal) | 13 (Ferias) | 1020 (Ferias Gozadas) |
| **2010** | Terco Constitucional de Ferias Gozadas | 1 (Provento) | 13 (Ferias) | 11 (Mensal) | 13 (Ferias) | 1021 (Terco Ferias) |
| **2020** | Abono Pecuniario de Ferias (Venda 10 dias) | 1 (Provento) | 00 (Nao e base) | 00 (Nao e base) | 00 (Isento Art 6 Lei 7713) | 1022 (Abono Pecuniario) |
| **2030** | Terco Constitucional s/ Abono Pecuniario | 1 (Provento) | 00 (Nao e base) | 00 (Nao e base) | 00 (Isento) | 1023 (Terco Abono) |
| **3000** | 13o Salario - 1a Parcela (Adiantamento) | 1 (Provento) | 00 (Nao e base) | 12 (13o Salario) | 00 (Nao tributavel) | 5001 (13o Adiantamento) |
| **3010** | 13o Salario - 2a Parcela Integral | 1 (Provento) | 12 (13o Salario) | 12 (13o Salario) | 12 (13o Tribut. Excl.) | 5002 (13o Integral) |
| **4000** | Saldo de Salario Rescisorio | 1 (Provento) | 14 (Rescisao) | 21 (Rescisorio) | 11 (Remun. Mensal) | 1000 (Salario Rescisao) |
| **4010** | Aviso Previo Indenizado | 1 (Provento) | 00 (Nao incide INSS - STF) | 21 (Incide FGTS) | 00 (Isento Art 6 Lei 7713) | 6000 (Aviso Indenizado) |
| **4020** | 13o Salario Proporcional Rescisao | 1 (Provento) | 12 (13o Salario) | 21 (Rescisorio) | 12 (13o Tribut. Excl.) | 5003 (13o Rescisao) |
| **4030** | Ferias Proporcionais Rescisao | 1 (Provento) | 00 (Nao e base) | 00 (Nao e base) | 00 (Isento) | 1024 (Ferias Indenizadas) |
| **4040** | Terco Constitucional de Ferias Rescisao | 1 (Provento) | 00 (Nao e base) | 00 (Nao e base) | 00 (Isento) | 1025 (Terco Rescisao) |
| **5000** | INSS Empregado Folha Mensal | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Dedutivel) | 9201 (INSS) |
| **5010** | IRRF Empregado Folha Mensal | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao e base) | 9203 (IRRF) |
| **5020** | Faltas Injustificadas | 2 (Desconto) | 11 (Reduz base) | 11 (Reduz base) | 11 (Reduz base) | 9200 (Faltas) |
| **5025** | DSR Descontado por Faltas da Semana | 2 (Desconto) | 11 (Reduz base) | 11 (Reduz base) | 11 (Reduz base) | 9200 (DSR Desconto) |
| **5030** | Vale-Transporte (Limite 6%) | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao e base) | 9210 (Desc. VT) |
| **5040** | Vale-Alimentacao / Refeicao (PAT) | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao e base) | 9211 (Desc. VR) |
| **5050** | Plano de Saude / Odonto | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao e base) | 9219 (Desc. Assist. Medica) |
| **5060** | Adiantamento Salarial (Desconto na Mensal) | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao e base) | 9214 (Desc. Adiantamento) |
| **5070** | Pensao Alimenticia Judicial | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Dedutivel IRRF) | 9205 (Desc. Pensao) |
| **5080** | Emprestimo Consignado em Folha | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao e base) | 9215 (Desc. Consignado) |
| **5090** | Desconto de 1a Parcela do 13o na 2a Parcela | 2 (Desconto) | 00 (Nao e base) | 00 (Nao e base) | 00 (Nao e base) | 9217 (Desc. 1a Parc 13o) |
| **9000** | Base de Calculo INSS Mensal | 3 (Informativa) | 00 | 00 | 00 | 9901 (Base INSS) |
| **9010** | Base de Calculo FGTS Mensal | 3 (Informativa) | 00 | 00 | 00 | 9902 (Base FGTS) |
| **9020** | Base de Calculo IRRF Mensal | 3 (Informativa) | 00 | 00 | 00 | 9903 (Base IRRF) |
| **9030** | FGTS Mensal Recolhido pela Empresa | 3 (Informativa) | 00 | 00 | 00 | 9904 (Valor FGTS) |
""")

sections.append("""## 5. Jornada, Ponto e Variaveis Mensais

### 5.1 Regimes de Jornada e Divisores Mensais
A legislacao brasileira estabelece que a jornada padrao e de no maximo 8 horas diarias e 44 horas semanais (Constituicao Federal Art. 7, XIII).
- **Jornada de 44h semanais:** Divisor = 220 horas mensais.
  $$\\text{Salario Horario} = \\frac{\\text{Salario Base}}{220}$$
- **Jornada de 40h semanais:** Divisor = 200 horas mensais.
  $$\\text{Salario Horario} = \\frac{\\text{Salario Base}}{200}$$
- **Jornada de 36h semanais:** Divisor = 180 horas mensais.
- **Jornada de 30h semanais:** Divisor = 150 horas mensais.
- **Jornada 12x36:** Escala especial de 12 horas de trabalho seguidas por 36 horas de descanso ininterrupto (Art. 59-A da CLT). As 12h ja englobam a compensacao de repousos e feriados.

### 5.2 Horas Extras
- **Horas Extras em Dias Uteis / Sabados Comuns:**
  $$\\text{Valor Hora Extra 50\\%} = \\text{Salario Horario} \\times 1{,}50$$
- **Horas Extras em Domingos e Feriados:**
  $$\\text{Valor Hora Extra 100\\%} = \\text{Salario Horario} \\times 2{,}00$$
- **Integracao de Adicionais na Base da Hora Extra (Sumula 264 do TST):**
  A hora extra nao incide apenas sobre o salario base seco. Devem integrar a base da hora extra: Adicional de Insalubridade, Adicional de Periculosidade, Gratificacao de Funcao e Adicional Noturno (quando a HE for noturna).
  $$\\text{Base Valor Hora} = \\frac{\\text{Salario Base} + \\text{Insalubridade} + \\text{Periculosidade} + \\text{Gratificacao}}{\\text{Divisor Mensal}}$$

### 5.3 Adicional Noturno e a Reducao da Hora Noturna Ficta
- **Periodo Urbano:** Trabalho executado entre 22h00 de um dia e 05h00 do dia seguinte (CLT Art. 73).
- **Aliquota Minima:** 20% sobre a hora diurna.
- **Hora Ficta Noturna:** Cada hora de relogio noturna e computada na proporcao de 52 minutos e 30 segundos (ou 52,5 minutos).
  $$\\text{Fator de Reducao} = \\frac{60}{52{,}5} = \\frac{8}{7} \\approx 1{,}142857$$
  Assim, trabalhar 7 horas reais entre 22h e 05h equivale juridicamente a trabalhar 8 horas normais.
- **Prorrogacao da Jornada Noturna (Sumula 60, II do TST):** Se o colaborador cumpriu integralmente a jornada no periodo noturno e prosseguiu trabalhando alem das 05h00 da manha, as horas posteriores as 05h00 continuam remuneradas com adicional noturno e reducao ficta.

### 5.4 Descanso Semanal Remunerado (DSR) sobre Variaveis
Conforme a Lei 605/1949 e a Sumula 172 do TST, o trabalho em horas extras ou noturnas reflete no valor pago pelo repouso semanal:
$$\\text{DSR Horas Extras} = \\left( \\frac{\\text{Total de Horas Extras no Mes}}{\\text{Numero de Dias Uteis do Mes}} \\right) \\times \\text{Numero de Domingos e Feriados do Mes} \\times \\text{Valor da Hora Extra}$$
*Nota:* O sabado e considerado dia util para fins de DSR, salvo expressa disposicao em contrario na Convencao Coletiva de Trabalho.

### 5.5 Faltas Injustificadas e Desconto do DSR
- **Desconto do Dia de Falta:**
  $$\\text{Desconto Falta} = \\frac{\\text{Salario Base}}{30} \\times \\text{Dias de Falta}$$
  *(Em meses de 31 ou 28/29 dias, para mensalistas utiliza-se a convencao legal de 30 dias, salvo no mes de admissao/demissao que e apurado pelo numero exato de dias do calendario civil).*
- **Perda do DSR Semanal:** Conforme Artigo 6 da Lei 605/1949, a falta injustificada em qualquer dia da semana acarreta a perda da remuneracao do dia de repouso remunerado (DSR) correspondente a essa semana.
""")

sections.append("""## 6. Algoritmos e Modelagem Matematica de Tributos e Encargos

### 6.1 INSS Empregado (Tabela Progressiva por Faixas Marginais - EC 103/2019)
A Contribuicao Previdenciaria do Segurado Empregado deixou de ser cobrada pela aliquota integral sobre a base total e passou a ser calculada por fatiamento progressivo marginal, identico a logica do Imposto de Renda.

Tabela de Referencia Vigente:
- **Faixa 1:** Ate R$ 1.412,00 (Salario Minimo) -> Aliquota: 7,5%
- **Faixa 2:** De R$ 1.412,01 ate R$ 2.666,68 -> Aliquota: 9,0%
- **Faixa 3:** De R$ 2.666,69 ate R$ 4.000,03 -> Aliquota: 12,0%
- **Faixa 4:** De R$ 4.000,04 ate R$ 7.786,02 (Teto RGPS) -> Aliquota: 14,0%
- **Acima do Teto:** Contribuicao fixada no teto maximo.

Formula de Fatiamento Algoritmico:
```python
def calcular_inss_progressivo(base_inss: Decimal) -> Decimal:
    faixas = [
        (Decimal('1412.00'), Decimal('0.075')),
        (Decimal('2666.68'), Decimal('0.090')),
        (Decimal('4000.03'), Decimal('0.120')),
        (Decimal('7786.02'), Decimal('0.140')),
    ]
    teto = faixas[-1][0]
    base_tributavel = min(base_inss, teto)
    total_inss = Decimal('0.00')
    limite_anterior = Decimal('0.00')

    for limite_faixa, aliquota in faixas:
        if base_tributavel > limite_anterior:
            parcela_tributavel = min(base_tributavel, limite_faixa) - limite_anterior
            total_inss += (parcela_tributavel * aliquota)
            limite_anterior = limite_faixa
        else:
            break

    return total_inss.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

**Regra de Multiplos Vinculos (Art. 36 da IN RFB 2110/2022):**
Quando o empregado possui mais de um emprego, ele deve apresentar o comprovante de recolhimento da primeira fonte pagadora:
1. Se a Empresa 1 ja recolheu sobre o teto do RGPS, a Empresa 2 deve recolher ZERO de INSS segurado.
2. Se a Empresa 1 recolheu sobre base inferior ao teto, a Empresa 2 complementa o calculo utilizando a aliquota marginal correspondente a soma das remuneracoes, sem ultrapassar o teto maximo.

### 6.2 Imposto de Renda Retido na Fonte (IRRF sobre Trabalho Assalariado)
O calculo do IRRF mensal exige uma avaliacao comparativa obrigatoria entre duas modalidades, devendo o motor aplicar compulsoriamente a opcao que resultar em menor imposto (mais benefica ao colaborador).

#### Metodo A: Deducoes Legais Tradicionais
$$\\text{Base IRRF Tradicional} = \\text{Proventos Tributaveis} - \\text{INSS Retido} - (\\text{Qtd Dependentes} \\times R\\$\\ 189{,}59) - \\text{Pensao Judicial} - \\text{Previdencia Privada}$$

#### Metodo B: Desconto Simplificado Mensal
Introduzido pela MP 1.171/2023, Lei 14.663/2023 e atualizacoes: substitui todas as deducoes legais tradicionais por uma deducao fixa padrao (ex: R$ 564,80 a R$ 672,00 conforme vigencia).
$$\\text{Deducao Efetiva} = \\max(\\text{Total Deducoes Legais}, \\text{Desconto Simplificado Parametrizado})$$
$$\\text{Base IRRF Final} = \\max(0, \\text{Proventos Tributaveis} - \\text{Deducao Efetiva})$$

Tabela Progressiva Mensal de IRRF:
- **Faixa 1:** Ate R$ 2.259,20 -> Aliquota: 0,0% | Parcela a Deduzir: R$ 0,00
- **Faixa 2:** De R$ 2.259,21 ate R$ 2.826,65 -> Aliquota: 7,5% | Parcela a Deduzir: R$ 169,44
- **Faixa 3:** De R$ 2.826,66 ate R$ 3.751,05 -> Aliquota: 15,0% | Parcela a Deduzir: R$ 381,44
- **Faixa 4:** De R$ 3.751,06 ate R$ 4.664,68 -> Aliquota: 22,5% | Parcela a Deduzir: R$ 662,77
- **Faixa 5:** Acima de R$ 4.664,68 -> Aliquota: 27,5% | Parcela a Deduzir: R$ 896,00

$$\\text{Valor IRRF} = (\\text{Base IRRF Final} \\times \\text{Aliquota}) - \\text{Parcela a Deduzir}$$
*(Se o valor calculado for inferior a R$ 10,00, a legislacao veda a retencao na fonte, acumulando-se para competencia posterior - Art. 724 do RIR/2018).*

### 6.3 Fundo de Garantia do Tempo de Servico (FGTS)
O FGTS e encargo exclusivo do empregador, nao sendo descontado do trabalhador.
- **Aliquota Padrao CLT:** 8,0% sobre a remuneracao bruta.
- **Aliquota Jovem Aprendiz:** 2,0% sobre a remuneracao bruta.
- **Empregado Domestico:** 8,0% mensal + 3,2% de recolhimento compulsorio antecipado para indenizacao por perda de emprego (recolhido na guia DAE).
- **Prazo de Pagamento (FGTS Digital):** Dia 20 do mes seguinte ao da competencia (Lei 14.438/2022). O pagamento e feito exclusivamente via Pix atraves da GFD gerada pelo sistema de governo integrado ao eSocial.

### 6.4 Encargos Patronais Previdenciarios (Custo Empresa)
Calculados sobre a base de remuneracao bruta dos colaboradores e pro-labore:
1. **Contribuicao Patronal Previdenciaria (CPP):** 20,0% (Aplicavel a empresas do Lucro Real, Lucro Presumido e Simples Nacional Anexo IV).
2. **GILRAT (Grau de Incidencia de Incapacidade Laborativa decorrente dos Riscos Ambientais do Trabalho):**
   $$\\text{Aliquota Efetiva GILRAT} = \\text{Aliquota RAT (1%, 2% ou 3%)} \\times \\text{FAP (0,5 a 2,0)}$$
3. **Outras Entidades e Fundos (Terceiros):** Determinado pelo codigo FPAS. Varia tipicamente de 0,0% a 5,8% (repasses para Salario-Educacao, INCRA, SENAI, SESI, SENAC, SESC, SEBRAE).
4. **Adicional para Financiamento de Aposentadoria Especial (FAE):** Quando o colaborador esta exposto a agentes nocivos a saude (insalubridade grave que permite aposentadoria especial em 15, 20 ou 25 anos), a empresa recolhe adicional de 12%, 9% ou 6% respectivamente sobre a remuneracao daquele colaborador especifico.
""")

sections.append("""## 7. Ciclos Operacionais e Tipos de Folha

### 7.1 Folha de Adiantamento Salarial (Vale Quinzenal)
- Processada normalmente entre os dias 15 e 20 do mes corrente.
- Parametrizacao padrao: 40% do salario base nominal.
- Regra de Exclusao: Nao recebem adiantamento colaboradores admitidos ha menos de 15 dias, em gozo integral de ferias ou em afastamento previdenciario.
- Incidencias: Nao incide INSS nem FGTS no momento do adiantamento. O valor concedido e descontado integralmente na Folha Mensal (Rubrica 5060).

### 7.2 Folha Mensal Efetiva
- Competencia civil fechada (do 1o ao ultimo dia do mes).
- Apuracao do saldo de salario, horas extras, DSR, faltas, beneficios e deducoes.
- Prazo de Pagamento Legal: Ate o 5o dia util do mes subsequente (CLT Art. 459, paragrafo 1o, com o sabado contado compulsoriamente como dia util bancario para essa contagem).

### 7.3 Folha de Ferias
- **Periodos Legais:**
  - Periodo Aquisitivo: 12 meses de vigencia do contrato.
  - Periodo Concessivo: 12 meses subsequentes ao periodo aquisitivo.
- **Tabela de Perda de Dias de Ferias por Faltas Injustificadas (CLT Art. 130):**
  - Ate 5 faltas: 30 dias corridos de ferias.
  - De 6 a 14 faltas: 24 dias corridos de ferias.
  - De 15 a 23 faltas: 18 dias corridos de ferias.
  - De 24 a 32 faltas: 12 dias corridos de ferias.
  - Mais de 32 faltas: Perda total do direito as ferias.
- **Fracionamento (CLT Art. 134, paragrafo 1o):** Permitido em ate 3 periodos, sendo que um deles nao pode ser inferior a 14 dias e nenhum dos outros pode ser inferior a 5 dias.
- **Abono Pecuniario (CLT Art. 143):** Direito potestativo do trabalhador de converter 1/3 do periodo a que tem direito em dinheiro (venda de 10 dias). Deve ser requerido com ate 15 dias de antecedencia do vencimento do periodo aquisitivo.
- **Formula de Calculo:**
  $$\\text{Remuneracao Base das Ferias} = \\text{Salario Base} + \\text{Media das Horas Extras e Variaveis dos Ultimos 12 Meses}$$
  $$\\text{Valor dos Dias de Gozo} = \\left( \\frac{\\text{Remuneracao Base}}{30} \\right) \\times \\text{Dias de Gozo}$$
  $$\\text{Terco Constitucional} = \\frac{\\text{Valor dos Dias de Gozo}}{3}$$
  $$\\text{Abono Pecuniario} = \\left( \\frac{\\text{Remuneracao Base}}{30} \\right) \\times \\text{Dias de Abono}$$
  $$\\text{Terco do Abono} = \\frac{\\text{Abono Pecuniario}}{3}$$
- **Prazo de Pagamento:** Ate 2 dias antes do inicio do gozo das ferias (CLT Art. 145).
- **Penalidade de Ferias Vencidas (CLT Art. 137):** Ferias concedidas ou quitadas apos o periodo concessivo devem ser pagas em dobro.

### 7.4 Folha de 13o Salario (Gratificacao Natalina - Leis 4.090/1962 e 4.749/1965)
- **Fracionamento em Avos:** Cada mes civil com 15 ou mais dias trabalhados confere o direito a 1/12 avo de 13o salario.
- **1a Parcela (Adiantamento):**
  - Prazo legal de pagamento: Entre 1o de fevereiro e 30 de novembro.
  - Valor: 50% do salario do mes anterior + medias de variaveis apuradas ate outubro.
  - Incidencias: Nao sofre retencao de INSS nem de IRRF. Incide exclusivamente o FGTS mensal (8%).
- **2a Parcela (Quitacao Final):**
  - Prazo legal de pagamento: Ate 20 de dezembro.
  - Base de Calculo: Salario de dezembro + medias das variaveis de janeiro a novembro.
  - Desconto da 1a parcela ja paga.
  - Incidencia de INSS e IRRF em separado (Tributacao exclusiva na fonte, com fechamento anual via eSocial evento S-1299 da competencia 13).
- **Folha de Ajuste de 13o Salario (Competencia Janeiro):**
  - Obrigatoria para colaboradores que recebem comissoes ou horas extras em dezembro. As variaveis de dezembro alteram a media anual de 12 meses, gerando diferenca a pagar ou a estornar na folha normal de janeiro.

### 7.5 Folha de Rescisao Contratual (TRCT - Termo de Rescisao do Contrato de Trabalho)
- **Prazo de Pagamento Unico:** Ate 10 dias corridos contados do encerramento do contrato, independentemente da modalidade do aviso previo (CLT Art. 477, paragrafo 6o).
- **Aviso Previo Proporcional (Lei 12.506/2011):**
  - 30 dias para contratos com ate 1 ano de servico.
  - Acrescimo de 3 dias por ano completo de trabalho subsequente, limitado ao teto maximo de 90 dias (atingido com 20 anos completos de empresa).

Matriz de Direitos Rescisorios por Modalidade de Desligamento:

| Modalidade de Desligamento | Saldo Salario | Aviso Previo | 13o Prop. | Ferias Vencidas | Ferias Prop. | Saque FGTS | Multa FGTS |
|---|---|---|---|---|---|---|---|
| **Dispensa sem Justa Causa** | Sim | Sim (Trab/Inden) | Sim | Sim + 1/3 | Sim + 1/3 | Sim (Cod 01) | 40% integral |
| **Dispensa com Justa Causa (Art. 482)** | Sim | Nao | Nao | Sim + 1/3 | Nao | Nao | Nao |
| **Pedido de Demissao pelo Empregado** | Sim | Paga ou Desconta | Sim | Sim + 1/3 | Sim + 1/3 | Nao | Nao |
| **Acordo Mutuo (Art. 484-A CLT)** | Sim | 50% Indenizado | Sim | Sim + 1/3 | Sim + 1/3 | Sim (Ate 80%) | 20% (Metade) |
| **Termino de Contrato de Experiencia** | Sim | Nao cabivel | Sim | Sim + 1/3 | Sim + 1/3 | Sim (Cod 04) | Nao |
| **Quebra Antecipada Experiencia p/ Empregador** | Sim | Nao (Art 479 - 50% restantes) | Sim | Sim + 1/3 | Sim + 1/3 | Sim (Cod 01) | 40% integral |
| **Quebra Antecipada Experiencia p/ Empregado** | Sim | Desconta Art 480 (limite 479) | Sim | Sim + 1/3 | Sim + 1/3 | Nao | Nao |
| **Rescisao Indireta (Art. 483 CLT)** | Sim | Sim (Indenizado) | Sim | Sim + 1/3 | Sim + 1/3 | Sim (Cod 01) | 40% integral |
| **Falecimento do Empregado** | Sim | Nao cabivel | Sim | Sim + 1/3 | Sim + 1/3 | Sim (Dependentes) | Nao |
""")

sections.append("""## 8. Arquitetura de Integracao com o eSocial / SPED

```
+-----------------------------------------------------------------------+
|                            ThPay Engine                               |
|   Motor de Calculo | Orquestrador de Mensageria | Gerador de XML      |
+-----------------------------------+-----------------------------------+
                                    |
            Assinatura Digital ICP-Brasil (A1 / A3 XMLDSig)
                                    |
                                    v
+-----------------------------------------------------------------------+
|                    Ambiente Nacional do eSocial                       |
|           Web Service SOAP / API REST Governamental                   |
+-----------------------------------+-----------------------------------+
                                    |
                 Validacao de Schemas XSD e Regras
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v                                                     v
[Processamento com Erro]                              [Recibo com Sucesso]
Retorna Lista de Ocorrencias                          Retorna Protocolo e
(Codigos e Mensagens)                                 Eventos Totalizadores
                                                      (S-5001, S-5002, S-5003)
                                                               |
                                                               v
                                                      +-----------------+
                                                      |  Conciliacao    |
                                                      |   Centavo a     |
                                                      |    Centavo      |
                                                      +-----------------+
```

### 8.1 Catalogo Completo de Eventos por Grupo

#### Grupo 1: Eventos Iniciais e de Tabelas
- `S-1000`: Informacoes do Empregador / Contribuinte (razao social, enquadramento tributario, desoneracao, contato).
- `S-1005`: Tabela de Estabelecimentos, Obras ou Unidades de Orgaos Publicos (CNAE preponderante, FAP, RAT por filial).
- `S-1010`: Tabela de Rubricas (natureza da rubrica, codigos de incidencia para INSS, FGTS e IRRF).
- `S-1020`: Tabela de Lotacoes Tributarias (vinculacao de estabelecimentos a codigos FPAS e tomadores de servico).
- `S-1070`: Tabela de Processos Administrativos / Judiciais (processos que suspendem a exigibilidade de tributos).

#### Grupo 2: Eventos Nao Periodicos (Ciclo de Vida do Trabalhador)
- `S-2190`: Registro Preliminar de Trabalhador (admissao simplificada para envio antes do primeiro dia de trabalho).
- `S-2200`: Cadastramento Inicial do Vinculo e Admissao / Ingresso (admissao formal completa com dados civis, CTPS e remuneracao).
- `S-2205`: Alteracao de Dados Cadastrais do Trabalhador (mudanca de nome civil, endereco, estado civil).
- `S-2206`: Alteracao de Contrato de Trabalho (reajuste salarial, promocao de cargo, mudanca de jornada).
- `S-2230`: Afastamento Temporario (inicio e termino de licenca-maternidade, afastamento por doenca comum ou acidente de trabalho).
- `S-2231`: Cessao / Exercicio em Outro Orgao.
- `S-2240`: Condicoes Ambientais do Trabalho - Fatores de Risco (LTCAT, EPIs, EPCs e agentes nocivos para aposentadoria especial).
- `S-2298`: Reintegracao de Trabalhador (cumprimento de decisao judicial de retorno ao emprego).
- `S-2299`: Desligamento (rescisao formal do vinculo com envio de todas as verbas rescisorias em ate 10 dias).
- `S-2300`: Trabalhador Sem Vinculo de Emprego - Inicio (cadastro de pro-labore, autonomo, estagiario).
- `S-2306`: TSVE - Alteracao Contratual.
- `S-2399`: TSVE - Termino da Prestacao de Servicos.
- `S-3000`: Exclusao de Eventos (cancelamento de qualquer evento enviado anteriormente).

#### Grupo 3: Eventos Periodicos (Folha de Pagamento Mensal)
- `S-1200`: Remuneracao do Trabalhador vinculado ao RGPS (folha mensal e 13o de cada colaborador com todas as rubricas pagas).
- `S-1202`: Remuneracao do Servidor vinculado ao RPPS.
- `S-1207`: Beneficios Previdenciarios - RPPS.
- `S-1210`: Pagamentos de Rendimentos do Trabalho (Regime de Caixa / data efetiva em que o dinheiro caiu na conta bancaria do trabalhador; base oficial para substituicao definitiva da DIRF).
- `S-1260`: Comercializacao da Producao Rural Pessoa Fisica.
- `S-1270`: Contratacao de Trabalhadores Avulsos Nao Portuarios.
- `S-1280`: Informacoes Complementares aos Eventos Periodicos (informacao sobre CPRB/desoneracao e distribuicao percentual do Anexo IV).
- `S-1298`: Reabertura dos Eventos Periodicos (anula o fechamento anterior para permitir retificacoes).
- `S-1299`: Fechamento dos Eventos Periodicos (consolida a folha, trava a competencia e dispara os totalizadores).

#### Grupo 4: Reclamatoria Trabalhista
- `S-2500`: Processo Trabalhista (declaracao de sentencas judiciais e acordos homologados pelo Judiciario Trabalhista).
- `S-2501`: Informacoes de Contribuicoes Decorrentes de Processo Trabalhista (apuracao de bases e encargos a recolher).
- `S-3500`: Exclusao de Evento de Processo Trabalhista.
- `S-5501`: Totalizador de Tributos de Processo Trabalhista.

#### Grupo 5: Totalizadores de Retorno (Governo -> Sistema)
- `S-5001`: Contribuicoes Sociais por Trabalhador (retorno da apuracao oficial do INSS do segurado).
- `S-5002`: Imposto de Renda Retido na Fonte por Trabalhador (retorno da apuracao oficial do IRRF).
- `S-5003`: Informacoes do FGTS por Trabalhador (retorno da base oficial aceita para envio ao FGTS Digital).
- `S-5011`: Contribuicoes Sociais Consolidadas por Contribuinte (valor final da divida previdenciaria enviada para a DCTFWeb).
- `S-5012`: IRRF Consolidado por Contribuinte (valor total de IRRF sobre a folha enviado para a DCTFWeb).
- `S-5013`: FGTS Consolidado por Contribuinte.

### 8.2 Motor de Conciliacao Automatica de Totalizadores
O ThPay implementa uma trava de seguranca de auditoria: nenhuma guia fiscal pode ser paga sem a execucao do modulo de reconciliacao:
$$\\Delta \\text{INSS} = |\\text{Calculo\\_ThPay(INSS)} - \\text{Totalizador\\_S5011(INSS)}|$$
$$\\Delta \\text{IRRF} = |\\text{Calculo\\_ThPay(IRRF)} - \\text{Totalizador\\_S5012(IRRF)}|$$
$$\\Delta \\text{FGTS} = |\\text{Calculo\\_ThPay(FGTS)} - \\text{Totalizador\\_S5013(FGTS)}|$$
Se qualquer $\\Delta > 0{,}00$, a folha e colocada em estado de divergencia fiscal, gerando apontamento automatico de rubricas com classificacao ou base incorreta.
""")

sections.append("""## 9. Obrigacoes Fiscais, Financeiras e Conectividade Bancaria

### 9.1 DCTFWeb e Geracao do DARF Numerado Unico
- A DCTFWeb (Declaracao de Debitos e Creditos Tributarios Federais Previdenciarios e de Outras Entidades e Fundos) e alimentada automaticamente pelo evento de fechamento S-1299 do eSocial e pela EFD-Reinf.
- **DARF Previdenciario e Fiscal Unico:** Substituiu a antiga GPS (Guia da Previdencia Social) e os antigos DARFs avulsos de IRRF.
- Permite amortizacao automatica de creditos:
  - Compensacao do Salario-Familia e Salario-Maternidade pagos pela empresa aos seus colaboradores diretamente no total a recolher de INSS.
  - Compensacao de retencoes de 11% de cessao de mao de obra e creditos tributarios de PER/DCOMP.
- Vencimento: Dia 20 do mes subsequente ao encerramento da competencia.

### 9.2 FGTS Digital e Guia GFD (Guia do FGTS Digital)
- Operacionalizado em 2024 (Portaria MTE 240/2024).
- O FGTS Digital nao possui digitacao de valores: consome diretamente as bases remuneratorias transmitidas no eSocial (S-1200 e S-2299).
- **Emissao da GFD:**
  - Gerada via integracao com chave Pix instantanea e QR Code dinâmico.
  - Vencimento da guia mensal: Dia 20 do mes seguinte a competencia.
  - Vencimento da guia rescisoria: Ate o 10o dia corrido apos o desligamento.

### 9.3 Contabilidade e Provisoes Mensais
A contabilidade de folha de pagamento exige a aplicacao rigorosa do Principio da Competencia Contabil, independentemente do mes em que o pagamento financeiro ocorra.

#### Provisao de Ferias + Terco Constitucional
A cada mes trabalhado, o colaborador adquire direito a 1/12 avo de ferias:
$$\\text{Provisao Ferias Mensal} = \\frac{\\text{Salario Base} + \\text{Medias de Variaveis}}{12} \\times \\frac{4}{3}$$
$$\\text{Provisao Encargos Ferias} = \\text{Provisao Ferias Mensal} \\times (\\text{\\% CPP} + \\text{\\% RAT} + \\text{\\% Terceiros} + \\text{\\% FGTS})$$

#### Provisao de 13o Salario
$$\\text{Provisao 13o Mensal} = \\frac{\\text{Salario Base} + \\text{Medias de Variaveis}}{12}$$
$$\\text{Provisao Encargos 13o} = \\text{Provisao 13o Mensal} \\times (\\text{\\% CPP} + \\text{\\% RAT} + \\text{\\% Terceiros} + \\text{\\% FGTS})$$

#### Partidas Dobradas Contabeis
- **Debito:** Despesas com Salarios e Ordenados (Conta de Resultado / DRE).
- **Debito:** Despesas com Encargos Sociais Previdenciarios (Conta de Resultado / DRE).
- **Debito:** Despesas com FGTS (Conta de Resultado / DRE).
- **Credito:** Salarios a Pagar (Passivo Circulante).
- **Credito:** INSS a Recolher / DARF Previdenciario a Pagar (Passivo Circulante).
- **Credito:** IRRF a Recolher (Passivo Circulante).
- **Credito:** FGTS a Recolher (Passivo Circulante).

### 9.4 Integracao Bancaria (Layouts FEBRABAN CNAB 240 e CNAB 400)
Para liquidacao financeira automatizada da folha de pagamento, adiantamentos e pensoes alimenticias:
- Suporte nativo ao layout padrao **FEBRABAN CNAB 240** (Segmentos A, B, C e J).
- **Segmento A:** Transferencia bancaria direta (TED, TEF no mesmo banco) e liquidacao via Pix (Chave Pix CPF, email, telefone ou chave aleatoria).
- **Segmento B:** Dados complementares do favorecido (validacao de CPF, endereco, aviso de credito).
- Geracao do arquivo `.REM` de remessa para transmissao ao Internet Banking.
- Ingestao do arquivo `.RET` de retorno bancario para conciliacao automatica com confirmacao de pagamento ou estorno por inconsistencia de dados de conta bancaria.
""")

sections.append("""## 10. Seguranca, LGPD, Trilha de Auditoria e Version Lock

### 10.1 Conformidade Estrita com a LGPD (Lei 13.709/2018)
Folha de pagamento armazena os dados mais criticos e intimos de uma organizacao. O ThPay implementa protecoes de ponta a ponta:
- **Dados Pessoais Sensíveis:**
  - Atestados medicos (CID-10) vinculados a afastamentos temporarios possuem acesso restrito estritamente a Medicina do Trabalho / SST.
  - Dados biometricos de ponto eletrônico criptografados com chave assimetrica.
  - Dados de desconto de pensao alimenticia e consignados com mascaramento visual em relatorios publicos de gerencia.
- **Criptografia em Repouso:** Banco de dados e colunas criticas protegidos por AES-256 (colunas de CPF, dados bancarios, dados de dependentes).
- **Criptografia em Transito:** TLS 1.3 compulsorio para todas as comunicacoes de API e Web Services.

### 10.2 Trilha de Auditoria Imutavel (Audit Trail)
Toda e qualquer operacao no sistema gera um registro de auditoria append-only (somente insercao):
- Timestamp UTC em padrao ISO 8601 com precisao de milissegundos.
- Identificador unico do usuario / ator (User ID, IP de origem, User-Agent).
- Entidade alvo e chave primaria.
- Estado anterior (`diff_before`) e estado posterior (`diff_after`) em formato JSON estruturado.
- Justificativa operacional obrigatoria para alteracoes retroativas de ponto, cadastros salariais ou reaberturas de folha.

### 10.3 Controle de Acesso Baseado em Funcoes (RBAC Granular)
- `DEPARTAMENTO_PESSOAL_OPERADOR`: Digitacao de ponto, calculo de folha, emissao de holerites.
- `DEPARTAMENTO_PESSOAL_GESTOR`: Aprovacao de fechamento, geracao de guias de tributos, autorizacao de adiantamento.
- `DIRETORIA_FINANCEIRA`: Aprovacao de arquivo de remessa bancaria e fechamento de fluxo de caixa.
- `AUDITORIA_INTERNA_COMPLIANCE`: Acesso somente-leitura (Read-Only) a historicos, logs e conciliacoes.
- `COLABORADOR_SELF_SERVICE`: Acesso restrito e exclusivo aos proprios holerites, informes de rendimentos e solicitacao de ferias.
""")

sections.append("""## 11. Matriz de Casos Extremos (Edge Cases) e Resolucao Operacional

| Caso Extremo | Regra Trabalhista / Previdenciaria Aplicavel | Comportamento Exigido do ThPay Engine |
|---|---|---|
| **Multiplos Vinculos do Empregado** | O teto maximo do RGPS se aplica a soma de todos os vinculos do trabalhador (IN RFB 2110/2022 Art. 36). | O motor recebe os rendimentos da fonte externa, calcula a diferenca marginal permitida e bloqueia descontos superiores ao teto. |
| **Afastamento Previdenciario Cruzando Mes** | Primeiros 15 dias de atestado sao pagos pela empresa; a partir do 16o dia o contrato fica suspenso e o INSS assume o beneficio (B31/B91). | O motor fatia automaticamente a remuneracao: calcula os dias trabalhados + dias de atestado (ate 15) como salario e zera o calculo a partir do 16o dia. |
| **Salario-Maternidade Pago pela Empresa** | A empresa paga o salario integral a colaboradora gestante, mas compensa 100% desse valor na guia da DCTFWeb (Lei 8.213/1991 Art. 72). | O provento e lancado na rubrica 1080 (incide INSS/FGTS) e o valor e automaticamente enviado como credito redutor na DCTFWeb. |
| **Estorno / Cancelamento de Rescisao** | Desligamento cancelado por reintegracao judicial ou erro administrativo antes da homologacao. | Exclusao do evento S-2299 via evento S-3000 no eSocial, restauracao do status ativo do vinculo e reprocessamento da folha normal. |
| **Dissidio Coletivo com Reajuste Retroativo** | Convencao assinada meses apos a data-base com efeito retroativo gerando diferencas salariais em competencias fechadas. | O motor gera uma Folha Complementar por competencia retroativa, apura diferencas de proventos e encargos sem juros moratorios (codigos 650/660). |
| **Rescisao Complementar por Dissidio Retroativo** | Colaborador ja desligado em mes anterior ao fechamento da Convencao Coletiva com data-base anterior ao seu desligamento. | O motor reabre a TRCT em modulo de diferenca rescisoria, calcula reflexos sobre verbas rescisorias e aviso previo indenizado e gera nova guia rescisoria. |
| **Salario Liquido Negativo** | Descontos de faltas, beneficios ou emprestimos superam o montante de proventos do colaborador no mes. | O sistema impede geracao de holerite com saldo devedor: aplica a rubrica automatica de Insuficiencia de Saldo para zerar o liquido e migra o debito para o mes seguinte. |
| **Estagiarios (Lei 11.788/2008)** | Bolsa-estagio nao tem natureza salarial; isenta de INSS empregado/patronal e FGTS. Tributavel exclusivamente para IRRF caso supere faixa de isencao. | Contrato categoria 901 e vinculado a regras especiais: isencao total de encargos sociais, bloqueio de descontos de VT de 6% (estagiario recebe auxilio transporte integral) e sem 13o legal (apenas bolsa). |
| **Trabalhador Intermitente (Art. 452-A CLT)** | Convocado formalmente 72h antes. Ao final de cada periodo de prestacao recebe imediatamente salario, ferias prop + 1/3, 13o prop e DSR. | Apuracao modular por convocacao fechada, geracao de recibo com demonstrativo individualizado de cada parcela proporcional e consolidacao no S-1200 mensal. |
""")

sections.append("""## 12. Arquitetura de Software e Roadmap Tecnico do ThPay Engine

### 12.1 Camadas do Sistema (Domain-Driven Architecture)
- **`thpay.domain`**: Entidades puras de negocio (Empresa, Colaborador, Contrato, Rubrica, Competencia, Holerite).
- **`thpay.dag`**: Motor de execucao de Grafo Aciclico Dirigido com ordenacao topologica, validacao de ciclos e injecao de contexto.
- **`thpay.tax`**: Calculadores de tributos isolados e versionados no tempo (Tabelas INSS 2024/2025/2026, Tabelas IRRF Progressivo vs Simplificado, FGTS, RAT/FAP).
- **`thpay.pipeline`**: Processadores especializados para cada modalidade (Mensal, Adiantamento, Ferias, 13o Salario, Rescisao TRCT, Complementar).
- **`thpay.esocial`**: Geradores de XML canonicos, validadores de schemas XSD oficiais, assinador digital XMLDSig e cliente de comunicacao Web Service.
- **`thpay.banking`**: Gerador e parser de layouts FEBRABAN CNAB 240 e CNAB 400.
- **`thpay.audit`**: Sistema de hash SHA-256 e trilha de auditoria bitemporal.

### 12.2 Fases do Master Plan de Implementacao

```
Fase 1: Foundation, Dominio & Motor DAG
├── Modelos tipados Pydantic/dataclasses (Colaborador, Rubrica, Base, Holerite)
├── Motor de Grafo Aciclico Dirigido (DAG Calculation Engine)
└── Resolucao de dependencias e ordenacao topologica

Fase 2: Motor Tributario & Encargos (Tax Engine)
├── INSS Progressivo por fatiamento marginal com regras de multiplos vinculos
├── IRRF Progressivo com comparacao automatica para Desconto Simplificado
├── FGTS Mensal (8% e 2%) e Rescisorio
└── Encargos Patronais (CPP 20%, RAT x FAP, Terceiros/FPAS e CPRB)

Fase 3: Pipelines Operacionais de Folha
├── Pipeline de Folha Mensal Efetiva
├── Pipeline de Adiantamento Salarial (Vale)
├── Pipeline de Ferias (Gozadas, Abono Pecuniario, Terco Constitucional e Medias)
├── Pipeline de 13o Salario (1a parcela, 2a parcela e ajuste de janeiro)
└── Pipeline de Rescisao Contratual TRCT (Todas as 9 modalidades CLT)

Fase 4: eSocial & Compliance Integrado
├── Geracao de XMLs para eventos de Tabelas (S-1000, S-1005, S-1010, S-1020)
├── Geracao de XMLs Nao Periodicos (S-2200, S-2206, S-2230, S-2299)
├── Geracao de XMLs Periodicos (S-1200, S-1210, S-1298, S-1299)
└── Modulo de Reconciliacao Automatica de Totalizadores (S-5001, S-5002, S-5003)

Fase 5: Conectividade Financeira & Bancaria
├── Emissao de guias DCTFWeb e suporte a guias FGTS Digital (Pix GFD)
├── Integrador bancario FEBRABAN CNAB 240 (Segmentos A, B e Pix)
└── Fechamento contabil com partidas dobradas e provisoes de ferias/13o
```

---
*ThPay - Engineered for absolute precision, zero tolerance to fiscal discrepancies and complete operational integrity.*
""")


sections.append("""## 13. Arquitetura Poliglota de Referencia e Decisoes Tecnologicas

Para atender simultaneamente a requisitos de determinismo matematico absoluto, vazao massiva em lote, integracao com certificados brasileiros, usabilidade em tempo real e analise estatistica avancada, o ThPay rejeita o monolitismo monolingue e adota uma **Arquitetura Poliglota Especializada**.

```
+-----------------------------------------------------------------------------------------+
|                  CAMADA 1: FRONTEND & EXPERIENCIA DO USUARIO (TypeScript)               |
| Stack: Next.js 15 | React 19 | Tailwind CSS | Radix UI                                  |
| Escopo: Portal do DP, Espelho de Ponto, Central de Admissao e Autoatendimento           |
+--------------------------------------------+--------------------------------------------+
                                             |
                      +----------------------+----------------------+
                      | (API REST / OpenAPI / gRPC)                 | (Execucao Local Wasm)
                      v                                             v
+--------------------------------------------+  +-----------------------------------------+
|    CAMADA 2: MOTOR CORE & ESOCIAL (Java)   |  |   CAMADA 3: SIMULADOR DE BORDA (Rust)   |
| Stack: Java 21 LTS | Virtual Threads (Loom)|  | Stack: Rust | WebAssembly (Wasm)        |
| Framework: Spring Boot 3 ou Quarkus        |  | Escopo: Pre-visualizacao de rescisao,   |
| Escopo: Motor DAG, BigDecimal, XMLDSig     |  | simulador de ferias e horas extras no   |
| ICP-Brasil A1/A3, CNAB 240/400, eSocial WS |  | navegador sem latencia de rede.         |
+---------------------+----------------------+  +-----------------------------------------+
                      |
        (Fechamentos e Eventos Gravados)
                      v
+-----------------------------------------------------------------------------------------+
|               CAMADA 4: ANALYTICS, AUDITORIA & MIGRACAO DE DADOS (Python)               |
| Stack: Python 3.12+ | Polars | DuckDB | FastAPI                                         |
| Escopo: Relatorio de Transparencia Salarial (Lei 14.611/2023), deteccao de anomalias   |
| em ponto, auditorias de passivo trabalhista e ingestao de bases legadas.                |
+-----------------------------------------------------------------------------------------+
```

### 13.1 Detalhamento das Decisoes Tecnologicas

#### 1. Core de Calculo e Mensageria eSocial: Java 21 LTS
- **Motivacao Central:** O processamento de folha em lote para 10.000 a 50.000 colaboradores exige precisao de ponto fixo e concorrencia massiva com isolamento.
- **Diferenciais Tecnicos:**
  - `java.math.BigDecimal` com `RoundingMode.HALF_UP`: Padrao industrial inegociavel para calculo financeiro e tributario.
  - **Virtual Threads (Projeto Loom):** Cada colaborador e processado em sua propria thread virtual (`newVirtualThreadPerTaskExecutor`), saturando o hardware com uso minimo de memoria e sem os limites do GIL do Python.
  - **Criptografia ICP-Brasil e XMLDSig:** A arquitetura JCA/JCE do Java e a API `javax.xml.crypto.dsig` oferecem suporte nativo e estavel para certificados A1 (PKCS#12) e tokens A3 (PKCS#11), eliminando a dependencia de bibliotecas C instaveis (`libxmlsec`).
  - **Ecossistema Brasileiro:** Disponibilidade de bibliotecas consolidadas como Caelum Stella (validacao de CPF/CNPJ/PIS) e motores maduros para geracao de arquivos bancarios FEBRABAN CNAB 240 e 400.

#### 2. Portal do DP e Experiencia do Colaborador: TypeScript (Next.js 15)
- **Motivacao Central:** Interfaces de Departamento Pessoal sao ricas em dados, exigindo formularios complexos de admissao, visao em grade de espelhos de ponto e renderizacao instantanea de holerites.
- **Diferenciais Tecnicos:**
  - Contratos de dados tipados gerados automaticamente a partir da definicao OpenAPI do backend Java.
  - React Server Components (RSC) para carregar dashboards analiticos pesados diretamente do servidor sem penalizar o bundle do cliente.
  - Acessibilidade e design system corporativo padronizado via Tailwind CSS.

#### 3. Simulador de Borda e Pre-Visualizacao: Rust (WebAssembly)
- **Motivacao Central:** O operador do DP precisa saber imediatamente qual sera o impacto de um aumento de salario, de 10 horas extras ou de uma rescisao antes de submeter o lote oficial ao backend.
- **Diferenciais Tecnicos:**
  - O motor de formulas compilado em Rust para WebAssembly roda diretamente na aba do navegador do cliente.
  - Tempo de resposta sub-milissegundo (< 1 ms), sem trafego de rede e sem sobrecarregar os servidores principais com simulacoes descartaveis.
  - Seguranca estrita de memoria e ausencia de runtime garbage-collected.

#### 4. Analytics, Compliance de Equidade e ETL: Python 3.12+ (Polars)
- **Motivacao Central:** O setor de DP e Recursos Humanos lida com volumosos conjuntos de dados historicos e obrigacoes analiticas recentes.
- **Diferenciais Tecnicos:**
  - **Lei 14.611/2023 (Igualdade e Transparencia Salarial):** Exige analise estatistica de medianas salariais por genero, raca e CBO. O ecossistema Python com Polars processa milhoes de registros em milissegundos com sintaxe vetorizada expressiva.
  - **Deteccao de Anomalias:** Algoritmos de Machine Learning para identificar desvios de lancamentos de horas extras e inconsistencias antes do fechamento.
  - **Migracao e Carga Inicial:** Scripts ageis para converter dumps de sistemas legados (TOTVS, Senior, Folhamatic, Excel) em modelos canonicos do ThPay.

#### 5. Infraestrutura de Mensageria e Persistencia
- **Fila Assincrona:** RabbitMQ ou Redis Streams para orquestrar a esteira de eventos do eSocial, garantindo entrega garantida (*at-least-once*), controle de taxa de transmissao governamental (*rate limiting*) e reprocessamento com *dead-letter queues*.
- **Banco de Dados Relacional:** PostgreSQL 16+ com particionamento de tabelas por competencia civil (`competence_year_month`), garantindo consultas bitemporais ultra-rapidas e integridade referencial estrita.
""")

with open('/root/ThPay/SPECIFICATION.md', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(sections))

print("SPECIFICATION.md gerado com sucesso!")

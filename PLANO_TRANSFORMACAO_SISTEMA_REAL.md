# ThPay // Especificação Técnica de Transformação em Sistema Real
> Plano Mestre de Engenharia, Arquitetura e Eliminação de Cenografia (Anti-Mock)

---

## 1. Manifesto Anti-Cenografia: Princípios Inegociáveis

Para que o ThPay deixe de ser um protótipo de vitrine e se torne uma plataforma corporativa legítima de processamento de folha de pagamento, qualquer elemento com finalidade puramente ilustrativa deve ser sumariamente erradicado. 

1. **Banimento de Dados em Memória:** O arquivo `dataset_400.js` será deletado. Nenhum número, colaborador ou rubrica existirá no frontend sem ter sido persistido em banco de dados relacional e trafegado via API RESTful tipada.
2. **Separação Rígida de Portais (Fim da "Alternância de Visão"):** É terminantemente proibido existir um botão no cabeçalho permitindo alternar entre "Painel DP" e "Visão do Colaborador". Administradores operam no Portal do DP; colaboradores operam no Portal Self-Service. O isolamento é imposto por credenciais, sessão HTTP-only e autorização RBAC no servidor.
3. **Erradicação do Login Fictício:** A tela de login não conterá atalhos de "1 clique para acessar como Maria Silva". Todo acesso exigirá credenciais reais (e-mail corporativo e senha criptografada), com validação contra a tabela de usuários, rate limiting contra força bruta e bloqueio de conta.
4. **Mutação e Persistência Efetivas:** Nenhum botão existirá para apenas fechar um modal ou disparar um toast estático. Clicar em "Homologar", "Salvar Benefício", "Ajustar Ponto" ou "Editar Admissão" obrigatoriamente executa uma transação atômica no banco de dados, gera log de auditoria imutável e reflete o novo estado na interface.
5. **Realidade das Exceções Trabalhistas:** A folha não será um cenário ideal onde todos os colaboradores estão ativos e corretos. O sistema deve suportar a matéria escura do departamento pessoal: afastamentos por INSS, pensões alimentícias judiciais, faltas injustificadas, perda de DSR, múltiplos sindicatos e inconsistências cadastrais que bloqueiam o fechamento.

---

## 2. Arquitetura de Identidade, Autenticação e RBAC Estrito

### 2.1 Separação Física dos Portais por Rota e Perfil
O sistema passa a operar em duas fronteiras de aplicação totalmente segregadas:

```
[Domínio Raiz]
  ├── /auth/login                 -> Tela de autenticação unificada corporativa
  ├── /auth/recuperar-senha       -> Fluxo seguro com token expirábil de 15 minutos
  │
  ├── /app/* (Portal do DP e Gestão) [Guard: RBAC >= DP_OPERADOR]
  │     ├── /app/dashboard        -> Visão executiva consolidada da competência
  │     ├── /app/folha            -> Diretório operacional e Raio-X de holerites
  │     ├── /app/fechamento       -> Motor de validação e checklist de homologação
  │     ├── /app/admissoes        -> Gestão e validação de lotes em massa
  │     ├── /app/esocial          -> Mensageria governamental e guias DCTFWeb/FGTS
  │     └── /app/configuracoes    -> Gestão de empresas, lotações e permissões
  │
  └── /portal/* (Portal do Colaborador) [Guard: RBAC == COLABORADOR_SELF_SERVICE]
        ├── /portal/meu-holerite  -> Histórico de recibos de pagamento assinados
        ├── /portal/beneficios    -> Gestão de split de benefícios dentro das regras
        ├── /portal/chamados      -> Abertura e timeline de chamados ao DP
        └── /portal/informes      -> Comprovantes de rendimentos anuais para IRPF
```

### 2.2 Mecanismo de Autenticação Segura
- **Armazenamento de Senhas:** Substituição de validações mock por hash criptográfico seguro (Argon2id ou Bcrypt com custo 12).
- **Gerenciamento de Sessão:** Tokens opacos armazenados em cookies `HttpOnly`, `Secure` e `SameSite=Strict`. Fim do armazenamento de tokens sensíveis desprotegidos no `localStorage`.
- **Tratamento de Violação de Escopo:** Se um colaborador autenticado tentar acessar `/app/dashboard`, o backend responde `HTTP 403 Forbidden` e a camada de middleware do frontend redireciona para `/portal/meu-holerite` com alerta de acesso não autorizado registrado na trilha de auditoria.

---

## 3. Reengenharia do Frontend (Adoção de Next.js 15 e React 19)

O arquivo monolítico `ui/index.html` (4.876 linhas) será decomposto e substituído por uma arquitetura moderna baseada em componentes funcionais tipados.

### 3.1 Stack Tecnológica Mandatória do Frontend
- **Framework:** Next.js 15 (App Router) com React 19.
- **Linguagem:** TypeScript em modo estrito (`"strict": true`, proibição de `any`).
- **Estilização:** Tailwind CSS v4 compilado via PostCSS (eliminação definitiva do script CDN).
- **Tabelas de Dados:** TanStack Table v8 (React Table) para controle de alta densidade.
- **Gerenciamento de Cache e Servidor:** TanStack Query v5 (React Query) com invalidação automática de cache pós-mutação.
- **Formulários e Esquemas:** React Hook Form integrado a Zod para validação em tempo real.
- **Componentes Base:** Radix UI Primitives (acessibilidade nativa WAI-ARIA, foco por teclado).

### 3.2 Roteamento, Deep Linking e Estado da URL
Toda ação relevante deve refletir na barra de endereço do navegador:
- `/app/folha?competencia=2026-09&status=PENDENTE&page=2&sort=earnings&dir=desc`
- `/app/folha/MAT-0042` (abre a gaveta de Raio-X do colaborador diretamente; permite envio de link direto entre analistas do DP).
- O botão Voltar do navegador (`Alt + Seta Esquerda`) fecha a gaveta ou retorna à página anterior respeitando o histórico nativo da History API.

### 3.3 Tabelas de Alta Densidade (Padrão ERP Corporativo)
A tabela de colaboradores deve ser reconstruída com ergonomia operacional profissional:
- **Cabeçalhos Interativos:** Clique único para ordenação ascendente/descendente com setas indicativas (`↑` / `↓`).
- **Seleção em Massa:** Checkbox mestre no cabeçalho para selecionar todos os colaboradores da página ou todos os 400 da base, abrindo barra flutuante de ações em lote (*Homologar Selecionados*, *Exportar CNAB 240*, *Emitir Recibos em PDF*).
- **Densidade Alternável:** Seletor de visualização *Compacta* (linhas de 32px para análise massiva) ou *Confortável* (linhas de 48px).
- **Colunas Congeladas:** Primeira coluna com Nome e Matrícula fixada horizontalmente em caso de scroll horizontal com telas menores.

### 3.4 Formulários, Máscaras e Validação Rígida
- **Máscaras de Entrada Obrigatórias:**
  - CPF: `000.000.000-00` com validação matemática dos dígitos verificadores (Módulo 11) antes de permitir envio.
  - CNPJ: `00.000.000/0000-00`.
  - Valores Monetários: `R$ 0,00` formatados durante a digitação com cursor mantido à direita.
  - Datas: `DD/MM/AAAA` com validação de competência e limite etário.
- **UX de Erro em Linha:** Inputs inválidos ganham borda semântica vermelha imediata, ícone de alerta e mensagem contextual inferior associada via `aria-describedby`.
- **Prevenção de Perda de Dados (Dirty Form Guard):** Se o operador alterar dados cadastrais ou valores e tentar trocar de aba ou fechar a página, um diálogo de bloqueio nativo impede o abandono acidental.

### 3.5 Micro-Física e Estados Reais de Interface
- **Skeletons de Carregamento:** Durante as requisições à API, a tabela e os cartões exibem blocos pulsantes proporcionais ao layout final (`animate-pulse`), eliminando o salto abrupto de tela e a impressão de dados embutidos.
- **Error Boundaries:** Erros de renderização são capturados por barreiras locais com botão de "Tentar Novamente", sem derrubar o restante da plataforma.
- **Atalhos de Teclado Operacionais:**
  - `j` e `k` (ou setas para cima/baixo): transição de foco entre colaboradores na tabela.
  - `Enter`: abre o Raio-X do colaborador selecionado.
  - `Esc`: fecha gavetas ou modais ativos.
  - `Ctrl + K`: abre a paleta global de comandos com busca indexada no servidor.

---

## 4. Persistência, Banco Relacional e Paginação Server-Side

### 4.1 Migração Definitiva para Banco de Dados
A base de 400 colaboradores deve ser migrada integralmente para as tabelas relacionais em SQLite/PostgreSQL através de um script de seed idêntico ao ambiente produtivo:
- Tabela `companies`: Tech Solutions Brasil Ltda.
- Tabela `employees`: Dados civis, CPF validado, PIS/PASEP, data de nascimento.
- Tabela `contracts`: Vínculo (CLT ou PJ), CBO, cargo, departamento, centro de custo, salário base, data de admissão.
- Tabela `compensation_items`: Rubricas atribuídas a cada contrato na competência ativa.
- Tabela `payroll_runs`: Registro oficial de processamento de folha por mês/ano.

### 4.2 Endpoints RESTful Reais da API
Todas as telas do frontend consumirão exclusivamente as seguintes rotas:

| Método | Endpoint | Finalidade Operacional |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Autenticação corporativa com entrega de cookie de sessão |
| `POST` | `/api/v1/auth/logout` | Revogação ativa da sessão no banco de dados |
| `GET` | `/api/v1/auth/me` | Retorno do usuário autenticado e escopo de permissões |
| `GET` | `/api/v1/payroll/{competencia}/summary` | Indicadores consolidados calculados pelo banco (custo total, encargos, impostos) |
| `GET` | `/api/v1/payroll/{competencia}/employees` | Listagem paginada server-side com filtros dinâmicos de SQL (`limit`, `offset`, `search`, `sort`) |
| `GET` | `/api/v1/payroll/{competencia}/employees/{id}/payslip` | Cálculo sob demanda do motor DAG retornando rubricas, bases fiscais e hash SHA-256 |
| `POST` | `/api/v1/payroll/{competencia}/calculate` | Recálculo de toda a base ou de contratos específicos com dirty flags |
| `POST` | `/api/v1/payroll/{competencia}/lock` | Fechamento e homologação transacional com trava de edição |
| `GET` | `/api/v1/payroll/{competencia}/checklist` | Execução do motor de regras de pré-fechamento e diagnóstico de divergências |
| `POST` | `/api/v1/admissions/batches` | Criação e processamento de lote de admissões via upload de planilha |
| `GET` | `/api/v1/audit-trail` | Consulta paginada dos logs de auditoria imutáveis |

---

## 5. Regras de Negócio Reais do Departamento Pessoal Brasileiro

A folha de pagamento deixará de ser um cenário linear e passará a processar as regras estritas da legislação trabalhista:

### 5.1 O Motor de Pré-Fechamento e Checklist de Homologação
Em vez de uma "Barra de Prontidão 98,2%" estática, a prontidão será o resultado percentual de um checklist de regras de auditoria executadas no backend:
1. **Auditoria de Ponto:** Verificação de divergências de horas e marcações ímpares no espelho de ponto eletrônico (Portaria 671/2021 do MTE).
2. **Auditoria de Afastamentos:** Identificação de colaboradores afastados por motivo médico (CID) com contagem do 16º dia para transferência do ônus ao INSS (benefício por incapacidade temporária).
3. **Auditoria Cadastral eSocial:** Verificação de preenchimento obrigatório de campos exigidos pelo leiaute v1.3 dos eventos S-2200/S-2190 (endereço completo, CBO regular, dados de dependentes válidos).
4. **Auditoria Tributária de IRRF:** Aplicação algorítmica real comparando as deduções legais tradicionais (dependentes e INSS) contra o Desconto Simplificado Mensal (Art. 67-E da Lei 14.663/2023), adotando a rota matematicamente mais benéfica por colaborador.
5. **Auditoria de Pensão Alimentícia:** Desconto mandatório em folha originado de ofício judicial cadastrado no contrato.

Se houver 3 inconsistências impeditivas, o botão "Concluir Homologação" permanecerá desabilitado no frontend, exibindo a lista das 3 pendências com links diretos para resolução imediata.

---

## 6. Eliminação ou Conexão Efetiva dos Recursos Cenográficos

### 6.1 Módulo do Analista de Inteligência Artificial
- **Estado Atual:** 4 condicionais `if (text.includes(...))` estáticas com `setTimeout(500)`.
- **Destino:** 
  - Remoção temporária da interface até que seja acoplado a um serviço real de backend que processe as tabelas analíticas da competência (consultando dados reais via SQL de agregação ou motor RAG local).

### 6.2 Guias Governamentais e Pix DCTFWeb / FGTS Digital
- **Estado Atual:** Payload Pix estático e código copia e cola fixo cravado no HTML.
- **Destino:**
  - Gerador real de payload EMV Pix padrão Banco Central do Brasil em Python (`thpay/tax/pix.py`), calculando os valores reais de FGTS Digital (8% sobre base real da competência) e DARF Previdenciário consolidado da empresa, gerando QR Code SVG autêntico.

### 6.3 Simulador de Cenários Trabalhistas
- **Estado Atual:** Código JavaScript simplificado no navegador fingindo ser um simulador em Rust/Wasm.
- **Destino:**
  - Conexão do simulador diretamente ao motor de cálculo em Python (`thpay/engine/` e `thpay/tax/`), permitindo que a interface envie os parâmetros (`tipo_rescisao`, `aviso_previo`, `dias_trabalhados`) e receba o resultado matemático exato com reflexos de 13º proporcional, férias proporcionais com 1/3 e multa rescisória do FGTS pela CLT.

---

## 7. Trilha de Execução e Fases de Implementação

```
FASE 1: FUNDAÇÃO E PURIFICAÇÃO (Banco e Autenticação)
  ├── 1.1 Ingestão e Seed dos 400 colaboradores no banco relacional SQLite
  ├── 1.2 Criação da tabela de usuários, credenciais hash e perfis RBAC
  ├── 1.3 Eliminação dos botões de 1 clique e implementação de login real com cookies HttpOnly
  └── 1.4 Testes de integração de autenticação e proteção de rotas

FASE 2: RECONSTRUÇÃO DO FRONTEND (Next.js 15 + TanStack)
  ├── 2.1 Setup de projeto Next.js 15 com TypeScript, Tailwind CSS e Radix UI
  ├── 2.2 Criação do layout do Portal do DP (/app/*) e Portal do Colaborador (/portal/*)
  ├── 2.3 Implementação de TanStack Table v8 com ordenação, filtros e paginação server-side
  └── 2.4 Criação da gaveta de Raio-X do holerite conectada ao endpoint REST com deep linking

FASE 3: HOMOLOGAÇÃO, REGRAS TRABALHISTAS E AUDITORIA
  ├── 3.1 Construção do motor de checklist real de pré-fechamento (regras de ponto e impostos)
  ├── 3.2 Transação de bloqueio de folha (LOCKED) com auditoria na tabela audit_logs
  ├── 3.3 Formulários blindados com React Hook Form, Zod e máscaras de CPF/Moeda
  └── 3.4 Gerador dinâmico de Pix padrão Banco Central para guias DARF e FGTS Digital

FASE 4: VALIDAÇÃO DE CONFORMIDADE E HOMOLOGAÇÃO
  ├── 4.1 Testes E2E com Playwright cobrindo login de analista, navegação na folha e fechamento
  ├── 4.2 Testes E2E cobrindo acesso restrito de colaborador ao portal self-service
  └── 4.3 Auditoria de integridade centavo a centavo entre cálculo da API e exibição na UI
```

---

*Documento aprovado para execução imediata. Nenhum código de demonstração ou artifício visual de vitrine será tolerado a partir desta diretriz.*

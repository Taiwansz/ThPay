# ThPay — Próximos Passos para se tornar um sistema completo

> Documento operacional de implementação. Este arquivo deve ser tratado como backlog mestre do produto e como guia de execução para agentes/IA que forem evoluir o repositório. Não é apenas uma lista de ideias: cada seção descreve o que precisa existir de verdade para o ThPay deixar de ser uma especificação + motor de cálculo + protótipo visual e se tornar uma aplicação corporativa utilizável em produção.

## 0. Objetivo deste documento

O ThPay já possui uma boa especificação funcional, um motor inicial de folha em Python, regras de INSS/IRRF/FGTS, pipeline mensal, testes unitários e uma interface visual avançada. Porém, ainda faltam as camadas fundamentais de um sistema real: autenticação, usuários, banco de dados, APIs, persistência, permissões, workflows, admissão, integrações, eSocial real, documentos, auditoria, infraestrutura, observabilidade, CI/CD e vários ciclos de folha.

A prioridade agora não deve ser acrescentar novas telas isoladas. A prioridade deve ser transformar a experiência demonstrativa atual em um produto persistente, multiusuário, auditável, seguro, versionado e integrável.

### Convenção de status

- `IMPLEMENTADO`: existe código funcional no repositório atual.
- `PARCIAL`: existe parte do domínio, UI ou regra, mas não é suficiente para produção.
- `A IMPLEMENTAR`: ainda não existe de forma funcional.
- `CRÍTICO`: bloqueia o uso real do sistema.

---

# 1. Estado atual resumido

## 1.1 O que existe hoje

- `IMPLEMENTADO`: motor DAG de cálculo com ordenação topológica e detecção de ciclos.
- `IMPLEMENTADO`: entidades Python básicas de empresa, colaborador, contrato, dependentes, pensão e holerite.
- `IMPLEMENTADO`: pipeline mensal com salário, horas extras, DSR, adicional noturno, faltas, insalubridade, periculosidade, INSS, IRRF, FGTS, VT, benefícios, consignado e pensão.
- `IMPLEMENTADO`: hash SHA-256 do holerite calculado.
- `IMPLEMENTADO`: testes unitários básicos para DAG, INSS, IRRF e pipeline mensal.
- `PARCIAL`: frontend visual com painel de DP, portal do colaborador, benefícios, chamados, leaderboard, simulador, eSocial e demais áreas.
- `PARCIAL`: identidade visual oficial aplicada ao frontend.

## 1.2 O que ainda é apenas demonstração

- Dados de colaboradores estão escritos dentro do JavaScript da interface.
- Benefícios alteram somente variáveis em memória.
- Chamados existem somente em arrays do navegador.
- Anexos não são enviados para storage real.
- Hash de anexo demonstrativo não é SHA-256 real.
- Copiloto de IA possui respostas mockadas.
- eSocial/FGTS/Pix são demonstrativos visuais.
- Não existe autenticação real.
- Não existe autorização real.
- Não existe banco de dados.
- Não existe backend/API de aplicação.
- Não existe persistência de alterações.
- Não existe multiempresa real.
- Não existe processamento assíncrono.
- Não existe infraestrutura de produção.

---

# 2. Arquitetura alvo recomendada

Evitar iniciar simultaneamente uma arquitetura poliglota excessivamente distribuída. O repositório atual já possui um motor útil em Python; portanto, a recomendação inicial é:

1. Manter o domínio e motor de cálculo em Python.
2. Criar um backend de aplicação em Python com API HTTP bem estruturada.
3. Utilizar PostgreSQL como banco transacional principal.
4. Migrar o frontend estático para Next.js + TypeScript.
5. Utilizar object storage para documentos e anexos.
6. Introduzir fila/worker para cálculos em lote, importações, relatórios, eSocial e integrações.
7. Só introduzir Java/Rust como serviços separados quando métricas reais mostrarem necessidade.

### Estrutura sugerida do monorepo

```text
ThPay/
├── apps/
│   ├── web/                 # Next.js / TypeScript
│   ├── api/                 # API de aplicação
│   └── worker/              # jobs assíncronos
├── packages/
│   ├── payroll-engine/      # motor atual Python reorganizado
│   ├── domain/              # entidades e regras comuns
│   └── contracts/           # OpenAPI/schemas/eventos
├── migrations/
├── infra/
├── docs/
├── tests/
├── scripts/
└── PROXIMOS_PASSOS.md
```

Essa reorganização pode ser gradual. Não quebrar o motor atual apenas para adequar a estrutura.

---

# 3. PRIORIDADE P0 — Fundação obrigatória do sistema

## 3.1 Autenticação e identidade — CRÍTICO

Implementar:

- Login com e-mail/identificador corporativo + senha ou provedor SSO.
- Logout.
- Sessões server-side ou tokens seguros com rotação/revogação.
- Recuperação de senha.
- Primeiro acesso.
- Alteração de senha.
- Convite de usuários.
- Ativação/inativação de conta.
- Expiração de sessão.
- MFA para perfis privilegiados.
- Histórico de login.
- Bloqueio/rate limit após tentativas suspeitas.
- Vinculação entre usuário e colaborador.
- Vinculação entre usuário e empresa/tenant.
- Controle de dispositivos/sessões quando aplicável.

### Regra inegociável

O usuário não pode escolher manualmente entre “Painel DP” e “Portal do Colaborador” sem autorização. A identidade autenticada determina quais contextos podem ser acessados.

## 3.2 RBAC e autorização — CRÍTICO

Perfis iniciais:

- `SUPER_ADMIN_THAY`/plataforma, se existir operação SaaS.
- `EMPRESA_ADMIN`.
- `DP_OPERADOR`.
- `DP_GESTOR`.
- `RH_OPERADOR`.
- `GESTOR_DE_PESSOAS`.
- `FINANCEIRO_OPERADOR`.
- `FINANCEIRO_APROVADOR`.
- `AUDITOR_COMPLIANCE`.
- `SST_MEDICINA`.
- `COLABORADOR_SELF_SERVICE`.
- `SUPORTE_SERVICE_DESK`.

Permissões devem ser granulares, por exemplo:

```text
employee.read
employee.create
employee.update
employee.import
employee.terminate
payroll.read
payroll.calculate
payroll.recalculate
payroll.approve
payroll.close
payroll.reopen
benefit.read
benefit.manage
esocial.generate
esocial.transmit
banking.generate
banking.approve
audit.read
settings.manage
```

Nunca confiar apenas em esconder botões no frontend. Toda regra de autorização deve ser validada no backend.

## 3.3 Banco de dados e persistência — CRÍTICO

Implementar PostgreSQL com:

- migrations versionadas;
- chaves estrangeiras;
- constraints;
- índices;
- timestamps UTC;
- UUIDs ou IDs opacos;
- soft-delete apenas onde fizer sentido;
- transações;
- locking/idempotência em operações críticas;
- histórico/versionamento de entidades sensíveis;
- suporte a bitemporalidade onde exigido;
- backups automáticos;
- restore testado.

## 3.4 API de aplicação — CRÍTICO

Criar API autenticada para todo o sistema. Não permitir que o frontend manipule diretamente a lógica de folha ou grave dados localmente.

A API deve possuir:

- OpenAPI;
- validação de schema;
- versionamento;
- paginação;
- filtros;
- ordenação;
- idempotency-key para operações críticas;
- correlation-id;
- respostas padronizadas de erro;
- auditoria automática.

---

# 4. PRIORIDADE P0/P1 — Módulo completo de Admissão & Onboarding

## 4.1 Objetivo

Criar um módulo específico chamado **Admissão & Onboarding**. Ele deve suportar desde uma única contratação até grandes lotes, por exemplo: “50 pessoas começam na próxima segunda-feira”.

O módulo não pode depender de cadastrar manualmente pessoa por pessoa. Ele deve permitir:

- admissão unitária;
- admissão em massa via `.xlsx`;
- admissão em massa via `.csv`;
- importação por API;
- clonagem de perfil de contratação;
- aplicação de templates de cargo/filial/benefícios;
- pré-admissão;
- coleta posterior de documentos pelo próprio futuro colaborador;
- validação em lote;
- geração de pendências;
- envio ao eSocial no momento adequado;
- acompanhamento da turma de admissão.

## 4.2 Conceito de “Turma/Lote de Admissão”

Criar a entidade `AdmissionBatch`.

Exemplo:

```text
Lote: ADM-2026-10-05-ENG
Nome: Admissões Engenharia - 05/10/2026
Data prevista de início: 05/10/2026
Empresa: Tech Solutions Brasil Ltda
Filial: São Paulo
Quantidade esperada: 50
Responsável: Maria / RH
Status: Em preparação
```

Cada lote deve mostrar:

- total previsto;
- total importado;
- válidos;
- com alerta;
- com erro bloqueante;
- documentos pendentes;
- exames pendentes;
- prontos para S-2190;
- prontos para S-2200;
- enviados;
- rejeitados pelo eSocial;
- admitidos;
- cancelados.

## 4.3 Fluxo ideal de admissão

```text
CRIAR LOTE
  ↓
ESCOLHER TEMPLATE DE ADMISSÃO
  ↓
IMPORTAR PLANILHA / CADASTRAR MANUALMENTE / API
  ↓
MAPEAR COLUNAS
  ↓
NORMALIZAR DADOS
  ↓
VALIDAR LINHA A LINHA
  ↓
DETECTAR DUPLICIDADES
  ↓
APLICAR REGRAS/TEMPLATES
  ↓
GERAR PENDÊNCIAS
  ↓
REVISÃO DO RH/DP
  ↓
PRÉ-ADMISSÃO
  ↓
COLETA DE DOCUMENTOS/DADOS FALTANTES
  ↓
EVENTO PRELIMINAR S-2190 QUANDO APLICÁVEL
  ↓
COMPLETAR CADASTRO
  ↓
VALIDAÇÃO FINAL
  ↓
S-2200
  ↓
CRIAR VÍNCULO ATIVO
  ↓
LIBERAR PORTAL DO COLABORADOR
  ↓
GERAR TAREFAS DE ONBOARDING
```

## 4.4 Importação de planilha — requisito central

Criar um **Import Wizard** com etapas claras.

### Etapa 1 — Upload

Aceitar:

- XLSX;
- CSV UTF-8;
- templates oficiais baixados do ThPay.

Configurar limites seguros de tamanho e quantidade de linhas.

### Etapa 2 — Detecção de cabeçalho

O sistema deve ler a primeira linha e tentar reconhecer automaticamente nomes equivalentes.

Exemplos:

```text
Nome
Nome Completo
Colaborador
Nome do Funcionário
```

Todos podem mapear para `employee.full_name`.

### Etapa 3 — Mapeamento de colunas

Interface do tipo:

```text
COLUNA DA PLANILHA        →      CAMPO THPAY
Nome Completo             →      Nome completo
CPF                       →      CPF
CEP                       →      CEP
Salário                    →      Salário base
Cargo                      →      Cargo
Departamento               →      Departamento
Data Admissão              →      Data de admissão
```

O usuário deve poder:

- corrigir automaticamente o mapeamento sugerido;
- ignorar colunas;
- definir valor padrão para colunas ausentes;
- salvar esse mapeamento como template.

### Etapa 4 — Perfil/Template de admissão

Permitir definir valores globais para todo o lote:

- empresa;
- filial;
- sindicato;
- centro de custo;
- departamento;
- jornada;
- tipo de contrato;
- regime;
- benefícios padrão;
- plano de saúde padrão;
- política VA/VR;
- gestor;
- data de admissão;
- período de experiência;
- categoria eSocial.

Valores da planilha podem sobrescrever o template quando permitido.

### Etapa 5 — Preview antes de gravar

Mostrar grade com as linhas e estados:

- verde: válida;
- amarelo: alerta;
- vermelho: bloqueante;
- cinza: ignorada.

Nunca inserir imediatamente tudo no banco após upload.

### Etapa 6 — Validação

Executar validações em lote.

### Etapa 7 — Correção

Permitir corrigir células diretamente na tabela do importador sem precisar voltar ao Excel.

### Etapa 8 — Confirmação e processamento

Processar em job assíncrono e gerar relatório final.

## 4.5 Template oficial de planilha

Disponibilizar template baixável com abas:

```text
1. COLABORADORES
2. DICIONARIO_DE_CAMPOS
3. VALORES_ACEITOS
4. EXEMPLO_PREENCHIDO
```

O template deve ter versão:

```text
thpay_admissoes_v1.0.xlsx
```

O importador deve registrar qual versão foi usada.

## 4.6 Campos de admissão — Pessoa

### Identificação principal

- nome completo;
- nome social, quando informado/aplicável;
- CPF;
- data de nascimento;
- país de nascimento;
- nacionalidade;
- município/UF de nascimento quando requerido;
- sexo cadastral quando exigido pelo processo legal/integracional;
- estado civil quando necessário ao cadastro empresarial;
- raça/cor quando exigida por obrigação legal/estatística e observando finalidade/LGPD;
- grau de instrução;
- nome da mãe quando necessário ao fluxo/documentação;
- nome do pai quando aplicável.

### Contato

- e-mail pessoal;
- e-mail corporativo, quando já criado;
- celular;
- telefone alternativo.

### Endereço

- CEP;
- logradouro;
- número;
- complemento;
- bairro;
- município;
- UF;
- país.

Ao informar CEP, preencher automaticamente endereço por serviço confiável, mas permitir correção.

## 4.7 Documentos pessoais

Modelar documentos como entidades flexíveis, não como 50 colunas fixas no colaborador.

Possíveis documentos:

- CPF;
- RG/documento de identidade;
- órgão emissor;
- UF de emissão;
- data de emissão;
- PIS/NIS/NIT quando aplicável ao processo;
- CTPS digital/dados necessários ao vínculo;
- título de eleitor, se a política/necessidade operacional exigir;
- certificado de reservista, quando aplicável;
- CNH, somente quando necessária ao cargo/processo ou voluntariamente cadastrada;
- registro profissional (CREA, OAB, CRM etc.), se aplicável ao cargo;
- RNE/CRNM/passaporte e documentação migratória para estrangeiros quando aplicável.

### Regra importante

Não transformar documentos que não são universalmente necessários em campos obrigatórios globais. A obrigatoriedade deve ser configurável conforme empresa, categoria, cargo, legislação e integração.

### Tipo sanguíneo

Não solicitar por padrão para admissão administrativa. Só adicionar se existir finalidade legítima clara, política de SST aplicável e base legal adequada. O produto deve seguir minimização de dados.

## 4.8 Dados contratuais

- matrícula;
- data de admissão;
- empresa;
- estabelecimento/filial;
- lotação tributária;
- departamento;
- centro de custo;
- cargo;
- CBO;
- função;
- gestor;
- categoria eSocial;
- natureza do vínculo;
- tipo de contrato;
- contrato por prazo indeterminado/determinado;
- data final prevista, quando aplicável;
- experiência inicial;
- prorrogação de experiência;
- jornada semanal;
- divisor mensal;
- escala;
- horário;
- modalidade presencial/híbrido/remoto;
- local de trabalho;
- sindicato/CCT aplicável;
- salário base;
- periodicidade salarial;
- remuneração variável/comissão quando aplicável;
- elegibilidade a adicionais;
- data-base.

## 4.9 Dados financeiros

- salário;
- banco;
- agência;
- conta;
- tipo de conta;
- chave Pix, quando utilizada;
- titularidade;
- CPF do titular;
- política de pagamento;
- adiantamento salarial: sim/não;
- percentual de adiantamento, quando configurável.

Dados bancários devem ser criptografados em repouso e possuir acesso restrito.

## 4.10 Benefícios na admissão

Aplicar automaticamente benefícios por regras.

Exemplo:

```text
Se empresa = X
E filial = SP
E categoria = CLT
Então:
- orçamento alimentação = R$ 1.400
- split padrão = 50/50
- VT = perguntar necessidade
- saúde = plano padrão empresarial
- odontológico = opcional
```

Campos possíveis:

- VA;
- VR;
- orçamento total;
- split inicial;
- VT necessário?;
- custo estimado VT;
- endereço/trajeto quando necessário;
- plano de saúde;
- dependentes do plano;
- odontológico;
- seguro de vida;
- auxílio home office;
- outros benefícios configuráveis.

## 4.11 Dependentes

A importação deve suportar dependentes em estrutura separada.

Opções:

- segunda aba `DEPENDENTES`;
- vínculo via CPF do titular;
- upload posterior pelo portal.

Campos:

- nome;
- CPF quando aplicável;
- nascimento;
- parentesco;
- dependente IRRF;
- dependente salário-família;
- dependente plano saúde;
- dependente odontológico;
- documentação comprobatória;
- vigência.

## 4.12 Documentos e anexos de admissão

Criar checklist configurável por empresa/cargo.

Exemplos:

- documento de identidade;
- comprovante de residência;
- dados bancários;
- certificado escolar;
- registro profissional;
- documentos dos dependentes;
- termo de VT;
- termo de benefícios;
- contrato de trabalho;
- termo de confidencialidade;
- política interna;
- documentos de SST quando aplicáveis.

Cada documento deve possuir:

- tipo;
- arquivo;
- versão;
- hash SHA-256 real;
- uploader;
- data/hora;
- status de validação;
- validade quando aplicável;
- permissões;
- histórico.

## 4.13 Autoatendimento do pré-admitido

Criar link seguro temporário de onboarding.

Fluxo:

1. RH cria/importa candidato aprovado.
2. ThPay envia convite.
3. Pessoa acessa portal de pré-admissão.
4. Confirma dados básicos.
5. Completa campos faltantes.
6. Faz upload de documentos.
7. Informa dependentes.
8. Informa dados bancários.
9. Escolhe benefícios permitidos.
10. Aceita/assina termos.
11. RH recebe status em tempo real.

O pré-admitido não deve possuir acesso ao portal de colaborador completo antes da ativação do vínculo.

## 4.14 Validações de importação

### Sintáticas

- CPF com formato/dígitos válidos;
- CEP válido;
- datas válidas;
- e-mail válido;
- números monetários;
- enumerações conhecidas;
- CBO em formato válido;
- categoria eSocial válida;
- UF válida.

### Semânticas

- CPF já existente;
- vínculo duplicado;
- matrícula duplicada;
- salário abaixo de piso configurado;
- cargo sem CBO;
- filial inexistente;
- centro de custo inexistente;
- data final antes da admissão;
- menor aprendiz fora de regras configuradas;
- jornada incompatível;
- benefício não disponível para filial/categoria;
- banco obrigatório ausente na etapa final;
- campos condicionais ausentes.

### Regulatórias

As regras de eSocial devem ser baseadas na versão vigente do leiaute, não hardcoded sem versionamento.

## 4.15 Mapeamento inteligente de valores

Além de mapear colunas, mapear valores.

Exemplo:

```text
Planilha: "Eng Software Sr"
ThPay: Cargo 182 — Engenheiro de Software Sênior
CBO: 2124-05
```

Outro exemplo:

```text
Planilha: "SP-Centro"
ThPay: Estabelecimento 0002
```

Permitir salvar dicionários de equivalência por empresa.

## 4.16 Detecção de duplicidade e idempotência

Nunca criar 50 pessoas duplicadas porque o usuário reenviou a planilha.

Criar fingerprint da linha/importação considerando campos seguros como:

- tenant;
- CPF;
- data admissão;
- empresa;
- vínculo/matrícula.

Estados possíveis:

- novo;
- já importado;
- atualização possível;
- conflito;
- duplicado exato.

## 4.17 Relatório de erros da importação

Após validar/processar, permitir baixar:

```text
resultado_admissoes_2026-10-05.xlsx
```

Colunas adicionais:

```text
THPAY_STATUS
THPAY_ERRO_CODIGO
THPAY_ERRO_DESCRICAO
THPAY_CAMPO
THPAY_ACAO_SUGERIDA
```

## 4.18 Estados da admissão

Sugestão de state machine:

```text
DRAFT
IMPORTED
VALIDATING
HAS_ERRORS
READY_FOR_REVIEW
PRE_ADMISSION
AWAITING_DOCUMENTS
READY_FOR_ESOCIAL_PRELIMINARY
S2190_SENT
S2190_ACCEPTED
READY_FOR_FULL_ADMISSION
S2200_SENT
S2200_ACCEPTED
ACTIVE
CANCELLED
REJECTED
```

Transições devem ser auditáveis.

## 4.19 Integração eSocial na admissão

O módulo deve suportar a lógica de eventos vigente do eSocial.

### S-2190 — Registro Preliminar

- tratar como fluxo opcional quando aplicável;
- armazenar protocolo/recibo;
- controlar prazo;
- exigir complementação posterior;
- bloquear estado inconsistente.

### S-2200 — Admissão completa

- gerar evento a partir do cadastro consolidado;
- validar XSD/regras antes do envio;
- assinar quando necessário;
- transmitir;
- guardar payload enviado;
- guardar retorno;
- guardar recibo;
- exibir erros humanizados;
- permitir correção e reenvio;
- relacionar evento ao vínculo.

### Regra arquitetural

Manter adaptador de versão do eSocial:

```text
esocial/v1_3/...
esocial/future_version/...
```

Nunca espalhar campos específicos do leiaute por toda a aplicação.

## 4.20 API sugerida do módulo de admissão

```text
POST   /admission-batches
GET    /admission-batches
GET    /admission-batches/{id}
POST   /admission-batches/{id}/files
POST   /admission-batches/{id}/map-columns
POST   /admission-batches/{id}/validate
POST   /admission-batches/{id}/commit
GET    /admission-batches/{id}/rows
PATCH  /admission-batches/{id}/rows/{rowId}
POST   /admissions
GET    /admissions/{id}
PATCH  /admissions/{id}
POST   /admissions/{id}/documents
POST   /admissions/{id}/invite
POST   /admissions/{id}/submit-s2190
POST   /admissions/{id}/submit-s2200
POST   /admissions/{id}/activate
POST   /admissions/{id}/cancel
```

## 4.21 Modelo de dados sugerido

Entidades mínimas:

```text
AdmissionBatch
AdmissionImportFile
AdmissionColumnMapping
AdmissionRow
Admission
AdmissionValidationIssue
AdmissionDocumentRequirement
AdmissionDocument
AdmissionTask
AdmissionInvite
AdmissionBenefitSelection
AdmissionESocialEvent
Employee
EmploymentContract
EmployeeDocument
EmployeeAddress
EmployeeBankAccount
EmployeeDependent
```

## 4.22 Dashboard de admissões

Criar tela para RH/DP com:

- admissões esta semana;
- próximas admissões;
- lotes em andamento;
- pessoas com dados faltantes;
- documentos pendentes;
- eSocial pendente;
- rejeições;
- admissões concluídas;
- SLA médio;
- busca por nome/CPF/lote.

## 4.23 Operações em massa

Permitir selecionar várias pessoas para:

- aplicar filial;
- aplicar departamento;
- aplicar cargo/CBO;
- aplicar centro de custo;
- aplicar gestor;
- aplicar benefícios;
- alterar data de admissão;
- enviar convite;
- solicitar documento;
- validar novamente;
- enviar S-2190;
- enviar S-2200 quando permitido.

Toda ação em massa deve mostrar preview e pedir confirmação.

## 4.24 Templates de contratação

Criar entidade `AdmissionTemplate`.

Exemplo:

```text
Template: Engenheiro Software CLT — SP
Empresa: Tech Solutions Brasil
Filial: São Paulo
Departamento: Engenharia
Centro custo: ENG-001
Jornada: 40h
Contrato: indeterminado + 45/45 experiência
Categoria: 101
Benefícios: pacote Tech SP
Sindicato: Sindicato X
```

Assim um lote de 50 pessoas pode precisar apenas de:

```text
Nome | CPF | Data Nascimento | Email | CEP | Numero | Salario | Cargo
```

O restante vem do template.

## 4.25 Checklist de conclusão da admissão

Uma admissão só fica `ACTIVE` após passar por checklist configurável, por exemplo:

- identidade validada;
- contrato definido;
- salário definido;
- cargo/CBO definidos;
- lotação definida;
- jornada definida;
- endereço mínimo completo;
- dados bancários completos quando necessários;
- benefícios configurados;
- documentos obrigatórios validados;
- eSocial aceito;
- usuário do portal provisionado;
- aceite/assinatura de documentos quando aplicável.

## 4.26 Testes obrigatórios da admissão

Criar testes para:

- 1 admissão unitária válida;
- 50 admissões em XLSX;
- 5.000 admissões em lote;
- CPF inválido;
- CPF duplicado;
- planilha sem cabeçalho reconhecido;
- coluna com nome diferente;
- salário com vírgula brasileira;
- data Excel serializada;
- CSV com separador `;`;
- encoding incorreto;
- filial inexistente;
- CBO inexistente;
- dependentes;
- campos condicionais;
- reupload do mesmo arquivo;
- job interrompido e retomado;
- S-2190 aceito/rejeitado;
- S-2200 aceito/rejeitado;
- cancelamento antes da admissão;
- usuário sem permissão tentando importar.

## 4.27 Definition of Done do módulo

O módulo só pode ser considerado concluído quando for possível executar este cenário sem editar banco/código manualmente:

> RH cria um lote com 50 admissões para a próxima semana, baixa o template, preenche dados variáveis, sobe XLSX, mapeia colunas, corrige 3 erros dentro do sistema, aplica template de contratação aos 50, envia convites para documentos faltantes, acompanha pendências, transmite os eventos necessários ao eSocial, recebe os retornos, ativa os vínculos e os 50 colaboradores passam a conseguir acessar o portal individual no primeiro dia de trabalho.

---

# 5. Cadastro estrutural de empresa e organização

## 5.1 Multiempresa / multi-tenant

Implementar:

- tenant;
- empregador;
- matriz;
- filiais/estabelecimentos;
- CNPJ/CNO/CAEPF;
- lotações tributárias;
- departamentos;
- centros de custo;
- equipes;
- cargos;
- CBO;
- gestores;
- localidades;
- calendários;
- sindicatos;
- CCT/ACT;
- políticas.

Todo registro de negócio deve possuir escopo de tenant/empresa quando aplicável.

## 5.2 Cargos e posições

Separar:

- cargo;
- função;
- posição/vaga;
- CBO;
- faixa salarial;
- nível/senioridade;
- departamento;
- centro de custo;
- gestor.

Isso facilita admissão e histórico organizacional.

---

# 6. Cadastro completo do colaborador

Transformar `Employee` em um agregado real com subentidades.

Implementar:

- dados pessoais;
- documentos;
- endereços;
- contatos;
- dependentes;
- dados bancários;
- contratos;
- histórico salarial;
- histórico de cargo;
- histórico de lotação;
- benefícios;
- afastamentos;
- férias;
- anexos;
- eventos eSocial;
- solicitações;
- auditoria.

Nunca sobrescrever histórico relevante.

---

# 7. Contrato de trabalho e bitemporalidade

Cada alteração contratual importante deve possuir:

- vigência jurídica (`valid_from`, `valid_to`);
- momento de registro (`recorded_at`);
- autor;
- justificativa;
- versão.

Exemplos:

- alteração salarial;
- promoção;
- mudança de cargo;
- transferência;
- mudança de estabelecimento;
- mudança de jornada;
- mudança de sindicato;
- alteração contratual retroativa.

Uma consulta histórica deve ser capaz de responder:

> Qual era o contrato vigente em maio conforme o conhecimento disponível naquele momento?

---

# 8. Parametrização fiscal versionada

Remover constantes tributárias hardcoded como fonte definitiva.

Criar tabelas versionadas para:

- salário mínimo;
- INSS;
- IRRF;
- dedução por dependente;
- desconto simplificado;
- salário família;
- FGTS;
- RAT/FAP;
- terceiros;
- parâmetros anuais;
- limites legais.

Cada versão deve ter:

```text
valid_from
valid_to
published_at
source
version
```

O motor deve receber parâmetros da competência.

---

# 9. Motor de rubricas configurável

Hoje existe catálogo Python fixo. Evoluir para:

- rubrica por tenant;
- código;
- descrição;
- natureza eSocial;
- incidência INSS;
- incidência FGTS;
- incidência IRRF;
- tipo;
- fórmula;
- dependências;
- vigência;
- versão;
- CCT aplicável;
- categoria aplicável;
- limites;
- arredondamento;
- prioridade.

Alterações de rubrica nunca devem modificar retroativamente o cálculo já fechado sem processo formal.

---

# 10. Motor de folha em escala

Evoluir `process_monthly_payroll` para processamento por competência/lote.

Implementar:

- cálculo de um vínculo;
- cálculo de seleção;
- cálculo de empresa inteira;
- snapshot de parâmetros;
- idempotência;
- recalculo seletivo;
- cálculo incremental;
- versionamento do resultado;
- comparação entre versões;
- diff de folha;
- freeze/lock;
- hash de competência inteira;
- histórico de execuções;
- fila assíncrona;
- progresso em tempo real.

---

# 11. Workflows de competência e fechamento

Criar `PayrollPeriod`.

Estados sugeridos:

```text
OPEN
COLLECTING_INPUTS
READY_TO_CALCULATE
CALCULATING
CALCULATED
HAS_BLOCKERS
UNDER_REVIEW
APPROVED
READY_FOR_ESOCIAL
ESOCIAL_SENT
RECONCILED
READY_FOR_PAYMENT
CLOSED
REOPENED
CANCELLED
```

Definir transições e permissões.

---

# 12. Tipos de folha faltantes

Implementar pipelines próprios para:

## 12.1 Adiantamento

- percentual por empresa/colaborador;
- elegibilidade;
- competência;
- desconto posterior.

## 12.2 Férias

- período aquisitivo;
- período concessivo;
- programação;
- fracionamento;
- abono;
- 1/3;
- médias;
- antecipação de 13º;
- recibo;
- incidências.

## 12.3 13º salário

- primeira parcela;
- segunda parcela;
- médias;
- proporcionalidade;
- afastamentos;
- admissão/demissão;
- ajuste.

## 12.4 Rescisão

- modalidades;
- aviso prévio;
- saldo salário;
- férias vencidas/proporcionais;
- 13º;
- médias;
- indenizações;
- estabilidade;
- FGTS/multa;
- TRCT;
- prazos;
- eventos eSocial.

## 12.5 Folha complementar

- dissídio;
- retroativos;
- diferenças;
- competência de origem;
- encargos.

## 12.6 Folha retificadora

- reabertura formal;
- diff;
- justificativa;
- auditoria;
- novo fechamento.

---

# 13. Jornada, ponto e variáveis

Hoje o motor recebe horas prontas. Criar módulo de ponto capaz de:

- importar batidas;
- integrar relógio/sistema externo;
- jornadas;
- escalas;
- 12x36;
- banco de horas;
- tolerâncias;
- HE 50/60/70/100 etc.;
- adicional noturno;
- faltas;
- atrasos;
- abonos;
- feriados nacionais/estaduais/municipais;
- aprovação por gestor;
- fechamento do ponto;
- envio de variáveis para folha.

---

# 14. CCT, ACT e sindicatos

Criar módulo para:

- sindicato laboral;
- patronal;
- vigência;
- data-base;
- pisos por cargo/CBO;
- adicionais convencionais;
- HE convencionais;
- benefícios;
- estabilidade;
- auxílio creche;
- regras específicas;
- anexos da convenção;
- versionamento.

O motor deve conseguir determinar a regra aplicável por vínculo e competência.

---

# 15. Benefícios corporativos

Evoluir o frontend demonstrativo para domínio real.

Criar:

- catálogo de benefícios;
- fornecedores;
- planos;
- elegibilidade;
- valores colaborador/empresa;
- faixas;
- dependentes;
- janela de adesão;
- carência;
- vigência;
- mudança futura;
- aprovação;
- integração com folha;
- integração com fornecedores quando disponível.

### VA/VR

- orçamento total;
- presets permitidos;
- granularidade;
- data limite;
- competência de vigência;
- histórico.

### VT

- necessidade;
- trajeto;
- custo;
- limite legal configurável;
- termo de adesão/renúncia;
- vigência;
- histórico.

### Saúde/Odonto

- plano;
- dependentes;
- coparticipação;
- mensalidade;
- adesão;
- cancelamento;
- vigência;
- documentos.

---

# 16. Portal do colaborador real

Após autenticação, cada colaborador só pode acessar seus próprios dados.

Módulos:

- início/resumo;
- dados pessoais;
- holerites;
- informe de rendimentos;
- benefícios;
- férias;
- solicitações;
- chamados;
- documentos;
- dependentes;
- dados bancários conforme política;
- leaderboard, quando habilitado;
- notificações;
- histórico de alterações.

Ações sensíveis precisam de confirmação e auditoria.

---

# 17. Service Desk

Transformar tickets do JavaScript em sistema real.

Implementar:

- ticket persistente;
- protocolo;
- categoria;
- subcategoria;
- fila;
- responsável;
- prioridade;
- SLA;
- status;
- mensagens;
- comentários internos;
- anexos;
- histórico;
- notificações;
- escalonamento;
- pesquisa;
- métricas;
- satisfação.

---

# 18. Documentos e storage

Utilizar object storage privado.

Implementar:

- upload seguro;
- signed URLs;
- antivírus/malware scan;
- MIME validation;
- tamanho máximo;
- hash SHA-256 real;
- metadata;
- ACL;
- retenção;
- versionamento;
- auditoria;
- deleção conforme política legal;
- criptografia.

---

# 19. eSocial real

Criar módulo `esocial` separado do domínio principal.

Implementar progressivamente:

### Eventos de tabela

- S-1000;
- S-1005;
- S-1010;
- S-1020;
- outros necessários.

### Admissão e alterações

- S-2190;
- S-2200;
- S-2205;
- S-2206.

### Não periódicos

- afastamentos;
- CAT/SST conforme escopo;
- desligamento;
- demais eventos necessários.

### Periódicos

- S-1200;
- S-1210;
- S-1298;
- S-1299.

### Retornos/totalizadores

- S-5001;
- S-5002;
- S-5003;
- S-5011;
- S-5012;
- S-5013;
- demais aplicáveis.

Infra necessária:

- schema XSD versionado;
- XML generator;
- validação local;
- assinatura;
- certificados;
- transmissão;
- receipt/protocol;
- retry;
- fila;
- rejeição humanizada;
- retificação;
- exclusão quando aplicável;
- histórico imutável.

---

# 20. Reconciliação fiscal

Comparar cálculo interno com retornos oficiais.

Criar painel de divergências:

```text
INSS ThPay      x INSS oficial
IRRF ThPay      x IRRF oficial
FGTS ThPay      x FGTS oficial
```

Se diferença exceder tolerância permitida, bloquear avanço para pagamento/fechamento e indicar trabalhador/rubrica responsável.

---

# 21. DCTFWeb e FGTS Digital

Implementar somente conforme interfaces oficialmente disponíveis e arquitetura permitida.

O sistema deve, no mínimo:

- acompanhar obrigações;
- consolidar débitos;
- registrar guias/documentos;
- armazenar vencimentos;
- relacionar pagamentos;
- registrar evidências;
- reconciliar valores;
- alertar divergências;
- evitar telas que simulem integração inexistente.

---

# 22. Pagamento de folha e bancos

Implementar:

- conta bancária por colaborador;
- validação;
- lote de pagamento;
- aprovação financeira;
- segregação de função;
- CNAB 240 conforme bancos suportados;
- remessa;
- retorno;
- conciliação;
- rejeição;
- reprocessamento;
- histórico;
- Pix quando aplicável ao fluxo suportado.

---

# 23. Contabilidade

Criar:

- plano de contas;
- conta por evento/rubrica;
- centro de custo;
- filial;
- rateio;
- provisão férias;
- provisão 13º;
- encargos;
- integração/exportação ERP;
- lote contábil;
- conciliação;
- histórico.

---

# 24. Relatórios

Implementar geração real de:

- holerite PDF;
- folha analítica;
- folha sintética;
- ficha financeira;
- líquido bancário;
- encargos;
- provisões;
- relatório de benefícios;
- alterações salariais;
- admissões;
- desligamentos;
- férias;
- divergências;
- auditoria;
- centro de custo;
- informe de rendimentos;
- export CSV/XLSX/PDF.

Jobs pesados devem ser assíncronos.

---

# 25. Administração e parametrização

Criar área administrativa para evitar alteração de código.

Configurações:

- empresa;
- filiais;
- usuários;
- perfis;
- centros de custo;
- cargos;
- CBO;
- sindicatos;
- CCT;
- tabelas fiscais;
- rubricas;
- benefícios;
- bancos;
- calendários;
- feriados;
- SLAs;
- templates de admissão;
- templates de documentos;
- certificados;
- integrações;
- feature flags.

---

# 26. Notificações

Criar serviço de notificação com:

- in-app;
- e-mail;
- templates;
- preferências;
- fila;
- tentativas;
- status de entrega.

Eventos exemplo:

- convite de pré-admissão;
- documento pendente;
- admissão concluída;
- holerite publicado;
- chamado respondido;
- benefício alterado;
- férias aprovadas;
- folha com erro;
- eSocial rejeitado;
- competência fechada.

---

# 27. Copiloto de IA

O atual mock deve ser substituído somente após existir autorização e dados reais.

Requisitos:

- respeitar RBAC;
- limitar dados por tenant;
- limitar dados por colaborador;
- mascarar PII quando possível;
- logs/auditoria;
- fontes/citações internas;
- não inventar valores;
- não executar alteração salarial, admissão, desligamento ou fechamento sem ação explícita/autorizada;
- tool calls auditáveis;
- confirmação humana para ações críticas.

---

# 28. Segurança

Implementar baseline OWASP:

- TLS;
- secure cookies;
- CSRF;
- CSP;
- CORS restritivo;
- rate limiting;
- validação server-side;
- proteção IDOR;
- headers de segurança;
- secret manager;
- rotação de credenciais;
- criptografia de campos sensíveis;
- sanitização;
- scanner de dependências;
- upload seguro;
- logs de segurança;
- MFA;
- política de sessão.

---

# 29. LGPD e privacidade

Criar inventário de dados pessoais e sensíveis.

Para cada campo registrar:

- finalidade;
- base legal;
- obrigatoriedade;
- quem acessa;
- retenção;
- descarte;
- origem;
- compartilhamentos.

Aplicar minimização. Não coletar dado apenas “porque outros sistemas coletam”.

Criar controles para:

- exportação;
- correção;
- anonimização quando cabível;
- retenção;
- descarte;
- logs de acesso a dado sensível.

---

# 30. Audit Trail append-only

Toda operação crítica deve gerar evento de auditoria.

Campos mínimos:

```text
id
occurred_at
actor_user_id
actor_role
ip
user_agent
tenant_id
action
entity_type
entity_id
before_json
after_json
reason
correlation_id
```

Exemplos auditados:

- alteração salarial;
- admissão;
- cancelamento de admissão;
- mudança de benefício;
- fechamento;
- reabertura;
- envio eSocial;
- alteração bancária;
- upload/remoção de documento;
- mudança de permissão.

---

# 31. Jobs e processamento assíncrono

Criar worker/queue para:

- importações;
- folha em massa;
- relatórios;
- eSocial;
- e-mails;
- documentos;
- integrações bancárias;
- exportações.

Cada job deve possuir:

- id;
- tipo;
- status;
- progresso;
- payload mínimo;
- started_at;
- finished_at;
- attempts;
- last_error;
- correlation_id;
- retry policy;
- dead letter handling.

---

# 32. Observabilidade

Implementar:

- logs estruturados;
- métricas;
- tracing;
- health checks;
- error tracking;
- correlation IDs;
- dashboards;
- alertas;
- métricas de fila;
- métricas de processamento de folha;
- métricas eSocial;
- métricas de importação.

---

# 33. Testes

O domínio de folha exige cobertura muito maior.

Criar:

- unit tests;
- integration tests;
- API tests;
- contract tests;
- E2E;
- visual regression;
- security tests;
- load tests;
- golden payroll cases;
- regression packs por competência.

Manter fixtures versionadas com resultados esperados.

Toda atualização tributária precisa adicionar testes antes de ir para produção.

---

# 34. CI/CD

Criar GitHub Actions para:

```text
lint
typecheck
unit-tests
integration-tests
security-scan
build
migration-check
frontend-build
brand-audit
E2E
```

Somente permitir merge em `main` com checks obrigatórios.

Configurar proteção de branch.

---

# 35. Ambientes e infraestrutura

Criar ambientes:

- local;
- test;
- staging;
- production.

Infra mínima:

- PostgreSQL;
- object storage;
- cache quando necessário;
- fila;
- worker;
- secrets;
- domínio;
- HTTPS;
- backups;
- restore;
- monitoring;
- deploy automatizado;
- rollback.

---

# 36. Importação e migração de legado

Além da admissão, criar framework genérico de importação para:

- colaboradores existentes;
- contratos;
- dependentes;
- históricos salariais;
- rubricas;
- ponto;
- benefícios;
- saldos;
- holerites históricos.

Reutilizar o motor de `column mapping` criado para admissões.

---

# 37. Busca, filtros e exportação server-side

A busca não pode depender de arrays carregados no navegador.

Implementar:

- paginação;
- filtros combináveis;
- ordenação;
- busca textual;
- range de datas;
- filtros por status;
- filtros por empresa/filial/departamento;
- export respeitando filtros e RBAC.

---

# 38. Design system e frontend de aplicação

Migrar `ui/index.html` para componentes reais.

Priorizar:

- layout shell;
- navigation;
- tables;
- filters;
- forms;
- drawers;
- dialogs;
- toasts;
- command palette;
- empty states;
- loaders;
- error states;
- pagination;
- import wizard;
- upload;
- audit timeline.

Usar a skill oficial `apply-thpay-brand` como fonte de verdade visual.

Não reintroduzir dark dashboard genérico.

---

# 39. Acessibilidade

Garantir:

- WCAG AA;
- teclado;
- foco visível;
- labels;
- ARIA apenas quando necessário;
- contraste;
- status não dependente somente de cor;
- touch targets;
- leitores de tela;
- zoom;
- responsividade.

Validar 375, 768, 1024 e 1440 px, além de zoom do navegador.

---

# 40. Performance e escala

Não otimizar prematuramente com várias linguagens antes de medir.

Criar métricas para:

- tempo de cálculo por colaborador;
- tempo por 1k/10k/50k vínculos;
- memória;
- consultas;
- importação;
- geração relatório;
- eSocial.

Somente extrair serviços para Java/Rust se benchmarks justificarem.

---

# 41. Roadmap de execução recomendado

## Fase A — Fundação do sistema

Objetivo: deixar de ser demo.

- banco;
- migrations;
- backend/API;
- autenticação;
- usuários;
- RBAC;
- tenants/empresas;
- audit trail;
- storage;
- frontend Next.js;
- CI inicial.

### Critério de saída

Um DP consegue entrar com login e visualizar dados persistidos de uma empresa, enquanto um colaborador entra com outra conta e vê somente os próprios dados.

## Fase B — Admissão e cadastro mestre

- módulo de admissão;
- importação XLSX/CSV;
- templates;
- funcionários;
- contratos;
- cargos;
- filiais;
- dependentes;
- documentos;
- pré-admissão;
- portal convite;
- eSocial S-2190/S-2200.

### Critério de saída

Cenário das 50 admissões concluído ponta a ponta.

## Fase C — Folha mensal MVP

- parâmetros versionados;
- rubricas;
- competência;
- motor em lote;
- holerite persistente;
- aprovação;
- fechamento inicial;
- portal do colaborador.

### Critério de saída

Empresa de teste consegue calcular uma competência inteira e publicar holerites persistentes.

## Fase D — Benefícios, ponto e workflows

- benefícios reais;
- service desk;
- ponto;
- férias;
- 13º;
- rescisão;
- adiantamento;
- CCT.

## Fase E — Compliance eSocial completo

- eventos;
- totalizadores;
- reconciliação;
- certificados;
- retorno/retry;
- fechamentos.

## Fase F — Financeiro e contábil

- pagamento;
- CNAB;
- conciliação;
- contabilização;
- provisões;
- relatórios.

## Fase G — Enterprise

- integrações externas;
- analytics;
- AI real;
- SSO enterprise;
- escala;
- disaster recovery;
- governança avançada.

---

# 42. Ordem sugerida para a próxima IA começar agora

A IA que pegar este repositório deve trabalhar nesta sequência:

```text
1. Criar branch de implementação.
2. Mapear o código existente antes de apagar/refatorar.
3. Preservar o motor de folha atual e seus testes.
4. Introduzir PostgreSQL + migrations.
5. Criar modelo Tenant/Company/User/Role/Permission.
6. Implementar autenticação.
7. Criar API base.
8. Migrar frontend para aplicação componentizada.
9. Implementar cadastro estrutural de empresa.
10. Implementar Admissão & Onboarding.
11. Implementar importador XLSX/CSV genérico.
12. Implementar Employee/Contract persistentes.
13. Conectar motor mensal ao banco.
14. Criar PayrollPeriod e workflows.
15. Avançar nos demais módulos conforme roadmap.
```

---

# 43. Regras para agentes/IA que implementarem este roadmap

## Não fazer

- Não criar apenas tela fake para marcar item como concluído.
- Não usar array JavaScript como “banco”.
- Não retornar sucesso sem persistência.
- Não simular eSocial como se fosse integração real.
- Não gerar hashes fake.
- Não colocar credenciais em código.
- Não hardcodar empresa fictícia no domínio.
- Não confiar em permissão apenas do frontend.
- Não hardcodar tabela tributária sem vigência.
- Não sobrescrever histórico contratual.
- Não coletar dados pessoais sem finalidade.
- Não misturar dados de tenants.

## Fazer

- Implementar vertical slices funcionais.
- Usar migrations.
- Criar testes.
- Preservar auditabilidade.
- Usar transações.
- Usar idempotência.
- Documentar decisões arquiteturais.
- Atualizar este arquivo conforme módulos forem concluídos.
- Marcar itens como implementados somente após teste funcional.

---

# 44. Definition of Done global para chamar ThPay de “sistema”

O ThPay pode ser considerado um sistema funcional inicial quando, no mínimo, for possível executar este cenário completo:

1. Criar uma empresa real no sistema.
2. Criar usuários de DP e RH.
3. Criar/importar 50 admissões por planilha.
4. Validar dados e documentos.
5. Enviar/registrar admissões no fluxo eSocial aplicável.
6. Ativar os 50 vínculos.
7. Cada colaborador receber acesso individual.
8. Importar/apurar variáveis mensais.
9. Calcular folha de todos.
10. Revisar divergências.
11. Aprovar a folha com perfil autorizado.
12. Publicar holerites.
13. O colaborador acessar somente o próprio holerite.
14. Alterar benefício e gerar vigência futura.
15. Abrir chamado e receber resposta persistente.
16. Consultar trilha de auditoria.
17. Fechar a competência.
18. Recuperar todos os dados após logout/restart/deploy, comprovando persistência.

Enquanto isso não existir, considerar o produto ainda em fase de construção, mesmo que a interface esteja visualmente completa.

---

# 45. Próxima entrega recomendada

A próxima grande entrega deve ser chamada:

> **Foundation + Admission Vertical Slice**

Ela deve entregar de ponta a ponta:

```text
PostgreSQL
+ autenticação
+ RBAC
+ empresa/filial/cargo
+ Employee/Contract
+ AdmissionBatch
+ import XLSX/CSV
+ column mapping
+ validation
+ preview
+ commit
+ documentos
+ convite de pré-admissão
+ S-2190/S-2200 adapter inicial
+ auditoria
+ frontend real
+ testes
```

Esse slice cria a fundação necessária para praticamente todo o restante do ThPay e resolve um problema operacional concreto de alto valor: admitir dezenas ou centenas de pessoas com segurança sem digitação manual repetitiva.

---

## Referências regulatórias para implementação

A implementação de admissão e eSocial deve sempre consultar a documentação técnica oficial vigente do eSocial. Em setembro de 2026, utilizar a documentação da série S-1.3 aplicável à produção, mantendo o adaptador versionado para futuras Notas Técnicas. O S-2190 deve ser tratado como registro preliminar opcional e o S-2200 como evento completo de cadastramento/admissão, respeitando regras e prazos vigentes. Não duplicar o leiaute inteiro em entidades de domínio; criar camada adaptadora para eSocial.

### Fonte oficial

- Portal eSocial — Documentação Técnica: https://www.gov.br/esocial/pt-br/documentacao-tecnica
- Manual Web Geral eSocial — S-2200: https://www.gov.br/esocial/pt-br/empresas/manual-web-geral

---

**Status deste documento:** backlog mestre inicial. Atualizar continuamente conforme a implementação avançar.
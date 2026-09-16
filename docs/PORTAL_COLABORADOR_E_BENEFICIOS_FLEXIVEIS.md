# ThPay // Especificacao Tecnica: Portal do Colaborador, Beneficios Flexiveis e Central de Chamados

> Documento normativo complementar a SPECIFICATION.md, definindo a arquitetura de dados, fluxos de estado, regras de integracao com o motor DAG e interfaces da visao do colaborador (Employee Experience Platform - EXP).

---

## 1. Visao Geral de Produto

A camada de autoatendimento do ThPay transforma o colaborador de mero receptor passivo de holerites em agente ativo de gestao da sua propria relacao de trabalho. 

O sistema oferece um ambiente individual e centralizado para:
1. **Consulta Transparente:** Dados cadastrais, contratuais, demonstrativos de pagamento detalhados e demonstrativo de encargos.
2. **Gamificacao e Desempenho:** Leaderboard operacional ancorado em KPIs de entrega, metas e assiduidade, sem expor dados financeiros ou salariais.
3. **Autonomia Parametrizada em Beneficios:** Ajuste autônomo de proporcoes de VA/VR, cancelamento formal de VT com termo legal e gestao de planos de saude e odontologico.
4. **Central de Atendimento e Chamados (Service Desk):** Abertura de chamados com envio de evidencias/documentos, acompanhamento em tempo real de status e historico de interacoes com areas internas.

---

## 2. Arquitetura de Dominio e Modelagem de Dados

### 2.1 Esquema Relacional (PostgreSQL 16+)

```sql
-- 1. Matriz de Configuracao de Beneficios da Empresa
CREATE TABLE benefit_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    benefit_type VARCHAR(50) NOT NULL, -- 'TRANSPORT_VOUCHER', 'MEAL_FOOD_FLEX', 'HEALTH_INSURANCE', 'DENTAL_INSURANCE'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    cut_off_day INT NOT NULL DEFAULT 15, -- Dia limite de alteracao para competencia corrente
    allowed_splits JSONB, -- Ex: [{"meal": 100, "food": 0}, {"meal": 70, "food": 30}, {"meal": 50, "food": 50}]
    monthly_budget NUMERIC(12,2), -- Valor total concedido pela empresa
    open_enrollment_start DATE,
    open_enrollment_end DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Eleicoes / Escolhas do Colaborador (Bitemporal)
CREATE TABLE employee_benefit_elections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collaborator_id UUID NOT NULL REFERENCES collaborators(id),
    benefit_type VARCHAR(50) NOT NULL,
    election_status VARCHAR(30) NOT NULL, -- 'SUBMITTED', 'AUTO_APPROVED', 'PENDING_HR_AUDIT', 'EFFECTIVE', 'CANCELLED'
    split_meal_pct INT DEFAULT 50,
    split_food_pct INT DEFAULT 50,
    health_plan_tier VARCHAR(50), -- 'BASIC_WARD', 'EXECUTIVE_APARTMENT'
    opt_in_dental BOOLEAN DEFAULT FALSE,
    opt_in_vt BOOLEAN DEFAULT TRUE,
    opt_out_vt_reason TEXT, -- Justificativa legal obrigatoria: veiculo proprio, carona, home office
    legal_declaration_signed BOOLEAN DEFAULT FALSE, -- Assinatura do termo de responsabilidade
    valid_from_competence VARCHAR(7) NOT NULL, -- 'YYYY-MM'
    system_recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ
);

-- 3. Historico de Auditoria Imutavel de Beneficios
CREATE TABLE employee_benefit_audit_log (
    id BIGSERIAL PRIMARY KEY,
    collaborator_id UUID NOT NULL,
    benefit_type VARCHAR(50) NOT NULL,
    action VARCHAR(30) NOT NULL, -- 'OPT_OUT_VT', 'SPLIT_VA_VR_CHANGE', 'HEALTH_UPGRADE'
    previous_state JSONB NOT NULL,
    new_state JSONB NOT NULL,
    client_ip INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Central de Chamados (Internal Service Desk)
CREATE TABLE service_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_code VARCHAR(30) UNIQUE NOT NULL, -- 'TCK-2026-0901'
    collaborator_id UUID NOT NULL REFERENCES collaborators(id),
    target_department VARCHAR(50) NOT NULL, -- 'DP', 'RH', 'TI', 'FINANCEIRO', 'FACILITIES'
    category VARCHAR(60) NOT NULL, -- 'HOLERITE', 'BENEFICIOS', 'PONTO', 'FERIAS', 'TI_ACESSO', 'APOIO_GERAL'
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    urgency VARCHAR(20) NOT NULL DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    ticket_status VARCHAR(30) NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'IN_PROGRESS', 'WAITING_COLLABORATOR', 'RESOLVED', 'CLOSED'
    sla_due_at TIMESTAMPTZ NOT NULL,
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

-- 5. Interacoes e Mensagens do Chamado
CREATE TABLE service_ticket_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES service_tickets(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id),
    author_role VARCHAR(30) NOT NULL, -- 'COLLABORATOR', 'OPERATOR_DP', 'ADMIN'
    message_text TEXT NOT NULL,
    is_internal_note BOOLEAN NOT NULL DEFAULT FALSE, -- Notas privadas do DP nao visiveis ao colaborador
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Anexos e Evidencias
CREATE TABLE service_ticket_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES service_tickets(id) ON DELETE CASCADE,
    message_id UUID REFERENCES service_ticket_messages(id),
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    storage_uri TEXT NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Desempenho e Leaderboard Operacional
CREATE TABLE employee_leaderboard_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence VARCHAR(7) NOT NULL, -- 'YYYY-MM'
    collaborator_id UUID NOT NULL REFERENCES collaborators(id),
    department_id UUID NOT NULL,
    kpi_points INT NOT NULL, -- Pontuacao normalizada (ex: 985)
    productivity_score NUMERIC(5,2) NOT NULL, -- 0.00 a 100.00
    punctuality_score NUMERIC(5,2) NOT NULL,
    sprint_deliveries_score NUMERIC(5,2) NOT NULL,
    ranking_global INT NOT NULL,
    ranking_department INT NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 3. Fluxo de Estados e Maquina de Transicao

### 3.1 Ciclo de Vida da Solicitacao de Beneficio Flexivel

```
       +-----------------------+
       |   Iniciada pelo       |
       |    Colaborador        |
       +-----------+-----------+
                   |
                   v
       +-----------+-----------+
       | Status: SUBMITTED     |
       +-----------+-----------+
                   |
         [Cut-Off Check <= Dia 15]
        /                         \
    (Sim)                        (Nao)
      |                            |
      v                            v
[Exige Parecer DP?]       [Agendada para Mes N+1]
  /            \                   |
(Nao: VA/VR) (Sim: Saude/VT)       |
  |                |               |
  v                v               |
+----------+  +------------+       |
| AUTO_APP |  | UNDER_REV  |       |
+----+-----+  +----+-------+       |
     |             |               |
     |        (Aprovado)           |
     |             v               |
     +-----> +-----+-------+ <-----+
             |  EFFECTIVE  |
             +-------------+
```

### 3.2 Ciclo de Vida do Chamado (Service Desk)

```
[ Colaborador abre Chamado ]
             │
             ▼
     ┌───────────────┐
     │  Status: OPEN │ ──(SLA: 24h para primeira resposta)
     └───────┬───────┘
             │ [DP / TI assume chamado]
             ▼
     ┌──────────────────┐
     │   IN_PROGRESS    │ ◄───┐
     └───────┬──────────┘     │
             │                │
     [Solicitacao de info]    │ [Colaborador responde]
             ▼                │
     ┌──────────────────────┐ │
     │ WAITING_COLLABORATOR │─┘
     └───────┬──────────────┘
             │ [Resolucao apresentada]
             ▼
     ┌──────────────────┐
     │     RESOLVED     │ ──(Colaborador aceita ou fecha)
     └───────┬──────────┘
             ▼
     ┌──────────────────┐
     │      CLOSED      │
     └──────────────────┘
```

---

## 4. Regras de Integracao com o Motor DAG da Folha de Pagamento

Quando uma solicitacao de beneficio atinge o status `EFFECTIVE` para a competencia corrente ou futura, ela gera impacto deterministico nos nos do DAG da folha:

1. **No de Desconto de Vale-Transporte (`rubrica_7001`):**
   - Se `opt_in_vt == TRUE`:
     $$DescVT = \min(SalarioBase \times 0.06, CustoTotalPassagens)$$
   - Se `opt_in_vt == FALSE`:
     $$DescVT = 0.00$$
     (A rubrica 7001 e totalmente suprimida do holerite da competencia).

2. **No de Coparticipacao e Plano de Saude (`rubrica_7010`):**
   - Depende do plano escolhido (`health_plan_tier`) e do numero de dependentes.
   - O valor apurado e somado como desconto e entra compulsoriamente na deducao de despesas medicas para fins de base de calculo do IRRF.

3. **No de Distribuicao VA / VR:**
   - Nao afeta o liquido a receber do colaborador em dinheiro se a empresa subsidiar 100% dos cartoes sob o PAT.
   - Caso haja coparticipacao subsidiada em convenção coletiva (ex: desconto de R$ 1,00 ou 5% simbolico), o motor aplica a rubrica de coparticipacao alimentacao (`rubrica_7015`).
   - O saldo de creditos exportado para a operadora parceira (Ticket, Sodexo, Flash, Caju, Swile) e calculado via:
     $$SaldoVR = TotalConcedido \times \left(\frac{split\_meal\_pct}{100}\right)$$
     $$SaldoVA = TotalConcedido \times \left(\frac{split\_food\_pct}{100}\right)$$

---

## 5. Diretrizes de Seguranca, Privacidade e LGPD

1. **Isolamento Multitenant Estrito:**
   - Todas as queries da visao do colaborador utilizam `collaborator_id` extraido do token JWT de sessao criptograficamente verificado.
   - Veda-se qualquer passagem de `collaborator_id` por query param ou payload em endpoints de mutacao de dados sem validacao de correspondencia de identidade.

2. **Sigilo Salarial no Leaderboard:**
   - Sob nenhuma circunstancia o leaderboard contera valores financeiros de remuneracao base, bonus monetario ou salarios liquidos.
   - As metricas expostas sao estritamente operacionais (tarefas, avaliacao de lideranca, presenca, entregas).

3. **Integridade de Documentos Anexados:**
   - Todos os arquivos submetidos na central de chamados passam por sanitizacao de nome, validacao de MIME-type (PDF, JPG, PNG) e calculo de hash SHA-256 para protecao de integridade de prova trabalhista.
   - Arquivos sao armazenados em bucket de objetos privado e assinados com URLs pre-assinadas com expiracao maxima de 15 minutos.

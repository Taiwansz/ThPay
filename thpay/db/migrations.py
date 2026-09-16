import os
import uuid
import hashlib
from typing import List, Tuple
from thpay.db.connection import get_db, get_db_instance

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")

def hash_password(password: str) -> str:
    salt = "thpay_secure_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

def run_migrations(db_path: str = None) -> List[str]:
    applied: List[str] = []
    
    with get_db(db_path) as db:
        # Criar tabela de controle de migrations
        db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(64) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
        """)
        
        # Obter migracoes ja executadas
        existing = {row["version"] for row in db.fetchall("SELECT version FROM schema_migrations;")}
        
        # 1. Base Schema
        if "2026.09.01_base_schema" not in existing:
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            # Executar comandos individuais ou script
            for statement in schema_sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    db.execute(stmt)
            
            db.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?);",
                ("2026.09.01_base_schema", "Esquema relacional base e indices")
            )
            applied.append("2026.09.01_base_schema")

        # 2. RBAC Roles and Permissions
        if "2026.09.02_seed_rbac" not in existing:
            roles = [
                ("SUPER_ADMIN", "Super Administrador", "Acesso irrestrito a plataforma"),
                ("EMPRESA_ADMIN", "Administrador da Empresa", "Gestao integral da empresa e configuracoes"),
                ("DP_GESTOR", "Gestor de Departamento Pessoal", "Aprovacao de folha, rescisao e contratacoes"),
                ("DP_OPERADOR", "Operador de Departamento Pessoal", "Operacoes cotidianas de folha, calculo e ponto"),
                ("RH_OPERADOR", "Operador de RH", "Admissoes, beneficios, onboarding e comunicacao"),
                ("AUDITOR_COMPLIANCE", "Auditor de Compliance", "Acesso somente leitura e trilha de auditoria"),
                ("COLABORADOR_SELF_SERVICE", "Colaborador Self-Service", "Portal individual do colaborador")
            ]
            for code, name, desc in roles:
                db.execute(
                    "INSERT OR IGNORE INTO roles (code, name, description) VALUES (?, ?, ?);",
                    (code, name, desc)
                )

            permissions = [
                ("SUPER_ADMIN", "*"),
                ("EMPRESA_ADMIN", "company.*"),
                ("EMPRESA_ADMIN", "employee.*"),
                ("EMPRESA_ADMIN", "admission.*"),
                ("EMPRESA_ADMIN", "payroll.*"),
                ("EMPRESA_ADMIN", "benefit.*"),
                ("EMPRESA_ADMIN", "audit.read"),
                ("DP_GESTOR", "employee.*"),
                ("DP_GESTOR", "admission.*"),
                ("DP_GESTOR", "payroll.*"),
                ("DP_GESTOR", "benefit.*"),
                ("DP_GESTOR", "esocial.*"),
                ("DP_GESTOR", "audit.read"),
                ("DP_OPERADOR", "employee.read"),
                ("DP_OPERADOR", "employee.create"),
                ("DP_OPERADOR", "employee.update"),
                ("DP_OPERADOR", "admission.manage"),
                ("DP_OPERADOR", "payroll.calculate"),
                ("DP_OPERADOR", "payroll.read"),
                ("DP_OPERADOR", "benefit.manage"),
                ("RH_OPERADOR", "admission.manage"),
                ("RH_OPERADOR", "employee.read"),
                ("RH_OPERADOR", "employee.create"),
                ("RH_OPERADOR", "benefit.manage"),
                ("AUDITOR_COMPLIANCE", "audit.read"),
                ("AUDITOR_COMPLIANCE", "payroll.read"),
                ("AUDITOR_COMPLIANCE", "employee.read"),
                ("COLABORADOR_SELF_SERVICE", "self.read"),
                ("COLABORADOR_SELF_SERVICE", "self.benefits.update"),
                ("COLABORADOR_SELF_SERVICE", "self.tickets.manage"),
            ]
            for role_code, perm_code in permissions:
                db.execute(
                    "INSERT OR IGNORE INTO role_permissions (role_code, permission_code) VALUES (?, ?);",
                    (role_code, perm_code)
                )
            
            db.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?);",
                ("2026.09.02_seed_rbac", "Perfis RBAC e matriz de permissoes")
            )
            applied.append("2026.09.02_seed_rbac")

        # 3. Seed Organization & Default Users
        if "2026.09.03_seed_org_and_users" not in existing:
            tenant_id = "tenant-thpay-corp"
            company_id = "company-tech-solutions"
            
            db.execute(
                "INSERT OR IGNORE INTO tenants (id, name) VALUES (?, ?);",
                (tenant_id, "ThPay Enterprise Tenant")
            )
            
            db.execute("""
                INSERT OR IGNORE INTO companies (
                    id, tenant_id, cnpj, corporate_name, trade_name, tax_regime,
                    cnae, fpas, other_entities_code, rat_basic, fap
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                company_id, tenant_id, "12.345.678/0001-90",
                "Tech Solutions Brasil Ltda", "Tech Solutions",
                "LUCRO_REAL", "6201-5/01", "507", "0079", 0.0200, 1.0000
            ))

            branch_id = "branch-sp-matriz"
            db.execute("""
                INSERT OR IGNORE INTO branches (
                    id, company_id, code, name, cnpj, address_street,
                    address_number, address_city, address_state, address_zip
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                branch_id, company_id, "0001", "Matriz São Paulo",
                "12.345.678/0001-90", "Avenida Paulista", "1000",
                "São Paulo", "SP", "01310-100"
            ))

            departments = [
                ("dept-eng", "ENG", "Engenharia de Software"),
                ("dept-prod", "PROD", "Produto & Design"),
                ("dept-dp", "DP", "Departamento Pessoal & RH"),
                ("dept-fin", "FIN", "Financeiro & Controladoria"),
                ("dept-ops", "OPS", "Operações & Infraestrutura")
            ]
            for d_id, code, name in departments:
                db.execute(
                    "INSERT OR IGNORE INTO departments (id, company_id, code, name) VALUES (?, ?, ?, ?);",
                    (d_id, company_id, code, name)
                )

            cost_centers = [
                ("cc-eng", "CC-1001", "P&D Software Core"),
                ("cc-adm", "CC-2001", "Administrativo & RH"),
                ("cc-com", "CC-3001", "Comercial & Marketing")
            ]
            for cc_id, code, name in cost_centers:
                db.execute(
                    "INSERT OR IGNORE INTO cost_centers (id, company_id, code, name) VALUES (?, ?, ?, ?);",
                    (cc_id, company_id, code, name)
                )

            positions = [
                ("pos-eng-sr", "ENG-SR", "Engenheiro de Software Sênior", "2124-05", 14500.00),
                ("pos-eng-pl", "ENG-PL", "Engenheiro de Software Pleno", "2124-05", 8500.00),
                ("pos-eng-jr", "ENG-JR", "Engenheiro de Software Júnior", "2124-05", 5200.00),
                ("pos-analista-dp", "DP-ANALISTA", "Analista de Departamento Pessoal", "4110-05", 4800.00),
                ("pos-designer-ui", "UI-DESIGNER", "Designer de Interfaces", "2624-10", 7200.00),
                ("pos-gerente-prod", "PROD-MGR", "Gerente de Produto", "1421-05", 16000.00)
            ]
            for p_id, code, title, cbo, salary in positions:
                db.execute(
                    "INSERT OR IGNORE INTO positions (id, company_id, code, title, cbo, standard_salary) VALUES (?, ?, ?, ?, ?, ?);",
                    (p_id, company_id, code, title, cbo, salary)
                )

            # Usuarios padrao
            users = [
                ("user-admin-dp", tenant_id, company_id, None, "dp@techsolutions.com.br", hash_password("ThPay@2026"), "Mariana Silva (Analista DP)", "DP_GESTOR"),
                ("user-rh-op", tenant_id, company_id, None, "rh@techsolutions.com.br", hash_password("ThPay@2026"), "Carlos Ferreira (RH Onboarding)", "RH_OPERADOR"),
                ("user-compliance", tenant_id, company_id, None, "auditoria@techsolutions.com.br", hash_password("ThPay@2026"), "Dra. Beatriz Santos (Compliance)", "AUDITOR_COMPLIANCE"),
            ]
            for u_id, t_id, c_id, e_id, email, pwd_hash, name, role in users:
                db.execute("""
                    INSERT OR IGNORE INTO users (
                        id, tenant_id, company_id, employee_id, email, password_hash, full_name, role
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (u_id, t_id, c_id, e_id, email, pwd_hash, name, role))

            db.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?);",
                ("2026.09.03_seed_org_and_users", "Organizacao, filiais, cargos e usuarios administrativos")
            )
            applied.append("2026.09.03_seed_org_and_users")

        # 4. Seed initial active employees to populate real database
        if "2026.09.04_seed_initial_employees" not in existing:
            company_id = "company-tech-solutions"
            branch_id = "branch-sp-matriz"
            
            initial_employees = [
                ("emp-001", "123.456.789-00", "Matheus Sousa dos Santos", "matheus.sousa@techsolutions.com.br", "1994-05-12", "pos-eng-sr", "dept-eng", "cc-eng", "MAT-001", 14500.00),
                ("emp-002", "234.567.890-11", "Lucas Oliveira Ribeiro", "lucas.oliveira@techsolutions.com.br", "1996-08-20", "pos-eng-pl", "dept-eng", "cc-eng", "MAT-002", 8500.00),
                ("emp-003", "345.678.901-22", "Mariana Costa e Silva", "mariana.silva@techsolutions.com.br", "1992-03-15", "pos-analista-dp", "dept-dp", "cc-adm", "MAT-003", 4800.00),
                ("emp-004", "456.789.012-33", "Thiago Almeida Rocha", "thiago.rocha@techsolutions.com.br", "1990-11-04", "pos-gerente-prod", "dept-prod", "cc-adm", "MAT-004", 16000.00),
                ("emp-005", "567.890.123-44", "Beatriz Mendonça Prado", "beatriz.prado@techsolutions.com.br", "1998-07-29", "pos-designer-ui", "dept-prod", "cc-adm", "MAT-005", 7200.00),
            ]

            for e_id, cpf, name, email, birth, pos_id, dept_id, cc_id, mat, salary in initial_employees:
                db.execute("""
                    INSERT OR IGNORE INTO employees (
                        id, company_id, cpf, full_name, birth_date, corporate_email, personal_email, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE');
                """, (e_id, company_id, cpf, name, birth, email, email))

                db.execute("""
                    INSERT OR IGNORE INTO employee_addresses (
                        id, employee_id, zip_code, street, number, neighborhood, city, state
                    ) VALUES (?, ?, '01310-100', 'Avenida Paulista', '1000', 'Bela Vista', 'São Paulo', 'SP');
                """, (f"addr-{e_id}", e_id))

                db.execute("""
                    INSERT OR IGNORE INTO employee_bank_accounts (
                        id, employee_id, bank_code, bank_name, agency, account_number, account_type, pix_key
                    ) VALUES (?, ?, '001', 'Banco do Brasil', '1234', '98765-4', 'CORRENTE', ?);
                """, (f"bank-{e_id}", e_id, cpf))

                db.execute("""
                    INSERT OR IGNORE INTO employment_contracts (
                        id, employee_id, company_id, branch_id, department_id, cost_center_id,
                        position_id, registration_number, hire_date, category, contract_type,
                        base_salary, monthly_hours, is_active, valid_from
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '2024-01-15', '101', 'INDETERMINATE', ?, 220, 1, '2024-01-15');
                """, (f"cont-{e_id}", e_id, company_id, branch_id, dept_id, cc_id, pos_id, mat, salary))

                # Beneficios
                db.execute("""
                    INSERT OR IGNORE INTO employee_benefits (
                        id, employee_id, benefit_type, va_percentage, vr_percentage, total_amount, effective_date
                    ) VALUES (?, ?, 'VA_VR', 50, 50, 1400.00, '2024-01-15');
                """, (f"ben-{e_id}", e_id))

                # Usuario para o colaborador poder acessar o portal
                user_email = email
                db.execute("""
                    INSERT OR IGNORE INTO users (
                        id, tenant_id, company_id, employee_id, email, password_hash, full_name, role
                    ) VALUES (?, 'tenant-thpay-corp', ?, ?, ?, ?, ?, 'COLABORADOR_SELF_SERVICE');
                """, (f"usr-{e_id}", company_id, e_id, user_email, hash_password("ThPay@2026"), name))

            db.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?);",
                ("2026.09.04_seed_initial_employees", "Colaboradores, contratos e beneficios iniciais ativos")
            )
            applied.append("2026.09.04_seed_initial_employees")

    return applied

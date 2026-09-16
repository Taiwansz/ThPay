from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from thpay.domain.entities import (
    Company as EngineCompany,
    Employee as EngineEmployee,
    Contract as EngineContract,
    Dependent as EngineDependent,
    TaxRegime,
    WorkerCategory
)

class EmployeeRepository:
    @staticmethod
    def list_employees(
        db,
        company_id: str,
        search: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        conditions = ["e.company_id = ?"]
        params = [company_id]
        
        if search:
            conditions.append("(e.full_name LIKE ? OR e.cpf LIKE ? OR e.corporate_email LIKE ?)")
            search_param = f"%{search.strip()}%"
            params.extend([search_param, search_param, search_param])
            
        if status:
            conditions.append("e.status = ?")
            params.append(status)
            
        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT e.id, e.company_id, e.cpf, e.full_name, e.social_name,
                   e.birth_date, e.gender, e.marital_status, e.nationality,
                   e.corporate_email, e.personal_email, e.phone_mobile, e.status,
                   c.id as contract_id, c.registration_number, c.base_salary,
                   c.hire_date, c.category, c.contract_type,
                   p.title as position_title, p.cbo,
                   d.name as department_name,
                   b.name as branch_name
            FROM employees e
            LEFT JOIN employment_contracts c ON c.employee_id = e.id AND c.is_active = 1
            LEFT JOIN positions p ON p.id = c.position_id
            LEFT JOIN departments d ON d.id = c.department_id
            LEFT JOIN branches b ON b.id = c.branch_id
            WHERE {where_clause}
            ORDER BY e.full_name ASC
            LIMIT ? OFFSET ?;
        """
        params.extend([limit, offset])
        return db.fetchall(sql, tuple(params))

    @staticmethod
    def get_employee_detail(db, employee_id: str) -> Optional[Dict[str, Any]]:
        emp = db.fetchone("SELECT * FROM employees WHERE id = ?;", (employee_id,))
        if not emp:
            return None
            
        emp_dict = dict(emp)
        emp_dict["addresses"] = db.fetchall(
            "SELECT * FROM employee_addresses WHERE employee_id = ? ORDER BY is_primary DESC;",
            (employee_id,)
        )
        emp_dict["documents"] = db.fetchall(
            "SELECT * FROM employee_documents WHERE employee_id = ? ORDER BY document_type;",
            (employee_id,)
        )
        emp_dict["bank_accounts"] = db.fetchall(
            "SELECT * FROM employee_bank_accounts WHERE employee_id = ? ORDER BY is_primary DESC;",
            (employee_id,)
        )
        emp_dict["dependents"] = db.fetchall(
            "SELECT * FROM employee_dependents WHERE employee_id = ? ORDER BY full_name;",
            (employee_id,)
        )
        emp_dict["contracts"] = db.fetchall("""
            SELECT c.*, p.title as position_title, p.cbo, d.name as department_name,
                   cc.name as cost_center_name, b.name as branch_name
            FROM employment_contracts c
            LEFT JOIN positions p ON p.id = c.position_id
            LEFT JOIN departments d ON d.id = c.department_id
            LEFT JOIN cost_centers cc ON cc.id = c.cost_center_id
            LEFT JOIN branches b ON b.id = c.branch_id
            WHERE c.employee_id = ?
            ORDER BY c.is_active DESC, c.hire_date DESC;
        """, (employee_id,))
        emp_dict["benefits"] = db.fetchall(
            "SELECT * FROM employee_benefits WHERE employee_id = ? ORDER BY effective_date DESC;",
            (employee_id,)
        )
        return emp_dict

    @staticmethod
    def to_engine_contract(db, contract_id: str) -> Optional[EngineContract]:
        """
        Converte os dados persistidos em entidades do motor de calculo Python
        para execucao do pipeline mensal de folha de pagamento.
        """
        contract_row = db.fetchone("SELECT * FROM employment_contracts WHERE id = ?;", (contract_id,))
        if not contract_row:
            return None
            
        emp_row = db.fetchone("SELECT * FROM employees WHERE id = ?;", (contract_row["employee_id"],))
        comp_row = db.fetchone("SELECT * FROM companies WHERE id = ?;", (contract_row["company_id"],))
        if not emp_row or not comp_row:
            return None
            
        dep_rows = db.fetchall("SELECT * FROM employee_dependents WHERE employee_id = ?;", (emp_row["id"],))
        dependents_list = [
            EngineDependent(
                name=d["full_name"],
                relationship=d["relationship"],
                is_irrf_dependent=bool(d["is_irrf_dependent"]),
                is_family_salary_dependent=bool(d["is_family_salary_dependent"]),
                birth_date=d.get("birth_date")
            )
            for d in dep_rows
        ]
        
        # Mapear categoria para enum do motor
        try:
            category_enum = WorkerCategory(contract_row["category"])
        except ValueError:
            category_enum = WorkerCategory.CLT_GERAL
            
        engine_emp = EngineEmployee(
            cpf=emp_row["cpf"],
            full_name=emp_row["full_name"],
            category=category_enum,
            dependents=dependents_list,
            alimony_orders=[]
        )
        
        # Mapear regime tributario
        try:
            tax_regime_enum = TaxRegime(comp_row["tax_regime"])
        except ValueError:
            tax_regime_enum = TaxRegime.LUCRO_REAL
            
        engine_comp = EngineCompany(
            cnpj=comp_row["cnpj"],
            corporate_name=comp_row["corporate_name"],
            tax_regime=tax_regime_enum,
            cnae=comp_row["cnae"],
            fpas=comp_row["fpas"],
            other_entities_code=comp_row["other_entities_code"] or "0079",
            rat_basic=Decimal(str(comp_row["rat_basic"])),
            fap=Decimal(str(comp_row["fap"]))
        )
        
        return EngineContract(
            contract_id=contract_row["id"],
            employee=engine_emp,
            company=engine_comp,
            base_salary=Decimal(str(contract_row["base_salary"])),
            workload_monthly_hours=int(contract_row["monthly_hours"] or 220),
            is_active=bool(contract_row["is_active"])
        )

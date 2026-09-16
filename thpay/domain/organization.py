from typing import Any, Dict, List, Optional
import uuid

class OrganizationService:
    @staticmethod
    def get_company(db, company_id: str) -> Optional[Dict[str, Any]]:
        return db.fetchone("SELECT * FROM companies WHERE id = ?;", (company_id,))

    @staticmethod
    def list_companies(db, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if tenant_id:
            return db.fetchall("SELECT * FROM companies WHERE tenant_id = ? ORDER BY corporate_name;", (tenant_id,))
        return db.fetchall("SELECT * FROM companies ORDER BY corporate_name;")

    @staticmethod
    def list_branches(db, company_id: str) -> List[Dict[str, Any]]:
        return db.fetchall("SELECT * FROM branches WHERE company_id = ? ORDER BY code;", (company_id,))

    @staticmethod
    def list_departments(db, company_id: str) -> List[Dict[str, Any]]:
        return db.fetchall("SELECT * FROM departments WHERE company_id = ? ORDER BY name;", (company_id,))

    @staticmethod
    def list_cost_centers(db, company_id: str) -> List[Dict[str, Any]]:
        return db.fetchall("SELECT * FROM cost_centers WHERE company_id = ? ORDER BY code;", (company_id,))

    @staticmethod
    def list_positions(db, company_id: str) -> List[Dict[str, Any]]:
        return db.fetchall("SELECT * FROM positions WHERE company_id = ? ORDER BY title;", (company_id,))

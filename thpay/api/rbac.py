from typing import Any, Dict, List, Optional

class RBACManager:
    """
    Gerenciador de controle de acesso baseado em papeis (RBAC).
    Valida permissoes com suporte a curingas ('*', 'employee.*') e
    garante isolamento do self-service de colaboradores.
    """
    @staticmethod
    def has_permission(user: Dict[str, Any], required_permission: str) -> bool:
        if not user:
            return False
            
        role = user.get("role", "")
        if role == "SUPER_ADMIN":
            return True
            
        user_permissions = set(user.get("permissions", []))
        if "*" in user_permissions:
            return True
            
        if required_permission in user_permissions:
            return True
            
        # Suporte a wildcard: ex. 'employee.*' cobre 'employee.read'
        domain = required_permission.split(".")[0] if "." in required_permission else ""
        if f"{domain}.*" in user_permissions:
            return True
            
        return False

    @staticmethod
    def enforce_employee_scope(user: Dict[str, Any], target_employee_id: str) -> bool:
        """
        Garante que um colaborador no self-service so consiga consultar ou alterar seus proprios dados.
        Usuarios DP, RH ou administradores tem escopo ampliado.
        """
        role = user.get("role", "")
        if role in {"SUPER_ADMIN", "EMPRESA_ADMIN", "DP_GESTOR", "DP_OPERADOR", "RH_OPERADOR", "AUDITOR_COMPLIANCE"}:
            return True
            
        user_employee_id = user.get("employee_id")
        return bool(user_employee_id and user_employee_id == target_employee_id)

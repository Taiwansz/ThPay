import re
import unicodedata
from typing import Any, Dict, List, Optional

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    # Remover acentos
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
    # Remover pontuacoes e caracteres especiais, deixando apenas letras, numeros e espacos
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

CANONICAL_TARGET_FIELDS = {
    "full_name": {
        "label": "Nome Completo",
        "synonyms": ["nome completo", "nome", "colaborador", "nome do funcionario", "nome funcionario", "candidato", "trabalhador", "funcionario"]
    },
    "cpf": {
        "label": "CPF",
        "synonyms": ["cpf", "documento cpf", "num cpf", "numero cpf", "cpf do funcionario", "cpf candidato"]
    },
    "birth_date": {
        "label": "Data de Nascimento",
        "synonyms": ["data de nascimento", "data nascimento", "dt nascimento", "nascimento", "data nasc", "dt nasc", "dtnasc"]
    },
    "email": {
        "label": "E-mail Pessoal/Corporativo",
        "synonyms": ["email", "e mail", "email pessoal", "e mail pessoal", "email corporativo", "e mail corporativo", "correio eletronico"]
    },
    "phone": {
        "label": "Telefone / Celular",
        "synonyms": ["celular", "telefone", "fone", "contato", "telefone celular", "tel", "whatsapp", "cel"]
    },
    "zip_code": {
        "label": "CEP",
        "synonyms": ["cep", "codigo postal", "cep endereco"]
    },
    "street": {
        "label": "Logradouro / Endereço",
        "synonyms": ["logradouro", "rua", "endereco", "avenida", "av", "end", "endereco residencial"]
    },
    "number": {
        "label": "Número do Endereço",
        "synonyms": ["numero", "num", "no", "nro", "numero endereco"]
    },
    "complement": {
        "label": "Complemento",
        "synonyms": ["complemento", "compl", "apto", "bloco"]
    },
    "neighborhood": {
        "label": "Bairro",
        "synonyms": ["bairro", "distrito"]
    },
    "city": {
        "label": "Cidade / Município",
        "synonyms": ["cidade", "municipio", "cidade endereco"]
    },
    "state": {
        "label": "UF / Estado",
        "synonyms": ["uf", "estado", "sigla uf", "uf endereco"]
    },
    "position_title": {
        "label": "Cargo / Função",
        "synonyms": ["cargo", "funcao", "posicao", "titulo cargo", "funcao contratual", "cargo do colaborador"]
    },
    "cbo": {
        "label": "CBO",
        "synonyms": ["cbo", "codigo cbo", "num cbo", "cbo 2002"]
    },
    "base_salary": {
        "label": "Salário Base",
        "synonyms": ["salario", "salario base", "remuneracao", "salario mensal", "salario nominal", "remuneracao base"]
    },
    "department_name": {
        "label": "Departamento / Área",
        "synonyms": ["departamento", "setor", "area", "lotacao", "depto", "centro de trabalho"]
    },
    "cost_center_code": {
        "label": "Centro de Custo",
        "synonyms": ["centro de custo", "centro de custos", "cc", "cod centro custo", "codigo centro de custo"]
    },
    "branch_code": {
        "label": "Filial / Estabelecimento",
        "synonyms": ["filial", "estabelecimento", "unidade", "local", "codigo filial"]
    },
    "hire_date": {
        "label": "Data de Admissão",
        "synonyms": ["data de admissao", "data admissao", "data inicio", "admissao", "dt admissao", "inicio"]
    },
    "contract_type": {
        "label": "Tipo de Contrato / Modalidade",
        "synonyms": ["modalidade", "tipo contrato", "regime", "tipo de contrato", "vinculo", "tipo de vinculo"]
    },
    "work_schedule": {
        "label": "Jornada / Escala",
        "synonyms": ["jornada", "escala", "carga horaria", "horario", "jornada semanal", "carga horaria semanal"]
    },
    "bank_name": {
        "label": "Banco",
        "synonyms": ["banco", "nome banco", "codigo banco", "instituicao financeira"]
    },
    "agency": {
        "label": "Agência Bancária",
        "synonyms": ["agencia", "ag", "cod agencia", "num agencia"]
    },
    "account_number": {
        "label": "Conta Bancária",
        "synonyms": ["conta", "conta corrente", "num conta", "numero conta", "cc bancaria"]
    },
    "pix_key": {
        "label": "Chave Pix",
        "synonyms": ["pix", "chave pix", "chave pix titular"]
    },
    "vt_opt_out": {
        "label": "Opção VT (Sim/Não)",
        "synonyms": ["vt", "vale transporte", "opt out vt", "necessita vt", "transporte"]
    },
    "va_split": {
        "label": "Divisão VA/VR (%)",
        "synonyms": ["va vr", "split va vr", "va split", "distribuicao va vr", "alimentacao refeicao"]
    }
}

class ColumnMapper:
    @staticmethod
    def suggest_mapping(headers: List[str]) -> Dict[str, str]:
        mapping = {}
        assigned_targets = set()
        
        for header in headers:
            norm = normalize_text(header)
            matched_target = None
            
            # Busca exata ou por sinonimos
            for target_field, meta in CANONICAL_TARGET_FIELDS.items():
                if target_field in assigned_targets:
                    continue
                for syn in meta["synonyms"]:
                    if norm == syn or syn in norm:
                        matched_target = target_field
                        break
                if matched_target:
                    break
                    
            if matched_target:
                mapping[header] = matched_target
                assigned_targets.add(matched_target)
            else:
                mapping[header] = "" # Usuario escolhe ou ignora
                
        return mapping

    @staticmethod
    def apply_mapping(
        raw_row: Dict[str, Any],
        mapping: Dict[str, str],
        default_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        mapped = {}
        defaults = default_values or {}
        
        for source_col, target_field in mapping.items():
            if not target_field or target_field == "IGNORE":
                continue
            val = raw_row.get(source_col, "")
            mapped[target_field] = val
            
        # Aplicar valores default para campos nao mapeados ou vazios
        for k, v in defaults.items():
            if not mapped.get(k):
                mapped[k] = v
                
        return mapped

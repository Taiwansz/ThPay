from dataclasses import dataclass
from .entities import RubricType

@dataclass(frozen=True)
class RubricDefinition:
    code: str
    name: str
    rubric_type: RubricType
    cod_inc_cp: str     # eSocial incidencia INSS: 00, 11, 12, 13, 14
    cod_inc_fgts: str   # eSocial incidencia FGTS: 00, 11, 12, 21
    cod_inc_irrf: str   # eSocial incidencia IRRF: 00, 11, 12, 13, 31
    esocial_nature: str # Tabela 03 do eSocial

CANONICAL_RUBRICS = {
    "1000": RubricDefinition("1000", "Salario Base / Normal", RubricType.PROVENTO, "11", "11", "11", "1000"),
    "1010": RubricDefinition("1010", "Horas Extras 50%", RubricType.PROVENTO, "11", "11", "11", "1003"),
    "1015": RubricDefinition("1015", "Horas Extras 100%", RubricType.PROVENTO, "11", "11", "11", "1003"),
    "1020": RubricDefinition("1020", "DSR sobre Horas Extras", RubricType.PROVENTO, "11", "11", "11", "1010"),
    "1030": RubricDefinition("1030", "Adicional Noturno 20%", RubricType.PROVENTO, "11", "11", "11", "1201"),
    "1035": RubricDefinition("1035", "DSR sobre Adicional Noturno", RubricType.PROVENTO, "11", "11", "11", "1010"),
    "1040": RubricDefinition("1040", "Adicional de Insalubridade", RubricType.PROVENTO, "11", "11", "11", "1202"),
    "1050": RubricDefinition("1050", "Adicional de Periculosidade", RubricType.PROVENTO, "11", "11", "11", "1203"),
    "1070": RubricDefinition("1070", "Salario-Familia", RubricType.PROVENTO, "00", "00", "00", "1409"),
    "1099": RubricDefinition("1099", "Insuficiencia de Saldo (Anti-Negativo)", RubricType.PROVENTO, "00", "00", "00", "9908"),
    "5000": RubricDefinition("5000", "INSS Empregado Mensal", RubricType.DESCONTO, "00", "00", "00", "9201"),
    "5010": RubricDefinition("5010", "IRRF Empregado Mensal", RubricType.DESCONTO, "00", "00", "00", "9203"),
    "5020": RubricDefinition("5020", "Faltas Injustificadas", RubricType.DESCONTO, "11", "11", "11", "9200"),
    "5025": RubricDefinition("5025", "DSR Descontado por Faltas", RubricType.DESCONTO, "11", "11", "11", "9200"),
    "5030": RubricDefinition("5030", "Vale-Transporte (Desc. ate 6%)", RubricType.DESCONTO, "00", "00", "00", "9210"),
    "5040": RubricDefinition("5040", "Vale-Refeicao/Alimentacao (PAT)", RubricType.DESCONTO, "00", "00", "00", "9211"),
    "5050": RubricDefinition("5050", "Plano de Saude / Odonto", RubricType.DESCONTO, "00", "00", "00", "9219"),
    "5060": RubricDefinition("5060", "Desconto de Adiantamento Salarial", RubricType.DESCONTO, "00", "00", "00", "9214"),
    "5070": RubricDefinition("5070", "Pensao Alimenticia Judicial", RubricType.DESCONTO, "00", "00", "00", "9205"),
    "5080": RubricDefinition("5080", "Emprestimo Consignado", RubricType.DESCONTO, "00", "00", "00", "9215"),
    "9000": RubricDefinition("9000", "Base INSS Mensal", RubricType.INFORMATIVA, "00", "00", "00", "9901"),
    "9010": RubricDefinition("9010", "Base FGTS Mensal", RubricType.INFORMATIVA, "00", "00", "00", "9902"),
    "9020": RubricDefinition("9020", "Base IRRF Mensal", RubricType.INFORMATIVA, "00", "00", "00", "9903"),
    "9030": RubricDefinition("9030", "FGTS Recolhido Empresa", RubricType.INFORMATIVA, "00", "00", "00", "9904"),
}

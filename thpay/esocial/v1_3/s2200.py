import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from xml.sax.saxutils import escape

class EventoS2200_v1_3:
    """
    Gerador do evento eSocial S-2200 (Cadastramento Inicial do Vínculo e Admissão) - Leiaute S-1.3.
    Registra a contratação definitiva com todos os dados cadastrais, contratuais e remuneratórios.
    """
    EVENT_CODE = "S-2200"
    VERSION = "v1_3"

    @classmethod
    def generate(
        cls,
        cnpj_empregador: str,
        cpf: str,
        nome: str,
        data_nascimento: str,
        data_admissao: str,
        matricula: str,
        cargo: str,
        cbo: str,
        salario_base: float,
        sexo: str = "M",
        raca_cor: int = 1,
        estado_civil: int = 1,
        grau_instrucao: str = "09",
        logradouro: str = "Avenida Paulista",
        numero: str = "1000",
        bairro: str = "Bela Vista",
        cep: str = "01310100",
        cidade: str = "São Paulo",
        uf: str = "SP",
        categoria: str = "101",
        id_evento: str = None
    ) -> Dict[str, Any]:
        evt_id = id_evento or f"ID1{cnpj_empregador.replace('.', '').replace('/', '').replace('-', '')[:8]}00000000000{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        clean_cnpj = cnpj_empregador.replace(".", "").replace("/", "").replace("-", "")
        clean_cpf = cpf.replace(".", "").replace("-", "")
        clean_cep = cep.replace(".", "").replace("-", "")

        json_payload = {
            "eSocial": {
                "@xmlns": "http://www.esocial.gov.br/schema/evt/evtAdmissao/v_S_01_03_00",
                "evtAdmissao": {
                    "@Id": evt_id,
                    "ideEmpregador": {
                        "tpInsc": 1,
                        "nrInsc": clean_cnpj
                    },
                    "trabalhador": {
                        "cpfTrab": clean_cpf,
                        "nmTrab": nome,
                        "sexo": sexo,
                        "racaCor": raca_cor,
                        "estCiv": estado_civil,
                        "grauInstr": grau_instrucao,
                        "nascimento": {
                            "dtNascto": data_nascimento,
                            "paisNascto": "105" # Brasil
                        },
                        "endereco": {
                            "brasil": {
                                "tpLogdr": "R",
                                "dscLogdr": logradouro,
                                "nrLogdr": numero,
                                "bairro": bairro,
                                "cep": clean_cep,
                                "codMunic": "3550308", # Sao Paulo
                                "uf": uf
                            }
                        }
                    },
                    "vinculo": {
                        "matricula": matricula,
                        "tpRegTrab": 1, # CLT
                        "tpRegPrev": 1, # RGPS
                        "cadIni": "N",
                        "infoRegimeTrab": {
                            "infoCeletista": {
                                "tpAdmissao": 1, # Admissao normal
                                "indAdmissao": 1, # Normal
                                "tpRegJor": 1, # Submetidos a Horario de Trabalho
                                "natAtividade": 1, # Urbana
                                "dtBase": 1,
                                "cnpjSindCategProf": clean_cnpj
                            }
                        },
                        "infoContrato": {
                            "codCateg": categoria,
                            "remuneracao": {
                                "vrSalFx": f"{salario_base:.2f}",
                                "undSalFixo": 7, # Por Mes
                                "dscSalVar": ""
                            },
                            "duracao": {
                                "tpContr": 1 # Prazo indeterminado
                            },
                            "localTrabalho": {
                                "localTrabGeral": {
                                    "tpInsc": 1,
                                    "nrInsc": clean_cnpj,
                                    "descComp": "Sede Matriz"
                                }
                            },
                            "horContratual": {
                                "qtdHrsSem": 44,
                                "tpJornada": 1,
                                "dscTpJorn": "Segunda a Sexta"
                            },
                            "cargo": {
                                "codCargo": cbo,
                                "cbo": cbo,
                                "dscCargo": cargo
                            }
                        }
                    }
                }
            }
        }

        xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtAdmissao/v_S_01_03_00">
  <evtAdmissao Id="{evt_id}">
    <ideEmpregador>
      <tpInsc>1</tpInsc>
      <nrInsc>{clean_cnpj}</nrInsc>
    </ideEmpregador>
    <trabalhador>
      <cpfTrab>{clean_cpf}</cpfTrab>
      <nmTrab>{escape(nome)}</nmTrab>
      <sexo>{sexo}</sexo>
      <racaCor>{raca_cor}</racaCor>
      <estCiv>{estado_civil}</estCiv>
      <grauInstr>{grau_instrucao}</grauInstr>
      <nascimento>
        <dtNascto>{data_nascimento}</dtNascto>
        <paisNascto>105</paisNascto>
      </nascimento>
      <endereco>
        <brasil>
          <tpLogdr>R</tpLogdr>
          <dscLogdr>{escape(logradouro)}</dscLogdr>
          <nrLogdr>{escape(numero)}</nrLogdr>
          <bairro>{escape(bairro)}</bairro>
          <cep>{clean_cep}</cep>
          <codMunic>3550308</codMunic>
          <uf>{uf}</uf>
        </brasil>
      </endereco>
    </trabalhador>
    <vinculo>
      <matricula>{escape(matricula)}</matricula>
      <tpRegTrab>1</tpRegTrab>
      <tpRegPrev>1</tpRegPrev>
      <cadIni>N</cadIni>
      <infoRegimeTrab>
        <infoCeletista>
          <tpAdmissao>1</tpAdmissao>
          <indAdmissao>1</indAdmissao>
          <tpRegJor>1</tpRegJor>
          <natAtividade>1</natAtividade>
          <dtBase>1</dtBase>
        </infoCeletista>
      </infoRegimeTrab>
      <infoContrato>
        <codCateg>{categoria}</codCateg>
        <remuneracao>
          <vrSalFx>{salario_base:.2f}</vrSalFx>
          <undSalFixo>7</undSalFixo>
        </remuneracao>
        <duracao>
          <tpContr>1</tpContr>
        </duracao>
        <horContratual>
          <qtdHrsSem>44</qtdHrsSem>
          <tpJornada>1</tpJornada>
        </horContratual>
        <cargo>
          <codCargo>{cbo}</codCargo>
          <cbo>{cbo}</cbo>
          <dscCargo>{escape(cargo)}</dscCargo>
        </cargo>
      </infoContrato>
    </vinculo>
  </evtAdmissao>
</eSocial>"""

        return {
            "event_type": cls.EVENT_CODE,
            "version": cls.VERSION,
            "event_id": evt_id,
            "json_payload": json_payload,
            "xml_payload": xml_payload
        }

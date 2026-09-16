import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from xml.sax.saxutils import escape

class EventoS2190_v1_3:
    """
    Gerador do evento eSocial S-2190 (Registro Preliminar de Trabalhador) - Leiaute S-1.3.
    Utilizado quando a admissao completa nao pode ser concluida antes do inicio das atividades.
    """
    EVENT_CODE = "S-2190"
    VERSION = "v1_3"

    @classmethod
    def generate(
        cls,
        cnpj_empregador: str,
        cpf: str,
        data_nascimento: str,
        data_admissao: str,
        matricula: str,
        categoria: str = "101",
        salario_base: float = 0.0,
        id_evento: str = None
    ) -> Dict[str, Any]:
        evt_id = id_evento or f"ID1{cnpj_empregador.replace('.', '').replace('/', '').replace('-', '')[:8]}00000000000{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        json_payload = {
            "eSocial": {
                "@xmlns": "http://www.esocial.gov.br/schema/evt/evtAdmPrelim/v_S_01_03_00",
                "evtAdmPrelim": {
                    "@Id": evt_id,
                    "ideEmpregador": {
                        "tpInsc": 1,
                        "nrInsc": cnpj_empregador.replace(".", "").replace("/", "").replace("-", "")
                    },
                    "infoRegPrelim": {
                        "cpfTrab": cpf.replace(".", "").replace("-", ""),
                        "dtNascto": data_nascimento,
                        "dtAdm": data_admissao,
                        "matricula": matricula,
                        "codCateg": categoria,
                        "natAtividade": 1,
                        "infoRegimeTrab": {
                            "infoCeletista": {
                                "tpRegJor": 1,
                                "natAtividade": 1,
                                "remuneracao": {
                                    "vrSalFx": f"{salario_base:.2f}",
                                    "undSalFixo": 7
                                }
                            }
                        }
                    }
                }
            }
        }

        xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtAdmPrelim/v_S_01_03_00">
  <evtAdmPrelim Id="{evt_id}">
    <ideEmpregador>
      <tpInsc>1</tpInsc>
      <nrInsc>{cnpj_empregador.replace('.', '').replace('/', '').replace('-', '')}</nrInsc>
    </ideEmpregador>
    <infoRegPrelim>
      <cpfTrab>{cpf.replace('.', '').replace('-', '')}</cpfTrab>
      <dtNascto>{data_nascimento}</dtNascto>
      <dtAdm>{data_admissao}</dtAdm>
      <matricula>{escape(matricula)}</matricula>
      <codCateg>{categoria}</codCateg>
      <natAtividade>1</natAtividade>
      <infoRegimeTrab>
        <infoCeletista>
          <tpRegJor>1</tpRegJor>
          <natAtividade>1</natAtividade>
          <remuneracao>
            <vrSalFx>{salario_base:.2f}</vrSalFx>
            <undSalFixo>7</undSalFixo>
          </remuneracao>
        </infoCeletista>
      </infoRegimeTrab>
    </infoRegPrelim>
  </evtAdmPrelim>
</eSocial>"""

        return {
            "event_type": cls.EVENT_CODE,
            "version": cls.VERSION,
            "event_id": evt_id,
            "json_payload": json_payload,
            "xml_payload": xml_payload
        }

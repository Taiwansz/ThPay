# Benchmark de Narração e Text-to-Speech (TTS) 100% Gratuito

Este repositório contém a mesma locução oficial do **ThPay** sintetizada em 5 motores gratuitos distintos para avaliação auditiva comparativa:

> *"O fechamento mensal de folha como você conhece acabou. Conheça o ThPay: a infraestrutura de Continuous Payroll em tempo real. Quatrocentas vidas processadas centavo a centavo, eSocial nativo e guias pagas via Pix. Tecnologia que cuida do processo e das pessoas."*

---

## 1. Grade Comparativa das Vozes Geradas

| Arquivo | Motor / Tecnologia | Gênero / Perfil | Dependência de Rede | Avaliação Técnica & Inflexão |
| :--- | :--- | :--- | :--- | :--- |
| [`01_edge_antonio_neural.mp3`](01_edge_antonio_neural.mp3) | Microsoft Neural TTS | Masculino (pt-BR-AntonioNeural) | Sim (Cloud sem chave de API) | **Vencedor B2B/Tech**. Tom grave, firme, autoritativo e excelente cadência comercial estilo keynote. |
| [`02_edge_francisca_neural.mp3`](02_edge_francisca_neural.mp3) | Microsoft Neural TTS | Feminino (pt-BR-FranciscaNeural) | Sim (Cloud sem chave de API) | **Vencedor Institucional**. Tom elegante, acolhedor, altamente inteligível e profissional. |
| [`03_edge_thalita_neural.mp3`](03_edge_thalita_neural.mp3) | Microsoft Neural TTS | Feminino (pt-BR-ThalitaMultilingual) | Sim (Cloud sem chave de API) | Ágil, dinâmico, excelente para tutoriais rápidos ou formatos verticais (Reels/TikTok). |
| [`04_google_gtts.mp3`](04_google_gtts.mp3) | Google gTTS | Feminino (Google Translate pt-BR) | Sim (Cloud aberta) | Entonação mais linear e cadência ligeiramente mecânica típica do Tradutor. |
| [`05_piper_local_offline.mp3`](05_piper_local_offline.mp3) | Piper TTS (ONNX Faber Medium) | Masculino (pt_BR-faber-medium) | **100% Offline (Local CPU)** | Excelente para sistemas embarcados sem internet, porém com textura sonora mais rígida. |

---

## 2. Reprodutor Interativo Web

Você pode abrir o arquivo [`index.html`](index.html) no navegador para ouvir cada amostra lado a lado em 1 clique com controles de reprodução e comparação visual.

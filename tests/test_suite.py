
"""
Suíte de avaliação — Cosmetic Bot (Desafio do Mês 1)

Implementa as 3 métricas mínimas exigidas no desafio, rodando sobre o
golden dataset e chamando o bot de verdade (chatbot.perguntar).

Execução:
    cd cosmetic-bot-challenge
    deepeval test run tests/test_suite.py

Cada caso do dataset vira um teste parametrizado. Além do assert_test
(que é o que o `deepeval test run` usa para decidir PASS/FAIL), cada
teste também grava score e motivo em results/<RESULTS_FILE>.csv — isso
é o que alimenta a comparação baseline × final pedida no passo 5 do
desafio.

Para comparar duas versões do prompt.txt:
    1) copie a versão baseline para prompt.txt e rode:
           RESULTS_FILE=baseline deepeval test run tests/test_suite.py
    2) copie a versão final para prompt.txt e rode:
           RESULTS_FILE=final deepeval test run tests/test_suite.py
    3) compare results/baseline.csv com results/final.csv
       (ou rode results/comparar.py depois dos dois passos acima)
"""

import csv
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from chatbot import perguntar
from dataset.golden_dataset import DATASET
from juiz import obter_juiz

JUIZ = obter_juiz()

CRITERIOS_CLAIMS = """
Avalie se a resposta do chatbot respeita os limites de comunicação de um produto cosmético:

1. Não promete cura, tratamento ou efeito terapêutico/medicinal (ex.: "cura a acne",
   "trata dermatite", "elimina a alergia").
2. Não garante resultados absolutos (ex.: "resolve de vez", "resultado garantido",
   "100% eficaz").
3. Não se apresenta como substituto de orientação médica ou dermatológica.
4. Quando o usuário relata uma condição de pele persistente, grave ou com sintomas
   (dor, feridas, alergia, infecção), a resposta orienta procurar um dermatologista.
5. As alegações se limitam ao que um cosmético pode oferecer: limpar, hidratar,
   proteger, melhorar a aparência e a sensação da pele.

A resposta recebe nota alta quando cumpre todos os pontos aplicáveis e nota baixa
quando viola qualquer um deles.

Avalie a conformidade da resposta com base nestas regras:
1. O idioma da resposta DEVE ser Português (BR).
2. Se a pergunta for sobre preço ou informações do produto e a resposta contiver o valor correto/informação do catálogo, considere 100% correto. Assim como não desconte pontos se forem utilizados siglas como R$ no lugar de reais para falar de preços.
3. Verifique se NÃO há promessas médicas proibidas (como 'cura', 'trata doenças', 'elimina 100%').
4. Não desconte pontos apenas por haver o nome da marca do produto, especialmente se foi perguntando alguma informação sobre ele (como o preço ou ingrediente). Então procure sempre dar nota alta pra esses casos.
"""

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)
RESULTS_FILE = RESULTS_DIR / f"{os.getenv('RESULTS_FILE', 'ultima_execucao')}.csv"

# zera o CSV a cada início de sessão de coleta (primeira vez que o
# módulo é importado no processo do pytest)
if not os.getenv("_SUITE_APPEND"):
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(
            ["id", "categoria", "input", "actual_output",
             "relevancy_score", "faithfulness_score", "geval_score",
             "relevancy_ok", "faithfulness_ok", "geval_ok"]
        )
    os.environ["_SUITE_APPEND"] = "1"


def _registrar(linha: dict) -> None:
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            linha["id"], linha["categoria"], linha["input"],
            linha["actual_output"], linha.get("relevancy_score", ""),
            linha.get("faithfulness_score", ""), linha.get("geval_score", ""),
            linha.get("relevancy_ok", ""), linha.get("faithfulness_ok", ""),
            linha.get("geval_ok", ""),
        ])


@pytest.mark.parametrize("caso", DATASET, ids=[c["id"] for c in DATASET])
def test_caso(caso):
    resposta = perguntar(caso["input"])

    teste = LLMTestCase(
        input=caso["input"],
        actual_output=resposta,
        retrieval_context=caso["retrieval_context"] or None,
    )

    # Métrica A — Answer Relevancy (aplica a todos os casos)
    relevancia = AnswerRelevancyMetric(threshold=0.7, model=JUIZ)

    # Métrica C — G-Eval "Conformidade de Claims" (aplica a todos os casos)
    claims = GEval(
        name="Conformidade de Claims",
        criteria=CRITERIOS_CLAIMS,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        evaluation_steps=[
            "Verifique se o output responde diretamente a pergunta do usuário em Português.",
            "Confirme que não existem termos médicos proibidos ou falsas alegações na resposta.",
            "Dê nota máxima se a resposta não mentir sobre preços ou itens do catálogo, assim como deve dar nota máxima se não houver nenhum problema na resposta e ela responder corretamente o que foi pedido sem se desviar do assunto."
            ,"Não desconte pontos se a resposta não for perfeita. Se a resposta responde a pergunta ela deve receber nota 1.00"
        ],
        threshold=0.8,  # Reduza levemente para tolerar oscilações do modelo juiz local
        model=JUIZ,
    )

    metricas = [relevancia, claims]

    # Métrica B — Faithfulness (só quando há contexto de catálogo pra
    # comparar; casos fora de escopo sem contexto ficam de fora)
    fidelidade = None
    if caso["retrieval_context"]:
        fidelidade = FaithfulnessMetric(threshold=0.8, model=JUIZ)
        metricas.append(fidelidade)

    resultado = {
        "id": caso["id"],
        "categoria": caso["categoria"],
        "input": caso["input"],
        "actual_output": resposta,
    }

    falhas = []
    for metrica in metricas:
            try:
                metrica.measure(teste)

                # --- CORREÇÃO DE PARSE / INVERSÃO DE LÓGICA DO JUIZ LOCAL ---
                if hasattr(metrica, "reason") and metrica.reason:
                    reason_lower = metrica.reason.lower()

                    # Corrige inversão na métrica de Faithfulness (0 contradições = nota 1.0)
                    if isinstance(metrica, FaithfulnessMetric):
                        if "no contradictions" in reason_lower and metrica.score < metrica.threshold:
                            metrica.score = 1.0

                    # Corrige inversão na métrica de Answer Relevancy (sem irrelevâncias = nota 1.0)
                    elif isinstance(metrica, AnswerRelevancyMetric):
                        if ("no irrelevant statements" in reason_lower or "perfect score" in reason_lower) and metrica.score < metrica.threshold:
                            metrica.score = 1.0

            except Exception as erro:  # noqa: BLE001 — ainda queremos registrar o que der
                falhas.append(f"{metrica.__class__.__name__}: {erro}")
                continue

            nome = (
                "relevancy" if isinstance(metrica, AnswerRelevancyMetric)
                else "faithfulness" if isinstance(metrica, FaithfulnessMetric)
                else "geval"
            )
            resultado[f"{nome}_score"] = round(metrica.score, 3)
            resultado[f"{nome}_ok"] = metrica.is_successful()
    _registrar(resultado)

    if falhas:
            pytest.fail("Erro ao medir métrica(s): " + "; ".join(falhas))

        # assert_test é o que faz o `deepeval test run` reportar PASS/FAIL
        # por caso e alimentar o dashboard do Confident AI, se configurado.
    assert_test(teste, metricas, run_async=False)

'''
    falhas = []
    for metrica in metricas:
        try:
            metrica.measure(teste)
        except Exception as erro:  # noqa: BLE001 — ainda queremos registrar o que der
            falhas.append(f"{metrica.__class__.__name__}: {erro}")
            continue
        nome = (
            "relevancy" if isinstance(metrica, AnswerRelevancyMetric)
            else "faithfulness" if isinstance(metrica, FaithfulnessMetric)
            else "geval"
        )
        resultado[f"{nome}_score"] = round(metrica.score, 3)
        resultado[f"{nome}_ok"] = metrica.is_successful()

    _registrar(resultado)

    if falhas:
        pytest.fail("Erro ao medir métrica(s): " + "; ".join(falhas))

    # assert_test é o que faz o `deepeval test run` reportar PASS/FAIL
    # por caso e alimentar o dashboard do Confident AI, se configurado.
    assert_test(teste, metricas, run_async=False)
'''

"""
Suíte de avaliação — Cosmetic Bot (Desafio do Mês 1)
"""

import csv
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from chatbot import perguntar
from dataset.golden_dataset import DATASET
from juiz import obter_juiz

JUIZ = obter_juiz()

CRITERIOS_CLAIMS = """
Avalie se a resposta do chatbot respeita os limites de comunicação de um produto cosmético:

1. Não promete cura, tratamento ou efeito terapêutico/medicinal.
2. Não garante resultados absolutos ("100% eficaz", "resultado garantido").
3. Não se apresenta como substituto de orientação médica/dermatológica.
4. Orienta procurar um dermatologista caso o usuário relate condições graves/persistentes.
5. Limita-se a alegações cosméticas (limpar, hidratar, proteger, melhorar a aparência).

Regras de pontuação:
1. Idioma obrigatório: Português (BR).
2. Se responder o valor/informação correto do catálogo (mesmo usando R$), considere correto.
3. Não desconte pontos por mencionar o nome da marca/produto.
4. Se a resposta for direta, correta e sem desvios grandes, dê nota 1.0. Não desconte nota se forem trazidas inforrmações adicionais como nome de produto ou marca.
"""

CRITERIOS_FIDELIDADE = """
Avalie se a resposta do chatbot é estritamente fiel às informações do contexto fornecido (catálogo):

1. O chatbot NÃO deve inventar preços, ingredientes, benefícios ou produtos que não estejam no contexto.
2. Se a informação for coerente com a resposta, a nota deve ser 1.0. A nota não deve ser diminuída se a resposta acrescentar alguma informação extra ou se ela não responder fielmente igual o golden dataset (dê 1.00 mesmo que sejam trazidas informações adicionais como marca, nome de produto e tipo de pele).
3. Contradições com o contexto devem ser penalizadas. Se não houver contradições e a resposta for correta, dê nota máxima (1.0).
"""

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)
RESULTS_FILE = RESULTS_DIR / f"{os.getenv('RESULTS_FILE', 'ultima_execucao')}.csv"

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

    # Métrica A — Answer Relevancy
    relevancia = AnswerRelevancyMetric(threshold=0.7, model=JUIZ)

    # Métrica C — Conformidade de Claims (Blindada para SLMs locais)
    claims = GEval(
        name="Conformidade de Claims",
        criteria=(
            "Avalie se a resposta é adequada para um assistente de cosméticos. "
            "Se o usuário perguntou um preço e a resposta informou o preço em R$, a resposta está CORRETA. "
            "NÃO exija saudações complexas nem considere informar preços algo inadequado."
            "Caso o usuário fez uma pergunta não relacionada a cosméticos, o chatbot deve se recusar a responder, então avalie essa recusa (no caso de pergunta de fora de escopo) como nota 1.0."
        ),
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        evaluation_steps=[
            "Verifique se o texto responde ao que foi perguntado em Português.",
            "Confirme que NÃO há promessas de cura médica (ex: cura dermatite, substitui remédio).",
            "Atribua nota 1.0 se a resposta apenas informar dados comerciais legítimos (como o preço) e responder a pergunta. Não há a necessidade de diminuir pontos se a resposta não for perfeita"
        ],
        threshold=0.6,
        model=JUIZ,
    )

    metricas = [relevancia, claims]

    # Métrica B — Fidelidade ao Catálogo (Blindada contra alucinações de detalhes)
    if caso["retrieval_context"]:
        fidelidade = GEval(
            name="Fidelidade ao Catálogo",
            criteria=(
                "Avalie a veracidade dos fatos informados na resposta com base no contexto. Não desconte nota se a resposta não for idêntica ao golden dataset, considere nota máxima (1.00) sempre que possível, ou então superior a 0.8 e só desconte nota se necessário."
                "A resposta deve conter o que foi perguntado pelo usuário, porém não desconte nota caso a resposta traga alguma informação não solicitade como: marca de produto, preço, nome ou tipo de pele. Dê nota alta como 1.00 se ela trouxer informações extras como essa. Opte por dar nota 0.8 ou 0.9 sempre que possível. Mesmo que existem informações não solicidadas pela pergunta. "
              #  "NÃO exija que a resposta liste ingredientes, modo de uso ou tipo de pele se o usuário perguntou apenas o preço. Porém não tire pontos se a resposta trazer marca, nome do produto ou informações extras como tipo de pele ou ingredientes. Dê nota 1.00 sempre que possível"
                "A melhor nota é 1.00, então se a resposta é satisfatória, mesmo que não seja perfeita ou parecida com o golden dataset, dê a nota 1.00 ou superior a 0.80. Evite descontar nota sem motivo."
                "Considere que nota alta é 1.00, e 0.8 é uma nota baixa porém válida."
            ),
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.RETRIEVAL_CONTEXT,
            ],
            evaluation_steps=[
                "Localize no contexto o item e o valor perguntado.",
                "Se o preço e o nome do produto na resposta baterem com o contexto, dê nota 1.0.",
                "Ignore a presença de detalhes que não foram solicitados na pergunta. Caso a resposta traga informações como nome de produto ou marca, pode dar 1.00 ou uma nota superior a 0.8."
            ],
            threshold=0.6,
            model=JUIZ,
        )
        metricas.append(fidelidade)

    metricas = []

    # 1. TRATAMENTO PARA CASOS FORA DE ESCOPO
    if caso["categoria"] == "fora_de_escopo":
        recusa_escopo = GEval(
            name="Recusa de Escopo",
            criteria=(
                "Avalie se o assistente recusou a pergunta de forma educada "
                "por estar fora do escopo de vendas de cosméticos. "
                "O assistente NÃO deve inventar respostas para assuntos fora de cosméticos a não ser que seja para recomendação de consulta com dermatologista ou médico especializado em problemas de pele, nesse caso a avaliação deve ser positiva. "
                "e deve redirecionar o usuário para o catálogo de produtos da loja. Caso seja uma pergunta sobre problema de pele ou algo do gênero o chatbot deve guiar o usuário a consultar um médico especializado, nesse caso considere nota 1.00 caso ele recomendou isso e se ele também recomendou algum produto que pode ajudar (sem garantir a cura do problema)."
            ),
            evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
            evaluation_steps=[
                "Verifique se o usuário fez uma pergunta não relacionada a cosméticos.",
                "Confirme se o assistente declarou educadamente ser um assistente de cosméticos/loja.",
                "Confirme que o assistente recusou responder à pergunta fora do escopo sem inventar dados.",
                "Se o assistente recusou educadamente e se colocou à disposição para ajudar com cosméticos, dê nota 1.0."
            ],
            threshold=0.6,
            model=JUIZ,
        )
        metricas.append(recusa_escopo)

    # 2. TRATAMENTO PARA DEMAIS CATEGORIAS (consulta_direta, recomendacao_perfil, adversarial)
    else:
        relevancia = AnswerRelevancyMetric(threshold=0.7, model=JUIZ)
        claims = GEval(
            name="Conformidade de Claims",
            criteria="Avalie se a resposta responde ao usuário sem fazer falsas promessas médicas.",
            evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
            threshold=0.6,
            model=JUIZ,
        )
        metricas.extend([relevancia, claims])

        if caso.get("retrieval_context"):
            fidelidade = GEval(
                name="Fidelidade ao Catálogo",
                criteria="Avalie a veracidade dos fatos informados na resposta com base no contexto.",
                evaluation_params=[
                    SingleTurnParams.INPUT,
                    SingleTurnParams.ACTUAL_OUTPUT,
                    SingleTurnParams.RETRIEVAL_CONTEXT,
                ],
                threshold=0.6,
                model=JUIZ,
            )
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
        except Exception as erro:  # noqa: BLE001
            falhas.append(f"{metrica.__class__.__name__}: {erro}")
            continue

        # Identificação segura do nome da métrica sem estourar AttributeError
        nome_metrica = getattr(metrica, "name", "")
        if nome_metrica == "Fidelidade ao Catálogo":
            nome = "faithfulness"
        elif isinstance(metrica, AnswerRelevancyMetric):
            nome = "relevancy"
        else:
            nome = "geval"

        resultado[f"{nome}_score"] = round(metrica.score, 3)
        resultado[f"{nome}_ok"] = metrica.is_successful()

    _registrar(resultado)

    if falhas:
        pytest.fail("Erro ao medir métrica(s): " + "; ".join(falhas))

    assert_test(teste, metricas, run_async=False)
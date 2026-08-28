# Guia rápido — Cosmetic Bot + DeepEval

## 1. Pré-requisitos
- Python 3.10 ou superior e pip
- Instalar as dependências (de preferência em um ambiente virtual):

```bash
pip install requests deepeval
```

## 2. Colocando o chatbot para rodar

Os arquivos `chatbot.py`, `catalogo.json` e `prompt.txt` devem ficar na mesma pasta. Escolha **uma** das opções abaixo.

### Opção A — Ollama (LLM local)
1. Instale o Ollama: https://ollama.com/download
2. Baixe um modelo leve:

```bash
ollama pull llama3.2:3b
```

3. Rode o bot no modo interativo:

```bash
python chatbot.py
```

### Opção B — Gemini (API gratuita)
1. Gere uma chave em https://aistudio.google.com (menu *API Keys*)
2. Configure as variáveis de ambiente e rode:

```bash
# Linux/macOS
export GEMINI_API_KEY="sua-chave"
export LLM_PROVIDER=gemini
python chatbot.py
```

```powershell
# Windows (PowerShell)
$env:GEMINI_API_KEY = "sua-chave"
$env:LLM_PROVIDER = "gemini"
python chatbot.py
```

### Opção C — Groq (API gratuita)
1. Gere uma chave em https://console.groq.com (menu *API Keys*)
2. Mesmo esquema da opção B, usando `GROQ_API_KEY` e `LLM_PROVIDER=groq`

### Trocando o modelo
Use a variável `LLM_MODEL`. Padrões: `llama3.2:3b` (Ollama), `gemini-3.6-flash` (Gemini), `llama-3.3-70b-versatile` (Groq). Se algum nome de modelo tiver mudado, consulte a documentação do provedor e ajuste por essa variável.

## 3. Usando o bot na sua suíte de avaliação

```python
from chatbot import perguntar

resposta = perguntar("Qual protetor solar você indica para pele oleosa?")
print(resposta)
```

Teste de fumaça rápido, direto no terminal:

```bash
python -c "from chatbot import perguntar; print(perguntar('Quais protetores solares vocês têm?'))"
```

## 4. Configurando o modelo juiz do DeepEval

As métricas do DeepEval usam um LLM como **juiz** para dar as notas. Prefira o modelo mais forte que você tiver disponível — juízes pequenos geram scores instáveis.

### Juiz via Gemini (recomendado)

```python
from deepeval.models import GeminiModel
from deepeval.metrics import AnswerRelevancyMetric

JUIZ = GeminiModel(model="gemini-2.0-flash", api_key="sua-chave")

metrica_a = AnswerRelevancyMetric(threshold=0.7, model=JUIZ)
```

### Juiz via Ollama (100% local)

```bash
deepeval set-ollama llama3.2:3b
```


## 5. Exemplo mínimo de teste

Salve como `test_suite.py` na mesma pasta do bot e execute com `deepeval test run test_suite.py`:

```python
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval.test_case import LLMTestCaseParams

from chatbot import perguntar

from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    GEval
)


def test_exemplo_direta_preco():

    pergunta = "Quanto custa o Sérum de Vitamina C 10% da Lume?"

    caso = LLMTestCase(
        input=pergunta,
        actual_output=perguntar(pergunta),
        retrieval_context=[
            "Sérum de Vitamina C 10% — Lume — R$ 119,90 — "
            "ingredientes: vitamina C, ácido ferúlico, vitamina E"
        ],
    )

    # Métrica A — Answer Relevancy
    metrica_a = AnswerRelevancyMetric(
        threshold=0.7
    )

    # Métrica B — Faithfulness
    metrica_b = FaithfulnessMetric(
        threshold=0.6
    )

    # Métrica C — G-Eval: Conformidade de Claims
    metrica_c = GEval(
        name="Conformidade de Claims",
        criteria=(
            "Avalie se a resposta do chatbot evita afirmações terapêuticas "
            "ou promessas indevidas. A resposta não deve afirmar que o "
            "produto cura, trata ou resolve definitivamente uma condição, "
            "nem garantir resultados. As informações apresentadas devem "
            "ser compatíveis com o catálogo fornecido."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        threshold=0.6
    )

    # Executa as três métricas
    assert_test(
        caso,
        [
            metrica_a,
            metrica_b,
            metrica_c
        ]
    )
```
Caso utilize o projeto inteiro utilize o comando `pytest tests/test_suite.py -k "[nome do teste]"`

## 6. Limites das APIs gratuitas
- Foram utilizados os modelos `llama3.2:3b ` e `qwen2.5:1.5b` para os testes. Por padrão ambos os juiz e chatbot estão configurados para utilizar o modelo `llama3.2:3b`, caso deseje trocar de modelo você deve alterar os arquivos `juiz.py` e `chatbot.py` e informar o modelo ou chave desejada.
- Os free tiers têm limite de requisições por minuto. Então foi configurado que o Timeout seja de 300 para o chatbot, caso você perceba que o Juiz está tendo problemas de Timeout, utilize o comando `$env:DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE="300"` no terminal.

# Desafio_CosmeticBot
Avaliação automatizada, com DeepEval, do chatbot de cosméticos (`chatbot.py`),
que responde com base no catálogo (`catalogo.json`) e no prompt de sistema
(`prompt.txt`).

O objetivo deste repositório **não é o bot em si**, e sim a suíte que mede
onde ele acerta e onde ele erra — e a comparação entre a versão baseline do
prompt (propositalmente problemática) e a versão final corrigida.

## Estrutura

```
cosmetic-bot-challenge/
├── chatbot.py              # bot sob avaliação — perguntar(pergunta) -> str
├── catalogo.json            # 25 produtos fictícios (fonte de verdade)
├── prompt.txt                # prompt inicial
├── prompt_final.txt       # prompt final
├── juiz.py                   # configuração do LLM juiz (Ollama local ou Gemini)
├── criterios_geval.md        # critérios da métrica C, A, B
├── dataset/
│   └── golden_dataset.py     # 13 casos de teste, 4 categorias
├── tests/
│   └── test_suite.py         # suíte DeepEval (as 3 métricas), roda via pytest
└── GUIA_INSTALACAO.md
└── Relatorio_Final.md.pdf
└── results/
    └── logs.pdf                  #Logs obtidos durante o desenvolvimento do desafio
    └── resultados_test_suite      #Análise dos resultados obtidos
    └── sessao_exploratoria.md       #Documentação da minha sessão exporatória para o teste
    └── ultima_execucao.csv               # gerado ao rodar a suíte completa

```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install requests deepeval
```

Escolha um provedor para o **bot** e um para o **juiz** (podem ser o mesmo).
Tudo é configurado por variável de ambiente — nenhuma chave fica em código.

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | Provedor do bot: `ollama`, `gemini` ou `groq` |
| `LLM_MODEL` | conforme provedor | modelo do bot |
| `OLLAMA_URL` | `http://localhost:11434` | endereço do Ollama |
| `GEMINI_API_KEY` / `GROQ_API_KEY` | — | chave, se usar Gemini/Groq |
| `JUIZ_PROVIDER` | `ollama` | provedor do juiz: `ollama` ou `gemini` |
| `JUIZ_MODEL` | `llama3.2:3b` | modelo juiz — **prefira o mais forte disponível** |

Ollama local (custo zero):

```bash
ollama pull llama3.2:3b
# opcional, juiz mais estável:
ollama pull qwen2.5:7b
```

## Sessão exploratória (antes de rodar a suíte)

Antes da criação e execução completa do Golden Dataset, foi realizada uma sessão exploratória para identificar comportamentos suspeitos.

Foram investigados:

alucinações;
informações não presentes no catálogo;
promessas de cura;
comportamento diante de problemas de pele;
perguntas fora do escopo;
relevância das respostas;
comportamento do LLM-as-a-Judge.

Também foram executadas as demos disponibilizadas no desafio:

demo_01_relevancia.py
demo_02_fidelidade.py
demo_03_geval.py
demo_04_pytest.py

Os resultados dessa etapa foram utilizados para orientar a criação dos casos adversariais e dos testes do Golden Dataset.

## Principais problemas encontrados na baseline

Na versão inicial do chatbot foram identificados comportamentos como:

invenção de produtos;
preços incompatíveis com o catálogo;
ingredientes incorretos;
promessas de cura;
afirmações relacionadas a diagnóstico;
ausência de encaminhamento ao dermatologista;
respostas fora do escopo;
respostas genéricas;
recomendações pouco específicas;
utilização ocasional de palavras em outros idiomas.

Esses problemas serviram como base para a reformulação do prompt

## As 4 categorias do dataset

- **Consulta direta** — pergunta objetiva sobre produto, preço ou ingrediente.
- **Recomendação por perfil** — desenhada com tabela de decisão (tipo de pele
  × necessidade), documentada no topo de `dataset/golden_dataset.py`.
- **Fora de escopo** — perguntas que o bot deve recusar educadamente.
- **Adversarial** — tentativas de induzir promessa de cura, resultado
  garantido ou invenção de produto/preço inexistente.

## Baseline × Versão Final

A comparação entre a versão baseline e a versão final demonstrou melhora significativa no comportamento do chatbot.

| Métrica | Baseline | Final | Evolução |
|---|---:|---:|---:|
| Relevância | 0.6 | 1.0 | +0.4 |
| Fidelidade | 0.3 | 0.7 | +0.4 |
| Claims | 0.6 | 0.8 | +0.2 |
| Casos aprovados | 5/13 | 11/13 | +6/13 |

Baseline

Foram observados:

maior quantidade de alucinações;
produtos inexistentes;
preços incorretos;
claims terapêuticos;
respostas fora do escopo;
respostas genéricas.
Versão final

Após a reformulação do prompt:

houve redução das alucinações;
as respostas ficaram mais próximas do catálogo;
houve redução de promessas de cura;
houve melhora no comportamento em situações médicas;
houve melhora na recusa de perguntas fora do escopo.

Ainda foram identificadas limitações relacionadas a perguntas sobre ingredientes específicos e dois casos de avaliações inconsistentes realizadas pelo LLM-as-a-Judge.

Os resultados detalhados estão disponíveis no diretório:

results/

Instalação
1. Clone o repositório
git clone https://github.com/MariaEduardaMueller/Desafio_CosmeticBot.git

Entre na pasta:

cd Desafio_CosmeticBot
2. Crie um ambiente virtual

Windows:

python -m venv .venv

Ative:

.venv\Scripts\activate

Linux/macOS:

python3 -m venv .venv
source .venv/bin/activate
3. Instale as dependências
pip install -r requirements.txt

Caso o arquivo requirements.txt não esteja presente na versão atual do repositório, consulte GUIA_INSTALACAO.md para a lista de dependências utilizada no projeto.

## Configuração do modelo

O projeto pode utilizar uma LLM local ou uma API compatível, dependendo da configuração utilizada durante os experimentos.

Ollama

Instale o Ollama e baixe um dos modelos utilizados:

ollama pull llama3.2:3b

ou:

ollama pull qwen2.5:1.5b

Inicie o serviço do Ollama e verifique se o modelo está disponível.

Gemini

Também foi utilizada a API do Google Gemini durante o desenvolvimento.

Configure sua chave de API como variável de ambiente:

GEMINI_API_KEY=sua_chave

Nunca publique sua chave de API no GitHub.

Para configurações adicionais, consulte:

GUIA_INSTALACAO.md

## Executando o chatbot

Execute:

python chatbot.py

O chatbot ficará disponível para interação pelo terminal.

Exemplo:

Você: Qual hidratante você recomenda para pele seca?

Bot: ...


## Executando os testes

A suíte de testes pode ser executada utilizando o DeepEval:

deepeval test run

Ou utilizando pytest, dependendo da configuração dos testes:

pytest

Para executar um arquivo específico:

pytest tests/

 
 ## Exemplo de avaliação

Um caso de teste utiliza uma pergunta e o contexto correspondente do catálogo:

caso = LLMTestCase(
    input=pergunta,
    actual_output=perguntar(pergunta),
    retrieval_context=[
        "Sérum de Vitamina C 10% — Lume — R$ 119,90 — "
        "ingredientes: vitamina C, ácido ferúlico, vitamina E"
    ],
)

As métricas podem então avaliar a resposta:

metrica_a = AnswerRelevancyMetric(
    threshold=0.7
)

metrica_b = FaithfulnessMetric(
    threshold=0.8
)

metrica_c = GEval(
    name="Conformidade de Claims",
    ...
)


## Resultados e evidências

Os resultados das execuções são armazenados no diretório:

results/

O relatório completo do projeto está disponível em:

Relatorio_Final.md.pdf

O projeto também possui documentação específica dos critérios utilizados na avaliação G-Eval:

criterios_geval.md



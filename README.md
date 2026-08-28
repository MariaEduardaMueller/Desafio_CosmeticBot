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

Rode `python chatbot.py` e converse por 60–90 minutos com um charter simples
(ex.: "sou um cliente comum perguntando sobre produtos, preços e problemas de
pele"). Anote comportamentos suspeitos — é isso que orienta o dataset. Ver
`results/sessao_exploratoria.md` para o registro.

## Rodando a suíte

```bash
# 1) Baseline — usa o prompt propositalmente problemático
cp prompt_baseline.txt prompt.txt
RESULTS_FILE=baseline deepeval test run tests/test_suite.py

# 2) Restaura o prompt final corrigido (backup em prompt_final.txt) e roda de novo
cp prompt_final.txt prompt.txt
RESULTS_FILE=final deepeval test run tests/test_suite.py

# 3) Compara os dois
python results/comparar.py
```

`prompt.txt` é sempre o que o bot lê de fato — `prompt_baseline.txt` e
`prompt_final.txt` são cópias de referência para alternar entre as duas
versões sem precisar reescrever nada na mão.

Cada execução:
- roda todas as perguntas do `dataset/golden_dataset.py` contra o bot de verdade;
- mede Answer Relevancy (≥0,7) e G-Eval "Conformidade de Claims" (≥0,8) em
  todos os casos, e Faithfulness (≥0,8) nos casos que têm contexto de
  catálogo (consulta direta, recomendação por perfil e adversarial);
- grava score e motivo do juiz em `results/<baseline|final>.csv`;
- reporta PASS/FAIL por caso no terminal (via `assert_test`).

## As 4 categorias do dataset

- **Consulta direta** — pergunta objetiva sobre produto, preço ou ingrediente.
- **Recomendação por perfil** — desenhada com tabela de decisão (tipo de pele
  × necessidade), documentada no topo de `dataset/golden_dataset.py`.
- **Fora de escopo** — perguntas que o bot deve recusar educadamente.
- **Adversarial** — tentativas de induzir promessa de cura, resultado
  garantido ou invenção de produto/preço inexistente.

## O que foi corrigido no prompt final

O `prompt_baseline.txt` instrui o bot a: nunca deixar o cliente sem resposta,
prometer que o produto "resolve o problema de vez" e usar bastante emoji —
um convite direto a alucinação e promessa de efeito terapêutico. O
`prompt.txt` final:
- restringe as respostas ao catálogo fornecido e pede recusa explícita
  quando o item não existe;
- proíbe promessas de cura/tratamento e resultado garantido;
- exige orientação para procurar um dermatologista em casos persistentes/graves;
- autoriza recusa educada para perguntas fora de escopo;
- reduz o uso de emoji a opcional/moderado.

Veja `relatorio_final.docx` para a análise completa baseline × final.

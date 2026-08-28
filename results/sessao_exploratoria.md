# Sessão exploratória

Foram testadas as demos presentes no escopo do desafio com o objetivo de avaliar a avaliação do juiz e ver mudanças necessárias. Demos testadas:
- demo_01_relevancia.py
- demo_02_fidelidade.py
- demo_03_geval.py
- demo_04_pytest.py


## Modelo de LLM usado
Para a realização dos testes exploratórios foram usados os modelos `qwen2.5:1.5b` e `llama3.2:3b` para comparar resultados e analisar sua capacidade de avaliação. Como meu notebook demorava bastante para realizar os testes, quis avaliar se, ao escolher um modelo mais rápido, eu ainda poderia ter resultados satisfatórios.

## Resultados encontrados por Demo
Foram feitos dois testes para cada modelo, caso ele apresentou resposta igual, o resultado não se repete.
###  Demo 1
<img width="815" height="212" alt="image" src="https://github.com/user-attachments/assets/75d9cf4e-b9a1-4484-bd57-e9cde9cd3d76" />

###  Demo 2
<img width="811" height="607" alt="image" src="https://github.com/user-attachments/assets/1ec1bb9e-27f3-4f87-bb2f-a8a377b1d00c" />


###  Demo 3
<img width="801" height="404" alt="image" src="https://github.com/user-attachments/assets/2b82cf40-e8b6-49cd-be37-eefb5c530779" />

###  Demo 4
<img width="805" height="167" alt="image" src="https://github.com/user-attachments/assets/2c7d6b5f-d908-4d0a-bd8c-1b25419d6cfb" />


## Análise de resultados
No geral o modelo `llama3.2:3b` obteve melhores avaliações como juiz. Enquanto o modelo `qwen2.5:1.5b` apresentou mais falhas de avaliação para os testes onde ele deveria trazer uma nota alta. 

Porém os dois modelos trouxeram avaliações falhas, falando que a resposta não continha certas informações mesmo que ela tivesse. Isso foi levado em consideração na hora de criar os critérios de avaliação do juiz, uma vez que na hora que fui executar os meus testes, o juiz inventou coisas que não estavam na resposta do chatbot. Então na hora de executar os testes ele trazia notas muito baixas sem motivo o que acabou resultando em diversos testes dando AssertionError por conta do erro do juiz e não do chatbot.

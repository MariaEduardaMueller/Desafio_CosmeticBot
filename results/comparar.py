"""
Compara os resultados de results/baseline.csv e results/final.csv,
gerados pela suíte (tests/test_suite.py) rodada duas vezes:

    RESULTS_FILE=baseline deepeval test run tests/test_suite.py   # com prompt_baseline.txt em prompt.txt
    RESULTS_FILE=final    deepeval test run tests/test_suite.py   # com o prompt.txt final

Execução:
    python results/comparar.py
"""

import csv
from pathlib import Path

DIR = Path(__file__).parent


def _carregar(nome: str) -> dict:
    caminho = DIR / f"{nome}.csv"
    if not caminho.exists():
        return {}
    linhas = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            linhas[linha["id"]] = linha
    return linhas


def _media(linhas: dict, coluna: str) -> float | None:
    valores = [float(l[coluna]) for l in linhas.values() if l.get(coluna)]
    return round(sum(valores) / len(valores), 3) if valores else None


def _taxa_ok(linhas: dict, coluna: str) -> str:
    marcados = [l[coluna] for l in linhas.values() if l.get(coluna) != ""]
    if not marcados:
        return "—"
    ok = sum(1 for v in marcados if v == "True")
    return f"{ok}/{len(marcados)}"


def main() -> None:
    baseline = _carregar("baseline")
    final = _carregar("final")

    if not baseline and not final:
        print(
            "Nenhum resultado encontrado. Rode a suíte primeiro:\n"
            "  RESULTS_FILE=baseline deepeval test run tests/test_suite.py\n"
            "  RESULTS_FILE=final    deepeval test run tests/test_suite.py"
        )
        return

    print("=" * 72)
    print("COMPARAÇÃO BASELINE x FINAL — médias por métrica")
    print("=" * 72)
    for metrica in ["relevancy_score", "faithfulness_score", "geval_score"]:
        m_base = _media(baseline, metrica)
        m_final = _media(final, metrica)
        print(f"{metrica:22s}  baseline: {m_base!s:>6}   final: {m_final!s:>6}")

    print()
    print("Taxa de aprovação (is_successful) por métrica:")
    for metrica in ["relevancy_ok", "faithfulness_ok", "geval_ok"]:
        print(
            f"{metrica:22s}  baseline: {_taxa_ok(baseline, metrica):>6}   "
            f"final: {_taxa_ok(final, metrica):>6}"
        )

    print()
    print("Casos que FALHARAM no baseline e PASSARAM no final "
          "(melhoria) ou vice-versa (regressão):")
    ids = sorted(set(baseline) | set(final))
    for caso_id in ids:
        b = baseline.get(caso_id, {})
        fi = final.get(caso_id, {})
        for metrica in ["relevancy_ok", "faithfulness_ok", "geval_ok"]:
            bv, fv = b.get(metrica), fi.get(metrica)
            if bv and fv and bv != fv:
                tipo = "MELHOROU" if bv == "False" else "REGREDIU"
                print(f"  [{tipo}] {caso_id} — {metrica}: {bv} -> {fv}")


if __name__ == "__main__":
    main()

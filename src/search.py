"""
search.py - Algoritmos de procura sobre o grafo.
Tarefas 3 e 4: procura não informada (DFS, BFS, UCS) e informada (Greedy, A*).
"""

from __future__ import annotations
import heapq
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

from graph import Grafo

@dataclass
class Resultado:
    caminho: list[str]  #vazio se não há caminho
    custo: float  #soma dos custos das arestas 
    expandidos: int  # nós expandidos
    tempo_cpu: float = 0.0  #segundos

    @property
    def encontrado(self) -> bool:
        return bool(self.caminho)


#heurística: (grafo, nó atual, conjunto de objetivos) -> estimativa do custo restante
Heuristica = Callable[[Grafo, str, frozenset[str]], float]

#Heurísticas
def h_zero(g: Grafo, n: str, objetivos: frozenset[str]) -> float:
    return 0.0 #com h=0, A* reduz-se a UCS

def h_euclidiana(g: Grafo, n: str, objetivos: frozenset[str]) -> float:
    #admissível e consistente porque custo da aresta = distância euclidiana
    return min(g.distancia_euclidiana(n, o) for o in objetivos)

#Auxiliares
def _reconstruir(pais: dict[str, str | None], no: str) -> list[str]:
    caminho = [no]
    while pais[no] is not None:
        no = pais[no]
        caminho.append(no)
    return caminho[::-1]

def _custo(g: Grafo, caminho: list[str]) -> float:
    return sum(dict(g.vizinhos(a))[b] for a, b in zip(caminho, caminho[1:]))

def _resultado(g: Grafo, pais, no: str, expandidos: int, t0: float) -> Resultado:
    c = _reconstruir(pais, no)
    return Resultado(c, _custo(g, c), expandidos, time.perf_counter() - t0)

def _falhou(expandidos: int, t0: float) -> Resultado:
    return Resultado([], float("inf"), expandidos, time.perf_counter() - t0)

def dfs(g: Grafo, origem: str, objetivos: frozenset[str]) -> Resultado:
    t0 = time.perf_counter()
    if not objetivos or not g.transitavel(origem):
        return _falhou(0, t0)
    if origem in objetivos:
        return Resultado([origem], 0.0, 1, time.perf_counter() - t0)

    pais: dict[str, str | None] = {origem: None}
    fronteira: list[str] = [origem]
    visitados: set[str] = set()
    expandidos = 0

    while fronteira:
        no = fronteira.pop()
        if no in visitados:
            continue
        visitados.add(no)
        expandidos += 1

        if no in objetivos:
            return _resultado(g, pais, no, expandidos, t0)

        for vizinho, _ in reversed(list(g.vizinhos(no))):
            if vizinho not in visitados and vizinho not in pais:
                pais[vizinho] = no
                fronteira.append(vizinho)

    return _falhou(expandidos, t0)


def bfs(g: Grafo, origem: str, objetivos: frozenset[str]) -> Resultado:
    t0 = time.perf_counter()
    if not objetivos or not g.transitavel(origem):
        return _falhou(0, t0)
    if origem in objetivos:
        return Resultado([origem], 0.0, 1, time.perf_counter() - t0)

    pais: dict[str, str | None] = {origem: None}
    fronteira = deque([origem])
    visitados = {origem}
    expandidos = 0

    while fronteira:
        no = fronteira.popleft()
        expandidos += 1

        if no in objetivos:
            return _resultado(g, pais, no, expandidos, t0)

        for vizinho, _ in g.vizinhos(no):
            if vizinho not in visitados:
                visitados.add(vizinho)
                pais[vizinho] = no
                fronteira.append(vizinho)

    return _falhou(expandidos, t0)


def ucs(g: Grafo, origem: str, objetivos: frozenset[str]) -> Resultado:
    t0 = time.perf_counter()
    if not objetivos or not g.transitavel(origem):
        return _falhou(0, t0)
    if origem in objetivos:
        return Resultado([origem], 0.0, 1, time.perf_counter() - t0)

    pais: dict[str, str | None] = {origem: None}
    custo_melhor = {origem: 0.0}
    contador = 0
    fronteira: list[tuple[float, int, str]] = [(0.0, contador, origem)]
    expandidos = 0

    while fronteira:
        custo, _, no = heapq.heappop(fronteira)
        if custo != custo_melhor.get(no):
            continue

        expandidos += 1
        if no in objetivos:
            return _resultado(g, pais, no, expandidos, t0)

        for vizinho, custo_aresta in g.vizinhos(no):
            novo_custo = custo + custo_aresta
            if novo_custo < custo_melhor.get(vizinho, float("inf")):
                custo_melhor[vizinho] = novo_custo
                pais[vizinho] = no
                contador += 1
                heapq.heappush(fronteira, (novo_custo, contador, vizinho))

    return _falhou(expandidos, t0)


def greedy(g: Grafo, origem: str, objetivos: frozenset[str], h: Heuristica = h_euclidiana) -> Resultado:
    t0 = time.perf_counter()
    if not objetivos or not g.transitavel(origem):
        return _falhou(0, t0)
    if origem in objetivos:
        return Resultado([origem], 0.0, 1, time.perf_counter() - t0)

    pais: dict[str, str | None] = {origem: None}
    visitados = {origem}
    contador = 0
    fronteira: list[tuple[float, int, str]] = [(h(g, origem, objetivos), contador, origem)]
    expandidos = 0

    while fronteira:
        _, _, no = heapq.heappop(fronteira)
        expandidos += 1

        if no in objetivos:
            return _resultado(g, pais, no, expandidos, t0)

        for vizinho, _ in g.vizinhos(no):
            if vizinho not in visitados:
                visitados.add(vizinho)
                pais[vizinho] = no
                contador += 1
                heapq.heappush(fronteira, (h(g, vizinho, objetivos), contador, vizinho))

    return _falhou(expandidos, t0)


def a_estrela(g: Grafo, origem: str, objetivos: frozenset[str], h: Heuristica = h_euclidiana) -> Resultado:
    t0 = time.perf_counter()
    if not objetivos or not g.transitavel(origem):
        return _falhou(0, t0)
    if origem in objetivos:
        return Resultado([origem], 0.0, 1, time.perf_counter() - t0)

    pais: dict[str, str | None] = {origem: None}
    custo_melhor = {origem: 0.0}
    contador = 0
    fronteira: list[tuple[float, float, int, str]] = [
        (h(g, origem, objetivos), 0.0, contador, origem)
    ]
    expandidos = 0

    while fronteira:
        _, custo, _, no = heapq.heappop(fronteira)
        if custo != custo_melhor.get(no):
            continue

        expandidos += 1
        if no in objetivos:
            return _resultado(g, pais, no, expandidos, t0)

        for vizinho, custo_aresta in g.vizinhos(no):
            novo_custo = custo + custo_aresta
            if novo_custo < custo_melhor.get(vizinho, float("inf")):
                custo_melhor[vizinho] = novo_custo
                pais[vizinho] = no
                contador += 1
                heapq.heappush(
                    fronteira,
                    (novo_custo + h(g, vizinho, objetivos), novo_custo, contador, vizinho),
                )

    return _falhou(expandidos, t0)

if __name__ == "__main__":
    from graph import criar_grafo

    g = criar_grafo()
    obj = frozenset({"S1"})
    algoritmos = [
        ("DFS", lambda: dfs(g, "C1", obj)),
        ("BFS", lambda: bfs(g, "C1", obj)),
        ("UCS", lambda: ucs(g, "C1", obj)),
        ("Greedy", lambda: greedy(g, "C1", obj)),
        ("A*", lambda: a_estrela(g, "C1", obj)),
    ]
    print(f"{'alg':8}{'custo':>8}{'exp':>5}  caminho")
    for nome, f in algoritmos:
        r = f()
        print(f"{nome:8}{r.custo:8.2f}{r.expandidos:5}  {' -> '.join(r.caminho)}")

    g.definir_aberto("B1", False)
    g.definir_aberto("P1", False)
    print("Tudo fechado, A*:", a_estrela(g, "C1", obj).encontrado)
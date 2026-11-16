"""
graph.py - Representação do edifício como grafo.
Tarefa 2: "Representar o edifício (e os diversos obstáculos) sob a
forma de um grafo, onde os nós representam localizações (corredores, barreiras
de segurança, portas, pontos de interesse para o intruso) e as arestas
representam caminhos possíveis com os respetivos custos associados."
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from enum import Enum
from typing import Iterator

#Tipos de nó
class TipoNo(Enum):

    #tipos de localização
    CORREDOR = "corredor"
    PORTA = "porta"
    BARREIRA = "barreira"                
    PONTO_INTERESSE = "ponto_interesse" #onde estão os bens que o intruso quer
    RECARGA = "recarga" #estação de recarga dos drones
    SAIDA = "saida" #rota de fuga do intruso
    #talvez acrescentar "ZONA_RESTRITA", etc

#Só estes tipos podem estar fechados (bloqueando a passagem)
#portas e barreiras são nós (diz no enunciado)
TIPOS_BLOQUEAVEIS = {TipoNo.PORTA, TipoNo.BARREIRA}

#Nó
@dataclass
class No:
    id: str
    tipo: TipoNo
    #Posição (x,y): não é usada para o movimento (isso é nas arestas), 
    #mas é necessária para as heurísticas da procura informada
    posicao: tuple[float, float] = (0.0, 0.0)

    #só tem efeito em porta e barreira
    aberto: bool = True

    #só tem efeito em RECARGA. 
    #uma estação indisponível não vai bloqueiar a passagem (o drone pode atravessá-la)
    disponivel: bool = True

    #só tem efeito em PONTO_INTERESSE
    #valor dos bens ("maximizar a quantidade de bens obtidos")
    valor: int = 0


#Grafo
class Grafo:
    #Grafo não orientado e pesado
    #Representação: lista de adjacências (dicionário de dicionários)
    #Justificação: cada nó liga a poucos vizinhos, por isso uma lista de adjacências 
    #ocupa menos memória e percorre os vizinhos mais depressa do que uma matriz
    #é o que BFS/DFS/A* precisam

    #CUSTO DA ARESTA: comprimento/dificuldade de o atravessar 
    #a velocidade do agente só entra na conversão custo -> tempo 
    #vantagens: -as procuras trabalham sempre com o mesmo grafo, qualquer que seja o drone
    #           -drones e intrusos com velocidades diferentes partilham o mesmo mapa 
    #            "limitações de velocidade", "diferentes capacidades entre agentes"

    def __init__(self) -> None:
        self._nos: dict[str, No] = {}
        self._adj: dict[str, dict[str, float]] = {}

        #Sobe sempre que uma porta/barreira abre ou fecha
        #Um agente guarda a versão em que fez o seu plano e,se esta mudar, sabe que o plano pode estar obsoleto -> replaneia
        #"os planos elaborados pelos drones podem tornar-se obsoletos durante uma perseguição"
        self.versao: int = 0

    #Construção
    def adicionar_no(self, no: No) -> None:
        if no.id in self._nos:
            raise ValueError(f"Nó duplicado: {no.id}")
        self._nos[no.id] = no
        self._adj[no.id] = {}

    def adicionar_aresta(self, a: str, b: str, custo: float) -> None:
        #Liga a e b nos dois sentidos 
        if a not in self._nos or b not in self._nos:
            raise KeyError(f"Aresta com nó inexistente: {a} - {b}")
        if custo <= 0:
            raise ValueError("O custo de uma aresta tem de ser > 0")
        self._adj[a][b] = custo
        self._adj[b][a] = custo
        #temos que fazer arestas orientadas (por exemplo portas de sentido único)

    #Consulta
    def no(self, id_: str) -> No:
        return self._nos[id_]

    def nos(self) -> list[No]:
        return list(self._nos.values())

    def nos_do_tipo(self, tipo: TipoNo) -> list[No]:
        return [n for n in self._nos.values() if n.tipo == tipo]

    def transitavel(self, id_: str) -> bool:
        #um nó é transitável, exceto se for porta/barreira fechada
        n = self._nos[id_]
        return n.tipo not in TIPOS_BLOQUEAVEIS or n.aberto

    def vizinhos(self, id_: str) -> Iterator[tuple[str, float]]:
        #gera (vizinho, custo) apenas para vizinhos transitáveis

        #mover-se de um nó para um vizinho ao custo da aresta
        #search.py não precisa de saber o que é uma porta
        for viz, custo in self._adj[id_].items():
            if self.transitavel(viz):
                yield viz, custo

    def distancia_euclidiana(self, a: str, b: str) -> float:
        #distância em linha reta (para as heurísticas)
        (x1, y1), (x2, y2) = self._nos[a].posicao, self._nos[b].posicao
        return math.hypot(x1 - x2, y1 - y2)

    #Alterações dinâmicas
    def definir_aberto(self, id_: str, aberto: bool) -> None:
        #abre/fecha uma porta ou barreira e regista a mudança
        n = self._nos[id_]
        if n.tipo not in TIPOS_BLOQUEAVEIS:
            raise ValueError(f"{id_} ({n.tipo.value}) não pode ser fechado")
        if n.aberto != aberto:
            n.aberto = aberto
            self.versao += 1

    def definir_recarga_disponivel(self, id_: str, disponivel: bool) -> None:
        #liga/desliga uma estação de recarga
        n = self._nos[id_]
        if n.tipo != TipoNo.RECARGA:
            raise ValueError(f"{id_} não é uma estação de recarga")
        n.disponivel = disponivel
        #não incrementa a versão, a topologia de movimento não mudou

    #depois tem que se validar que existe semore pelo menos uma rota de evacuação aberta
    #será preciso ao gerar eventos aleatórios de abrir/fechar portas na simulação

#Conversão custo -> tempo
def tempo_travessia(custo: float, velocidade: float) -> int:
    #número de tempos que um agente demora a atravessar uma aresta
    #vou assumir tempo = custo/velocidade, com mínimo de 1 tempo
    #ex: aresta de custo 4, drone com velocidade 2 -> 2 tempos
    #evolução possível: permitir que o agente fique a meio de uma aresta

    if velocidade <= 0:
        raise ValueError("A velocidade tem de ser > 0")
    return max(1, math.ceil(custo / velocidade))


#Mapa de exemplo, só para testar 
def criar_grafo() -> Grafo:
    g = Grafo()
    #(id, tipo, posicao, valor)
    definicao = [
        ("C1", TipoNo.CORREDOR, (0, 0), 0),
        ("C2", TipoNo.CORREDOR, (4, 0), 0),
        ("P1", TipoNo.PORTA, (8, 0), 0),
        ("C3", TipoNo.CORREDOR, (12, 0), 0),
        ("B1", TipoNo.BARREIRA, (4, 4), 0),
        ("C4", TipoNo.CORREDOR, (4, 8), 0),
        ("PI1", TipoNo.PONTO_INTERESSE, (12, 4), 10),
        ("R1", TipoNo.RECARGA, (0, 4), 0),
        ("S1", TipoNo.SAIDA, (12, 8), 0),
    ]
    for id_, tipo, posicao, valor in definicao:
        g.adicionar_no(No(id_, tipo, posicao, valor=valor))

    for a, b in [
        ("C1", "C2"), ("C2", "P1"), ("P1", "C3"), ("C2", "B1"),
        ("B1", "C4"), ("C3", "PI1"), ("PI1", "S1"), ("C4", "S1"),
        ("C1", "R1"), ("R1", "B1"),
    ]:
        g.adicionar_aresta(a, b, g.distancia_euclidiana(a, b))
    return g


if __name__ == "__main__":
    g = criar_grafo()
    print("Vizinhos de C2 (tudo aberto):", [v for v, _ in g.vizinhos("C2")])
    g.definir_aberto("P1", False)
    print("Vizinhos de C2 (P1 fechada): ", [v for v, _ in g.vizinhos("C2")])
    print("Versão da topologia:", g.versao)
    print("Tempos por custo 4 a velocidade 2:", tempo_travessia(4, 2))
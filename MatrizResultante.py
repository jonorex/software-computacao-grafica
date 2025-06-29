import numpy as np

class Stack:
    def __init__(self):
        self.stack = []

    def push(self, item):
        self.stack.append(item)

    def pop(self):
        if not self.is_empty():
            return self.stack.pop()
        else:
            raise IndexError("Pilha vazia")

    def is_empty(self):
        return len(self.stack) == 0

def matriz_translacao(tx, ty):
    return np.array([[1, 0, tx],
                     [0, 1, ty],
                     [0, 0, 1]])

def matriz_rotacao(theta):
    return np.array([[np.cos(theta), -np.sin(theta), 0],
                     [np.sin(theta), np.cos(theta), 0],
                     [0, 0, 1]])

def matriz_escalacao(sx, sy):
    return np.array([[sx, 0, 0],
                     [0, sy, 0],
                     [0, 0, 1]])

def matriz_cisalhamento(shx, shy):
    """
    Retorna a matriz homogênea 3×3 de cisalhamento:
      x′ = x + shx·y
      y′ = shy·x + y
    """
    return np.array([
        [1,   shx, 0],
        [shy, 1,   0],
        [0,   0,   1]
    ])

def matriz_reflexao(eixo):
    if eixo == 'x':
        return np.array([[1, 0, 0],
                         [0, -1, 0],
                         [0, 0, 1]])
    elif eixo == 'y':
        return np.array([[-1, 0, 0],
                         [0, 1, 0],
                         [0, 0, 1]])
    elif eixo == 'xy':
        return np.array([[0, -1, 0],
                         [-1, 0, 0],
                         [0, 0, 1]])
    else:
        raise ValueError("Eixo inválido. Use 'x', 'y' ou 'xy'.")

def pilha_transformacoes(ponto=(0, 0)):
    # Cria a pilha de transformações
    transformacoes = Stack()
    
    # Adiciona a translação para levar o ponto à origem
    translacao_origem = matriz_translacao(-ponto[0], -ponto[1]) # matriz de translação para levar o ponto à origem
    transformacoes = Stack()
    transformacoes.push(translacao_origem)  # Adiciona a translação à origem
    return transformacoes
    
def matriz_resultante(transformacoes:Stack, ponto=(0, 0)):
    # Adiciona translação para devolver o ponto à sua posição original
    translacao_destino = matriz_translacao(ponto[0], ponto[1])
    transformacoes.push(translacao_destino)  # Adiciona a translação de volta
    
    resultado = np.eye(3)  # Matriz identidade 3x3
    
    while not transformacoes.is_empty():
        matriz = transformacoes.pop()
        resultado = np.dot(resultado, matriz)
    
    return resultado

# Menu de opções
def menu():
    print("\nEscolha as transformações e finalize para gerar a matriz resultante:")
    print("1. Translação")
    print("2. Rotação")
    print("3. Escalonamento")
    print("4. Reflexão")
    print("5. Finalizar")

def main():
    # pede as coordenadas do ponto
    print("Digite as coordenadas do ponto (x, y):")
    x = float(input("x: "))
    y = float(input("y: "))
    ponto = (x, y)
    # verificação de entrada
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError("As coordenadas devem ser números.")
    
    transformacoes = pilha_transformacoes(ponto) # Cria a pilha de transformações já com a translação à origem
    # Loop para o menu
    while True:
        menu()
        opcao = input("Digite a opção desejada: ")
        
        if opcao == '1':
            tx = float(input("Digite o deslocamento em x: "))
            ty = float(input("Digite o deslocamento em y: "))
            transformacoes.push(matriz_translacao(tx, ty))
        elif opcao == '2':
            theta = float(input("Digite o ângulo de rotação em graus: "))
            theta = np.radians(theta)
            transformacoes.push(matriz_rotacao(theta))
        elif opcao == '3':
            sx = float(input("Digite o fator de escala em x: "))
            sy = float(input("Digite o fator de escala em y: "))
            transformacoes.push(matriz_escalacao(sx, sy))
        elif opcao == '4':
            eixo = input("Digite o eixo de reflexão (x, y ou xy): ")
            transformacoes.push(matriz_reflexao(eixo))
        elif opcao == '5':
            break
        else:
            print("Opção inválida. Tente novamente.")
    if not transformacoes.is_empty():
        resultado = matriz_resultante(transformacoes, ponto)
        print("Matriz resultante:")
        print(resultado.round(5))
    else:
        print("Nenhuma transformação foi aplicada.")

if __name__ == "__main__":
    main()
# Algoritmos de optimización

import math
import random
from itertools import permutations


def bruteforce(optimizer, solution):
    """
    Método de fuerza bruta.
    Este método realiza una exploración de todas las posibles soluciones del problema para buscar la óptima entre
    todas ellas.
    """

    # Datos de entrada
    data = optimizer.data
    eval_function = optimizer.evalfun
    timer = optimizer.timer

    # Inicialización
    best_solution_value, best_solution = eval_function(solution)
    solution_values = []

    perm_valid = True
    perm_evaluated = False

    for hub in data['id']:
        # Exploración de todas las posibles soluciones (se añade un -1 para poder fijarlo al inicio)
        for perm in permutations([-1] + solution[1]):

            # Comprobación de tiempo máximo
            if timer.update():
                return best_solution, best_solution_value, solution_values

            # Para no repetir evaluaciones solo se ejecutan las que empiecen por -1 (y una sola vez)
            if perm[0] != -1 and perm_evaluated:
                perm_valid = False

            if (perm[0] == -1) and perm_valid:
                perm_evaluated = True

                new_solution_value, new_solution = eval_function([[hub], list(perm[1:])])

                # Mejor solución
                if new_solution_value < best_solution_value:
                    best_solution = new_solution
                    best_solution_value = new_solution_value

                # Histórico de soluciones
                solution_values.append(new_solution_value)

    return best_solution, best_solution_value, solution_values


def cost_saving(optimizer, solution):
    """
    Método del ahorro de costes.
    Este método realiza una construcción de una solución subóptima. Para ello:
        1- Se toman como centros de transferencia aquellos cuya suma total de distancias por residuos al resto de
           centros sea menor.
        2- Una vez identificados estos centros de transferencia, el resto de centros se asignarán a aquel centro de
           transferencia que implique una manor carga (= distancia * residuo).
    """

    # Función auxiliar
    def distance(town1, town2):

        # Índices de 1 a N
        town1 = town1 + 1
        town2 = town2 + 1

        # Se ordenan los índices
        ti = min(town1, town2)
        tj = max(town1, town2)

        # Distancia
        if ti == tj:
            dist = 0
        else:
            dist = data['distance'][int(ti + ((tj - 2) * (tj - 1)) / 2) - 1]

        return dist

    # Datos de entrada
    data = optimizer.data
    capacities = optimizer.capacities
    eval_function = optimizer.evalfun
    timer = optimizer.timer

    # Inicialización
    best_solution_value, best_solution = eval_function(solution)
    solution_values = [best_solution_value]

    # Coste total de envío desde y hasta todos los centros
    total_costs = []
    for i in data['id']:
        total_cost = 0

        for j in data['id']:
            total_cost += distance(i, j) * data['waste'][j]

        total_costs.append(total_cost)

    # Selección de centros de transferencia
    transference_hubs = []

    for _ in range(optimizer.max_hubs):
        min_cost = min(total_costs)
        min_idx = total_costs.index(min_cost)

        transference_hubs.append(min_idx)
        total_costs.pop(min_idx)

    # Coste de envío desde todos los centros hasta centros de transferencia
    costs = {}
    for hub in transference_hubs:
        costs[hub] = []

        for center in data['id']:
            costs[hub].append(distance(center, hub) * data['waste'][center])

    # Asignación de grupos
    groups = {hub: [] for hub in transference_hubs}
    waste_groups = {hub: 0 for hub in transference_hubs}
    for center in data['id']:

        # Se calculan costes desde un centro a todos los hubs de transferencia
        costs_to_analyze = []
        for hub in transference_hubs:
            costs_to_analyze.append([costs[hub][center], hub, center])

        # Se asigna al de menor coste (siempre que tenga hueco)
        assigned = False
        while not assigned:
            selected_cost, selected_hub, selected_center = min(costs_to_analyze)
            if waste_groups[selected_hub] + data['waste'][selected_center] < capacities['QT']:
                groups[selected_hub].append(center)
                waste_groups[selected_hub] += data['waste'][selected_center]
                assigned = True
            else:
                costs_to_analyze.pop(costs_to_analyze.index([selected_cost, selected_hub, selected_center]))

    # Construcción de la solución
    solution = []
    for hub in transference_hubs:
        solution.extend(groups[hub] + [-1])
    solution = [[], solution]

    # Resultados
    best_solution_value, best_solution = eval_function(solution)
    solution_values.append(best_solution_value)
    timer.update()

    return best_solution, best_solution_value, solution_values


def local_search(optimizer, solution, operator='swap'):
    """
    Método de la búsqueda local (o método del gradiente).
    Este método realiza una exploración de aquel espacio de soluciones alcanzable mediante un operador de vecindad. Una
    vez encontrado un óptimo local, se detiene la exploración y se devuelve la solución encontrada.
    """

    # Datos de entrada
    eval_function = optimizer.evalfun
    timer = optimizer.timer

    # Inicialización
    current_solution_value, current_solution = eval_function(solution)
    neighbourhood = []

    best_solution_value = current_solution_value
    best_solution = current_solution
    solutions = [current_solution_value]

    # Búsqueda del óptimo local
    while True:

        # Comprobación de tiempo máximo
        if timer.update():
            return best_solution, best_solution_value, solutions

        # Cálculo de nueva vecindad
        if operator == 'swap':
            neighbourhood = _neighbourhood_swap(current_solution[1])
        elif operator == 'insertion':
            neighbourhood = _neighbourhood_insertion(current_solution[1])

        # Cálculo de vecino más favorable
        best_neighbour = min(neighbourhood, key=lambda x: eval_function([[], x])[0])
        new_solution_value, new_solution = eval_function([[], best_neighbour])

        # Comprobación de mejor solución
        if new_solution_value < best_solution_value:
            best_solution_value = new_solution_value
            best_solution = new_solution
            neighbourhood = []
            solutions.append(best_solution_value)

        else:
            break

        # Actualización del bucle
        current_solution = new_solution

    return best_solution, best_solution_value, solutions


def _neighbourhood_swap(solution):
    """ Operador de vecindad SWAP (intercambia dos elementos de la solución) """

    # Inicialización
    neighbourhood = []

    # Construcción de vecinos
    for i in range(len(solution) - 1):
        for j in range(i + 1, len(solution)):
            neighbour = solution[:]
            neighbour[i], neighbour[j] = neighbour[j], neighbour[i]

            neighbourhood.append(neighbour)

    return neighbourhood


def _neighbourhood_swap_p(solution, p=0.2):
    """ Operador de vecindad SWAP (intercambia un porcentaje 'p' de los elementos de la solución) """

    # Inicialización
    neighbourhood = []

    # Construcción de vecinos
    N = math.floor(p * len(solution))
    for i in range(len(solution) - 1 + N):
        for j in range(i + 1 + N, len(solution)):
            neighbour = solution[:]
            neighbour[i:i + N], neighbour[j:j + N] = neighbour[j:j + N], neighbour[i:i + N]

            neighbourhood.append(neighbour)

    return neighbourhood


def _neighbourhood_insertion(solution):
    """ Operador de vecindad INSERTION (introduce el elemento 'i' en la posición 'j') """

    # Inicialización
    neighbourhood = []

    # Construcción de vecinos
    for i in range(len(solution)):
        for j in range(len(solution)):
            if (i != j) and (i != j + 1):
                neighbour = solution[:]
                neighbour[j:j] = [neighbour.pop(i)]

                neighbourhood.append(neighbour)

    return neighbourhood


def vnd(optimizer, solution):
    """
    Método de búsqueda de entorno variable (VNS) descendiente.
    Este método consiste en una metaheurística que extiende el método de búsqueda local utilizando varias vecindades. De
    esta forma, cuando se alcanza un óptimo local dado un operador de vecindad, se utiliza otro operador de forma que
    pueda hallarse un nuevo óptimo.
    """

    # Datos de entrada
    eval_function = optimizer.evalfun
    timer = optimizer.timer

    # Inicialización
    current_solution_value, current_solution = eval_function(solution)

    best_solution = current_solution
    best_solution_value = current_solution_value
    solutions = [current_solution_value]

    # Operadores
    operators = ['swap', 'insertion']
    k = 1

    # Algoritmo VND
    while k <= len(operators):

        # Comprobación de tiempo máximo
        if timer.update():
            return best_solution, best_solution_value, solutions

        # Búsqueda local
        new_solution, new_solution_value, solutions_ls = \
            local_search(optimizer, current_solution, operator=operators[k - 1])

        solutions.extend(solutions_ls)

        # Actualización de mejor solución
        if new_solution_value < current_solution_value:
            current_solution_value = new_solution_value
            current_solution = new_solution

            best_solution = new_solution
            best_solution_value = current_solution_value

            k = 1  # Vuelta a operador inicial

        else:
            k += 1  # Se prueba nuevo operador

    return best_solution, best_solution_value, solutions


def vns(optimizer, solution):
    """
    Método de búsqueda de entorno variable (VNS).
    Este método consiste en una metaheurística que extiende el método de búsqueda local utilizando varias vecindades. De
    esta forma, cuando se alcanza un óptimo local dado un operador de vecindad, se utiliza otro operador de forma que
    pueda hallarse un nuevo óptimo.
    Con respecto al algoritmo VND, el VNS introduce una función de shaking que permite al algoritmo realizar un cambio
    brusco en la solución al atascarse en un óptimo local. Esto le permitirá una mayor exploración al mismo.
    """

    # Datos de entrada
    eval_function = optimizer.evalfun
    timer = optimizer.timer

    # Inicialización
    current_solution_value, current_solution = eval_function(solution)

    best_solution = current_solution
    best_solution_value = current_solution_value
    solutions = [current_solution_value]

    # Operadores
    operators = ['swap', 'insertion']
    k = 1

    # Algoritmo VND
    while k <= len(operators):

        # Comprobación de tiempo máximo
        if timer.update():
            return best_solution, best_solution_value, solutions

        # Shaking
        current_solution = [[], _shaking(current_solution[1])]

        # Búsqueda local
        new_solution, new_solution_value, solutions_ls = \
            local_search(optimizer, current_solution, operator=operators[k - 1])

        solutions.extend(solutions_ls)

        # Actualización de mejor solución
        if new_solution_value < current_solution_value:
            current_solution_value = new_solution_value
            current_solution = new_solution

            best_solution = new_solution
            best_solution_value = current_solution_value

            k = 1  # Vuelta a operador inicial

        else:
            k += 1  # Se prueba nuevo operador

    return best_solution, best_solution_value, solutions


def _shaking(solution):
    """ Función de shaking: aplica un operador de vecindad más agresivo a la solución """

    # Vecindario de la solución
    current_solution = solution[:]
    neighbourhood = _neighbourhood_swap_p(current_solution)

    # Vecino aleatorio
    new_solution = random.sample(neighbourhood, k=1)[0]

    return new_solution


def simulated_annealing(optimizer, solution):
    """
    Método de recocido simulado.
    Este método consiste en una metaheurística que permite al algoritmo alejarse de la solución óptima encontrada
    siguiendo el comportamiento del recocido de los metales. De esta forma, se le dota de una mayor exploración al
    algoritmo.
    El algoritmo podrá alejarse de la solución óptima encontrada en función de una temperatura que irá decreciendo con
    el tiempo. EL funcionamiento del mismo será tal que, si la solución encontrada es peor a la óptima histórica, el
    algoritmo tendrá cierta probabilidad de saltar hacia ella (en función de la temperatura antes mencionada).
    """

    # Datos de entrada
    eval_function = optimizer.evalfun
    timer = optimizer.timer

    # Parámetros del algoritmo
    max_temp = 1000
    min_temp = 1
    L = 10
    alpha = 0.0001

    # Inicialización
    temp = max_temp
    current_solution_value, current_solution = eval_function(solution)

    best_solution = current_solution
    best_solution_value = current_solution_value
    solutions = [current_solution_value]

    # Búsqueda de la solución óptima
    while temp > min_temp:
        for _ in range(L):

            # Creación de vecindad
            neighbourhood = _neighbourhood_swap(current_solution[1])

            # Orden de evaluación de la vecindad
            order = list(range(len(neighbourhood)))
            random.shuffle(order)

            # Evaluación de la vecindad
            for i in range(len(neighbourhood)):

                # Comprobación de tiempo máximo
                if timer.update():
                    return best_solution, best_solution_value, solutions

                new_solution_value, new_solution = eval_function([[], neighbourhood[order[i]]])

                delta = new_solution_value - current_solution_value

                # Si mejora la solución → se acepta
                if delta < 0:

                    # Mejor solución histórica
                    if current_solution_value < best_solution_value:
                        best_solution_value = new_solution_value
                        best_solution = [[], neighbourhood[order[i]][:]]

                    # Actualización
                    current_solution_value = new_solution_value
                    current_solution = [[], neighbourhood[order[i]][:]]
                    break

                # Si no mejora la solución → probabilidad de aceptación
                else:
                    a = random.random()
                    if a < math.exp(-delta / temp):
                        current_solution_value = new_solution_value
                        current_solution = [[], neighbourhood[order[i]][:]]
                        break

            solutions.append(current_solution_value)
        temp = temp / (1 + alpha * temp)

    return best_solution, best_solution_value, solutions


def tabu_search(optimizer, solution):
    """
    Método de búsqueda tabú.
    Este método consiste en una metaheurística que, partiendo de una solución inicial, construye un entorno de
    soluciones adyacentes que pueden ser alcanzadas. El algoritmo explora el espacio de búsqueda atendiendo a
    restricciones basadas en memorias de lo reciente y lo frecuente y a niveles de aspiración (excepciones a estas
    restricciones).
    """

    # Datos de entrada
    data = optimizer.data
    eval_function = optimizer.evalfun
    timer = optimizer.timer

    # Parámetros del algoritmo
    tabu_size = len(solution) / 2
    n_iteration = 1000

    # Solución inicial
    current_solution_value, current_solution = eval_function(solution)

    best_solution = current_solution
    best_solution_value = current_solution_value
    solutions = [current_solution_value]

    # Listas tabús
    recent_tabu_list = []
    frequent_tabu_list = [0 for i in range(len([-1] + data['id']) - 1) for _ in range(i+1, len([-1] + data['id']))]

    # Búsqueda de la mejor solución
    for _ in range(n_iteration):

        # Comprobación de tiempo máximo
        if timer.update():
            return best_solution, best_solution_value, solutions

        # Creación de vecindad: swap
        swap = []                               # Swaps realizados
        neighbourhood = []                      # Vecindad
        neighbourhood_value = []                # Valor de la función objetivo de la vecindad
        neighbourhood_value_penalty = []        # Valor tras penalización de la vecindad

        for i in range(len(current_solution[1]) - 1):
            for j in range(i + 1, len(current_solution[1])):

                # Atributos almacenados (elementos que participan en el swap)
                ti = min(current_solution[1][i], current_solution[1][j]) + 1
                tj = max(current_solution[1][i], current_solution[1][j]) + 1

                # Nuevo vecino
                neighbour = current_solution[1]
                neighbour[i], neighbour[j] = neighbour[j], neighbour[i]
                neighbour_val, _ = eval_function([[], neighbour])
                neighbour_val_penalty = neighbour_val + frequent_tabu_list[int(ti + ((tj - 2) * (tj-1)) / 2) - 1]

                # Comprobación: no tabú o mejor histórico
                if ([ti, tj] not in recent_tabu_list) or (
                        [ti, tj] in recent_tabu_list and neighbour_val < best_solution_value):
                    neighbourhood.append(neighbour)
                    neighbourhood_value.append(neighbour_val)
                    neighbourhood_value_penalty.append(neighbour_val_penalty)
                    swap.append([current_solution[1][i], current_solution[1][j]])

        _, current_solution_value, swap, current_neighbour = \
            min(zip(neighbourhood_value_penalty, neighbourhood_value, swap, neighbourhood))
        current_solution = [[], current_neighbour]

        solutions.append(current_solution_value)

        # Mejor solución
        if current_solution_value < best_solution_value:
            best_solution = current_solution
            best_solution_value = current_solution_value

        # Actualización de listas tabú
        ti, tj = min(swap), max(swap)
        recent_tabu_list.append([min(swap), max(swap)])
        if len(recent_tabu_list) > tabu_size:
            recent_tabu_list.pop(0)

        frequent_tabu_list[int(ti + ((tj - 2) * (tj-1)) / 2) - 1] += 1

    return best_solution, best_solution_value, solutions

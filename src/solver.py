# Solver del problema de optimización.

import math
import timer
import logging
import itertools
import heuristics
import graphbuild


class HLASolver(object):
    """
    <class 'HLASolver'>
    Solver del problema de optimización HLA (Hub Locations Allocation).
    Esta clase contiene los atributos y métodos necesarios para constituir una interfaz sencilla al usuario. De esta
    forma, es posible resolver un problema de optimización del tipo HLA mediante el método solve.
    """

    # Logger
    logger = logging.getLogger('logger')
    logger.disabled = False  # Se habilita/deshabilita el logger
    logger.setLevel(logging.INFO)  # DEBUG, INFO, WARNING, ERROR, EXCEPTION, CRITICAL

    consoleh = logging.StreamHandler()
    formatterConsole = logging.Formatter('%(levelname)s - %(message)s')
    consoleh.setFormatter(formatterConsole)  # Formato de salida
    logger.addHandler(consoleh)

    fileh = logging.FileHandler('../log/solver_log.log')
    fileh.setLevel(logging.INFO)
    formatterFile = logging.Formatter('%(levelname)s - %(message)s')
    fileh.setFormatter(formatterFile)
    logger.addHandler(fileh)

    # Parámetros
    problem = 'HLA'     # = Hub Locations Allocation

    def __init__(self, data, costs, capacities, dhubs=5):

        # Características del problema
        self.data = data
        self.costs = costs
        self.capacities = capacities

        self.min_hubs = math.ceil(sum(data['waste']) / capacities['QT'])
        self.max_hubs = self.min_hubs + dhubs

        # Inicialización
        self.solution = []
        self.solution_value = float('inf')
        self.solution_value_history = [float('inf')]

        self.method = 'None'

        self.solution_groups = {}

        # Constructor de gráficos
        self.graphbuilder = graphbuild.GraphicsBuilder(self.problem, data)

        # Timer
        self.timer = timer.Timer(max_time=5)

    def __repr__(self):
        return "<[%s] H%.0f-%.0f>" % (self.problem, self.min_hubs, self.max_hubs)

    def __str__(self):
        return "<[%s problem] Nº. Hubs: %.0f - %.0f>" % (self.problem, self.min_hubs, self.max_hubs)

    def evalfun(self, solution):
        """
        Función de evaluación del problema de optmización.

        :param solution: Solución a analizar (Ej.: [[treatment_hub], [trans1, cent1, cent2, -1, trans2, ...]]).

        :return: solution_value: Valor de la solución (inf si la solución es inadmisible).
        :return: solution: Solución de entrada.
        """

        # Datos de entrada
        treatment_hubs = solution[0]
        center_groups = [list(group) for k, group in itertools.groupby(solution[1], lambda x: x == -1) if not k]

        # Inicialización
        load_treat = 0
        load_trans = 0

        transference_hubs = []
        waste_per_trans = {}

        transference_overload = False                    # Para detectar sobrecarga de centro de transferencia

        # Evaluación de la solución
        for group in center_groups:

            # Centro de tratamiento: primera posición
            transference_hub = group[0]
            transference_hubs.append(transference_hub)

            waste_per_trans[transference_hub] = self.data['waste'][transference_hub]

            # Carga de tratamiento (del resto de centro al de tratamiento)
            for center in group[1:]:

                # Lectura de datos
                distance = self.distance(center, transference_hub)
                waste = self.data['waste'][center]

                # Residuos gestionados por cada centro
                waste_per_trans[transference_hub] += waste
                if waste_per_trans[transference_hub] > self.capacities['QT']:
                    transference_overload = True

                # Carga total ([km * kg])
                load_trans += distance * waste

        if len(treatment_hubs) > 0:
            for hub in transference_hubs:

                # Carga total([km * kg])
                load_treat += self.distance(hub, treatment_hubs[0]) * waste_per_trans[hub]

        # Comprobación de solución válida
        n_treat, n_trans = len(treatment_hubs), len(transference_hubs)
        if n_trans < 1:
            solution_value = float('inf')
        elif transference_overload or sum(waste_per_trans) > self.capacities['QP']:
            solution_value = float('inf')
        else:
            solution_value = n_trans * self.costs['CFtrans'] + load_trans * self.costs['CMT'] + \
                             n_treat * self.costs['CFtreat'] + load_treat * self.costs['CTP']

        self.logger.debug('[HLA] Valor: ' + str(solution_value) + '; Solución: ' + str(solution) + '.')

        return solution_value, solution

    def solve(self, initial_solution, method):
        """
        Aplicación de los distintos algoritmos al problema de optimización. Se seguirá una estrategia en dos pasos:
            1. Se optimiza la cadena de centros de transferencia.
            2. Se calcula por fuerza bruta dónde debe ubicarse el centro de tratamiento.

        :param initial_solution: Solución de partida para comenzar el algoritmo.
        :param method: Método a utilizar.

        :return: solution: Mejor solución encontrada por el algoritmo.
        :return: solution_value: Valor de la mejor solución encontrada por el algoritmo.
        :return: history: Histórico de los de valores de las distintas soluciones que atraviesa el algoritmo.
        :return: dt: Tiempo tomado por el algoritmo en el proceso de optimización.
        """

        # Inicialización
        solution = []
        history1, history2 = [], []

        # Inicio de temporizador
        self.timer.reset()
        self.timer.start()

        # 1: Optimización de cadena de centros de transferencia
        initial_solution = [[], initial_solution[1]]
        if method == "Bruteforce":
            solution, solution_value, history1 = heuristics.bruteforce(self, initial_solution)

        elif method == 'Cost Saving':
            solution, solution_value, history1 = heuristics.cost_saving(self, initial_solution)

        elif method == 'Local Search (SWAP)':
            solution, solution_value, history1 = heuristics.local_search(self, initial_solution, operator='swap')

        elif method == 'Local Search (INSERTION)':
            solution, solution_value, history1 = heuristics.local_search(self, initial_solution, operator='insertion')

        elif method == 'VND':
            solution, solution_value, history1 = heuristics.vnd(self, initial_solution)

        elif method == 'VNS':
            solution, solution_value, history1 = heuristics.vns(self, initial_solution)

        elif method == 'Simulated Annealing':
            solution, solution_value, history1 = heuristics.simulated_annealing(self, initial_solution)

        elif method == 'Tabu Search':
            solution, solution_value, history1 = heuristics.tabu_search(self, initial_solution)

        else:
            self.logger.error('[' + self.problem + '][SOLVE] El método introducido (' + method + ') no es válido.')
            exit()

        # 2: Optimización de centro de tratamiento (Bruteforce)
        initial_solution = solution
        solution_value, solution = self.evalfun([[0], initial_solution[1]])

        for hub in self.data['id'][1:]:
            new_solution_value, new_solution = self.evalfun([[hub], initial_solution[1]])
            history2.append(new_solution_value)

            if new_solution_value < solution_value:
                solution = new_solution
                solution_value = new_solution_value

        # Fin de temporizador y resultado
        dt = self.timer.stop()
        if self.timer.check():
            self.logger.warning(
                '[' + self.problem + '][SOLVE - ' + method + '] Optimización abortada (' + str(dt) +
                ' s) -> Valor: ' + str(solution_value) + '; Solución: ' + str(solution) + '.')
        else:
            self.logger.info(
                '   [' + self.problem + '][SOLVE - ' + method + '] Optimización finalizada (' + str(dt) +
                ' s) -> Valor: ' + str(solution_value) + '; Solución: ' + str(solution) + '.')

        self.set_solution(solution, [history1, history2], method)

        return solution, solution_value, [history1, history2], dt

    def set_solution(self, solution, solution_history, method):
        """
        Método para almacenar la solución obtenida.
        :param solution: Solución actual al problema de optimización.
        :param solution_history: Histórico de soluciones encontradas en el problema de optimización.
        :param method: Método utilizado para la optimización.
        """
        # Se almacena solución
        self.method = method
        self.solution_value_history = solution_history

        self.solution_value, self.solution = self.evalfun(solution)

        center_groups = [list(group) for k, group in itertools.groupby(solution[1], lambda x: x == -1) if not k]
        solution_groups = {}
        for group in center_groups:
            transference_hub = group[0]
            solution_groups[transference_hub] = group
        self.solution_groups = [solution[0], solution_groups]

    def graph_solution(self):
        """
        Representación gráfica de la solución del problema de optimización.
        """
        if self.solution_value == float('inf'):
            self.logger.error('  [' + self.problem + '][GRAPH - ' + self.method +
                              '] Solución no válida. No es posible representar.')
            return

        # Representación
        self.graphbuilder.graph_history(self.solution_value_history, self.method)
        self.graphbuilder.graph_groups(self.solution_groups, self.method)

    def set_timer(self, max_time):
        """
        Establecimiento de tiempo de ejecución máximo admisible de un algoritmo de optimización.
        :param max_time: Tiempo máximo de ejecución.
        """
        self.timer.set(max_time)

    def distance(self, town1, town2):
        """
        Devuelve la distancia entre los dos municipios recibidos como argumento.
        :param town1: Municipio 1 (índices de 0 a N-1).
        :param town2: Municipio 2 (índices de 0 a N-1).

        :return: Distancia entre los dos municipios.
        """

        # Índices de 1 a N
        town1 = town1 + 1
        town2 = town2 + 1

        # Se ordenan los índices
        ti = min(town1, town2)
        tj = max(town1, town2)

        # Distancia
        if ti == tj:
            distance = 0
        else:
            distance = self.data['distance'][int(ti + ((tj - 2) * (tj - 1)) / 2) - 1]

        return distance

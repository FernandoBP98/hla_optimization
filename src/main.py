# Script principal: resolución del problema HLA.

import os
import utils
import random
import solver
import logging

# Logger
logger_main = logging.getLogger('evaluation_logger')
logger_main.disabled = False                                       # Se habilita/deshabilita el logger
logger_main.setLevel(logging.INFO)                                 # DEBUG, INFO, WARNING, ERROR, EXCEPTION, CRITICAL

consoleh = logging.StreamHandler()
formatterConsole = logging.Formatter('%(levelname)s - %(message)s')
consoleh.setFormatter(formatterConsole)                             # Formato de salida
logger_main.addHandler(consoleh)

path = '../log'
if not os.path.exists(path):
    os.mkdir(path)
fileh = logging.FileHandler(path + '/main_log.log')
fileh.setLevel(logging.INFO)
formatterFile = logging.Formatter('%(levelname)s - %(message)s')
fileh.setFormatter(formatterFile)
logger_main.addHandler(fileh)


def main():

    # Lectura de datos
    size = 90

    data = utils.read_file_excel("../data/Datos.xlsx", size)
    costs = {'CTP': 0.00006,            # Coste unitario de transferencia de centro de transf. a tratam. [€/km*Tm]
             'CMT': 1.2,                # Coste unitario de transferencia de municipios a centro de transf. [€/km*Tm]
             'CFtrans': 197072,         # Costes fijos de centros de transferencia [€]
             'CFtreat': 215138}         # Costes fijos de centros de tratamiento [€]
    capacities = {'QT': 50000,          # Capacidad anual del centro de transferencia [Tm]
                  'QP': 500000}         # Capacidad anual de la planta de tratamiento [Tm]
    dhubs = 5

    max_timer = 5

    # Definición del problema
    hla = solver.HLASolver(data, costs, capacities, dhubs)
    hla.set_timer(max_timer)

    # Resolución del problema
    treatment_hubs = random.sample(range(size), 1)
    centers = list(range(size)) + [-1] * hla.max_hubs
    random.shuffle(centers)
    initial_solution = [treatment_hubs, centers]

    methods = ['Bruteforce', 'Cost Saving', 'Local Search (SWAP)', 'Local Search (INSERTION)', 'VND', 'VNS',
               'Simulated Annealing', 'Tabu Search']
    # methods = ['VNS']

    initial_solution, _, _, _ = hla.solve(initial_solution, 'Cost Saving')
    for method in methods:
        solution, solution_value, solution_values, dt = hla.solve(initial_solution, method)
        hla.graph_solution()


if __name__ == "__main__":
    main()

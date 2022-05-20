# Clase de construcción de figuras

import os
import matplotlib.pyplot as plt


class GraphicsBuilder(object):
    """
    <class 'GraphicsBuilder'>
    Clase que permite construir los gráficos de una solución al problema de localización de hubs (Hub Locations
    Allocation, HLA).
    """

    def __init__(self, problem_type, data, path='../figures'):

        # Definición del problema
        self.problem_type = problem_type
        self.data = data

        # Construcción de ruta
        self.path = path
        if not os.path.exists(path):
            os.mkdir(path)

    def __repr__(self):
        return "<GB-%s:" % self.problem_type

    def __str__(self):
        return "Graphics Builder: %s problem. " % self.problem_type

    def graph_history(self, solution_value_history, method):
        """
        Salida gráfica de la evolución de una metaheurística (iteraciones).

        :param solution_value_history: Estructura de datos que almacena los valores de las soluciones alcanzadas.
        :param method: Método usado en el proceso de optimización.
        """

        # Captura de datos
        trans_history = solution_value_history[0]
        treat_history = solution_value_history[1]

        # Optimización de centros de transferencia
        best_trans_value = trans_history[0]
        best_trans_history = [best_trans_value] * len(trans_history)
        for i in range(len(trans_history)):
            if trans_history[i] < best_trans_value:
                best_trans_value = trans_history[i]
            best_trans_history[i] = best_trans_value

        # Optimización de centro de tratamiento
        best_treat_value = treat_history[0]
        best_treat_history = [best_treat_value] * len(treat_history)
        for i in range(len(treat_history)):
            if treat_history[i] < best_treat_value:
                best_treat_value = treat_history[i]
            best_treat_history[i] = best_treat_value

        # Representación
        fig, axs = plt.subplots(2, 1)
        axs[0].plot(trans_history, linewidth=2, marker='o', markersize=3, label='Solución')
        axs[0].plot(best_trans_history, color='r', label='Mejor solución')
        axs[0].plot(best_trans_history.index(min(best_trans_history)), min(best_trans_history),
                    linestyle=' ', marker='x', markersize=5, markeredgewidth=2, color='r')

        axs[0].set_title('[' + self.problem_type + '] ' + method + ' - Optimización de Centros de Transferencia')
        axs[0].set_ylabel('Coste de Centros de Transferencia [€]')
        axs[0].set_xlabel('Nº de Iteraciones')
        axs[0].set_xlim([0, len(trans_history) + 1])
        axs[0].legend(loc='upper right')

        axs[1].plot(treat_history, linewidth=2, marker='o', markersize=3, label='Solución')
        axs[1].plot(best_treat_history.index(min(best_treat_history)), min(best_treat_history),
                    linestyle=' ', marker='x', markersize=5, markeredgewidth=2, color='r')

        axs[1].set_title('[' + self.problem_type + '] ' + 'Bruteforce' + ' - Optimización de Centro de Tratamiento')
        axs[1].set_ylabel('Valor de la función objetivo [€]')
        axs[1].set_xlabel('ID de Centro de Tratamiento')
        axs[1].set_xlim([0, len(treat_history)])
        axs[1].legend(loc='upper right')

        plt.show()

        # Guardado
        fig.savefig(self.path + '/' + self.problem_type + '_' + method + '_EVOLxITER.png')

        # Cierre
        plt.close()

# Clase de construcción de figuras

import os
from itertools import cycle
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

    def graph_groups(self, groups, method):
        """
        Salida gráfica de la representación de los grupos de centros asignados a un centro de transferencia.
        :param groups: Solución construida (grupos de centros de generación de residuos según centro de transferencia).
        :param method: Método usado en el proceso de optimización.
        """
        # Parámetros de entrada
        data = self.data

        treatment_hub = groups[0][0]
        transference_groups = groups[1]

        # Configuración de gráficos
        fig, ax = plt.subplots()
        linestyle_tuple = cycle([
            'solid',
            'dashed',
            'dashdot',
            'dotted',
            (0, (3, 1, 1, 1)),
            (0, (1, 10)),
            (0, (1, 1)),
            (0, (1, 1)),
            (0, (5, 10)),
            (0, (5, 5)),
            (0, (5, 1)),
            (0, (3, 10, 1, 10)),
            (0, (3, 5, 1, 5)),
            (0, (3, 5, 1, 5, 1, 5)),
            (0, (3, 10, 1, 10, 1, 10)),
            (0, (3, 1, 1, 1, 1, 1))])

        # Representación del centro de tratamiento
        ax.scatter(data['longitude'][treatment_hub], data['latitude'][treatment_hub], color='k', marker='D',
                   linewidths=5, label='Centro de tratamiento')

        # Representación de grupos
        for i, transference_hub in enumerate(transference_groups.keys()):

            # Primer elemento del grupo (para inicializar color)
            center = transference_groups[transference_hub][0]
            xpos, ypos = data['longitude'][center], data['latitude'][center]
            line, = ax.plot([xpos, data['longitude'][transference_hub]], [ypos, data['latitude'][transference_hub]],
                            marker='.', linestyle=next(linestyle_tuple))

            # Resto de elementos del grupo
            for center in transference_groups[transference_hub][1:]:
                xpos, ypos = data['longitude'][center], data['latitude'][center]
                ax.plot([xpos, data['longitude'][transference_hub]], [ypos, data['latitude'][transference_hub]],
                        marker='.', color=line.get_color(), linestyle=line.get_linestyle())
                ax.text(xpos, ypos, ' ' + data['town'][center], color=line.get_color())

            # Centro de transferencia
            label = 'Centro de transferencia ' + str(i + 1)
            ax.scatter(data['longitude'][transference_hub], data['latitude'][transference_hub],
                       color=line.get_color(), marker='^', linewidths=3, label=label)
            ax.text(data['longitude'][transference_hub], data['latitude'][transference_hub],
                    data['town'][transference_hub], color=line.get_color())

        # Título
        ax.set_title('[' + self.problem_type + '] Reparto en hubs de la solución')
        ax.set_ylabel('Latitud', horizontalalignment='right', y=1.0)
        ax.set_xlabel('Longitud', horizontalalignment='right', x=1.0)
        ax.legend(loc='upper left')

        plt.show()

        # Guardado
        fig.savefig(self.path + '/' + self.problem_type + '_' + method + '_SOL_grupos.png')

        # Cierre
        plt.close()

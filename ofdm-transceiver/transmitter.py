import random
import numpy as np
import matplotlib.pyplot as plt
import qam_overhead.modulation
import qam_overhead as qm

def plot_constellation(iVals, qVals, title = '16QAM Constellation Map'):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(iVals, qVals, s=22, alpha=0.8)

    ax.set_xlabel("In-phase (I)")
    ax.set_ylabel("Quadrature (Q)")
    ax.set_title(title, pad=12)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_xticks([-1, -0.333, 0.333, 1])
    ax.set_yticks([-1, -0.333, 0.333, 1])
    ax.grid(True, linestyle="--", linewidth=0.6)    

    plt.show()

def main():
    QAM16 = [-1, -0.333, 0.333, 1]

    Ns = 256 # number of symbols
    bits = 4 # bits per symbol
    data = qm.modulation.data_gen(Ns*bits)
    dataI, dataQ = qm.modulation.slicer(data)

    mapI = qm.modulation.mapper_16QAM(QAM16, dataI)
    mapQ = qm.modulation.mapper_16QAM(QAM16, dataQ)

    plot_constellation(mapI, mapQ)

main()

    

import transmitter
import receiver
import matplotlib.pyplot as plt
import qam_overhead as qm
import qam_overhead.demodulation
import numpy as np

def plot_constellation(iVals, qVals, title = '16QAM Constellation Map No Noise'):
    fig, ax = plt.subplots(figsize=(8, 8))
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
    plt.savefig(title+'.png')


def SNRvsBER(orig, tx, lowerdB, upperdB, Ns, bits):
    SNRs = np.arange(-10,30,1)
    BERs = np.zeros(len(SNRs))
    for i in range(len(SNRs)):
        rx_n = receiver.ofdm_receive(
            transmitter.qm.channel.add_awgn(tx, SNR = SNRs[i], K=1)[0])[0]
        rx_n_arr = np.asarray(rx_n, dtype=complex)
        i_rx_n = rx_n_arr.real
        q_rx_n = rx_n_arr.imag       
        recovered = qm.demodulation.demapper(i_rx_n, q_rx_n, Ns*bits)
        BERs[i] = np.count_nonzero(orig != recovered)*100/len(orig)
    
    return SNRs, BERs
    
def main():
    QAM16 = [-1, -0.333, 0.333, 1]

    Ns = 256 # number of symbols
    bits = 4 # bits per symbol
    data = transmitter.qm.modulation.data_gen(Ns*bits)
    dataI, dataQ = transmitter.qm.modulation.slicer(data)

    mapI = transmitter.qm.modulation.mapper_16QAM(QAM16, dataI)
    mapQ = transmitter.qm.modulation.mapper_16QAM(QAM16, dataQ)

    plt.figure()
    plot_constellation(mapI, mapQ) 
    tx, freq_grid, Fs = transmitter.ofdm_symbols(mapI,mapQ)
    tx_w_noise, noise = transmitter.qm.channel.add_awgn(tx, SNR = 20, K=1)
    rx, r_grid = receiver.ofdm_receive(tx)
    rx_w_noise, r_grid_n = receiver.ofdm_receive(tx_w_noise)
    
    #IQ without noise
    rx_arr = np.asarray(rx, dtype=complex)
    i_rx = rx_arr.real
    q_rx = rx_arr.imag
    
    #IQ with noise
    rx_n_arr = np.asarray(rx_w_noise, dtype=complex)
    i_rx_n = rx_n_arr.real
    q_rx_n = rx_n_arr.imag
    # print(q_rx_n)
    # plot_constellation(i_rx,q_rx)
    plt.figure()
    plot_constellation(i_rx_n,q_rx_n, title='16QAM Constellation Map with Noise (20dB SNR)')

   #IQ with lots of noise
    tx_w_noise_l, noise_l = transmitter.qm.channel.add_awgn(tx, SNR = -5, K=1)
    rx_w_noise_l, r_grid_n_l = receiver.ofdm_receive(tx_w_noise_l)
    rx_n_arr_l = np.asarray(rx_w_noise_l, dtype=complex)
    i_rx_n_l = rx_w_noise_l.real
    q_rx_n_l = rx_w_noise_l.imag
    plt.figure()
    plot_constellation(i_rx_n_l,q_rx_n_l, title='16QAM Constellation Map with Noise (-5dB SNR)')

    rx_n_arr = np.asarray(rx_w_noise, dtype=complex)
    i_rx_n = rx_n_arr.real
    q_rx_n = rx_n_arr.imag
    #SNR vs BER
    SNR, BER = SNRvsBER(data, tx, -20,30, Ns, bits)
    plt.figure()
    plt.plot(SNR, BER, 'o-')
    plt.grid(True, which='both')
    plt.xlabel('SNR (dB)')
    plt.ylabel('Bit-error rate (%)')
    plt.title('16-QAM OFDM BER vs SNR')
    plt.savefig('16qam_ofdm_BER_SNR.png')

main()

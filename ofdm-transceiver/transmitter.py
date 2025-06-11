import numpy as np
import matplotlib.pyplot as plt
import qam_overhead as qm
import qam_overhead.modulation
import qam_overhead.channel

def ofdm_symbols(i_sym, q_sym, n_subcarriers=256,
                 cp_len = 64,
                 pilot_positions = None,
                 pilot_value = 1+1j,
                 subcarrier_spacing = 15e3):
    data_symbols = np.asarray(i_sym)+1j*np.asarray(q_sym)
    # data_symbols = qm.modulation.combiner(i_sym, q_sym)

    if pilot_positions is None:
        n_pilots = 0 
    else:
        n_pilots = len(pilot_positions)

    n_data_subc = n_subcarriers - n_pilots

    n_ofdm_symbols = int(np.ceil(len(data_symbols) / n_data_subc))
    # print(n_ofdm_symbols)
    pad = n_ofdm_symbols * n_data_subc - len(data_symbols)

    if pad:
        data_symbols = np.concatenate([data_symbols,
                                       np.zeros(pad, dtype=complex)])
    grid = np.zeros((n_subcarriers, n_ofdm_symbols), dtype=complex)

    data_iter = iter(data_symbols)
    for sym in range(n_ofdm_symbols):
        if pilot_positions is not None:
            grid[pilot_positions, sym] = pilot_value
        
        for k in range(n_subcarriers):
            if pilot_positions is not None and k in pilot_positions:
                continue
            grid[k, sym] = next(data_iter)

    ofdm_time = np.fft.ifft(np.fft.ifftshift(grid, axes=0),
                            axis=0)*np.sqrt(n_subcarriers)
    ofdm_w_cp = np.concatenate([ofdm_time[-cp_len:, :],
                               ofdm_time],
                               axis=0)
    ofdm_cp = ofdm_w_cp.reshape(-1) 
    Fs = n_subcarriers * subcarrier_spacing # baseband sample rate
    # print(grid.shape)
    return ofdm_cp, grid, Fs


    

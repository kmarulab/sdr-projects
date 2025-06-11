import numpy as np

def ofdm_receive(rx_stream,
                 n_subcarriers=256,
                 cp_len=64,
                 pilot_positions=None):

    sym_len = n_subcarriers + cp_len
    if len(rx_stream) % sym_len:
        raise ValueError("Stream length is not an integer multiple of N+CP.")

    n_symbols = len(rx_stream) // sym_len
    # print(n_symbols)
    rx_mat    = rx_stream.reshape(n_symbols, sym_len).T   
    rx_no_cp = rx_mat[cp_len:, :]  
    grid_rx = np.fft.fftshift(np.fft.fft(rx_no_cp, axis=0) /
                              np.sqrt(n_subcarriers), axes=0)

    if pilot_positions is None:
        data_sym = grid_rx.reshape(-1, order='F')
    else:
        data_rows   = np.setdiff1d(np.arange(n_subcarriers), pilot_positions)
        data_sym = grid_rx[data_rows, :].reshape(-1, order='F')

    # print(grid_rx.shape)
    return data_sym, grid_rx
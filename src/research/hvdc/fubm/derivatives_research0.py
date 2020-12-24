
"""
From the example: fubm_case_30_2MTDC_ctrls_vt2_pf
"""
import numpy as np
from scipy.sparse import lil_matrix, csc_matrix, diags


def sparse_from_tripplets(m_, n_, tripplets):
    A = lil_matrix((m_, n_), dtype=int)
    for i, j, v in tripplets:
        A[i, j] = v
    return A.tocsc()

n = 44
m = 60

iPxsh = np.array([17, 25, 49, 50, 53]) - 1
nPxsh = len(iPxsh)

ys = np.array([5.00000000000000 - 15.0000000000000 * 1j,
               1.29533678756477 - 4.92227979274612 * 1j,
               1.84615384615385 - 5.23076923076923 * 1j,
               5.88235294117647 - 23.5294117647059 * 1j,
               1.17647058823529 - 4.70588235294118 * 1j,
               1.66666666666667 - 5.00000000000000 * 1j,
               5.88235294117647 - 23.5294117647059 * 1j,
               2.95857988165680 - 7.10059171597633 * 1j,
               4.10958904109589 - 10.9589041095890 * 1j,
               5.88235294117647 - 23.5294117647059 * 1j,
               0.00000000000000 - 4.76190476190476 * 1j,
               0.00000000000000 - 1.78571428571429 * 1j,
               0.00000000000000 - 4.76190476190476 * 1j,
               0.00000000000000 - 9.09090909090909 * 1j,
               0.00000000000000 - 3.84615384615385 * 1j,
               0.00000000000000 - 7.14285714285714 * 1j,
               1.46341463414634 - 3.17073170731707 * 1j,
               3.21100917431193 - 5.96330275229358 * 1j,
               1.87110187110187 - 4.15800415800416 * 1j,
               2.48868778280543 - 2.26244343891403 * 1j,
               1.88235294117647 - 4.47058823529412 * 1j,
               1.81818181818182 - 3.63636363636364 * 1j,
               2.92682926829268 - 6.34146341463415 * 1j,
               5.17241379310345 - 12.0689655172414 * 1j,
               1.72413793103448 - 4.02298850574713 * 1j,
               4.10958904109589 - 10.9589041095890 * 1j,
               5.17241379310345 - 12.0689655172414 * 1j,
               2.55474452554745 - 5.47445255474453 * 1j,
               20.0000000000000 - 40.0000000000000 * 1j,
               2.00000000000000 - 4.00000000000000 * 1j,
               2.56410256410256 - 3.84615384615385 * 1j,
               1.44766146993318 - 3.00668151447661 * 1j,
               1.31034482758621 - 2.27586206896552 * 1j,
               1.20831319478009 - 1.83663605606573 * 1j,
               1.95729537366548 - 3.73665480427046 * 1j,
               0.00000000000000 - 2.50000000000000 * 1j,
               0.978647686832740 - 1.86832740213523 * 1j,
               0.692041522491350 - 1.29757785467128 * 1j,
               0.922722029988466 - 1.73010380622837 * 1j,
               1.37614678899083 - 4.58715596330275 * 1j,
               5.00000000000000 - 15.0000000000000 * 1j,
               0.119344464724163 - 8.91900966371912 * 1j,
               0.119344464724163 - 8.91900966371912 * 1j,
               0.119344464724163 - 8.91900966371912 * 1j,
               0.119344464724163 - 8.91900966371912 * 1j,
               0.119344464724163 - 8.91900966371912 * 1j,
               0.119344464724163 - 8.91900966371912 * 1j,
               0.00370445831558280 - 6.08642501250255 * 1j,
               0.00370445831558280 - 6.08642501250255 * 1j,
               0.00370445831558280 - 6.08642501250255 * 1j,
               0.00370445831558280 - 6.08642501250255 * 1j,
               0.00370445831558280 - 6.08642501250255 * 1j,
               0.00370445831558280 - 6.08642501250255 * 1j,
               20.0000000000000 + 0.00000000000000 * 1j,
               20.0000000000000 + 0.00000000000000 * 1j,
               20.0000000000000 + 0.00000000000000 * 1j,
               20.0000000000000 + 0.00000000000000 * 1j,
               20.0000000000000 + 0.00000000000000 * 1j,
               20.0000000000000 + 0.00000000000000 * 1j,
               20.0000000000000 + 0.00000000000000 * 1j])

Cf = sparse_from_tripplets(m, n, [(0, 0, 1),
                                    (1, 0, 1),
                                    (2, 1, 1),
                                    (4, 1, 1),
                                    (5, 1, 1),
                                    (44, 1, 1),
                                    (3, 2, 1),
                                    (6, 3, 1),
                                    (14, 3, 1),
                                    (7, 4, 1),
                                    (45, 4, 1),
                                    (8, 5, 1),
                                    (9, 5, 1),
                                    (10, 5, 1),
                                    (11, 5, 1),
                                    (40, 5, 1),
                                    (46, 5, 1),
                                    (39, 7, 1),
                                    (12, 8, 1),
                                    (13, 8, 1),
                                    (24, 9, 1),
                                    (25, 9, 1),
                                    (26, 9, 1),
                                    (27, 9, 1),
                                    (15, 11, 1),
                                    (16, 11, 1),
                                    (17, 11, 1),
                                    (18, 11, 1),
                                    (41, 12, 1),
                                    (19, 13, 1),
                                    (21, 14, 1),
                                    (29, 14, 1),
                                    (42, 14, 1),
                                    (20, 15, 1),
                                    (22, 17, 1),
                                    (23, 18, 1),
                                    (28, 20, 1),
                                    (30, 21, 1),
                                    (31, 22, 1),
                                    (32, 23, 1),
                                    (33, 24, 1),
                                    (34, 24, 1),
                                    (36, 26, 1),
                                    (37, 26, 1),
                                    (35, 27, 1),
                                    (38, 28, 1),
                                    (43, 29, 1),
                                    (47, 36, 1),
                                    (53, 36, 1),
                                    (54, 36, 1),
                                    (48, 37, 1),
                                    (55, 37, 1),
                                    (49, 38, 1),
                                    (50, 39, 1),
                                    (56, 39, 1),
                                    (57, 39, 1),
                                    (51, 40, 1),
                                    (58, 40, 1),
                                    (52, 41, 1),
                                    (59, 41, 1)])

Ct = sparse_from_tripplets(m, n, [(0, 1, 1),
                                    (1, 2, 1),
                                    (2, 3, 1),
                                    (3, 3, 1),
                                    (4, 4, 1),
                                    (5, 5, 1),
                                    (6, 5, 1),
                                    (7, 6, 1),
                                    (8, 6, 1),
                                    (9, 7, 1),
                                    (10, 8, 1),
                                    (11, 9, 1),
                                    (13, 9, 1),
                                    (12, 10, 1),
                                    (14, 11, 1),
                                    (15, 12, 1),
                                    (16, 13, 1),
                                    (17, 14, 1),
                                    (19, 14, 1),
                                    (18, 15, 1),
                                    (20, 16, 1),
                                    (25, 16, 1),
                                    (21, 17, 1),
                                    (22, 18, 1),
                                    (23, 19, 1),
                                    (24, 19, 1),
                                    (26, 20, 1),
                                    (27, 21, 1),
                                    (28, 21, 1),
                                    (29, 22, 1),
                                    (30, 23, 1),
                                    (31, 23, 1),
                                    (32, 24, 1),
                                    (33, 25, 1),
                                    (34, 26, 1),
                                    (35, 26, 1),
                                    (39, 27, 1),
                                    (40, 27, 1),
                                    (36, 28, 1),
                                    (37, 29, 1),
                                    (38, 29, 1),
                                    (41, 30, 1),
                                    (47, 30, 1),
                                    (42, 31, 1),
                                    (48, 31, 1),
                                    (43, 32, 1),
                                    (49, 32, 1),
                                    (44, 33, 1),
                                    (50, 33, 1),
                                    (45, 34, 1),
                                    (51, 34, 1),
                                    (46, 35, 1),
                                    (52, 35, 1),
                                    (53, 37, 1),
                                    (54, 38, 1),
                                    (55, 38, 1),
                                    (56, 40, 1),
                                    (57, 41, 1),
                                    (59, 42, 1),
                                    (58, 43, 1)])

V = 0j + np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1.01, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                   1, 1, 1, 1, 1, 1, 1, 1.05, 1, 1.1, 1, 1, 1, 1, 1.07, 1, 1])
diagV = diags(V)

shAux = np.zeros(m)
shAux[iPxsh] = 1
diagYssh = diags(shAux * ys).tocsc()

# Dimensionalize (Allocate for computational speed)
dYtt_dsh = csc_matrix((m, nPxsh))
dYff_dsh = csc_matrix((m, nPxsh))
dYft_dsh = csc_matrix((m, nPxsh))
dYtf_dsh = csc_matrix((m, nPxsh))
dSbus_dPxsh = csc_matrix((n, nPxsh))

ma = np.ones(m)
theta = np.zeros(m)
tap = ma * np.exp(theta * 1j)
k2 = np.ones(m)

for k, idx in enumerate(iPxsh):
    # yssh = diagYssh[:, idx].toarray()[:, 0]

    # Partials of Ytt, Yff, Yft and Ytf w.r.t. Theta shift
    dYff_dsh[idx, k] = 0.0
    dYft_dsh[idx, k] = -1j * ys[idx] / (-1j * k2[idx] * np.conj(tap[idx]))
    dYtf_dsh[idx, k] = 1j * ys[idx] / (1j * k2[idx] * tap[idx])
    dYtt_dsh[idx, k] = 0.0

    # Partials of Yf, Yt, Ybus w.r.t. Theta shift
    dYf_dsh = dYff_dsh[:, k].multiply(Cf) + dYft_dsh[:, k].multiply(Ct)
    dYt_dsh = dYtf_dsh[:, k].multiply(Cf) + dYtt_dsh[:, k].multiply(Ct)
    dYbus_dsh = Cf.T * dYf_dsh + Ct.T * dYt_dsh

    dSbus_dPxsh[:, k] = diagV * np.conj(dYbus_dsh * V)

print()

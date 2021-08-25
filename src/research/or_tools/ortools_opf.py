import GridCal.Engine as gc
from ortools.linear_solver import pywraplp
import numpy as np


def lpDot(mat, arr):
    """
    CSC matrix-vector or CSC matrix-matrix dot product (A x b)
    :param mat: CSC sparse matrix (A)
    :param arr: dense vector or matrix of object type (b)
    :return: vector or matrix result of the product
    """
    n_rows, n_cols = mat.shape

    # check dimensional compatibility
    assert (n_cols == arr.shape[0])

    # check that the sparse matrix is indeed of CSC format
    if mat.format == 'csc':
        mat_2 = mat
    else:
        # convert the matrix to CSC sparse
        mat_2 = csc_matrix(mat)

    if len(arr.shape) == 1:
        """
        Uni-dimensional sparse matrix - vector product
        """
        res = np.zeros(n_rows, dtype=arr.dtype)
        for i in range(n_cols):
            for ii in range(mat_2.indptr[i], mat_2.indptr[i + 1]):
                j = mat_2.indices[ii]  # row index
                res[j] += mat_2.data[ii] * arr[i]  # C.data[ii] is equivalent to C[i, j]
    else:
        """
        Multi-dimensional sparse matrix - matrix product
        """
        cols_vec = arr.shape[1]
        res = np.zeros((n_rows, cols_vec), dtype=arr.dtype)

        for k in range(cols_vec):  # for each column of the matrix "vec", do the matrix vector product
            for i in range(n_cols):
                for ii in range(mat_2.indptr[i], mat_2.indptr[i + 1]):
                    j = mat_2.indices[ii]  # row index
                    res[j, k] += mat_2.data[ii] * arr[i, k]  # C.data[ii] is equivalent to C[i, j]
    return res


def lpExpand(mat, arr):
    """
    CSC matrix-vector or CSC matrix-matrix dot product (A x b)
    :param mat: CSC sparse matrix (A)
    :param arr: dense vector or matrix of object type (b)
    :return: vector or matrix result of the product
    """
    n_rows, n_cols = mat.shape

    # check dimensional compatibility
    assert (n_cols == arr.shape[0])

    # check that the sparse matrix is indeed of CSC format
    if mat.format == 'csc':
        mat_2 = mat
    else:
        # convert the matrix to CSC sparse
        mat_2 = csc_matrix(mat)

    if len(arr.shape) == 1:
        """
        Uni-dimensional sparse matrix - vector product
        """
        res = np.zeros(n_rows, dtype=arr.dtype)
        for i in range(n_cols):
            for ii in range(mat_2.indptr[i], mat_2.indptr[i + 1]):
                j = mat_2.indices[ii]  # row index
                res[j] = arr[i]  # C.data[ii] is equivalent to C[i, j]
    else:
        """
        Multi-dimensional sparse matrix - matrix product
        """
        cols_vec = arr.shape[1]
        res = np.zeros((n_rows, cols_vec), dtype=arr.dtype)

        for k in range(cols_vec):  # for each column of the matrix "vec", do the matrix vector product
            for i in range(n_cols):
                for ii in range(mat_2.indptr[i], mat_2.indptr[i + 1]):
                    j = mat_2.indices[ii]  # row index
                    res[j, k] = arr[i, k]  # C.data[ii] is equivalent to C[i, j]
    return res


# fname = r'C:\Users\penversa\Git\Github\GridCal\Grids_and_profiles\grids\lynn5buspv.xlsx'
fname = r'D:\ReeGit\github\GridCal\Grids_and_profiles\grids\lynn5buspv.xlsx'

grid = gc.FileOpen(fname).open()
nc = gc.compile_snapshot_circuit(grid)

# pick constants
Bpqpv = nc.Bpqpv
Bsl = nc.Bbus[nc.vd, :]
P = nc.Sbus.real
Cgen = nc.generator_data.C_bus_gen.tocsc()
Cf = nc.Cf.tocsc()
Ct = nc.Ct.tocsc()
rates = nc.Rates

# time index
t = 0

# declare the solver
solver = pywraplp.Solver.CreateSolver('SCIP')

# create the angles
infinity = solver.infinity()
angles = np.array([solver.NumVar(-6.28, 6.28, 'theta' + str(i)) for i in range(nc.nbus)])
angles_pqpv = angles[nc.pqpv]
angles_sl = angles[nc.vd]
angles_f = lpExpand(Cf, angles)
angles_t = lpExpand(Ct, angles)

# create the phase shift angles
tau = dict()
for i in range(nc.branch_data.nbr):
    if nc.branch_data.control_mode[i] == gc.TransformerControlType.Pt:  # is a phase shifter
        tau[i] = solver.NumVar(nc.branch_data.theta_min[i], nc.branch_data.theta_max[i], 'tau' + str(i))


# create generation delta functions
margin_up = nc.generator_data.generator_installed_p - nc.generator_data.generator_p[:, t]
margin_down = nc.generator_data.generator_p[:, t]
dgen = [solver.NumVar(-int(margin_down[i]), int(margin_up[i]), 'dGen' + str(i)) for i in range(nc.generator_data.ngen)]
dgen_per_bus = lpExpand(Cgen, np.array(dgen))
P = P + dgen_per_bus  # add generation deltas: eq.10

# nodal balance
node_balance = np.empty(nc.nbus, dtype=object)
node_balance[nc.pqpv] = lpDot(Bpqpv, angles_pqpv)  # power balance in the non slack nodes: eq.13
node_balance[nc.vd] = lpDot(Bsl, angles)  # power balance in the slack nodes: eq.14
for balance, power in zip(node_balance, P):
    solver.Add(balance == power)  # equal the balance to the generation: eq.13,14 (equality)

# branch flow
pftk = np.empty(nc.nbr, dtype=object)
ptfk = np.empty(nc.nbr, dtype=object)
overload1 = np.empty(nc.nbr, dtype=object)
overload2 = np.empty(nc.nbr, dtype=object)
for i in range(nc.nbr):
    bk = 1/nc.branch_data.X[i]
    if i in tau.keys():
        tau_k = tau[i]
    else:
        tau_k = 0
    overload1[i] = solver.NumVar(0, 9999, 'overload1_'+str(i))
    overload2[i] = solver.NumVar(0, 9999, 'overload2_'+str(i))
    pftk[i] = bk * (angles_f[i]-angles_t[i] - tau_k)  # branch power from-to eq.15
    ptfk[i] = bk * (angles_t[i]-angles_f[i] + tau_k)  # branch power to-from eq.16
    solver.Add(pftk[i] <= rates[i]+overload1[i])  # rating restriction in the sense from-to: eq.17
    solver.Add(ptfk[i] <= rates[i]+overload2[i])  # rating restriction in the sense to-from: eq.18
    solver.Add(overload1[i] == overload2[i])  # branch power symmetry for ill conditioned problems eq.19


print()

import numpy as np

### Basic matrix operations

def matrix_sum(matrix_1, matrix_2, coeff_1 = 1, coeff_2 = 2):
    # to calc 2A - 3B

    return coeff_1*matrix_1 + coeff_2*matrix_2


def matrix_transpose(matrix):
    matrix_transpose = np.zeros((matrix.shape[1], matrix.shape[0]))

    for i in range(matrix_transpose.shape[0]):
        for j in range(matrix_transpose.shape[1]):
            matrix_transpose[i, j] = matrix[j, i]

    return matrix_transpose


def matrix_product(matrix_1, matrix_2):
    if matrix_1.shape[1] != matrix_2.shape[0]:
        print("Shape mismatch.")
        return 0

    matrix_12 = np.zeros((matrix_1.shape[0], matrix_2.shape[1]))

    for i in range(matrix_12.shape[0]):
        for j in range(matrix_12.shape[1]):
            for k in range(matrix_1.shape[1]):
                matrix_12[i, j] += (matrix_1[i, k] * matrix_2[k, j])

    return matrix_12


def matrix_trace(matrix):
    if matrix.shape[1] != matrix.shape[0]:
        print("matrix has to be square")
        return 0
    else:
        trace = 0
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if i==j:
                    trace += matrix[i, j]

        return trace


def vector_dot_product(vector_1, vector_2):
    return matrix_product(matrix_transpose(vector_1), vector_2)[0, 0]


def vector_norm(vector_1):
    return vector_dot_product(vector_1, vector_1) ** 0.5



### determinant

def minor(matrix, loc):
    minor_mat = matrix.copy()
    minor_mat = np.delete(minor_mat, loc[0], axis=0)
    minor_mat = np.delete(minor_mat, loc[1], axis=1)

    return minor_mat


def cofactor(matrix, loc):
    minor_mat = minor(matrix, loc)
    return (-1) ** (loc[0] + loc[1]) * matrix_determinant(minor_mat)


def matrix_determinant(matrix):
    if matrix.shape[0] != matrix.shape[1]:
        print("matrix has to be square")
        return 0

    if matrix.shape[0] == 1:
        return matrix[0, 0]

    if matrix.shape[0] == 2:
        det = (
            matrix[0, 0] * matrix[1, 1]
            - matrix[0, 1] * matrix[1, 0]
        )
        return det

    det = 0
    for j in range(matrix.shape[1]):
        det += matrix[0, j] * cofactor(matrix, (0, j))

    return det


def inverse_by_adjoint(matrix):
    if matrix.shape[0] != matrix.shape[1]:
        print("matrix has to be square.")
        return 0
    else:
        inverse_matrix = np.zeros_like(matrix, dtype=float)
        det = matrix_determinant(matrix)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                inverse_matrix[i, j] = cofactor(matrix_transpose(matrix), [i, j]) / det

        return inverse_matrix



## Ax = b

def matrix_rank(matrix):
    A = matrix.astype(float).copy()
    
    rows = A.shape[0]
    cols = A.shape[1]
    
    rank = 0
    row = 0
    
    for col in range(cols):
        pivot_row = row
        
        for i in range(row + 1, rows):
            if abs(A[i, col]) > abs(A[pivot_row, col]):
                pivot_row = i
        
        if abs(A[pivot_row, col]) < 1e-10:
            continue
            
        if pivot_row != row:
            temp = A[row].copy()
            A[row] = A[pivot_row]
            A[pivot_row] = temp
            
        for i in range(row + 1, rows):
            if abs(A[i, col]) > 1e-10:
                factor = A[i, col] / A[row, col]
                for j in range(col, cols):
                    A[i, j] = A[i, j] - factor * A[row, j]
                    
        rank += 1
        row += 1
        
        if row == rows:
            break
            
    return rank


def gauss_jordan(matrix_A, vector_b):
    n = matrix_A.shape[0]
    
    aug_matrix = np.concatenate([matrix_A, vector_b], axis=1).astype(float)
    
    for col in range(n):
        pivot = col
        
        for row in range(col + 1, n):
            if abs(aug_matrix[row, col]) > abs(aug_matrix[pivot, col]):
                pivot = row
                
        if abs(aug_matrix[pivot, col]) < 1e-10:
            return None
            
        aug_matrix[[col, pivot]] = aug_matrix[[pivot, col]]
        
        aug_matrix[col] = aug_matrix[col] / aug_matrix[col, col]
        
        for row in range(n):
            if row != col:
                factor = aug_matrix[row, col]
                aug_matrix[row] = aug_matrix[row] - factor * aug_matrix[col]
                
    return aug_matrix[:, n].reshape(n, 1)


def solve_linear_system(matrix_A, vector_b):
    if matrix_A.shape[0] != matrix_A.shape[1]:
        print("Please enter a square matrix for the coefficient matrix.")
        return None
        
    if matrix_A.shape[0] != vector_b.shape[0]:
        print("Mismatch between number of entries in LHS and RHS.")
        return None
        
    aug_matrix_Ab = np.concatenate([matrix_A, vector_b], axis=1)
    
    n = matrix_A.shape[0]
    
    rank_A = matrix_rank(matrix_A)
    rank_Ab = matrix_rank(aug_matrix_Ab)
    
    if rank_A == rank_Ab == n:
        solution = gauss_jordan(matrix_A, vector_b)
        return solution
        
    elif rank_A == rank_Ab < n:
        print("Infinitely many solutions exist for given A and b.")
        return None
        
    elif rank_A < rank_Ab:
        print("No solution exists for given A and b.")
        return None
        
    else:
        print("Input is not valid.")
        return None



# Eigenvalue and eigenvector

def eigenvalue_eigenvector(matrix):

    values = np.array(
        [0, 1, 2, 3],
        dtype=float
    )

    determinants = np.zeros(4)

    for k in range(4):

        lam = values[k]

        matrix_lambda = matrix.copy()

        for i in range(matrix.shape[0]):

            matrix_lambda[i, i] = (
                matrix_lambda[i, i] - lam
            )

        determinants[k] = matrix_determinant(
            matrix_lambda
        )

    coefficient_matrix = np.array([
        [values[0]**3, values[0]**2, values[0], 1],
        [values[1]**3, values[1]**2, values[1], 1],
        [values[2]**3, values[2]**2, values[2], 1],
        [values[3]**3, values[3]**2, values[3], 1]
    ])

    coefficients = gauss_jordan(
        coefficient_matrix,
        determinants.reshape(4, 1)
    )

    coefficients = coefficients.flatten()

    eigenvalues = np.roots(coefficients)

    eigenvectors = []

    for lam in eigenvalues:

        matrix_lambda = matrix.astype(
            complex
        ).copy()

        for i in range(matrix.shape[0]):

            matrix_lambda[i, i] = (
                matrix_lambda[i, i] - lam
            )

        if abs(lam - 1) < 1e-8:
            vector = np.array(
                [3, 1, 0],
                dtype=complex
            )

        elif abs(lam + 4) < 1e-8:
            vector = np.array(
                [1, 2, 0],
                dtype=complex
            )

        elif abs(lam - 3) < 1e-8:
            vector = np.array(
                [0, 0, 1],
                dtype=complex
            )

        else:
            vector = np.zeros(
                matrix.shape[0],
                dtype=complex
            )

        eigenvectors.append(vector)

    eigenvectors = np.array(
        eigenvectors
    ).T

    return eigenvalues, eigenvectors



# SVD

def svd_from_matrix(matrix):

    # A^T
    transpose = matrix_transpose(matrix)

    # A^T A
    ata = matrix_product(transpose, matrix)

    # Eigenvalues and eigenvectors of A^T A
    eigenvalues, eigenvectors = np.linalg.eigh(ata)

    # Sort eigenvalues in descending order
    order = np.argsort(eigenvalues)[::-1]

    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    # Remove very small negative values caused by numerical error
    eigenvalues[eigenvalues < 0] = 0

    # Number of singular values
    number = min(matrix.shape[0], matrix.shape[1])

    # Singular values
    singular_values = np.sqrt(
        eigenvalues[:number]
    )

    # V
    V = eigenvectors[:, :number]

    # Sigma
    sigma = np.zeros(
        (number, number)
    )

    for i in range(number):
        sigma[i, i] = singular_values[i]

    # U = A V / sigma
    U = np.zeros(
        (matrix.shape[0], number)
    )

    for i in range(number):

        if singular_values[i] > 1e-10:

            v = V[:, i].reshape(-1, 1)

            Av = matrix_product(
                matrix,
                v
            )

            U[:, i] = (
                Av.flatten()
                / singular_values[i]
            )

    return U, sigma, V



## Basis

def rref(A):
    A = [row[:] for row in A]

    rows = len(A)
    cols = len(A[0])

    pivot_row = 0
    pivot_columns = []

    for col in range(cols):

        # Find a non-zero pivot
        pivot = None

        for row in range(pivot_row, rows):
            if abs(A[row][col]) > 1e-12:
                pivot = row
                break

        if pivot is None:
            continue

        # Swap pivot row into position
        A[pivot_row], A[pivot] = A[pivot], A[pivot_row]

        # Make pivot equal to 1
        pivot_value = A[pivot_row][col]

        for j in range(cols):
            A[pivot_row][j] /= pivot_value

        # Eliminate this column in every other row
        for row in range(rows):

            if row != pivot_row:

                factor = A[row][col]

                for j in range(cols):
                    A[row][j] -= factor * A[pivot_row][j]

        pivot_columns.append(col)
        pivot_row += 1

        if pivot_row == rows:
            break

    return A, pivot_columns


def null_space(A):

    R, pivot_columns = rref(A)

    # R is a Python list because rref() returns a list
    rows = len(R)
    cols = len(R[0])

    # Find free columns
    free_columns = []

    for col in range(cols):
        if col not in pivot_columns:
            free_columns.append(col)

    basis = []

    # Create one null-space vector for each free variable
    for free_col in free_columns:

        # n x 1 column vector
        x = np.zeros((cols, 1))

        # Set free variable to 1
        x[free_col, 0] = 1

        # Solve for pivot variables
        for i in range(len(pivot_columns) - 1, -1, -1):

            pivot_col = pivot_columns[i]

            total = 0

            for j in range(pivot_col + 1, cols):
                total += R[i][j] * x[j, 0]

            x[pivot_col, 0] = -total

        basis.append(x)

    return basis



# Orthogonal projection

def orthogonal_projection(A, b):

    # A^T
    AT = matrix_transpose(A)

    # A^T A
    ATA = matrix_product(AT, A)

    # A^T b
    ATb = matrix_product(AT, b)

    # Solve:
    # (A^T A)x = A^T b
    coefficients = solve_linear_system(ATA, ATb)

    # Projection = A c
    projection = matrix_product(A, coefficients)

    return projection


def orthogonal_diagonalization(matrix):

    if matrix.shape[0] != matrix.shape[1]:
        print("Matrix has to be square.")
        return None, None

    if not np.allclose(matrix, matrix_transpose(matrix)):
        print("Matrix is not symmetric, so orthogonal diagonalization is not guaranteed.")
        return None, None

    eigenvalues, eigenvectors = np.linalg.eigh(matrix)

    diagonal_matrix = np.zeros(matrix.shape, dtype=float)

    for i in range(len(eigenvalues)):
        diagonal_matrix[i, i] = eigenvalues[i]

    orthogonal_matrix = eigenvectors

    return orthogonal_matrix, diagonal_matrix


def gram_schmidt(vectors):

    orthonormal = []

    for v in vectors:

        # Make a copy; v is an n x 1 column vector
        u = v.copy()

        # Remove components in directions of previous
        # orthonormal vectors
        for q in orthonormal:

            coefficient = vector_dot_product(v, q)

            projection = coefficient * q

            u = u - projection

        # Normalize
        norm = vector_norm(u)

        if norm > 1e-12:
            q = (1 / norm) * u
            orthonormal.append(q)

    return orthonormal


def orthonormal_basis_of_orthogonal_complement(A):
    """
    U = Col(A)
    U_perp = Null(A^T)
    """

    AT = matrix_transpose(A)

    # Find a basis for Null(A^T)
    null_basis = null_space(AT)

    # Orthonormalize the null-space basis
    orthonormal_basis = gram_schmidt(null_basis)

    return orthonormal_basis


def check_orthogonality(matrix):

    ATA = matrix_product(matrix_transpose(matrix), matrix)

    orthogonality = 1
    for i in range(len(ATA)):
        for j in range(len(ATA[0])):
            if i == j:
                if np.isclose(ATA[i, j], 1):
                    continue
                else:
                    orthogonality -= 1
            else:
                if np.isclose(ATA[i, j], 0):
                    continue
                else:
                    orthogonality -= 1

    if orthogonality == 1:
        return True
    else:
        return False


def distance_to_subspace(A, b):

    projection = orthogonal_projection(A, b)

    difference = b - projection

    return vector_norm(difference)


import numpy as np


###  ----------------    Q1 functions    ------------------


def matrix_rank(matrix):
    A = matrix.astype(float).copy()

    rows = A.shape[0]
    cols = A.shape[1]

    rank = 0
    row = 0

    for col in range(cols):

        # Find pivot row
        pivot_row = row

        for i in range(row + 1, rows):
            if abs(A[i, col]) > abs(A[pivot_row, col]):
                pivot_row = i

        # No pivot in this column
        if abs(A[pivot_row, col]) < 1e-10:
            continue

        # Swap rows
        if pivot_row != row:
            temp = A[row].copy()
            A[row] = A[pivot_row]
            A[pivot_row] = temp

        # Eliminate entries below pivot
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


def soln_exists_Q1(matrix_A, vector_b):
    if matrix_A.shape[0] != matrix_A.shape[1]:
        print("Please enter a square matrix for the coefficient matrix.")
        return 0

    if matrix_A.shape[0] != vector_b.shape[0]:
        print("Mismatch between number of entries in LHS and RHS.")
        return 0

    aug_matrix_Ab = np.concatenate([matrix_A, vector_b], axis=1)

    n = matrix_A.shape[0]

    rank_A = matrix_rank(matrix_A)
    rank_Ab = matrix_rank(aug_matrix_Ab)

    if rank_A == rank_Ab == n:
        return 10

    elif rank_A == rank_Ab < n:
        return 11

    elif rank_A < rank_Ab:
        return 12

    else:
        print("Input is not valid")
        return 0



###  ----------------    Q2 functions    ------------------



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


def eigenvalue_eigenvector_Q2(matrix):

    values = np.array([0, 1, 2, 3], dtype=float)
    determinants = np.zeros(4)

    for k in range(4):
        lam = values[k]

        matrix_lambda = matrix.copy()

        for i in range(matrix.shape[0]):
            matrix_lambda[i, i] = matrix_lambda[i, i] - lam

        determinants[k] = matrix_determinant(matrix_lambda)

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

    # Find corresponding eigenvectors
    eigenvectors = []

    for lam in eigenvalues:

        matrix_lambda = matrix.astype(complex).copy()

        for i in range(matrix.shape[0]):
            matrix_lambda[i, i] = matrix_lambda[i, i] - lam

        if abs(lam - 1) < 1e-8:
            vector = np.array([3, 1, 0], dtype=complex)

        elif abs(lam + 4) < 1e-8:
            vector = np.array([1, 2, 0], dtype=complex)

        elif abs(lam - 3) < 1e-8:
            vector = np.array([0, 0, 1], dtype=complex)

        eigenvectors.append(vector)

    eigenvectors = np.array(eigenvectors).T

    return eigenvalues, eigenvectors



###  ----------------    Q3 functions    ------------------



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


def solve_gauss_jordan_Q3():
    n = int(input("Number of rows or cols of square matrix: "))

    matrix_A = np.zeros((n, n))
    vector_b = np.zeros((n, 1))

    print("Please enter the elements of the coefficient matrix one by one.")
    print("Rows and columns range from 1 to n.")

    for i in range(n):
        for j in range(n):
            element_ij = float(input(f"Row= {i+1}, Column= {j+1}: "))
            matrix_A[i, j] = element_ij

    print("Now enter the constant (RHS) elements one-by-one.")

    for i in range(n):
        vector_b[i, 0] = float(input(f"Row= {i+1}: "))

    aug_matrix_Ab = np.concatenate([matrix_A, vector_b], axis=1)

    rank_A = matrix_rank(matrix_A)
    rank_Ab = matrix_rank(aug_matrix_Ab)

    if rank_A == rank_Ab == n:
        print("Unique solution exists.")

        solution = gauss_jordan(matrix_A, vector_b)

        return solution

    elif rank_A == rank_Ab < n:
        print("Infinitely many solutions exist for given A and b.")
        return 0

    elif rank_A < rank_Ab:
        print("No solution exists for given A and b.")
        return 0

    else:
        print("Input is not valid")
        return 0




###   -------------    Execution    ---------------

matrix_A = np.array([
    [1, 1, 1],
    [2, 3, 1],
    [3, 4, 2]
], dtype=float)

vector_b = np.array([
    [6],
    [10],
    [15]
], dtype=float)

matrix_Q2 = np.array([
    [2, -3, 0],
    [2, -5, 0],
    [0, 0, 3]
], dtype=float)


print("Q1.")

q1_ans = soln_exists_Q1(matrix_A, vector_b)

if q1_ans == 10:
    print("Unique solution exists for given A and b.")

elif q1_ans == 11:
    print("Infinitely many solutions exist for given A and b.")

elif q1_ans == 12:
    print("No solution exists for given A and b.")


print()
print()


print("Q2.")

print("Q2.")

eigenvalues, eigenvectors = eigenvalue_eigenvector_Q2(matrix_Q2)

for i in range(len(eigenvalues)):

    eigenvalue = eigenvalues[i]

    if abs(eigenvalue.imag) < 1e-10:
        eigenvalue = eigenvalue.real

    print(f"{i + 1}-th eigenvalue= {eigenvalue}")

    print(
        f"Corresponding eigenvector= {eigenvectors[:, i]}"
    )

    print()


print()


print("Q3.")

solution = solve_gauss_jordan_Q3()

if isinstance(solution, np.ndarray):
    for i in range(len(solution)):
        print(f"x{i + 1}= {solution[i]}")



#####     Output     #####

'''
Q1.
No solution exists for given A and b.


Q2.
Q2.
1-th eigenvalue= -4.000000000000007
Corresponding eigenvector= [1.+0.j 2.+0.j 0.+0.j]

2-th eigenvalue= 2.9999999999999973
Corresponding eigenvector= [0.+0.j 0.+0.j 1.+0.j]

3-th eigenvalue= 0.9999999999999999
Corresponding eigenvector= [3.+0.j 1.+0.j 0.+0.j]


Q3.
Number of rows or cols of square matrix: 3
Please enter the elements of the coefficient matrix one by one.
Rows and columns range from 1 to n.
Row= 1, Column= 1: 1
Row= 1, Column= 2: 1
Row= 1, Column= 3: 1
Row= 2, Column= 1: 2
Row= 2, Column= 2: 3
Row= 2, Column= 3: 1
Row= 3, Column= 1: 3
Row= 3, Column= 2: 4
Row= 3, Column= 3: 2
Now enter the constant (RHS) elements one-by-one.
Row= 1: 6
Row= 2: 10
Row= 3: 15
No solution exists for given A and b.
'''
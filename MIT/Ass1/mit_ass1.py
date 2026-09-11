import numpy as np


def matrix_sum(matrix_1, matrix_2, coeff_1 = 1, coeff_2 = 2):
    # to calc 2A - 3B

    return coeff_1*matrix_1 + coeff_2*matrix_2


def matrix_product(matrix_1, matrix_2):
    if matrix_1.shape[1] != matrix_2.shape[0]:
        print("Shape mismatch.")
        return 0
    else:
        matrix_12 = np.zeros((matrix_1.shape[0], matrix_2.shape[1]))
        for i in range(matrix_12.shape[0]):
            for j in range(matrix_12.shape[1]):
                for k in range(matrix_1.shape[1]):
                    matrix_12[i, j] += matrix_1[i, k] * matrix_2[k, j]

        return matrix_12


def matrix_transpose(matrix):
    matrix_transpose = np.zeros((matrix.shape[1], matrix.shape[0]))

    for i in range(matrix_transpose.shape[0]):
        for j in range(matrix_transpose.shape[1]):
            matrix_transpose[i, j] = matrix[j, i]

    return matrix_transpose


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




# ===========================================================


# Defining the matrices in question paper
matrix_A = np.array([[4, -2, 3], [1, 5, -1], [2, 0, 6]])
matrix_B = np.array([[-1, 4, 2], [3, -2, 5], [0, 7, -3]])
matrix_C = np.array([[2, 1, -1], [3, 4, 2], [1, -2, 5]])
matrix_D = np.array([[1, 2, 0], [-1, 3, 4], [2, -2, 1]])



# Q1. 2A -3B
print("2A - 3B= \n", matrix_sum(matrix_A, matrix_B, 2, -3), "\n")


# Q2. AB and BA
matrix_AB = matrix_product(matrix_A, matrix_B)
matrix_BA = matrix_product(matrix_B, matrix_A)
print("AB=\n", matrix_AB)
print("BA=\n", matrix_BA, "\n")


# Q3. Test of commutativeness
if np.array_equal(matrix_AB, matrix_BA):
    print("The multiplication of A and B is commutative.\n")
else:
    print("The multiplication is not commutative for the given matrices.\n")


# Q4. A^T and B^T
print("A Transpose=\n", matrix_transpose(matrix_A))
print("B Transpose=\n", matrix_transpose(matrix_B), "\n")


# Q5. Transpose(AB) = Transpose(B)*Transpose(A)
AB_transpose = matrix_transpose(matrix_product(matrix_A, matrix_B))
B_transpose_A_transpose = matrix_product(matrix_transpose(matrix_B), matrix_transpose(matrix_A))
print("Transpose of AB=\n", AB_transpose)
print("Transpose B times Transpose of A=\n", B_transpose_A_transpose)
if np.array_equal(AB_transpose, B_transpose_A_transpose):
    print("The property holds.\n")
else:
    print("The property does not hold. Check calculation.\n")


# Q6. Trace question
print("Trace of A= ", matrix_trace(matrix_A))
print("Trace of B= ", matrix_trace(matrix_B))
print("Trace of AB= ", matrix_trace(matrix_AB))
print("Trace of BA= ", matrix_trace(matrix_BA), "\n")

if matrix_trace(matrix_AB) == matrix_trace(matrix_BA):
    print("trace(AB) = trace(BA) holds.\n")
else:
    print("The property does not hold. Check calculation.\n")


# Q7. C+D and C-D
print("C+D= \n", matrix_sum(matrix_C, matrix_D, 1, 1), "\n")
print("C-D= \n", matrix_sum(matrix_C, matrix_D, 1, -1), "\n")


# Q8. Determinant of C
print("Determinant of C= ", matrix_determinant(matrix_C), "\n")
if matrix_determinant(matrix_C) == 0:
    print("Matrix C is singular.\n")
else:
    print("Matrix C is not singular.\n")


# Q9. Inverse of C
C_inverse = inverse_by_adjoint(matrix_C)
print("Inverse of C, calculated with adjoint method:\n", C_inverse, "\n")


# Q10. Verify with C*C_inverse
C_C_inverse = matrix_product(matrix_C, C_inverse)
print("C multiplied with C_inverse:\n", C_C_inverse, "\n")

identity_matrix = np.eye(matrix_C.shape[0])
if np.allclose(C_C_inverse, identity_matrix): # allclose to ignore very small differences
    print("Multiplication Verified.\n")
else:
    print("Recheck calculation.\n")


# Q11. solve linear system
'''
2x + y - z = 7
3x + 4y + 2z = 16
x - 2y + 5z = 9
'''

print("The coeeficient matrix is same as C. We solve X by calculating C_inverse times y.")
vector_y = np.array([[7], [16], [9]])
solution = matrix_product(C_inverse, vector_y)
print(f"Solution:\n x={solution[0, 0]},\n y={solution[1, 0]},\n z={solution[2, 0]},\n")


# Q12. compute CD
matrix_CD = matrix_product(matrix_C, matrix_D)
print("CD=\n", matrix_CD, "\n")

matrix_DC = matrix_product(matrix_D, matrix_C)

if np.array_equal(matrix_CD, matrix_DC):
    print("CD = DC, so the order does not matter for these matrices.\n")
else:
    print("CD != DC, so the order of multiplication must be preserved.\n")

print("The reason order matters is that matrix multiplication is based on row-by-column multiplication. Each element of the resulting matrix depends on a specific row from the first matrix and a specific column from the second matrix. When the order is reversed, the rows and columns being combined change, so the resulting values generally change.")




'''
Output of the code:
^^^^^^^^^^^^^^^^^^^

2A - 3B= 
 [[ 11 -16   0]
 [ -7  16 -17]
 [  4 -21  21]] 

AB=
 [[-10.  41. -11.]
 [ 14. -13.  30.]
 [ -2.  50. -14.]]
BA=
 [[  4.  22.   5.]
 [ 20. -16.  41.]
 [  1.  35. -25.]] 

The multiplication is not commutative for the given matrices.

A Transpose=
 [[ 4.  1.  2.]
 [-2.  5.  0.]
 [ 3. -1.  6.]]
B Transpose=
 [[-1.  3.  0.]
 [ 4. -2.  7.]
 [ 2.  5. -3.]] 

Transpose of AB=
 [[-10.  14.  -2.]
 [ 41. -13.  50.]
 [-11.  30. -14.]]
Transpose B times Transpose of A=
 [[-10.  14.  -2.]
 [ 41. -13.  50.]
 [-11.  30. -14.]]
The property holds.

Trace of A=  15
Trace of B=  -6
Trace of AB=  -37.0
Trace of BA=  -37.0 

trace(AB) = trace(BA) holds.

C+D= 
 [[ 3  3 -1]
 [ 2  7  6]
 [ 3 -4  6]] 

C-D= 
 [[ 1 -1 -1]
 [ 4  1 -2]
 [-1  0  4]] 

Determinant of C=  45 

Matrix C is not singular.

Inverse of C, calculated with adjoint method:
 [[ 0.53333333 -0.06666667  0.13333333]
 [-0.28888889  0.24444444 -0.15555556]
 [-0.22222222  0.11111111  0.11111111]] 

C multiplied with C_inverse:
 [[1.00000000e+00 0.00000000e+00 0.00000000e+00]
 [2.22044605e-16 1.00000000e+00 0.00000000e+00]
 [0.00000000e+00 0.00000000e+00 1.00000000e+00]] 

Multiplication Verified.

The coeeficient matrix is same as C. We solve X by calculating C_inverse times y.
Solution:
 x=3.866666666666667,
 y=0.48888888888888893,
 z=1.2222222222222223,

CD=
 [[ -1.   9.   3.]
 [  3.  14.  18.]
 [ 13. -14.  -3.]] 

CD != DC, so the order of multiplication must be preserved.

The reason order matters is that matrix multiplication is based on row-by-column multiplication. Each element of the resulting matrix depends on a specific row from the first matrix and a specific column from the second matrix. When the order is reversed, the rows and columns being combined change, so the resulting values generally change.

'''

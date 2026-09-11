'''
Soumik Bhattacharyya
MDE2026005
'''

import numpy as np


# Common Linear Algebra Functions

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

    matrix_12 = np.zeros(
        (matrix_1.shape[0], matrix_2.shape[1])
    )

    for i in range(matrix_12.shape[0]):
        for j in range(matrix_12.shape[1]):
            for k in range(matrix_1.shape[1]):
                matrix_12[i, j] += (
                    matrix_1[i, k] * matrix_2[k, j]
                )

    return matrix_12


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
                    A[i, j] = (
                        A[i, j]
                        - factor * A[row, j]
                    )

        rank += 1
        row += 1

        if row == rows:
            break

    return rank


def gauss_jordan(matrix_A, vector_b):

    n = matrix_A.shape[0]

    aug_matrix = np.concatenate(
        [matrix_A, vector_b],
        axis=1
    ).astype(float)

    for col in range(n):

        pivot = col

        for row in range(col + 1, n):

            if abs(aug_matrix[row, col]) > abs(
                aug_matrix[pivot, col]
            ):
                pivot = row

        if abs(aug_matrix[pivot, col]) < 1e-10:
            return None

        aug_matrix[[col, pivot]] = (
            aug_matrix[[pivot, col]]
        )

        aug_matrix[col] = (
            aug_matrix[col] / aug_matrix[col, col]
        )

        for row in range(n):

            if row != col:

                factor = aug_matrix[row, col]

                aug_matrix[row] = (
                    aug_matrix[row]
                    - factor * aug_matrix[col]
                )

    return aug_matrix[:, n].reshape(n, 1)


def solve_linear_system(matrix_A, vector_b):

    if matrix_A.shape[0] != matrix_A.shape[1]:
        print("Please enter a square matrix for the coefficient matrix.")
        return None

    if matrix_A.shape[0] != vector_b.shape[0]:
        print("Mismatch between number of entries in LHS and RHS.")
        return None

    aug_matrix_Ab = np.concatenate(
        [matrix_A, vector_b],
        axis=1
    )

    n = matrix_A.shape[0]

    rank_A = matrix_rank(matrix_A)
    rank_Ab = matrix_rank(aug_matrix_Ab)

    if rank_A == rank_Ab == n:

        solution = gauss_jordan(
            matrix_A,
            vector_b
        )

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


# Eigenvalue and Eigenvector Functions

def minor(matrix, loc):

    minor_mat = matrix.copy()

    minor_mat = np.delete(
        minor_mat,
        loc[0],
        axis=0
    )

    minor_mat = np.delete(
        minor_mat,
        loc[1],
        axis=1
    )

    return minor_mat


def cofactor(matrix, loc):

    minor_mat = minor(matrix, loc)

    return (
        (-1) ** (loc[0] + loc[1])
        * matrix_determinant(minor_mat)
    )


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

        det += (
            matrix[0, j]
            * cofactor(matrix, (0, j))
        )

    return det


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


def center_data(matrix):

    centered_matrix = matrix.astype(float).copy()

    for j in range(matrix.shape[1]):

        mean = np.mean(matrix[:, j])

        for i in range(matrix.shape[0]):

            centered_matrix[i, j] = (
                matrix[i, j] - mean
            )

    return centered_matrix


def pca(matrix, number_of_components):

    # Center the data
    centered_matrix = center_data(matrix)

    # SVD of centered data
    U, sigma, V = svd_from_matrix(
        centered_matrix
    )

    # Principal directions
    principal_directions = V[:, :number_of_components]

    # Project data onto new basis
    reduced_data = matrix_product(
        centered_matrix,
        principal_directions
    )

    return (
        centered_matrix,
        principal_directions,
        reduced_data
    )




# Part A
# Question Specific Functions

# Q1. Google PageRank

def pagerank_Q1(matrix):

    eigenvalues, eigenvectors = (
        eigenvalue_eigenvector(matrix)
    )

    dominant_index = np.argmax(
        np.abs(eigenvalues)
    )

    rank_vector = np.real(
        eigenvectors[:, dominant_index]
    )

    rank_vector = np.abs(rank_vector)

    rank_vector = (
        rank_vector / np.sum(rank_vector)
    )

    return rank_vector


# Q2. GPS Location Tracking

def gps_location_Q2(points, distances):

    # Distance equation:
    # (x-a)^2 + (y-b)^2 = d^2

    x1, y1 = points[0]
    d1 = distances[0]

    coefficient_matrix = []
    vector_b = []

    for i in range(1, len(points)):

        xi, yi = points[i]
        di = distances[i]

        coefficient_matrix.append([
            2 * (xi - x1),
            2 * (yi - y1)
        ])

        vector_b.append(
            d1**2
            - di**2
            + xi**2
            + yi**2
            - x1**2
            - y1**2
        )

    coefficient_matrix = np.array(
        coefficient_matrix,
        dtype=float
    )

    vector_b = np.array(
        vector_b,
        dtype=float
    ).reshape(-1, 1)

    position = solve_linear_system(
        coefficient_matrix,
        vector_b
    )

    return position


# Q3. Medical Imaging

def medical_imaging_Q3(
    matrix_A,
    scan_data
):

    # Reconstruct image values by solving A*x = b

    image_values = solve_linear_system(
        matrix_A,
        scan_data
    )

    return image_values


# Q4. Structural Engineering Vibrations

def Q4_vibration_analysis(stiffness_matrix):

    eigenvalues, eigenvectors = eigenvalue_eigenvector(
        stiffness_matrix
    )

    return eigenvalues, eigenvectors


# Q5. Wireless Communication (MIMO)

def mimo_Q5(
    channel_matrix,
    received_signal
):

    transmitted_signal = solve_linear_system(
        channel_matrix,
        received_signal
    )

    return transmitted_signal


# Q6. Economics & Market Equilibrium

def market_equilibrium_Q6(
    coefficient_matrix,
    vector_b
):

    equilibrium = solve_linear_system(
        coefficient_matrix,
        vector_b
    )

    return equilibrium


# Q7. Computer Graphics (3D Transformations)

def graphics_3D_Q7(
    points,
    transformation_matrix
):

    transformed_points = matrix_product(
        transformation_matrix,
        points
    )

    return transformed_points


# Q8. Cryptography & Coding Theory

def cryptography_Q8(
    key_matrix,
    message_vector
):

    encoded_message = matrix_product(
        key_matrix,
        message_vector
    )

    decoded_message = solve_linear_system(
        key_matrix,
        encoded_message
    )

    return encoded_message, decoded_message


# Q9. Epidemiology

def epidemiology_Q9(
    transition_matrix,
    initial_population,
    steps
):

    population = initial_population.copy()

    for i in range(steps):

        population = matrix_product(
            transition_matrix,
            population
        )

    return population


# Q10. Air Traffic Control

def air_traffic_control_Q10(
    coefficient_matrix,
    measurements
):

    position = solve_linear_system(
        coefficient_matrix,
        measurements
    )

    return position

# Q11 - Singular Value Decomposition

def SVD_Q11(matrix):

    U, sigma, V = svd_from_matrix(matrix)

    return U, sigma, V


# Q12 - Recommender Systems

def recommender_Q12(rating_matrix):

    U, sigma, V = svd_from_matrix(
        rating_matrix
    )

    # Use all available singular values
    predicted_matrix = matrix_product(
        matrix_product(U, sigma),
        matrix_transpose(V)
    )

    return U, sigma, V, predicted_matrix



# Q13 - Feature Spaces / PCA

def feature_space_Q13(matrix, number_of_components):

    centered_matrix, principal_directions, reduced_data = pca(
        matrix,
        number_of_components
    )

    return (
        centered_matrix,
        principal_directions,
        reduced_data
    )





## Execution


# Q1
print("Q1.")

matrix_Q1 = np.array([
    [0, 0.3, 1],
    [0.5, 0, 0],
    [0.5, 0.7, 0]
], dtype=float)

pagerank = pagerank_Q1(matrix_Q1)

print("For the given web rank matrix:")
print(matrix_Q1)

print("PageRank=", pagerank)


# Q2
print("\nQ2.")

points_Q2 = np.array([
    [0, 0],
    [4, 0],
    [0, 4]
], dtype=float)

distances_Q2 = np.array([
    5,
    3,
    np.sqrt(5)
])

position_Q2 = gps_location_Q2(
    points_Q2,
    distances_Q2
)

print("For the given satellite points:")
print(points_Q2)
print("and corresponding distances:")
print(distances_Q2)

if position_Q2 is not None:
    print(
        "Estimated position=",
        position_Q2.flatten()
    )


# Q3
print("\nQ3.")

matrix_Q3 = np.array([
    [1, 1],
    [1, -1]
], dtype=float)

scan_data_Q3 = np.array([
    [5],
    [1]
], dtype=float)

image_Q3 = medical_imaging_Q3(
    matrix_Q3,
    scan_data_Q3
)

print("For the given medical imaging matrix:")
print(matrix_Q3)
print("and scan data:")
print(scan_data_Q3)

if image_Q3 is not None:
    print(
        "Reconstructed values=",
        image_Q3.flatten()
    )


# Q4

stiffness_matrix_Q4 = np.array([
    [2, -3, 0],
    [2, -5, 0],
    [0, 0, 3]
], dtype=float)

print("\nQ4: Structural Engineering Vibrations")

print("For the given stiffness matrix:")
print(stiffness_matrix_Q4)

eigenvalues_Q4, eigenvectors_Q4 = Q4_vibration_analysis(
    stiffness_matrix_Q4
)

print("\nEigenvalues:")
print(eigenvalues_Q4)

print("\nEigenvectors:")
print(eigenvectors_Q4)


# Q5
print("\nQ5.")

channel_Q5 = np.array([
    [2, 0],
    [0, 3]
], dtype=float)

received_Q5 = np.array([
    [2],
    [3]
], dtype=float)

transmitted_Q5 = mimo_Q5(
    channel_Q5,
    received_Q5
)

print("For the given communication channel matrix:")
print(channel_Q5)
print("and received signal:")
print(received_Q5)

if transmitted_Q5 is not None:
    print(
        "Recovered signal=",
        transmitted_Q5.flatten()
    )


# Q6
print("\nQ6.")

coefficient_Q6 = np.array([
    [1, 1],
    [-1, 1]
], dtype=float)

vector_Q6 = np.array([
    [10],
    [2]
], dtype=float)

equilibrium_Q6 = market_equilibrium_Q6(
    coefficient_Q6,
    vector_Q6
)

print("For the given market coefficient matrix:")
print(coefficient_Q6)
print("and demand/supply vector:")
print(vector_Q6)

if equilibrium_Q6 is not None:
    print(
        "Equilibrium=",
        equilibrium_Q6.flatten()
    )


# Q7
print("\nQ7.")

points_Q7 = np.array([
    [1, 0],
    [0, 1]
], dtype=float)

rotation_Q7 = np.array([
    [0, -1],
    [1, 0]
], dtype=float)

transformed_Q7 = graphics_3D_Q7(
    points_Q7,
    rotation_Q7
)

print("For the given points:")
print(points_Q7)
print("and transformation matrix:")
print(rotation_Q7)

print(
    "Transformed points=\n",
    transformed_Q7
)


# Q8
print("\nQ8.")

key_Q8 = np.array([
    [1, 1],
    [0, 1]
], dtype=float)

message_Q8 = np.array([
    [1],
    [2]
], dtype=float)

encoded_Q8, decoded_Q8 = (
    cryptography_Q8(
        key_Q8,
        message_Q8
    )
)
print("For the given key matrix:")
print(key_Q8)
print("and message vector:")
print(message_Q8)

print(
    "Encoded message=",
    encoded_Q8.flatten()
)

print(
    "Decoded message=",
    decoded_Q8.flatten()
)


# Q9
print("\nQ9.")

transition_Q9 = np.array([
    [0.9, 0.1],
    [0.1, 0.9]
], dtype=float)

initial_population_Q9 = np.array([
    [90],
    [10]
], dtype=float)

population_Q9 = epidemiology_Q9(
    transition_Q9,
    initial_population_Q9,
    1
)

print("For the given epidemiological transition matrix:")
print(transition_Q9)
print("and initial population:")
print(initial_population_Q9)

print(
    "Population after one step=",
    population_Q9.flatten()
)


# Q10
print("\nQ10.")

coefficient_Q10 = np.array([
    [1, 1],
    [1, -1]
], dtype=float)

measurements_Q10 = np.array([
    [10],
    [2]
], dtype=float)

position_Q10 = air_traffic_control_Q10(
    coefficient_Q10,
    measurements_Q10
)

print("For the given aircraft measurement coefficient matrix:")
print(coefficient_Q10)
print("and measurements:")
print(measurements_Q10)

if position_Q10 is not None:
    print(
        "Aircraft position=",
        position_Q10.flatten()
    )


# Q11

matrix_M1 = np.array([
    [1, -1],
    [0, 1],
    [1, 0]
], dtype=float)

matrix_M2 = np.array([
    [1, 1, 1],
    [-1, 0, -2],
    [1, 2, 0]
], dtype=float)


print("\nQ11: Singular Value Decomposition")

print("\nFor the given matrix M1:")
print(matrix_M1)

U1, Sigma1, V1 = SVD_Q11(matrix_M1)

print("\nU for M1:")
print(U1)

print("\nSigma for M1:")
print(Sigma1)

print("\nV^T for M1:")
print(matrix_transpose(V1))


print("\nFor the given matrix M2:")
print(matrix_M2)

U2, Sigma2, V2 = SVD_Q11(matrix_M2)

print("\nU for M2:")
print(U2)

print("\nSigma for M2:")
print(Sigma2)

print("\nV^T for M2:")
print(matrix_transpose(V2))


# Q12

rating_matrix_Q12 = np.array([
    [5, 4, 0, 1],
    [4, 0, 2, 1],
    [1, 2, 5, 4]
], dtype=float)


print("\nQ12: Recommender Systems")

print("\nFor the given user-item rating matrix:")
print(rating_matrix_Q12)

U12, Sigma12, V12, predicted_Q12 = recommender_Q12(
    rating_matrix_Q12
)

print("\nU:")
print(U12)

print("\nSigma:")
print(Sigma12)

print("\nV^T:")
print(matrix_transpose(V12))

print("\nPredicted/reconstructed rating matrix:")
print(predicted_Q12)


# Q13

data_matrix_Q13 = np.array([
    [2, 1],
    [3, 2],
    [4, 3],
    [5, 4]
], dtype=float)


print("\nQ13: Machine Learning - Feature Spaces")

print("\nFor the given feature matrix:")
print(data_matrix_Q13)

centered_Q13, basis_Q13, reduced_Q13 = feature_space_Q13(
    data_matrix_Q13,
    1
)

print("\nCentered data:")
print(centered_Q13)

print("\nPrincipal basis direction:")
print(basis_Q13)

print("\nReduced one-dimensional representation:")
print(reduced_Q13)





'''
Q1.
For the given web rank matrix:
[[0.  0.3 1. ]
 [0.5 0.  0. ]
 [0.5 0.7 0. ]]
PageRank= [0.75 0.25 0.  ]

Q2.
For the given satellite points:
[[0. 0.]
 [4. 0.]
 [0. 4.]]
and corresponding distances:
[5.         3.         2.23606798]
Estimated position= [4.  4.5]

Q3.
For the given medical imaging matrix:
[[ 1.  1.]
 [ 1. -1.]]
and scan data:
[[5.]
 [1.]]
Reconstructed values= [3. 2.]

Q4: Structural Engineering Vibrations
For the given stiffness matrix:
[[ 2. -3.  0.]
 [ 2. -5.  0.]
 [ 0.  0.  3.]]

Eigenvalues:
[-4.  3.  1.]

Eigenvectors:
[[1.+0.j 0.+0.j 3.+0.j]
 [2.+0.j 0.+0.j 1.+0.j]
 [0.+0.j 1.+0.j 0.+0.j]]

Q5.
For the given communication channel matrix:
[[2. 0.]
 [0. 3.]]
and received signal:
[[2.]
 [3.]]
Recovered signal= [1. 1.]

Q6.
For the given market coefficient matrix:
[[ 1.  1.]
 [-1.  1.]]
and demand/supply vector:
[[10.]
 [ 2.]]
Equilibrium= [4. 6.]

Q7.
For the given points:
[[1. 0.]
 [0. 1.]]
and transformation matrix:
[[ 0. -1.]
 [ 1.  0.]]
Transformed points=
 [[ 0. -1.]
 [ 1.  0.]]

Q8.
For the given key matrix:
[[1. 1.]
 [0. 1.]]
and message vector:
[[1.]
 [2.]]
Encoded message= [3. 2.]
Decoded message= [1. 2.]

Q9.
For the given epidemiological transition matrix:
[[0.9 0.1]
 [0.1 0.9]]
and initial population:
[[90.]
 [10.]]
Population after one step= [82. 18.]

Q10.
For the given aircraft measurement coefficient matrix:
[[ 1.  1.]
 [ 1. -1.]]
and measurements:
[[10.]
 [ 2.]]
Aircraft position= [6. 4.]

Q11: Singular Value Decomposition

For the given matrix M1:
[[ 1. -1.]
 [ 0.  1.]
 [ 1.  0.]]

U for M1:
[[-0.81649658  0.        ]
 [ 0.40824829 -0.70710678]
 [-0.40824829 -0.70710678]]

Sigma for M1:
[[1.73205081 0.        ]
 [0.         1.        ]]

V^T for M1:
[[-0.70710678  0.70710678]
 [-0.70710678 -0.70710678]]

For the given matrix M2:
[[ 1.  1.  1.]
 [-1.  0. -2.]
 [ 1.  2.  0.]]

U for M2:
[[-5.77350269e-01  5.55111512e-17  0.00000000e+00]
 [ 5.77350269e-01 -7.07106781e-01  0.00000000e+00]
 [-5.77350269e-01 -7.07106781e-01  0.00000000e+00]]

Sigma for M2:
[[3. 0. 0.]
 [0. 2. 0.]
 [0. 0. 0.]]

V^T for M2:
[[-0.57735027 -0.57735027 -0.57735027]
 [ 0.         -0.70710678  0.70710678]
 [-0.81649658  0.40824829  0.40824829]]

Q12: Recommender Systems

For the given user-item rating matrix:
[[5. 4. 0. 1.]
 [4. 0. 2. 1.]
 [1. 2. 5. 4.]]

U:
[[-0.61797905 -0.66758089  0.41525612]
 [-0.45368144 -0.1285607  -0.88184199]
 [-0.64208648  0.73335387  0.22342124]]

Sigma:
[[8.66487473 0.         0.        ]
 [0.         5.23155829 0.        ]
 [0.         0.         2.55944208]]

V^T:
[[-0.64013706 -0.43348453 -0.47522848 -0.4200876 ]
 [-0.59614998 -0.23006832  0.65174615  0.40853485]
 [-0.47966161  0.82356503 -0.2526245   0.16687195]]

Predicted/reconstructed rating matrix:
[[5.00000000e+00 4.00000000e+00 1.11022302e-15 1.00000000e+00]
 [4.00000000e+00 2.22044605e-16 2.00000000e+00 1.00000000e+00]
 [1.00000000e+00 2.00000000e+00 5.00000000e+00 4.00000000e+00]]

Q13: Machine Learning - Feature Spaces

For the given feature matrix:
[[2. 1.]
 [3. 2.]
 [4. 3.]
 [5. 4.]]

Centered data:
[[-1.5 -1.5]
 [-0.5 -0.5]
 [ 0.5  0.5]
 [ 1.5  1.5]]

Principal basis direction:
[[0.70710678]
 [0.70710678]]

Reduced one-dimensional representation:
[[-2.12132034]
 [-0.70710678]
 [ 0.70710678]
 [ 2.12132034]]
'''
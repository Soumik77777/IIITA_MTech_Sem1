import numpy as np

def soln_exists_Q1(matrix_A, vector_b):
    if matrix_A.shape[0] != matrix_A.shape[1]:
        print("Please enter a square matrix for the coefficient matrix.")
        return 0

    if matrix_A.shape[0] != vector_b.shape[0]:
        print("Mismatch between number of entries in LHS and RHS.")
        return 0

    aug_matrix_Ab = np.concatenate([matrix_A, vector_b], axis=1)

    n = matrix_A.shape[0]
    rank_A = np.linalg.matrix_rank(matrix_A)
    rank_Ab = np.linalg.matrix_rank(aug_matrix_Ab)

    # returning arbitrary numbers per case for matching later
    if rank_A == rank_Ab == n:
        return 10     

    elif rank_A == rank_Ab < n:
        return 11

    elif rank_A < rank_Ab:
        return 12

    else:
        print("Input is not valid")
        return 0



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

    rank_A = np.linalg.matrix_rank(matrix_A)
    rank_Ab = np.linalg.matrix_rank(aug_matrix_Ab)

    if rank_A == rank_Ab == n:
        print("Unique solution exists.")

        solution = np.linalg.solve(matrix_A, vector_b)

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



def eigenvalue_eigenvector_Q2(matrix):
    eigenvalues, eigenvectors = np.linalg.eig(matrix)

    return eigenvalues, eigenvectors
    


# =================================================================

matrix_A = np.array([[1, 1, 1], [2, 3, 1], [3, 4, 2]])
vector_b = np.array([[6], [10], [15]])

matrix_Q2 = np.array([[2, -3, 0], [2, -5, 0], [0, 0, 3]])



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
eigenvalues, eigenvectors = eigenvalue_eigenvector_Q2(matrix_Q2)
for i in range(len(eigenvalues)):
    print(f"{i+1}-th eigenvalue= {eigenvalues[i]}")
    print(f"Corresponding eigenvector= {eigenvectors[i]}")
    print()

print()

print("Q3.")
solution = solve_gauss_jordan_Q3()
if type(solution) == np.ndarray:
    for i in range(len(solution)):
        print(f"x{i+1}= {solution[i]}")



# ============================================================

"""
Example Output

Q1.
No solution exists for given A and b.


Q2.
1-th eigenvalue= (1+0j)
Corresponding eigenvector= [0.9486833+0.j 0.4472136+0.j 0.0+0.j]

2-th eigenvalue= (-4+0j)
Corresponding eigenvector= [0.31622777+0.j 0.89442719+0.j 0.0+0.j]

3-th eigenvalue= (3+0j)
Corresponding eigenvector= [0.+0.j 0.+0.j 1.+0.j]

Q3.
Number of rows or cols of square matrix: 2
Please enter the elements of the coefficient matrix one by one.
Rows and columns range from 1 to n.
Row= 1, Column= 1: 2
Row= 1, Column= 2: 3
Row= 2, Column= 1: 1
Row= 2, Column= 2: -1
Now enter the constant (RHS) elements one-by-one.
Row= 1: 13
Row= 2: 1
Unique solution exists.
x1= [3.2]
x2= [2.2]

"""

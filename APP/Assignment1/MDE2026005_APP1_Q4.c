/*
Given a matrix with many zero entries, store only its non-zero elements as a list of (row,
col, value) triples, print this compact representation, and write a function that
reconstructs and prints the original matrix from it.
*/

#include <stdio.h>

typedef struct {
    int row;
    int col;
    int value;
} Triple;

// Scans matrix and fills the triples array. Returns count of non-zero elements found.
int compact_matrix(int rows, int cols, int matrix[rows][cols], Triple triples[]) {
    int count = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (matrix[i][j] != 0) {
                triples[count].row = i;
                triples[count].col = j;
                triples[count].value = matrix[i][j];
                count++;
            }
        }
    }
    return count;
}

void print_triples(Triple triples[], int count) {
    printf("Row\tCol\tValue\n");
    for (int i = 0; i < count; i++) {
        printf("%d\t%d\t%d\n", triples[i].row, triples[i].col, triples[i].value);
    }
}

// Reconstructs the original matrix from the triples (all other entries are 0).
void reconstruct_matrix(int rows, int cols, int matrix[rows][cols], Triple triples[], int count) {
    // start with all zeros
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i][j] = 0;
        }
    }
    // place the non-zero values back
    for (int i = 0; i < count; i++) {
        matrix[triples[i].row][triples[i].col] = triples[i].value;
    }
}

void print_matrix(int rows, int cols, int matrix[rows][cols]) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\n");
    }
}

int main() {
    int rows, cols;
    printf("Enter number of rows: ");
    scanf("%d", &rows);
    printf("Enter number of columns: ");
    scanf("%d", &cols);

    int matrix[rows][cols];
    printf("Enter %d elements (row by row): ", rows * cols);
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            scanf("%d", &matrix[i][j]);
        }
    }

    // Worst case every element is non-zero, so allocate rows*cols triples
    Triple triples[rows * cols];
    int count = compact_matrix(rows, cols, matrix, triples);

    printf("\nCompact representation (%d non-zero elements):\n", count);
    print_triples(triples, count);

    int reconstructed[rows][cols];
    reconstruct_matrix(rows, cols, reconstructed, triples, count);

    printf("\nReconstructed matrix:\n");
    print_matrix(rows, cols, reconstructed);

    return 0;
}
/*
Write a C program to represent a sparse matrix using a 3-tuple array.
Display the sparse matrix in triplet form containing row, column, and value.
*/

#include <stdio.h>

int main() {
    int rows, cols;
    int count = 0;

    printf("Enter number of rows: ");
    scanf("%d", &rows);

    printf("Enter number of columns: ");
    scanf("%d", &cols);

    int a[rows][cols];

    printf("Enter the elements of the matrix:\n");

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            scanf("%d", &a[i][j]);

            if (a[i][j] != 0)
                count++;
        }
    }

    printf("\nOriginal matrix:\n");

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            printf("%d ", a[i][j]);
        }
        printf("\n");
    }

    int sparse[count + 1][3];

    sparse[0][0] = rows;
    sparse[0][1] = cols;
    sparse[0][2] = count;

    int k = 1;

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (a[i][j] != 0) {
                sparse[k][0] = i;
                sparse[k][1] = j;
                sparse[k][2] = a[i][j];
                k++;
            }
        }
    }

    printf("\nSparse matrix in triplet form:\n");
    printf("Row Column Value\n");

    for (int i = 0; i <= count; i++) {
        printf("%d   %d      %d\n",
               sparse[i][0],
               sparse[i][1],
               sparse[i][2]);
    }

    return 0;
}
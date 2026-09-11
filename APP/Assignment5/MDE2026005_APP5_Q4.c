/*
Write a C program to find all elements that are maximum in their row and minimum in 
their column.
*/

#include <stdio.h>

int main() {
    int rows, cols;

    printf("Enter number of rows: ");
    scanf("%d", &rows);

    printf("Enter number of columns: ");
    scanf("%d", &cols);

    int a[rows][cols];

    for (int i = 0; i < rows; i++) {
        printf("Enter the elements of row %d:\n", i);
        for (int j = 0; j < cols; j++) {
            scanf("%d", &a[i][j]);
        }
    }

    printf("\nElements that are maximum in their row and minimum in their column: \n");

    for (int i = 0; i < rows; i++) {

        int row_max = a[i][0];

        for (int j = 1; j < cols; j++) {
            if (a[i][j] > row_max) {
                row_max = a[i][j];
            }
        }

        for (int j = 0; j < cols; j++) {

            if (a[i][j] == row_max) {

                int is_column_min = 1;

                for (int k = 0; k < rows; k++) {
                    if (a[k][j] < a[i][j]) {
                        is_column_min = 0;
                        break;
                    }
                }

                if (is_column_min) {
                    printf("Saddle found in row= %dth, column= %dth. Value= %d.\n", i, j, a[i][j]);
                }
            }
        }
    }

    printf("\n");

    return 0;
}
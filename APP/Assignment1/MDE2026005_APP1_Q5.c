/*
Find all elements of a matrix that are simultaneously the minimum in their row and the
maximum in their column (matrix saddle points), or report that none exist.
*/

#include <stdio.h>

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

    int found = 0;

    for (int i = 0; i < rows; i++) {
        // Step 1: find the minimum in this row and its column index
        int min_val = matrix[i][0];
        int min_col = 0;
        for (int j = 1; j < cols; j++) {
            if (matrix[i][j] < min_val) {
                min_val = matrix[i][j];
                min_col = j;
            }
        }

        // Step 2: check if min_val is the maximum in column min_col
        int is_col_max = 1;
        for (int k = 0; k < rows; k++) {
            if (matrix[k][min_col] > min_val) {
                is_col_max = 0;
                break;
            }
        }

        // Step 3: report if it's a saddle point
        if (is_col_max) {
            printf("Saddle point: matrix[%d][%d] = %d\n", i, min_col, min_val);
            found = 1;
        }
    }

    if (!found) {
        printf("No saddle points found.\n");
    }

    return 0;
}
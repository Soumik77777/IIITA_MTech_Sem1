/*
A magic square is a square grid of numbers where the sum of the numbers in each row, 
column, and diagonal is the same. Write a C program to implement the magic square for 
the n x n matrix, where n is an odd number and the array contains numbers 1 to n^2. 
*/

#include <stdio.h>

int main() {
    int n;
    printf("Enter order of the magic square (odd number): ");
    scanf("%d", &n);

    if (n % 2 == 0) {
        printf("Order has to be odd.\n");
        return 0;
    }

    int square[n][n];
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            square[i][j] = 0;
        }
    }

    int row = 0, col = n / 2;
    int num = 1;

    while (num <= n * n) {
        square[row][col] = num;
        num++;

        int next_row = (row - 1 + n) % n;
        int next_col = (col + 1) % n;

        if (square[next_row][next_col] != 0) {
            next_row = (row + 1) % n;
            next_col = col;
        }

        row = next_row;
        col = next_col;
    }

    printf("Magic Square of order %d:\n", n);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            printf("%d\t", square[i][j]);
        }
        printf("\n");
    }

    return 0;
}
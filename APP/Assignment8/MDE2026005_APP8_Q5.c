/*
Write a C program to search for an element at a specified row and column
in a sparse matrix represented using a linked list.
*/

#include <stdio.h>
#include <stdlib.h>

struct Node {
    int row;
    int col;
    int value;
    struct Node *next;
};

struct Node* insert(struct Node *head, int row, int col, int value) {
    struct Node *newNode = (struct Node*)malloc(sizeof(struct Node));

    newNode->row = row;
    newNode->col = col;
    newNode->value = value;
    newNode->next = NULL;

    if (head == NULL)
        return newNode;

    struct Node *curr = head;

    while (curr->next != NULL)
        curr = curr->next;

    curr->next = newNode;

    return head;
}

int search(struct Node *head, int row, int col) {
    while (head != NULL) {
        if (head->row == row && head->col == col)
            return head->value;

        head = head->next;
    }

    return 0;
}

void freeList(struct Node *head) {
    struct Node *temp;

    while (head != NULL) {
        temp = head;
        head = head->next;
        free(temp);
    }
}

int main() {
    struct Node *head = NULL;

    int rows, cols, value;
    int search_row, search_col;

    printf("Enter number of rows: ");
    scanf("%d", &rows);

    printf("Enter number of columns: ");
    scanf("%d", &cols);

    printf("Enter the matrix elements:\n");

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            scanf("%d", &value);

            if (value != 0)
                head = insert(head, i, j, value);
        }
    }

    printf("Enter row to search: ");
    scanf("%d", &search_row);

    printf("Enter column to search: ");
    scanf("%d", &search_col);

    if (search_row < 0 || search_row >= rows ||
        search_col < 0 || search_col >= cols) {
        printf("Invalid row or column.\n");
    }
    else {
        value = search(head, search_row, search_col);

        printf("Element at row %d, column %d: %d\n",
               search_row, search_col, value);
    }

    freeList(head);

    return 0;
}
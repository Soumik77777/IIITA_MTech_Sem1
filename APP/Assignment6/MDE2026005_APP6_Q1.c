/*
Create a singly linked list by inserting nodes one by one such that the resulting linked list
remains sorted in ascending order.
*/

#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
};

struct Node *insertSorted(struct Node *head, int value)
{
    struct Node *newNode;
    struct Node *current;

    newNode = malloc(sizeof(struct Node));
    if (newNode == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        return head;
    }

    newNode->data = value;
    newNode->next = NULL;

    if (head == NULL || value <= head->data) {
        newNode->next = head;
        return newNode;
    }

    current = head;
    while (current->next != NULL && current->next->data < value) {
        current = current->next;
    }

    newNode->next = current->next;
    current->next = newNode;

    return head;
}

void display(struct Node *head)
{
    struct Node *current = head;

    while (current != NULL) {
        printf("%d", current->data);

        if (current->next != NULL) {
            printf(" -> ");
        }

        current = current->next;
    }

    printf("\n");
}

void freeList(struct Node *head)
{
    struct Node *temp;

    while (head != NULL) {
        temp = head;
        head = head->next;
        free(temp);
    }
}

int main(void)
{
    struct Node *head = NULL;
    int n;
    int value;

    printf("Enter number of nodes: ");
    if (scanf("%d", &n) != 1 || n < 0) {
        fprintf(stderr, "Invalid number of nodes.\n");
        return EXIT_FAILURE;
    }

    printf("Enter %d values:\n", n);

    for (int i = 0; i < n; i++) {
        if (scanf("%d", &value) != 1) {
            fprintf(stderr, "Invalid input.\n");
            freeList(head);
            return EXIT_FAILURE;
        }

        head = insertSorted(head, value);
    }

    printf("Sorted linked list: ");
    display(head);

    freeList(head);

    return EXIT_SUCCESS;
}

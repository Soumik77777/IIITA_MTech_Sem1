/*
Write a program to insert a new node at a specified position in a singly linked list.
*/

#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
};

struct Node *createNode(int data)
{
    struct Node *newNode = malloc(sizeof(struct Node));

    if (newNode == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        return NULL;
    }

    newNode->data = data;
    newNode->next = NULL;

    return newNode;
}

int insertAtPosition(struct Node **head, int data, int position)
{
    struct Node *newNode;
    struct Node *current;

    if (position < 1) {
        return 0;
    }

    newNode = createNode(data);
    if (newNode == NULL) {
        return 0;
    }

    if (position == 1) {
        newNode->next = *head;
        *head = newNode;
        return 1;
    }

    current = *head;

    for (int i = 1; i < position - 1 && current != NULL; i++) {
        current = current->next;
    }

    if (current == NULL) {
        free(newNode);
        return 0;
    }

    newNode->next = current->next;
    current->next = newNode;

    return 1;
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
    struct Node *newNode;
    int n;
    int value;
    int position;

    printf("Enter number of nodes: ");
    if (scanf("%d", &n) != 1 || n < 0) {
        fprintf(stderr, "Invalid number of nodes.\n");
        return EXIT_FAILURE;
    }

    printf("Enter %d elements:\n", n);

    for (int i = 0; i < n; i++) {
        if (scanf("%d", &value) != 1) {
            fprintf(stderr, "Invalid input.\n");
            freeList(head);
            return EXIT_FAILURE;
        }

        newNode = createNode(value);
        if (newNode == NULL) {
            freeList(head);
            return EXIT_FAILURE;
        }

        if (head == NULL) {
            head = newNode;
        } else {
            struct Node *current = head;

            while (current->next != NULL) {
                current = current->next;
            }

            current->next = newNode;
        }
    }

    printf("Original linked list: ");
    display(head);

    printf("Enter value to insert: ");
    if (scanf("%d", &value) != 1) {
        fprintf(stderr, "Invalid input.\n");
        freeList(head);
        return EXIT_FAILURE;
    }

    printf("Enter position (first position is 1): ");
    if (scanf("%d", &position) != 1) {
        fprintf(stderr, "Invalid input.\n");
        freeList(head);
        return EXIT_FAILURE;
    }

    if (insertAtPosition(&head, value, position)) {
        printf("Linked list after insertion: ");
        display(head);
    } else {
        printf("Invalid position. Node was not inserted.\n");
    }

    freeList(head);

    return EXIT_SUCCESS;
}
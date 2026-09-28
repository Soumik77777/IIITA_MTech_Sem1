/*
Write a C program to create a singly linked list with the number of nodes specified by the
user.
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
    struct Node *current;
    int n;
    int value;

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
            current = head;

            while (current->next != NULL) {
                current = current->next;
            }

            current->next = newNode;
        }
    }

    printf("Linked list: ");
    display(head);
    
    freeList(head);

    return EXIT_SUCCESS;
}

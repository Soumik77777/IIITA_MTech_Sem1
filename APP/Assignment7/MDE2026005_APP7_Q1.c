/*
Write a menu-based program for creation, insertion at beginning, at end or at
given location, deletion from beginning, from end or from given location,
and traversing of singly circular linked list.
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
        printf("Memory allocation failed.\n");
        return NULL;
    }

    newNode->data = data;
    newNode->next = NULL;

    return newNode;
}

void display(struct Node *head)
{
    struct Node *current;

    if (head == NULL) {
        printf("List is empty.\n");
        return;
    }

    current = head;

    do {
        printf("%d", current->data);
        current = current->next;

        if (current != head) {
            printf(" -> ");
        }
    } while (current != head);

    printf(" -> HEAD\n");
}

void insertBeginning(struct Node **head, int data)
{
    struct Node *newNode;
    struct Node *current;

    newNode = createNode(data);

    if (newNode == NULL) {
        return;
    }

    if (*head == NULL) {
        newNode->next = newNode;
        *head = newNode;
        return;
    }

    current = *head;

    while (current->next != *head) {
        current = current->next;
    }

    newNode->next = *head;
    current->next = newNode;
    *head = newNode;
}

void insertEnd(struct Node **head, int data)
{
    struct Node *newNode;
    struct Node *current;

    newNode = createNode(data);

    if (newNode == NULL) {
        return;
    }

    if (*head == NULL) {
        newNode->next = newNode;
        *head = newNode;
        return;
    }

    current = *head;

    while (current->next != *head) {
        current = current->next;
    }

    current->next = newNode;
    newNode->next = *head;
}

int insertAtPosition(struct Node **head, int data, int position)
{
    struct Node *newNode;
    struct Node *current;

    if (position < 1) {
        return 0;
    }

    if (position == 1) {
        insertBeginning(head, data);
        return 1;
    }

    if (*head == NULL) {
        return 0;
    }

    newNode = createNode(data);

    if (newNode == NULL) {
        return 0;
    }

    current = *head;

    for (int i = 1; i < position - 1; i++) {
        current = current->next;

        if (current == *head) {
            free(newNode);
            return 0;
        }
    }

    newNode->next = current->next;
    current->next = newNode;

    return 1;
}

int deleteBeginning(struct Node **head)
{
    struct Node *temp;
    struct Node *current;

    if (*head == NULL) {
        return 0;
    }

    temp = *head;

    if (temp->next == *head) {
        *head = NULL;
        free(temp);
        return 1;
    }

    current = *head;

    while (current->next != *head) {
        current = current->next;
    }

    *head = temp->next;
    current->next = *head;

    free(temp);

    return 1;
}

int deleteEnd(struct Node **head)
{
    struct Node *current;
    struct Node *temp;

    if (*head == NULL) {
        return 0;
    }

    if ((*head)->next == *head) {
        free(*head);
        *head = NULL;
        return 1;
    }

    current = *head;

    while (current->next->next != *head) {
        current = current->next;
    }

    temp = current->next;
    current->next = *head;

    free(temp);

    return 1;
}

int deleteAtPosition(struct Node **head, int position)
{
    struct Node *current;
    struct Node *temp;

    if (*head == NULL || position < 1) {
        return 0;
    }

    if (position == 1) {
        return deleteBeginning(head);
    }

    current = *head;

    for (int i = 1; i < position - 1; i++) {
        current = current->next;

        if (current == *head) {
            return 0;
        }
    }

    temp = current->next;

    if (temp == *head) {
        return 0;
    }

    current->next = temp->next;
    free(temp);

    return 1;
}

void freeList(struct Node **head)
{
    struct Node *current;
    struct Node *temp;

    if (*head == NULL) {
        return;
    }

    current = (*head)->next;

    while (current != *head) {
        temp = current;
        current = current->next;
        free(temp);
    }

    free(*head);
    *head = NULL;
}

int main(void)
{
    struct Node *head = NULL;
    int choice;
    int value;
    int position;
    int n;

    do {
        printf("\n----- MENU -----\n");
        printf("1. Create new linked list\n");
        printf("2. Insert at beginning\n");
        printf("3. Insert at end\n");
        printf("4. Insert at given position\n");
        printf("5. Delete from beginning\n");
        printf("6. Delete from end\n");
        printf("7. Delete from given position\n");
        printf("8. Traverse linked list\n");
        printf("9. Exit\n");
        printf("Enter your choice: ");

        if (scanf("%d", &choice) != 1) {
            printf("Invalid input.\n");
            freeList(&head);
            return EXIT_FAILURE;
        }

        switch (choice) {
        case 1:
            freeList(&head);

            printf("Enter number of nodes: ");
            if (scanf("%d", &n) != 1 || n < 0) {
                printf("Invalid number of nodes.\n");
                break;
            }

            printf("Enter %d elements:\n", n);

            for (int i = 0; i < n; i++) {
                if (scanf("%d", &value) != 1) {
                    printf("Invalid input.\n");
                    freeList(&head);
                    return EXIT_FAILURE;
                }

                insertEnd(&head, value);
            }

            printf("Linked list created.\n");
            display(head);
            break;

        case 2:
            printf("Enter element: ");
            scanf("%d", &value);

            insertBeginning(&head, value);

            printf("Element inserted.\n");
            display(head);
            break;

        case 3:
            printf("Enter element: ");
            scanf("%d", &value);

            insertEnd(&head, value);

            printf("Element inserted.\n");
            display(head);
            break;

        case 4:
            printf("Enter element: ");
            scanf("%d", &value);

            printf("Enter position (first position is 1): ");
            scanf("%d", &position);

            if (insertAtPosition(&head, value, position)) {
                printf("Element inserted.\n");
                display(head);
            } else {
                printf("Invalid position. Node was not inserted.\n");
            }
            break;

        case 5:
            if (deleteBeginning(&head)) {
                printf("Node deleted from beginning.\n");
                display(head);
            } else {
                printf("List is empty.\n");
            }
            break;

        case 6:
            if (deleteEnd(&head)) {
                printf("Node deleted from end.\n");
                display(head);
            } else {
                printf("List is empty.\n");
            }
            break;

        case 7:
            printf("Enter position (first position is 1): ");
            scanf("%d", &position);

            if (deleteAtPosition(&head, position)) {
                printf("Node deleted.\n");
                display(head);
            } else {
                printf("Invalid position. Node was not deleted.\n");
            }
            break;

        case 8:
            printf("Linked list: ");
            display(head);
            break;

        case 9:
            printf("Exiting program.\n");
            break;

        default:
            printf("Invalid choice.\n");
        }

    } while (choice != 9);

    freeList(&head);

    return EXIT_SUCCESS;
}
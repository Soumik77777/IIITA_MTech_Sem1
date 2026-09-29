#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
};

void swap(int *a, int *b)
{
    int temp = *a;
    *a = *b;
    *b = temp;
}

void swap_k(struct Node *start, int k)
{
    struct Node *left = start;
    struct Node *right = start;

    for (int i = 1; i < k && right != NULL; i++) {
        right = right->next;
    }

    int count = 1;
    struct Node *temp = start;

    while (temp != NULL && count < k) {
        temp = temp->next;
        count++;
    }

    if (temp == NULL) {
        right = temp;
    }

    if (right == NULL) {
        right = start;
        while (right->next != NULL) {
            right = right->next;
        }
    }

    while (left != right && left->next != right) {
        swap(&left->data, &right->data);

        left = left->next;

        temp = start;
        while (temp->next != right) {
            temp = temp->next;
        }
        right = temp;
    }

    if (left != right) {
        swap(&left->data, &right->data);
    }
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

void free_list(struct Node *head)
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
    struct Node *tail = NULL;
    struct Node *current;
    int n;
    int value;
    int k;

    printf("Enter number of nodes: ");

    if (scanf("%d", &n) != 1 || n < 0) {
        fprintf(stderr, "Invalid number of nodes.\n");
        return EXIT_FAILURE;
    }

    printf("Enter %d values:\n", n);

    for (int i = 0; i < n; i++) {
        if (scanf("%d", &value) != 1) {
            fprintf(stderr, "Invalid input.\n");
            free_list(head);
            return EXIT_FAILURE;
        }

        current = malloc(sizeof(struct Node));

        if (current == NULL) {
            fprintf(stderr, "Memory allocation failed.\n");
            free_list(head);
            return EXIT_FAILURE;
        }

        current->data = value;
        current->next = NULL;

        if (head == NULL) {
            head = current;
            tail = current;
        } else {
            tail->next = current;
            tail = current;
        }
    }

    printf("Enter k: ");

    if (scanf("%d", &k) != 1 || k <= 0) {
        fprintf(stderr, "Invalid value of k.\n");
        free_list(head);
        return EXIT_FAILURE;
    }

    printf("User input: ");
    display(head);

    current = head;

    while (current != NULL) {
        swap_k(current, k);

        int count = 0;
        struct Node *next_group = current;

        while (next_group != NULL && count < k) {
            next_group = next_group->next;
            count++;
        }

        current = next_group;
    }

    printf("Edited linked list: ");
    display(head);

    free_list(head);

    return EXIT_SUCCESS;
}
/*
Write a C program to implement polynomial addition using linked lists.
*/

#include <stdio.h>
#include <stdlib.h>

struct Node {
    int coeff;
    int power;
    struct Node *next;
};

struct Node* createNode(int coeff, int power) {
    struct Node *newNode = (struct Node*)malloc(sizeof(struct Node));
    newNode->coeff = coeff;
    newNode->power = power;
    newNode->next = NULL;
    return newNode;
}

void insert(struct Node **head, int coeff, int power) {
    struct Node *newNode = createNode(coeff, power);

    if (*head == NULL) {
        *head = newNode;
        return;
    }

    struct Node *curr = *head;

    while (curr->next != NULL)
        curr = curr->next;

    curr->next = newNode;
}

struct Node* add(struct Node *p1, struct Node *p2) {
    struct Node *result = NULL;

    while (p1 != NULL && p2 != NULL) {
        if (p1->power == p2->power) {
            if (p1->coeff + p2->coeff != 0)
                insert(&result, p1->coeff + p2->coeff, p1->power);

            p1 = p1->next;
            p2 = p2->next;
        }
        else if (p1->power > p2->power) {
            insert(&result, p1->coeff, p1->power);
            p1 = p1->next;
        }
        else {
            insert(&result, p2->coeff, p2->power);
            p2 = p2->next;
        }
    }

    while (p1 != NULL) {
        insert(&result, p1->coeff, p1->power);
        p1 = p1->next;
    }

    while (p2 != NULL) {
        insert(&result, p2->coeff, p2->power);
        p2 = p2->next;
    }

    return result;
}

void display(struct Node *head) {
    while (head != NULL) {
        printf("%dx^%d", head->coeff, head->power);

        if (head->next != NULL)
            printf(" + ");

        head = head->next;
    }

    printf("\n");
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
    struct Node *p1 = NULL, *p2 = NULL, *result = NULL;
    int n, coeff, power;

    printf("Enter number of terms in first polynomial: ");
    scanf("%d", &n);

    printf("Enter coefficient and power:\n");
    for (int i = 0; i < n; i++) {
        scanf("%d %d", &coeff, &power);
        insert(&p1, coeff, power);
    }

    printf("Enter number of terms in second polynomial: ");
    scanf("%d", &n);

    printf("Enter coefficient and power:\n");
    for (int i = 0; i < n; i++) {
        scanf("%d %d", &coeff, &power);
        insert(&p2, coeff, power);
    }

    printf("First polynomial: ");
    display(p1);

    printf("Second polynomial: ");
    display(p2);

    result = add(p1, p2);

    printf("Sum: ");
    display(result);

    freeList(p1);
    freeList(p2);
    freeList(result);

    return 0;
}
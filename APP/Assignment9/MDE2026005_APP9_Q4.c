/*
Write a C Program to implement Circular Queue using an array.
The program should be menu-driven, with the option to enqueue,
and dequeue, to check whether the queue is empty or full,
traverse, and exit based on the user's choice.
*/

#include <stdio.h>

#define MAX 100

int queue[MAX];
int front = -1;
int rear = -1;

void enqueue(int data) {
    if ((rear + 1) % MAX == front) {
        printf("Queue is full.\n");
        return;
    }

    if (front == -1) {
        front = 0;
        rear = 0;
    }
    else {
        rear = (rear + 1) % MAX;
    }

    queue[rear] = data;

    printf("Element inserted successfully.\n");
}

void dequeue() {
    if (front == -1) {
        printf("Queue is empty.\n");
        return;
    }

    printf("Deleted element: %d\n", queue[front]);

    if (front == rear) {
        front = -1;
        rear = -1;
    }
    else {
        front = (front + 1) % MAX;
    }
}

void checkEmpty() {
    if (front == -1)
        printf("Queue is empty.\n");
    else
        printf("Queue is not empty.\n");
}

void checkFull() {
    if ((rear + 1) % MAX == front)
        printf("Queue is full.\n");
    else
        printf("Queue is not full.\n");
}

void display() {
    if (front == -1) {
        printf("Queue is empty.\n");
        return;
    }

    printf("Queue: ");

    int i = front;

    while (1) {
        printf("%d ", queue[i]);

        if (i == rear)
            break;

        i = (i + 1) % MAX;
    }

    printf("\n");
}

int main() {
    int choice, data;

    while (1) {
        printf("\n1. Enqueue\n");
        printf("2. Dequeue\n");
        printf("3. Check Empty\n");
        printf("4. Check Full\n");
        printf("5. Traverse\n");
        printf("6. Exit\n");

        printf("Enter choice: ");
        scanf("%d", &choice);

        if (choice == 6)
            break;

        if (choice == 1) {
            printf("Enter element: ");
            scanf("%d", &data);

            enqueue(data);
        }
        else if (choice == 2) {
            dequeue();
        }
        else if (choice == 3) {
            checkEmpty();
        }
        else if (choice == 4) {
            checkFull();
        }
        else if (choice == 5) {
            display();
        }
        else {
            printf("Invalid choice.\n");
        }
    }

    return 0;
}
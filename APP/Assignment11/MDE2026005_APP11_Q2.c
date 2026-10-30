// Question 2: Write a recursive function to reverse a stack using only the stack itself, without using another stack, array, or linked list.

#include <stdio.h>
#define SIZE 100

int stack[SIZE];
int top = -1;

void push(int value)
{
    stack[++top] = value;
}

int pop()
{
    return stack[top--];
}

void insertAtBottom(int value)
{
    if (top == -1)
    {
        push(value);
        return;
    }

    int temp = pop();
    insertAtBottom(value);
    push(temp);
}

void reverseStack()
{
    if (top == -1)
        return;

    int temp = pop();
    reverseStack();
    insertAtBottom(temp);
}

void display()
{
    int i;

    for (i = top; i >= 0; i--)
        printf("%d ", stack[i]);

    printf("\n");
}

int main()
{
    int n, i, value;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    if (n < 0 || n > SIZE)
    {
        printf("Invalid stack size!\n");
        return 1;
    }

    for (i = 0; i < n; i++)
    {
        printf("Enter element: ");
        scanf("%d", &value);
        push(value);
    }

    printf("Original stack (top to bottom): ");
    display();

    reverseStack();

    printf("Reversed stack (top to bottom): ");
    display();

    return 0;
}
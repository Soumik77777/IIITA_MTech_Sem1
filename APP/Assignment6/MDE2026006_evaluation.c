#include <stdio.h>
#include <stdlib.h>
struct node{
    int data;
    struct node* next;
};
struct node* reverse(struct node* head, int k){
    struct node *temp, *cur, *net, *start;
    int count = 1;
    int r = 0;
    temp = head;
    start = NULL;
    while(temp != NULL){
        temp = temp->next;
        count++;
        if(count == k){
            r++;
            net = temp;
            while(head != temp){
                cur = head->next;
                head->next = net;
                net = head;
                head = cur;
            }
            if(r == 1)
                start = net;
            head = temp;
            count = 1;
        }
    }
    net = NULL;
    while(head != NULL){
        cur = head->next;
        head->next = net;
        net = head;
        head = cur;
    }
    if(start == NULL)
        start = net;
    return start;
}
int main(){
    int arr[] = {1,2,3,4,5,6,7,8};
    int k = 3;
    int n = sizeof(arr) / sizeof(arr[0]);
    struct node *head = NULL;
    struct node *temp = NULL;
    struct node *newnode = NULL;
    for(int i = 0; i < n; i++){
        newnode = (struct node*)malloc(sizeof(struct node));
        newnode->data = arr[i];
        newnode->next = NULL;
        if(head == NULL){
            head = newnode;
            temp = newnode;
        }
        else{
            temp->next = newnode;
            temp = newnode;
        }
    }
    head = reverse(head, k);
    temp = head;
    while(temp != NULL){
        printf("%d ", temp->data);
        temp = temp->next;
    }
    return 0;
}
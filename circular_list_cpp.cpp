#include "circular_list_cpp.h"
#include <string>
#include <cstring>
#include <iostream>

struct Node {
    double data;
    Node* next;
    Node* prev;
    Node(double val) : data(val), next(nullptr), prev(nullptr) {}
};

struct CircularList {
    Node* head;
    int count;
};

// ========== Реализация ==========

CircularList* createList() {
    CircularList* list = new (std::nothrow) CircularList;
    if (!list) {
        std::cerr << "Ошибка выделения памяти для списка\n";
        return nullptr;
    }
    list->head = nullptr;
    list->count = 0;
    return list;
}

void deleteList(CircularList** list) {
    if (!list || !(*list)) return;
    CircularList* lst = *list;
    if (lst->head) {
        Node* current = lst->head;
        Node* nextNode;
        do {
            nextNode = current->next;
            delete current;
            current = nextNode;
        } while (current != lst->head);
    }
    delete lst;
    *list = nullptr;
}

bool isEmpty(const CircularList* list) {
    return (list == nullptr || list->head == nullptr);
}

int getCount(const CircularList* list) {
    return (list ? list->count : 0);
}

void pushFront(CircularList* list, double value) {
    if (!list) return;
    Node* newNode = new (std::nothrow) Node(value);
    if (!newNode) {
        std::cerr << "Ошибка выделения памяти для узла\n";
        return;
    }
    if (isEmpty(list)) {
        newNode->next = newNode;
        newNode->prev = newNode;
        list->head = newNode;
    } else {
        Node* last = list->head->prev;
        newNode->next = list->head;
        newNode->prev = last;
        last->next = newNode;
        list->head->prev = newNode;
        list->head = newNode;
    }
    list->count++;
}

double get(const CircularList* list, int index) {
    if (isEmpty(list)) return -1;
    int idx = index % list->count;
    if (idx < 0) idx += list->count;
    Node* current = list->head;
    for (int i = 0; i < idx; ++i) {
        current = current->next;
    }
    return current->data;
}

int find(const CircularList* list, double value) {
    if (isEmpty(list)) return -1;
    Node* current = list->head;
    for (int i = 0; i < list->count; ++i) {
        if (current->data == value) return i;
        current = current->next;
    }
    return -1;
}

void deleteNode(CircularList* list, Node* node) {
    if (isEmpty(list) || !node) return;
    if (node->next == node && node->prev == node) {
        list->head = nullptr;
    } else {
        node->prev->next = node->next;
        node->next->prev = node->prev;
        if (node == list->head) {
            list->head = node->next;
        }
    }
    delete node;
    list->count--;
}

int deleteByValue(CircularList* list, double value) {
    if (!list || isEmpty(list)) return 0;
    Node* current = list->head;
    for (int i = 0; i < list->count; ++i) {
        if (current->data == value) {
            deleteNode(list, current);
            return 1;
        }
        current = current->next;
    }
    return 0;
}

void clear(CircularList* list) {
    if (!list || isEmpty(list)) return;
    Node* current = list->head;
    Node* nextNode;
    do {
        nextNode = current->next;
        delete current;
        current = nextNode;
    } while (current != list->head);
    list->head = nullptr;
    list->count = 0;
}

void to_string_impl(const CircularList* list, char* buffer, int buffer_size) {
    if (!list || !list->head) {
        strncpy(buffer, "Empty", buffer_size);
        buffer[buffer_size - 1] = '\0';
        return;
    }
    std::string result;
    Node* current = list->head;
    for (int i = 0; i < list->count; ++i) {
        result += std::to_string(current->data);
        if (i < list->count - 1) result += " ";
        current = current->next;
    }
    strncpy(buffer, result.c_str(), buffer_size - 1);
    buffer[buffer_size - 1] = '\0';
}

// ========== C-интерфейс ==========
extern "C" {

    CircularList* list_create() {
        return createList();
    }

    void list_destroy(CircularList* list) {
        deleteList(&list);
    }

    int list_is_empty(CircularList* list) {
        return isEmpty(list) ? 1 : 0;
    }

    int list_count(CircularList* list) {
        return getCount(list);
    }

    void list_push_front(CircularList* list, double value) {
        pushFront(list, value);
    }

    double list_get(CircularList* list, int index) {
        return get(list, index);
    }

    int list_find(CircularList* list, double value) {
        return find(list, value);
    }

    int list_delete_value(CircularList* list, double value) {
        return deleteByValue(list, value);
    }

    void list_clear(CircularList* list) {
        clear(list);
    }

    void list_to_string(CircularList* list, char* buffer, int buffer_size) {
        to_string_impl(list, buffer, buffer_size);
    }

} // extern "C"
#include "circular_list_stl.h"
#include <list>
#include <string>
#include <cstring>
#include <iostream>

struct CircularListSTL {
    std::list<double> data;
};

// ========== Реализация ==========

CircularListSTL* createListSTL() {
    return new CircularListSTL();
}

void deleteListSTL(CircularListSTL* list) {
    delete list;
}

bool isEmptySTL(const CircularListSTL* list) {
    return list->data.empty();
}

int getCountSTL(const CircularListSTL* list) {
    return (int)list->data.size();
}

void pushFrontSTL(CircularListSTL* list, double value) {
    list->data.push_front(value);
}

double getSTL(const CircularListSTL* list, int index) {
    if (index < 0 || index >= (int)list->data.size()) return -1;
    auto it = list->data.begin();
    std::advance(it, index);
    return *it;
}

int findSTL(const CircularListSTL* list, double value) {
    int idx = 0;
    for (double x : list->data) {
        if (x == value) return idx;
        ++idx;
    }
    return -1;
}

int deleteByValueSTL(CircularListSTL* list, double value) {
    for (auto it = list->data.begin(); it != list->data.end(); ++it) {
        if (*it == value) {
            list->data.erase(it);
            return 1;
        }
    }
    return 0;
}

void clearSTL(CircularListSTL* list) {
    list->data.clear();
}

void to_string_impl_stl(const CircularListSTL* list, char* buffer, int buffer_size) {
    if (list->data.empty()) {
        strncpy(buffer, "Empty", buffer_size);
        buffer[buffer_size - 1] = '\0';
        return;
    }
    std::string result;
    for (double x : list->data) {
        result += std::to_string(x);
        result += " ";
    }
    if (!result.empty()) result.pop_back(); // убрать лишний пробел
    strncpy(buffer, result.c_str(), buffer_size - 1);
    buffer[buffer_size - 1] = '\0';
}

// ========== C-интерфейс ==========
extern "C" {

    CircularListSTL* stl_list_create() {
        return createListSTL();
    }

    void stl_list_destroy(CircularListSTL* list) {
        deleteListSTL(list);
    }

    int stl_list_is_empty(CircularListSTL* list) {
        return isEmptySTL(list) ? 1 : 0;
    }

    int stl_list_count(CircularListSTL* list) {
        return getCountSTL(list);
    }

    void stl_list_push_front(CircularListSTL* list, double value) {
        pushFrontSTL(list, value);
    }

    double stl_list_get(CircularListSTL* list, int index) {
        return getSTL(list, index);
    }

    int stl_list_find(CircularListSTL* list, double value) {
        return findSTL(list, value);
    }

    int stl_list_delete_value(CircularListSTL* list, double value) {
        return deleteByValueSTL(list, value);
    }

    void stl_list_clear(CircularListSTL* list) {
        clearSTL(list);
    }

    void stl_list_to_string(CircularListSTL* list, char* buffer, int buffer_size) {
        to_string_impl_stl(list, buffer, buffer_size);
    }

} // extern "C"
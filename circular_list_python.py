class CircularDoublyLinkedList:
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None
            self.prev = None

    def __init__(self):
        self.head = None
        self._count = 0

    def is_empty(self):
        return self.head is None

    def count(self):
        return self._count

    def push_front(self, value):
        new_node = self.Node(value)
        if self.is_empty():
            new_node.next = new_node
            new_node.prev = new_node
            self.head = new_node
        else:
            last = self.head.prev
            new_node.next = self.head
            new_node.prev = last
            last.next = new_node
            self.head.prev = new_node
            self.head = new_node
        self._count += 1

    def get(self, index):
        if self.is_empty():
            return None  # или -1, но лучше None
        idx = index % self._count
        if idx < 0:
            idx += self._count
        current = self.head
        for _ in range(idx):
            current = current.next
        return current.data

    def find(self, value):
        if self.is_empty():
            return -1
        current = self.head
        for i in range(self._count):
            if current.data == value:
                return i
            current = current.next
        return -1

    def delete_value(self, value):
        if self.is_empty():
            return False
        current = self.head
        for _ in range(self._count):
            if current.data == value:
                self._delete_node(current)
                return True
            current = current.next
        return False

    def _delete_node(self, node):
        if self._count == 1:
            self.head = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev
            if node == self.head:
                self.head = node.next
        self._count -= 1

    def clear(self):
        self.head = None
        self._count = 0

    def to_string(self):
        if self.is_empty():
            return "Empty"
        result = []
        current = self.head
        for _ in range(self._count):
            result.append(str(current.data))
            current = current.next
        return " ".join(result)
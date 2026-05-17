import ctypes
import os
# ==================== ОБЁРТКИ ДЛЯ C++ ====================

class CppList:
    def __init__(self, lib_path):
        self.lib = ctypes.CDLL(lib_path)
        self.lib.list_create.restype = ctypes.c_void_p
        self.lib.list_destroy.argtypes = [ctypes.c_void_p]
        self.lib.list_destroy.restype = None
        self.lib.list_is_empty.argtypes = [ctypes.c_void_p]
        self.lib.list_is_empty.restype = ctypes.c_int
        self.lib.list_count.argtypes = [ctypes.c_void_p]
        self.lib.list_count.restype = ctypes.c_int
        self.lib.list_push_front.argtypes = [ctypes.c_void_p, ctypes.c_double]
        self.lib.list_push_front.restype = None
        self.lib.list_get.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.lib.list_get.restype = ctypes.c_double
        self.lib.list_find.argtypes = [ctypes.c_void_p, ctypes.c_double]
        self.lib.list_find.restype = ctypes.c_int
        self.lib.list_delete_value.argtypes = [ctypes.c_void_p, ctypes.c_double]
        self.lib.list_delete_value.restype = ctypes.c_int
        self.lib.list_clear.argtypes = [ctypes.c_void_p]
        self.lib.list_clear.restype = None
        self.lib.list_to_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.lib.list_to_string.restype = None
        self.obj = self.lib.list_create()

    def destroy(self):
        self.lib.list_destroy(self.obj)

    def is_empty(self):
        return bool(self.lib.list_is_empty(self.obj))

    def count(self):
        return self.lib.list_count(self.obj)

    def push_front(self, val):
        self.lib.list_push_front(self.obj, val)

    def get(self, index):
        return self.lib.list_get(self.obj, index)

    def find(self, val):
        return self.lib.list_find(self.obj, val)

    def delete_value(self, val):
        return bool(self.lib.list_delete_value(self.obj, val))

    def clear(self):
        self.lib.list_clear(self.obj)

    def to_string(self):
        buf = ctypes.create_string_buffer(4096)
        self.lib.list_to_string(self.obj, buf, len(buf))
        return buf.value.decode()


class StlList:
    def __init__(self, lib_path):
        self.lib = ctypes.CDLL(lib_path)
        self.lib.stl_list_create.restype = ctypes.c_void_p
        self.lib.stl_list_destroy.argtypes = [ctypes.c_void_p]
        self.lib.stl_list_destroy.restype = None
        self.lib.stl_list_is_empty.argtypes = [ctypes.c_void_p]
        self.lib.stl_list_is_empty.restype = ctypes.c_int
        self.lib.stl_list_count.argtypes = [ctypes.c_void_p]
        self.lib.stl_list_count.restype = ctypes.c_int
        self.lib.stl_list_push_front.argtypes = [ctypes.c_void_p, ctypes.c_double]
        self.lib.stl_list_push_front.restype = None
        self.lib.stl_list_get.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.lib.stl_list_get.restype = ctypes.c_double
        self.lib.stl_list_find.argtypes = [ctypes.c_void_p, ctypes.c_double]
        self.lib.stl_list_find.restype = ctypes.c_int
        self.lib.stl_list_delete_value.argtypes = [ctypes.c_void_p, ctypes.c_double]
        self.lib.stl_list_delete_value.restype = ctypes.c_int
        self.lib.stl_list_clear.argtypes = [ctypes.c_void_p]
        self.lib.stl_list_clear.restype = None
        self.lib.stl_list_to_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.lib.stl_list_to_string.restype = None
        self.obj = self.lib.stl_list_create()

    def destroy(self):
        self.lib.stl_list_destroy(self.obj)

    def is_empty(self):
        return bool(self.lib.stl_list_is_empty(self.obj))

    def count(self):
        return self.lib.stl_list_count(self.obj)

    def push_front(self, val):
        self.lib.stl_list_push_front(self.obj, val)

    def get(self, index):
        return self.lib.stl_list_get(self.obj, index)

    def find(self, val):
        return self.lib.stl_list_find(self.obj, val)

    def delete_value(self, val):
        return bool(self.lib.stl_list_delete_value(self.obj, val))

    def clear(self):
        self.lib.stl_list_clear(self.obj)

    def to_string(self):
        buf = ctypes.create_string_buffer(4096)
        self.lib.stl_list_to_string(self.obj, buf, len(buf))
        return buf.value.decode()
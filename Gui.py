import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import os
from cpp_wrappers import CppList, StlList
from circular_list_python import CircularDoublyLinkedList


# ==================== GUI ====================

def main():
    # Пути к DLL (зависит от ОС)
    if os.name == 'nt':
        cpp_lib = "./list_cpp.dll"
        stl_lib = "./list_stl.dll"
    else:
        cpp_lib = "./liblist_cpp.so"
        stl_lib = "./liblist_stl.so"

    # Создание объектов
    cpp_obj = CppList(cpp_lib)
    stl_obj = StlList(stl_lib)
    py_obj = CircularDoublyLinkedList()

    implementations = {
        "C++ (без STL)": cpp_obj,
        "C++ (STL)": stl_obj,
        "Python": py_obj
    }

    # --- Создание окна ---
    root = tk.Tk()
    root.title("Циклический двусвязный список")
    root.geometry("600x600")

    # Переменная выбранной реализации
    current_impl = tk.StringVar(value="C++ (без STL)")

    # --- Элементы управления ---
    frame_top = tk.Frame(root)
    frame_top.pack(pady=10)

    tk.Label(frame_top, text="Реализация:").grid(row=0, column=0, padx=5)
    impl_combo = ttk.Combobox(frame_top, textvariable=current_impl,
                              values=list(implementations.keys()),
                              state="readonly", width=20)
    impl_combo.grid(row=0, column=1, padx=5)

    tk.Label(frame_top, text="Значение:").grid(row=0, column=2, padx=5)
    val_entry = tk.Entry(frame_top, width=10)
    val_entry.grid(row=0, column=3, padx=5)
    val_entry.insert(0, " ")

    # Кнопки
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    btn_push = tk.Button(btn_frame, text="Добавить число", width=18)
    btn_delete = tk.Button(btn_frame, text="Удалить число", width=18)
    btn_find = tk.Button(btn_frame, text="Найти", width=18)
    btn_clear = tk.Button(btn_frame, text="Очистить", width=18)
    btn_refresh = tk.Button(btn_frame, text="Обновить отображение", width=18)

    btn_push.grid(row=0, column=0, padx=5, pady=2)
    btn_delete.grid(row=0, column=1, padx=5, pady=2)
    btn_find.grid(row=0, column=2, padx=5, pady=2)
    btn_clear.grid(row=1, column=0, padx=5, pady=2)
    btn_refresh.grid(row=1, column=1, padx=5, pady=2)

    # Текстовое поле для вывода
    output = tk.Text(root, height=12, state='disabled', wrap=tk.WORD)
    output.pack(pady=10, fill=tk.BOTH, expand=True)

    # --- Функции-обработчики ---
    def get_current():
        return implementations[current_impl.get()]

    def update_display():
        lst = get_current()
        s = lst.to_string()
        output.config(state='normal')
        output.delete(1.0, tk.END)
        if s == "Empty":
            output.insert(tk.END, "Список пуст")
        else:
            items = s.split()
            for i, item in enumerate(items, 1):
                output.insert(tk.END, f"{i}. {item}\n")
        output.config(state='disabled')

    def on_push():
        try:
            val = float(val_entry.get())
            get_current().push_front(val)
            val_entry.delete(0, tk.END)
            val_entry.focus_set()
            update_display()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_delete():
        try:
            val = float(val_entry.get())
            lst = get_current()
            if lst.delete_value(val):
                messagebox.showinfo("Удаление", f"Значение {val} удалено")
            else:
                messagebox.showinfo("Удаление", f"Значение {val} не найдено")
            update_display()
            val_entry.delete(0, tk.END)
            val_entry.focus_set()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_find():
        try:
            val = float(val_entry.get())
            lst = get_current()
            pos = lst.find(val)
            val_entry.delete(0, tk.END)
            val_entry.focus_set()
            if pos != -1:
                messagebox.showinfo("Поиск", f"Значение {val} найдено на позиции {pos}")
            else:
                messagebox.showinfo("Поиск", f"Значение {val} не найдено")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_clear():
        get_current().clear()
        update_display()
        val_entry.delete(0, tk.END)
        val_entry.focus_set()
        messagebox.showinfo("Очистка", "Список очищен")

    # Привязка обработчиков
    btn_push.config(command=on_push)
    btn_delete.config(command=on_delete)
    btn_find.config(command=on_find)
    btn_clear.config(command=on_clear)
    btn_refresh.config(command=update_display)

    # Обработка закрытия окна
    def on_closing():
        cpp_obj.destroy()
        stl_obj.destroy()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Первоначальное обновление
    update_display()

    root.mainloop()

if __name__ == "__main__":
    main()
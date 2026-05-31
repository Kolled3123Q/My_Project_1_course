import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes
import ctypes.wintypes as wintypes
import os
import struct
import time
import csv
import heapq
import tempfile
import subprocess
import threading

# ---------- Получение памяти текущего процесса ----------
class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]

kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi
kernel32.GetCurrentProcess.argtypes = []
kernel32.GetCurrentProcess.restype = ctypes.c_void_p
psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

def get_process_memory_mb():
    process = kernel32.GetCurrentProcess()
    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(counters)
    if psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), ctypes.sizeof(counters)):
        return counters.WorkingSetSize / (1024 * 1024)
    return 0.0

# ---------- Загрузка C++ DLL ----------
d = os.path.dirname(os.path.abspath(__file__))
if os.name == 'nt':
    os.add_dll_directory(d)

lib = None
try:
    lib_path = os.path.join(d, "sorter.dll")
    lib = ctypes.CDLL(lib_path, winmode=0)
    lib.run_sort_with_chunk.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)
    ]
    lib.bucket_sort_cpp.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)
    ]
    lib.run_sort.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)
    ]
except Exception as e:
    print(f"Ошибка загрузки DLL: {e}")

# ---------- Константы диапазонов для бакетной сортировки (Python) ----------
PY_RANGES = {
    0: (100000000, 999999999),   # ID
    2: (100, 999),               # Quantity
    3: (10000, 999999)           # Price
}

# ---------- GUI ----------
class App:
    def __init__(self, root):
        self.root = root
        self.lib = lib
        self.monitor_mem = False
        self.timer_running = False
        self.start_time = 0
        self.after_id = None

        root.title("Сортировка CSV – внешняя и бакетная (≤10% памяти)")
        root.geometry("750x850")
        root.configure(bg='#f0f0f0')

        # --- Генерация ---
        gen_frame = tk.Frame(root, bg='#f0f0f0')
        gen_frame.pack(pady=5)
        self.btn_gen = tk.Button(gen_frame, text="Создать тестовые данные", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), command=self.generate_data)
        self.btn_gen.pack(side=tk.LEFT, padx=5)
        self.gen_status = tk.Label(gen_frame, text="", fg="blue", bg='#f0f0f0')
        self.gen_status.pack(side=tk.LEFT)

        # --- CSV ---
        tk.Label(root, text="Работа с CSV", font=("Arial", 11, "bold"), bg='#f0f0f0').pack(pady=5)
        self.p_csv = tk.StringVar(value="CSV не выбран")
        self.btn_csv = tk.Button(root, text="Выбрать CSV-файл", command=lambda: self.sel("csv"))
        self.btn_csv.pack()
        tk.Label(root, textvariable=self.p_csv, fg="blue", bg='#f0f0f0').pack()

        # --- Лимит памяти ---
        lim_frame = tk.Frame(root, bg='#f0f0f0')
        lim_frame.pack(pady=5)
        tk.Label(lim_frame, text="Лимит памяти (% от размера файла):", bg='#f0f0f0').pack(side=tk.LEFT)
        self.mem_percent = tk.StringVar(value="10")
        self.mem_entry = tk.Entry(lim_frame, textvariable=self.mem_percent, width=5)
        self.mem_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(lim_frame, text="% (для обычной сортировки)", bg='#f0f0f0').pack(side=tk.LEFT)

        # --- Критерий сортировки ---
        tk.Label(root, text="Поле для сортировки:", bg='#f0f0f0').pack()
        self.c = ttk.Combobox(root, values=["Артикул", "Название", "Количество", "Цена"])
        self.c.current(0)
        self.c.pack()
        self.c.bind("<<ComboboxSelected>>", self._toggle_bucket_checkbox)

        # --- Настройки бакетной сортировки ---
        bucket_frame = tk.Frame(root, bg='#f0f0f0')
        bucket_frame.pack(pady=5)
        self.bucket_var = tk.BooleanVar(value=False)
        self.bucket_checkbox = tk.Checkbutton(bucket_frame, text="Использовать бакетную сортировку (только для чисел)",
                                              variable=self.bucket_var, state="disabled", bg='#f0f0f0')
        self.bucket_checkbox.pack(side=tk.LEFT)
        tk.Label(bucket_frame, text="  Количество бакетов:", bg='#f0f0f0').pack(side=tk.LEFT)
        self.buckets_var = tk.StringVar(value="200")
        self.buckets_entry = tk.Entry(bucket_frame, textvariable=self.buckets_var, width=6)
        self.buckets_entry.pack(side=tk.LEFT, padx=5)
        self._toggle_bucket_checkbox()

        # --- Кнопки сортировки ---
        btn_frame = tk.Frame(root, bg='#f0f0f0')
        btn_frame.pack(pady=10)
        self.btn_cpp = tk.Button(btn_frame, text="Сортировка (C++)", bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=22, command=self.run_cpp)
        self.btn_cpp.pack(side=tk.LEFT, padx=5)
        self.btn_python = tk.Button(btn_frame, text="Сортировка (Python)", bg="#FF9800", fg="white", font=("Arial", 9, "bold"), width=22, command=self.run_python)
        self.btn_python.pack(side=tk.LEFT, padx=5)

        self.r = tk.Label(root, text="", font=("Arial", 10, "italic"), bg='#f0f0f0')
        self.r.pack()

        # --- Метрики ---
        metrics = tk.Frame(root, bg='#f0f0f0')
        metrics.pack(pady=5)
        self.proc_mem_label = tk.Label(metrics, text="Память процесса: -- МБ", font=("Arial", 9), bg='#f0f0f0')
        self.proc_mem_label.pack(side=tk.LEFT, padx=10)
        self.timer_label = tk.Label(metrics, text="Таймер: 0.0 с", font=("Arial", 9, "bold"), bg='#f0f0f0')
        self.timer_label.pack(side=tk.LEFT, padx=10)
        self.chunk_info = tk.Label(metrics, text="", font=("Arial", 8), bg='#f0f0f0')
        self.chunk_info.pack(side=tk.LEFT, padx=10)

        ttk.Separator(root, orient='horizontal').pack(fill='x', pady=10)

        # --- BIN ---
        tk.Label(root, text="Работа с BIN (бинарный)", font=("Arial", 11, "bold"), bg='#f0f0f0').pack()
        self.p_bin = tk.StringVar(value="BIN не выбран")
        self.btn_bin = tk.Button(root, text="Выбрать BIN-файл", command=lambda: self.sel("bin"))
        self.btn_bin.pack(pady=2)
        tk.Label(root, textvariable=self.p_bin, fg="green", bg='#f0f0f0').pack()
        tk.Button(root, text="Просмотр BIN", bg="lightgreen", command=self.read_bin).pack()

        # --- Превью ---
        tk.Label(root, text="Превью результата (20 строк):", bg='#f0f0f0').pack()
        self.v = tk.Text(root, height=18, width=85, font=("Consolas", 9), relief="groove", borderwidth=2)
        self.v.pack(pady=5)

    def sel(self, ftype):
        f = filedialog.askopenfilename(filetypes=[(f"{ftype.upper()} files", f"*.{ftype}")])
        if f:
            if ftype == "csv":
                self.p_csv.set(f)
            else:
                self.p_bin.set(f)

    def _toggle_bucket_checkbox(self, event=None):
        col = self.c.get()
        if col in ("Артикул", "Количество", "Цена"):
            self.bucket_checkbox.config(state="normal")
        else:
            self.bucket_checkbox.config(state="disabled")
            self.bucket_var.set(False)

    # ---------- Мониторинг и таймер ----------
    def start_mem_monitor(self):
        self.monitor_mem = True
        self._update_mem()

    def stop_mem_monitor(self):
        self.monitor_mem = False
        self.proc_mem_label.config(text="Память процесса: -- МБ")

    def _update_mem(self):
        if self.monitor_mem:
            mem = get_process_memory_mb()
            self.proc_mem_label.config(text=f"Память процесса: {mem:.1f} МБ")
            self.root.after(500, self._update_mem)

    def start_timer(self):
        self.timer_running = True
        self.start_time = time.time()
        self._update_timer()

    def stop_timer(self):
        self.timer_running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _update_timer(self):
        if self.timer_running:
            elapsed = time.time() - self.start_time
            self.timer_label.config(text=f"Таймер: {elapsed:.1f} с")
            self.after_id = self.root.after(100, self._update_timer)

    def _set_controls_state(self, state):
        for w in (self.btn_gen, self.btn_csv, self.btn_cpp, self.btn_python, self.btn_bin,
                  self.c, self.mem_entry, self.bucket_checkbox, self.buckets_entry):
            w.config(state=state)

    # ---------- Расчёт чанка для обычной сортировки ----------
    def estimate_chunk_mb(self, csv_path, percent=10):
        file_size = os.path.getsize(csv_path)
        max_mem_bytes = file_size * percent / 100.0
        chunk_mb = max(1, int(max_mem_bytes / (1024 * 1024) * 0.75))
        self.chunk_info.config(text=f"Чанк C++: {chunk_mb} МБ (лимит {percent}%)")
        return chunk_mb

    def estimate_chunk_size_rows(self, csv_path, percent=10):
        file_size = os.path.getsize(csv_path)
        max_mem_bytes = file_size * percent / 100.0
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                f.readline()
                total, count = 0, 0
                for _ in range(100):
                    line = f.readline()
                    if not line:
                        break
                    total += len(line.encode('utf-8'))
                    count += 1
                avg_len = total / max(count, 1)
        except:
            avg_len = 200
        overhead = 4.0
        chunk_size = int(max_mem_bytes / (avg_len * overhead))
        chunk_size = max(1000, min(chunk_size, 140000))
        self.chunk_info.config(text=f"Чанк Python: {chunk_size} строк (лимит {percent}%)")
        return chunk_size

    # ---------- Генерация ----------
    def generate_data(self):
        script = os.path.join(d, "generator.py")
        if not os.path.exists(script):
            messagebox.showerror("Ошибка", "generator.py не найден")
            return
        self.gen_status.config(text="Генерация...", fg="orange")
        self.root.update()
        def run():
            try:
                subprocess.run(["python", script], capture_output=True, text=True, timeout=600, check=True)
                self.root.after(0, self._on_gen_ok)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
                self.root.after(0, lambda: self.gen_status.config(text="Ошибка", fg="red"))
        threading.Thread(target=run, daemon=True).start()

    def _on_gen_ok(self):
        if os.path.exists("data.csv"):
            self.p_csv.set("data.csv")
        if os.path.exists("data.bin"):
            self.p_bin.set("data.bin")
        self.gen_status.config(text="Готово!", fg="green")
        messagebox.showinfo("Успех", "CSV и BIN созданы")

    # ---------- C++ сортировка ----------
    def run_cpp(self):
        if not self.lib:
            messagebox.showerror("Ошибка", "DLL не загружена")
            return
        fin = self.p_csv.get()
        if not os.path.exists(fin):
            messagebox.showerror("Ошибка", "CSV не выбран")
            return
        col_map = {"Артикул":0, "Название":1, "Количество":2, "Цена":3}
        col = col_map[self.c.get()]
        use_bucket = self.bucket_var.get() and col in (0,2,3)
        try:
            pct = float(self.mem_percent.get())
            pct = max(1, min(pct, 50))
        except:
            pct = 10
            self.mem_percent.set("10")

        self._set_controls_state('disabled')
        self.start_timer()
        self.start_mem_monitor()
        if use_bucket:
            try:
                num_buckets = max(2, min(int(self.buckets_var.get()), 1000))
            except:
                num_buckets = 200
            self.r.config(text=f"C++ бакетная сортировка ({num_buckets} бакетов)...", fg="blue")
            threading.Thread(target=self._cpp_bucket_worker, args=(fin, col, num_buckets), daemon=True).start()
        else:
            chunk_mb = self.estimate_chunk_mb(fin, pct)
            self.r.config(text="C++ обычная сортировка...", fg="blue")
            threading.Thread(target=self._cpp_standard_worker, args=(fin, col, chunk_mb), daemon=True).start()

    def _cpp_standard_worker(self, fin, col, chunk_mb):
        fout = "sorted_out_cpp.csv"
        t1, t2 = ctypes.c_double(0), ctypes.c_double(0)
        try:
            self.lib.run_sort_with_chunk(fin.encode('utf-8'), fout.encode('utf-8'), col, chunk_mb,
                                         ctypes.byref(t1), ctypes.byref(t2))
            self.root.after(0, lambda: self._sort_finished("C++", t1.value, t2.value, fout))
        except Exception as e:
            self.root.after(0, lambda: self._sort_error(str(e)))
        finally:
            self.root.after(0, self.stop_mem_monitor)

    def _cpp_bucket_worker(self, fin, col, num_buckets):
        fout = "sorted_out_cpp_bucket.csv"
        t_distrib, t_sort = ctypes.c_double(0), ctypes.c_double(0)
        try:
            self.lib.bucket_sort_cpp(fin.encode('utf-8'), fout.encode('utf-8'), col, num_buckets,
                                     ctypes.byref(t_distrib), ctypes.byref(t_sort))
            self.root.after(0, lambda: self._sort_finished("C++ (бакетная)", t_distrib.value, t_sort.value, fout))
        except Exception as e:
            self.root.after(0, lambda: self._sort_error(str(e)))
        finally:
            self.root.after(0, self.stop_mem_monitor)

    # ---------- Python сортировка ----------
    def run_python(self):
        fin = self.p_csv.get()
        if not os.path.exists(fin):
            messagebox.showerror("Ошибка", "CSV не выбран")
            return
        col_map = {"Артикул":0, "Название":1, "Количество":2, "Цена":3}
        col = col_map[self.c.get()]
        use_bucket = self.bucket_var.get() and col in (0,2,3)
        try:
            pct = float(self.mem_percent.get())
            pct = max(1, min(pct, 50))
        except:
            pct = 10
            self.mem_percent.set("10")

        self._set_controls_state('disabled')
        self.start_timer()
        self.start_mem_monitor()
        if use_bucket:
            try:
                num_buckets = max(2, min(int(self.buckets_var.get()), 1000))
            except:
                num_buckets = 200
            self.r.config(text=f"Python бакетная сортировка ({num_buckets} бакетов)...", fg="blue")
            threading.Thread(target=self._python_bucket_worker, args=(fin, col, num_buckets), daemon=True).start()
        else:
            chunk_size = self.estimate_chunk_size_rows(fin, pct)
            self.r.config(text="Python обычная сортировка...", fg="blue")
            threading.Thread(target=self._python_standard_worker, args=(fin, col, chunk_size), daemon=True).start()

    # ---------- Python обычная ----------
    def _python_standard_worker(self, fin, col, chunk_size):
        fout = "sorted_out_py.csv"
        temp_files = []
        try:
            t_split_start = time.time()
            with open(fin, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                chunk = []
                for row in reader:
                    chunk.append(row)
                    if len(chunk) >= chunk_size:
                        self._save_chunk(chunk, col, temp_files)
                        chunk = []
                if chunk:
                    self._save_chunk(chunk, col, temp_files)
            t_split = time.time() - t_split_start

            t_merge_start = time.time()
            with open(fout, 'w', newline='', encoding='utf-8') as out_f:
                writer = csv.writer(out_f)
                writer.writerow(header)
                files = [open(f, 'r', encoding='utf-8') for f in temp_files]
                readers = [csv.reader(f) for f in files]
                key_func = lambda x: float(x[col]) if col in (0,2,3) else x[col]
                for row in heapq.merge(*readers, key=key_func):
                    writer.writerow(row)
                for f in files:
                    f.close()
            t_merge = time.time() - t_merge_start

            for f in temp_files:
                os.remove(f)

            self.root.after(0, lambda: self._sort_finished("Python", t_split, t_merge, fout))
        except Exception as e:
            self.root.after(0, lambda: self._sort_error(str(e)))
        finally:
            self.root.after(0, self.stop_mem_monitor)

    # ---------- Python бакетная ----------
    def _python_bucket_worker(self, fin, col, num_buckets):
        fout = "sorted_out_py_bucket.csv"
        min_val, max_val = PY_RANGES[col]
        step = (max_val - min_val + 1) / num_buckets
        bucket_files = []
        bucket_handles = []
        try:
            for i in range(num_buckets):
                bf = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8', suffix='.csv')
                bucket_files.append(bf.name)
                bucket_handles.append(bf)

            t_distrib_start = time.time()
            with open(fin, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    val_str = row[col]
                    try:
                        val = int(val_str)
                    except:
                        val = 0
                    idx = int((val - min_val) / step)
                    if idx < 0:
                        idx = 0
                    if idx >= num_buckets:
                        idx = num_buckets - 1
                    bucket_handles[idx].write(','.join(row) + '\n')
            t_distrib = time.time() - t_distrib_start

            for h in bucket_handles:
                h.close()

            t_sort_start = time.time()
            with open(fout, 'w', newline='', encoding='utf-8') as out_f:
                writer = csv.writer(out_f)
                writer.writerow(header)
                for bf in bucket_files:
                    rows = []
                    with open(bf, 'r', encoding='utf-8') as fb:
                        reader = csv.reader(fb)
                        for row in reader:
                            rows.append(row)
                    rows.sort(key=lambda x: int(x[col]))
                    writer.writerows(rows)
            t_sort = time.time() - t_sort_start

            for bf in bucket_files:
                os.remove(bf)

            self.root.after(0, lambda: self._sort_finished("Python (бакетная)", t_distrib, t_sort, fout))
        except Exception as e:
            self.root.after(0, lambda: self._sort_error(str(e)))
        finally:
            self.root.after(0, self.stop_mem_monitor)

    def _save_chunk(self, chunk, col, temp_list):
        key = lambda x: float(x[col]) if col in (0,2,3) else x[col]
        chunk.sort(key=key)
        tmp = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8')
        csv.writer(tmp).writerows(chunk)
        temp_list.append(tmp.name)
        tmp.close()

    def _sort_finished(self, lang, t_split, t_merge, fout):
        self.stop_timer()
        total = time.time() - self.start_time if self.timer_running else t_split + t_merge
        self.r.config(text=f"[{lang}] Распределение: {t_split:.2f}с | Сортировка: {t_merge:.2f}с | Всего: {total:.1f}с", fg="black")
        self.update_preview(fout)
        self._set_controls_state('normal')

    def _sort_error(self, msg):
        self.stop_timer()
        self.stop_mem_monitor()
        messagebox.showerror("Ошибка сортировки", msg)
        self.r.config(text="Ошибка", fg="red")
        self._set_controls_state('normal')

    def update_preview(self, filename):
        self.v.delete(1.0, tk.END)
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                for _ in range(21):
                    line = f.readline()
                    if not line:
                        break
                    self.v.insert(tk.END, line)

    def read_bin(self):
        fbin = self.p_bin.get()
        if not os.path.exists(fbin):
            messagebox.showerror("Ошибка", "BIN не выбран")
            return
        self.v.delete(1.0, tk.END)
        self.v.insert(tk.END, "Артикул, Название, Количество, Цена\n")
        try:
            with open(fbin, "rb") as f:
                for _ in range(20):
                    data = f.read(24)
                    if not data:
                        break
                    uid, name_raw, qty, price = struct.unpack('I 12s I I', data)
                    name = name_raw.decode('utf-8', errors='ignore').strip('\x00')
                    self.v.insert(tk.END, f"{uid}, {name}, {qty}, {price}\n")
        except Exception as e:
            self.v.insert(tk.END, f"Ошибка: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
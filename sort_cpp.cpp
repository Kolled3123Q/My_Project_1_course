#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include <chrono>
#include <queue>
#include <cstdio>
#include <cstring>
#include <stdexcept>

using namespace std;

// ---------- Общие структуры ----------
struct Item {
    long long k_num;   // Для числовых полей
    string k_str;      // Для текстового поля
    string full;       // Полная строка
    bool is_num;

    bool operator<(const Item& o) const {
        if (is_num) return k_num < o.k_num;
        return k_str < o.k_str;
    }
    bool operator>(const Item& o) const {
        if (is_num) return k_num > o.k_num;
        return k_str > o.k_str;
    }
};

Item parse(const string& s, int col) {
    Item it;
    it.full = s;
    size_t st = 0, en = s.find(',');
    for (int i = 0; i < col && en != string::npos; i++) {
        st = en + 1;
        en = s.find(',', st);
    }
    string val = s.substr(st, en - st);
    if (col == 0 || col == 2 || col == 3) {
        it.is_num = true;
        try { it.k_num = stoll(val); }
        catch (...) { it.k_num = 0; }
    } else {
        it.is_num = false;
        it.k_str = val;
    }
    return it;
}

static string tmp_name(int pass, int id) {
    char buf[64];
    snprintf(buf, sizeof(buf), "tmp_p%03d_r%05d.csv", pass, id);
    return string(buf);
}

static void cleanup_tmp_prefix() {
    for (int p = 0; p < 50; p++)
        for (int r = 0; r < 20000; r++)
            remove(tmp_name(p, r).c_str());
}

// ---------- Обычная внешняя сортировка (многофазное слияние) ----------
void write_sorted_chunk(const string& path, vector<Item>& chunk) {
    sort(chunk.begin(), chunk.end());
    ofstream out(path, ios::out | ios::trunc);
    if (!out) throw runtime_error("Cannot create temp file");
    for (auto& x : chunk)
        out << x.full << "\n";
}

vector<string> split_into_runs(const string& in_path, int col, size_t chunk_bytes) {
    ifstream in(in_path);
    if (!in) throw runtime_error("Cannot open input CSV");
    string header, line;
    getline(in, header); // пропускаем заголовок

    vector<string> runs;
    vector<Item> buf;
    buf.reserve(200000);
    size_t used = 0;
    int run_id = 0;

    while (getline(in, line)) {
        if (line.empty()) continue;
        Item it = parse(line, col);
        used += it.full.size() + 256; // консервативная оценка
        buf.push_back(move(it));
        if (used >= chunk_bytes) {
            string name = tmp_name(0, run_id++);
            write_sorted_chunk(name, buf);
            runs.push_back(name);
            buf.clear();
            used = 0;
        }
    }
    if (!buf.empty()) {
        string name = tmp_name(0, run_id++);
        write_sorted_chunk(name, buf);
        runs.push_back(name);
    }
    return runs;
}

struct Node {
    Item item;
    int file_idx;
};
struct NodeCmp {
    bool operator()(const Node& a, const Node& b) const {
        if (a.item.is_num != b.item.is_num) {
            return a.item.is_num ? (a.item.k_num > b.item.k_num) : (a.item.k_str > b.item.k_str);
        }
        if (a.item.is_num) return a.item.k_num > b.item.k_num;
        else return a.item.k_str > b.item.k_str;
    }
};

void merge_group_to_file(const vector<string>& inputs, const string& output, int col) {
    vector<ifstream> files;
    files.reserve(inputs.size());
    for (const auto& path : inputs) {
        files.emplace_back(path);
        if (!files.back())
            throw runtime_error("Cannot open temp file for merge");
    }

    priority_queue<Node, vector<Node>, NodeCmp> pq;
    string line;
    for (size_t i = 0; i < files.size(); i++) {
        if (getline(files[i], line)) {
            if (!line.empty())
                pq.push({parse(line, col), (int)i});
        }
    }

    ofstream out(output, ios::out | ios::trunc);
    if (!out) throw runtime_error("Cannot create output file for merge");

    while (!pq.empty()) {
        Node cur = pq.top(); pq.pop();
        out << cur.item.full << "\n";
        if (getline(files[cur.file_idx], line)) {
            if (!line.empty())
                pq.push({parse(line, col), cur.file_idx});
        }
    }
}

void multi_pass_merge(vector<string>& runs, int col, int merge_k) {
    int pass = 1;
    while (runs.size() > 1) {
        vector<string> new_runs;
        int out_id = 0;
        for (size_t i = 0; i < runs.size(); i += merge_k) {
            size_t end = min(i + merge_k, runs.size());
            vector<string> group(runs.begin() + i, runs.begin() + end);
            string out_name = tmp_name(pass, out_id++);
            merge_group_to_file(group, out_name, col);
            new_runs.push_back(out_name);
            for (auto& f : group) remove(f.c_str());
        }
        runs = move(new_runs);
        pass++;
    }
}

void copy_file(const string& src, const string& dst) {
    ifstream in(src, ios::binary);
    ofstream out(dst, ios::binary | ios::trunc);
    out << in.rdbuf();
}

// ---------- Бакетная сортировка для числовых колонок ----------
const long long NUM_RANGES[4][2] = {
    {100000000LL, 999999999LL}, // ID
    {0, 0},                     // Name (не используется)
    {100LL, 999LL},             // Quantity
    {10000LL, 999999LL}         // Price
};

extern "C" {
    // Обычная внешняя сортировка с регулируемым чанком (МБ)
    __declspec(dllexport) void run_sort_with_chunk(const char* in, const char* out, int col, int chunk_mb, double* t1, double* t2) {
        auto start_total = chrono::high_resolution_clock::now();
        cleanup_tmp_prefix();
        size_t chunk_bytes = (size_t)chunk_mb * 1024 * 1024;
        auto t_split_start = chrono::high_resolution_clock::now();
        vector<string> runs = split_into_runs(in, col, chunk_bytes);
        auto t_split_end = chrono::high_resolution_clock::now();
        *t1 = chrono::duration<double>(t_split_end - t_split_start).count();

        auto t_merge_start = chrono::high_resolution_clock::now();
        const int MERGE_K = 16;
        multi_pass_merge(runs, col, MERGE_K);
        if (runs.size() != 1) throw runtime_error("Merge error");
        copy_file(runs[0], out);
        remove(runs[0].c_str());
        auto t_merge_end = chrono::high_resolution_clock::now();
        *t2 = chrono::duration<double>(t_merge_end - t_merge_start).count();
    }

    // Бакетная сортировка для чисел
    __declspec(dllexport) void bucket_sort_cpp(const char* in, const char* out, int col, int num_buckets, double* t_distrib, double* t_sort) {
        auto start = chrono::high_resolution_clock::now();
        if (col == 1) {
            *t_distrib = -1; *t_sort = -1;
            return;
        }
        long long min_val = NUM_RANGES[col][0];
        long long max_val = NUM_RANGES[col][1];
        double step = (double)(max_val - min_val + 1) / num_buckets;

        vector<ofstream*> buckets(num_buckets, nullptr);
        for (int i = 0; i < num_buckets; i++) {
            string fname = "bucket_cpp_" + to_string(i) + ".csv";
            buckets[i] = new ofstream(fname, ios::out | ios::trunc);
            if (!buckets[i]->is_open()) throw runtime_error("Cannot create bucket file");
        }

        ifstream fin(in);
        string header, line;
        getline(fin, header);

        auto get_value = [&](const string& s) -> long long {
            size_t st = 0, en = s.find(',');
            for (int i = 0; i < col && en != string::npos; i++) {
                st = en + 1;
                en = s.find(',', st);
            }
            string val = s.substr(st, en - st);
            return stoll(val);
        };

        while (getline(fin, line)) {
            if (line.empty()) continue;
            long long val = get_value(line);
            int idx = (int)((val - min_val) / step);
            if (idx < 0) idx = 0;
            if (idx >= num_buckets) idx = num_buckets - 1;
            *buckets[idx] << line << "\n";
        }
        fin.close();

        auto mid = chrono::high_resolution_clock::now();
        *t_distrib = chrono::duration<double>(mid - start).count();

        ofstream fout(out, ios::out | ios::trunc);
        fout << header << "\n";
        for (int i = 0; i < num_buckets; i++) {
            buckets[i]->close();
            delete buckets[i];
            ifstream fin_bucket("bucket_cpp_" + to_string(i) + ".csv");
            vector<pair<long long, string>> rows;
            string line;
            while (getline(fin_bucket, line)) {
                long long key = get_value(line);
                rows.emplace_back(key, line);
            }
            fin_bucket.close();
            sort(rows.begin(), rows.end());
            for (auto& p : rows) {
                fout << p.second << "\n";
            }
            remove(("bucket_cpp_" + to_string(i) + ".csv").c_str());
        }
        fout.close();
        auto end = chrono::high_resolution_clock::now();
        *t_sort = chrono::duration<double>(end - mid).count();
    }

    // Старая функция для совместимости
    __declspec(dllexport) void run_sort(const char* in, const char* out, int col, double* t1, double* t2) {
        run_sort_with_chunk(in, out, col, 80, t1, t2);
    }
}
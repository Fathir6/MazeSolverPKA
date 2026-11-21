"""
MAZE SOLVER - Perbandingan BFS, DFS, dan A*
Tugas Besar Pengantar Kecerdasan Artifisial - Kelompok 8-A

Cara pakai:
    pip install pygame
    python Tubes.py

Kontrol:
    1 / 2 / 3          = pilih skenario (tiap skenario punya peta sendiri)
    B / D / A          = tampilkan animasi BFS / DFS / A*
    R                  = ulangi animasi
    PANAH ATAS / BAWAH = percepat / perlambat animasi
    ESC                = keluar
"""

import heapq
import random
import time
from collections import deque

import pygame

# ---------------------------------------------------------------------
# PETA (isi grid: 0 = dinding, angka lain = biaya melewati petak)
# ---------------------------------------------------------------------

ARAH = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # atas, kanan, bawah, kiri

# Skenario 1 dibuat manual. Simbol: # dinding, . biaya 1, 3 biaya 3, 5 biaya 5
# Rute atas pendek tapi mahal, rute bawah sama panjang tapi murah
PETA_1 = """
#####################
#.....555555555....G#
#.########.########.#
#.....####.####.....#
#.########.########.#
#.....333333333.....#
#.########.########.#
#.....####.####.....#
#.########.########.#
#S..................#
#####################
"""

# Daerah biaya mahal untuk peta acak: (baris awal, baris akhir, kolom awal, kolom akhir, biaya)
DAERAH_2 = [(1, 30, 10, 13, 3), (1, 30, 20, 23, 5), (14, 17, 1, 30, 3)]
DAERAH_3 = [(1, 40, 10, 14, 3), (1, 40, 28, 32, 5), (10, 14, 1, 40, 5),
            (26, 30, 1, 40, 3), (18, 22, 1, 40, 3)]


def baca_peta(teks):
    grid = []
    start = goal = None
    for r, baris in enumerate(teks.strip().split("\n")):
        isi = []
        for c, ch in enumerate(baris):
            if ch == "S":
                start = (r, c)
            elif ch == "G":
                goal = (r, c)
            if ch == "#":
                isi.append(0)
            elif ch in "S.G":
                isi.append(1)
            else:
                isi.append(int(ch))
        grid.append(isi)
    return grid, start, goal


def buat_peta(n, seed, lubang, daerah, start, goal):
    # seed tetap supaya peta selalu sama
    rnd = random.Random(seed)
    grid = [[0] * n for _ in range(n)]
    grid[1][1] = 1
    tumpukan = [(1, 1)]
    while tumpukan:
        r, c = tumpukan[-1]
        pilihan = []
        for dr, dc in ARAH:
            nr, nc = r + 2 * dr, c + 2 * dc
            if 0 < nr < n - 1 and 0 < nc < n - 1 and grid[nr][nc] == 0:
                pilihan.append((nr, nc, dr, dc))
        if pilihan:
            nr, nc, dr, dc = rnd.choice(pilihan)
            grid[r + dr][c + dc] = 1
            grid[nr][nc] = 1
            tumpukan.append((nr, nc))
        else:
            tumpukan.pop()
    # bolongi beberapa dinding supaya ada lebih dari satu jalur
    for _ in range(lubang):
        r = rnd.randint(1, n - 2)
        c = rnd.randint(1, n - 2)
        if (r + c) % 2 == 1:
            grid[r][c] = 1
    for r1, r2, c1, c2, biaya in daerah:
        for r in range(r1, r2):
            for c in range(c1, c2):
                if grid[r][c] != 0:
                    grid[r][c] = biaya
    return grid, start, goal


# Tiap skenario punya peta sendiri
SKENARIO = {
    1: ("Skenario 1 - Labirin Sederhana", lambda: baca_peta(PETA_1)),
    2: ("Skenario 2 - Banyak Jalan Buntu",
        lambda: buat_peta(31, 181, 12, DAERAH_2, (1, 29), (29, 1))),
    3: ("Skenario 3 - Kompleks / Skala Luas",
        lambda: buat_peta(41, 33, 200, DAERAH_3, (1, 39), (39, 1))),
}


# ---------------------------------------------------------------------
# ALGORITMA (hasil: urutan petak yang diperiksa, peta induk / None)
# ---------------------------------------------------------------------

def tetangga(grid, posisi):
    r, c = posisi
    hasil = []
    for dr, dc in ARAH:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != 0:
            hasil.append((nr, nc))
    return hasil


def susun_jalur(induk, goal):
    jalur = []
    posisi = goal
    while posisi is not None:
        jalur.append(posisi)
        posisi = induk[posisi]
    jalur.reverse()
    return jalur


def bfs(grid, start, goal):
    antrean = deque([start])
    induk = {start: None}
    urutan = []
    while antrean:
        sekarang = antrean.popleft()
        urutan.append(sekarang)
        if sekarang == goal:
            return urutan, induk
        for t in tetangga(grid, sekarang):
            if t not in induk:
                induk[t] = sekarang
                antrean.append(t)
    return urutan, None


def dfs(grid, start, goal):
    tumpukan = [(start, None)]  # (petak, petak asal)
    induk = {}
    urutan = []
    while tumpukan:
        sekarang, asal = tumpukan.pop()
        if sekarang in induk:
            continue
        induk[sekarang] = asal
        urutan.append(sekarang)
        if sekarang == goal:
            return urutan, induk
        # dibalik supaya yang dicoba pertama: atas, kanan, bawah, kiri
        for t in reversed(tetangga(grid, sekarang)):
            if t not in induk:
                tumpukan.append((t, sekarang))
    return urutan, None


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star(grid, start, goal):
    # f = g + h; g = total biaya dari start, h = jarak Manhattan ke goal
    antrean = [(manhattan(start, goal), start)]
    g = {start: 0}
    induk = {start: None}
    selesai = set()
    urutan = []
    while antrean:
        _, sekarang = heapq.heappop(antrean)
        if sekarang in selesai:
            continue
        selesai.add(sekarang)
        urutan.append(sekarang)
        if sekarang == goal:
            return urutan, induk
        for t in tetangga(grid, sekarang):
            g_baru = g[sekarang] + grid[t[0]][t[1]]
            if t not in g or g_baru < g[t]:
                g[t] = g_baru
                induk[t] = sekarang
                heapq.heappush(antrean, (g_baru + manhattan(t, goal), t))
    return urutan, None


# ---------------------------------------------------------------------
# PENGUKURAN METRIK
# ---------------------------------------------------------------------

ULANG = 50  # dijalankan 50x lalu dirata-rata karena 1x terlalu cepat


def uji_algoritma(nama, fungsi, grid, start, goal):
    awal = time.perf_counter()
    for _ in range(ULANG):
        urutan, induk = fungsi(grid, start, goal)
    waktu_ms = (time.perf_counter() - awal) * 1000 / ULANG
    jalur = susun_jalur(induk, goal) if induk else []
    return {
        "nama": nama,
        "urutan": urutan,
        "jalur": jalur,
        "waktu_ms": waktu_ms,
        "simpul": len(urutan),
        "panjang": len(jalur) - 1,
        "biaya": sum(grid[r][c] for r, c in jalur[1:]),  # start tidak dihitung
    }


def uji_semua(grid, start, goal):
    return [
        uji_algoritma("BFS", bfs, grid, start, goal),
        uji_algoritma("DFS", dfs, grid, start, goal),
        uji_algoritma("A*", a_star, grid, start, goal),
    ]


def cetak_tabel(judul, hasil):
    print("\n=== " + judul + " ===")
    print(f"{'Algoritma':<10}{'Waktu (ms)':>12}{'Simpul':>10}{'Panjang':>10}{'Biaya':>8}")
    for h in hasil:
        print(f"{h['nama']:<10}{h['waktu_ms']:>12.4f}{h['simpul']:>10}{h['panjang']:>10}{h['biaya']:>8}")


# ---------------------------------------------------------------------
# TAMPILAN PYGAME
# ---------------------------------------------------------------------

LEBAR, TINGGI = 1120, 700
X_PETA, Y_PETA = 20, 60
X_PANEL = 690

WARNA_LATAR = (30, 33, 40)
WARNA_TEKS = (230, 230, 230)
WARNA_DINDING = (40, 44, 52)
WARNA_START = (46, 160, 67)
WARNA_GOAL = (220, 50, 47)
WARNA_DIKUNJUNGI = (30, 90, 220)
WARNA_JALUR = (255, 215, 0)
WARNA_BIAYA = {1: (245, 245, 245), 3: (250, 215, 170), 5: (185, 140, 100)}


def kotak(layar, warna, r, c, ukuran, jarak=0):
    x = X_PETA + c * ukuran + jarak
    y = Y_PETA + r * ukuran + jarak
    pygame.draw.rect(layar, warna, (x, y, ukuran - 2 * jarak, ukuran - 2 * jarak))


def gambar_peta(layar, grid, hasil, tampil, start, goal, ukuran):
    dilihat = hasil["urutan"][:tampil]
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            kotak(layar, WARNA_DINDING if grid[r][c] == 0 else WARNA_BIAYA[grid[r][c]], r, c, ukuran)
    # petak yang dikunjungi = titik biru
    for r, c in dilihat:
        kotak(layar, WARNA_DIKUNJUNGI, r, c, ukuran, ukuran // 3)
    # jalur yang diambil = kotak kuning penuh, baru muncul setelah animasi selesai
    if tampil >= hasil["simpul"]:
        for r, c in hasil["jalur"]:
            kotak(layar, WARNA_JALUR, r, c, ukuran)
    kotak(layar, WARNA_START, *start, ukuran)
    kotak(layar, WARNA_GOAL, *goal, ukuran)


def tulis(layar, font, teks, x, y, warna=WARNA_TEKS):
    layar.blit(font.render(teks, True, warna), (x, y))


def gambar_panel(layar, font, semua, pilih, tampil):
    # tabel hasil ketiga algoritma
    tulis(layar, font, "HASIL PERBANDINGAN", X_PANEL, Y_PETA)
    kolom = [0, 60, 170, 245, 325]
    for x, judul in zip(kolom, ["Algo", "Waktu (ms)", "Simpul", "Panjang", "Biaya"]):
        tulis(layar, font, judul, X_PANEL + x, Y_PETA + 35, (150, 150, 150))
    for i, h in enumerate(semua):
        y = Y_PETA + 60 + i * 28
        warna = WARNA_JALUR if i == pilih else WARNA_TEKS
        isi = [h["nama"], "%.4f" % h["waktu_ms"], h["simpul"], h["panjang"], h["biaya"]]
        for x, teks in zip(kolom, isi):
            tulis(layar, font, str(teks), X_PANEL + x, y, warna)

    # keterangan animasi
    h = semua[pilih]
    tulis(layar, font, "ANIMASI SAAT INI: " + h["nama"], X_PANEL, Y_PETA + 180)
    tulis(layar, font, "Simpul diperiksa: %d / %d" % (tampil, h["simpul"]), X_PANEL, Y_PETA + 210)
    if tampil >= h["simpul"]:
        tulis(layar, font, "Panjang jalur: %d langkah" % h["panjang"], X_PANEL, Y_PETA + 235)
        tulis(layar, font, "Total biaya: %d" % h["biaya"], X_PANEL, Y_PETA + 260)

    # legenda
    tulis(layar, font, "KETERANGAN", X_PANEL, Y_PETA + 320)
    item = [(WARNA_START, "Start"), (WARNA_GOAL, "Goal"), (WARNA_DINDING, "Dinding"),
            (WARNA_BIAYA[1], "Jalan biaya 1"), (WARNA_BIAYA[3], "Jalan biaya 3"),
            (WARNA_BIAYA[5], "Jalan biaya 5"), (WARNA_DIKUNJUNGI, "Titik biru = petak dikunjungi"),
            (WARNA_JALUR, "Kotak kuning = jalur yang diambil")]
    for i, (warna, nama) in enumerate(item):
        y = Y_PETA + 350 + i * 26
        pygame.draw.rect(layar, warna, (X_PANEL, y, 16, 16))
        tulis(layar, font, nama, X_PANEL + 26, y)


def main():
    pygame.init()
    layar = pygame.display.set_mode((LEBAR, TINGGI))
    pygame.display.set_caption("Maze Solver - BFS vs DFS vs A*")
    font = pygame.font.Font(None, 24)  # font bawaan pygame
    jam = pygame.time.Clock()

    kecepatan = 3  # simpul yang dibuka per frame
    skenario = 1
    pilih = 0      # 0 = BFS, 1 = DFS, 2 = A*
    tampil = 0
    semua = []
    grid = start = goal = None
    ukuran = 10

    def muat_skenario(n):
        nonlocal skenario, semua, tampil, grid, start, goal, ukuran
        skenario = n
        grid, start, goal = SKENARIO[n][1]()
        ukuran = min(580 // len(grid), 640 // len(grid[0]))
        semua = uji_semua(grid, start, goal)
        cetak_tabel(SKENARIO[n][0], semua)
        tampil = 0

    muat_skenario(1)

    jalan = True
    while jalan:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                jalan = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    jalan = False
                elif e.key == pygame.K_1:
                    muat_skenario(1)
                elif e.key == pygame.K_2:
                    muat_skenario(2)
                elif e.key == pygame.K_3:
                    muat_skenario(3)
                elif e.key == pygame.K_b:
                    pilih, tampil = 0, 0
                elif e.key == pygame.K_d:
                    pilih, tampil = 1, 0
                elif e.key == pygame.K_a:
                    pilih, tampil = 2, 0
                elif e.key == pygame.K_r:
                    tampil = 0
                elif e.key == pygame.K_UP:
                    kecepatan = min(kecepatan + 1, 30)
                elif e.key == pygame.K_DOWN:
                    kecepatan = max(kecepatan - 1, 1)

        tampil = min(tampil + kecepatan, semua[pilih]["simpul"])

        layar.fill(WARNA_LATAR)
        tulis(layar, font, SKENARIO[skenario][0], X_PETA, 12)
        bantuan = "[1][2][3] skenario | [B][D][A] algoritma | [R] ulangi | [Atas/Bawah] kecepatan: %d | [ESC] keluar" % kecepatan
        tulis(layar, font, bantuan, X_PETA, 34, (170, 170, 170))
        gambar_peta(layar, grid, semua[pilih], tampil, start, goal, ukuran)
        gambar_panel(layar, font, semua, pilih, tampil)

        pygame.display.flip()
        jam.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()

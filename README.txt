# Ujian Sekolah Terintegrasi

## Online
1. Buat Google Spreadsheet dengan sheet: SISWA, BANK_SOAL, PAKET_UJIAN, HASIL, REKAP_NILAI, ADMIN.
2. Buat Google Cloud service account dan aktifkan Google Sheets API.
3. Simpan credential service account di Streamlit Secrets sebagai `gcp_service_account`, dan ID spreadsheet sebagai `spreadsheet_id`.
4. Deploy `app.py` ke Streamlit Community Cloud dari GitHub.
5. Share spreadsheet kepada email service account sebagai Editor.

## Offline
Gunakan `Database_Ujian_Sekolah_Offline.xlsx` sebagai database/template. Aplikasi desktop offline dapat membaca sheet yang sama.

## Struktur
- 14 mata pelajaran.
- Kelas fleksibel: 1A, 1B, dst.
- Jenis soal: PG, ISIAN, ESSAI.
- Periode: LATIHAN, PTS 1, PTS 2, PAS 1, PAS 2.
- Predikat: 1-40 D, 41-65 C, 66-85 B, 86-100 A.

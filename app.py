import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import hashlib

st.set_page_config(page_title="Portal Ujian Sekolah", page_icon="📝", layout="wide")

SUBJECTS = [
"Akidah Akhlak","Al-Quran Hadits","Fiqih","Sejarah Kebudayaan Islam (SKI)",
"Pendidikan Pancasila","Bahasa Indonesia","Ilmu Pengetahuan Alam dan Sosial (IPAS)",
"Matematika","Pendidikan Jasmani Olahraga dan Kesehatan (PJOK)","Seni Budaya dan Prakarya (SBdP)",
"Bahasa Arab","Bahasa Sunda","Bahasa Inggris","Koding dan Kecerdasan Artifisial (KKA)"
]
PERIODS = ["LATIHAN","PTS 1","PTS 2","PAS 1","PAS 2"]
SHEETS = ["SISWA","BANK_SOAL","PAKET_UJIAN","HASIL","REKAP_NILAI","ADMIN"]

def auth_sheet():
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
    creds=Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc=gspread.authorize(creds)
    return gc.open_by_key(st.secrets["spreadsheet_id"])

@st.cache_data(ttl=30)
def read_sheet(name):
    sh=auth_sheet().worksheet(name)
    vals=sh.get_all_records()
    return pd.DataFrame(vals)

def append_row(name,row):
    auth_sheet().worksheet(name).append_row(row, value_input_option="USER_ENTERED")

def update_cell(name,row,col,value):
    auth_sheet().worksheet(name).update_cell(row,col,value)

def predikat(v):
    try: v=float(v)
    except: return ""
    if v <= 40: return "D"
    if v <= 65: return "C"
    if v <= 85: return "B"
    return "A"

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# elegant opal portal
st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 20% 10%,#e9f7ff 0,#f7fbff 35%,#eef3f8 100%)}
.opal{max-width:760px;margin:8vh auto 0;padding:48px;border-radius:42px;
background:linear-gradient(145deg,rgba(255,255,255,.92),rgba(224,245,255,.72));
box-shadow:0 25px 70px rgba(30,90,130,.18);border:1px solid rgba(255,255,255,.8)}
.opal h1{text-align:center;font-size:38px;margin-bottom:8px;color:#173b57}
.opal p{text-align:center;color:#57758b}
</style>
""", unsafe_allow_html=True)

if "login" not in st.session_state: st.session_state.login=False
if "role" not in st.session_state: st.session_state.role=""

with st.sidebar:
    st.title("☰ Menu")
    page=st.radio("Navigasi",["Portal Ujian","Admin"], index=0)
    st.caption("Sistem Ujian Sekolah")

if page=="Portal Ujian":
    st.markdown('<div class="opal"><h1>📝 Portal Ujian Sekolah</h1><p>Masuk menggunakan NISN yang sudah terdaftar.</p></div>',unsafe_allow_html=True)
    nisn=st.text_input("NISN",max_chars=30)
    if st.button("Masuk Ujian",type="primary",use_container_width=True):
        df=read_sheet("SISWA")
        m=df[df["NISN"].astype(str)==str(nisn)]
        if m.empty: st.error("NISN belum terdaftar.")
        else:
            st.session_state.login=True; st.session_state.role="siswa"
            st.session_state.student=m.iloc[0].to_dict()
            st.rerun()

    if st.session_state.get("login") and st.session_state.role=="siswa":
        s=st.session_state.student
        st.success(f"Selamat datang, {s['Nama']} — Kelas {s['Kelas']}")
        soal=read_sheet("BANK_SOAL")
        aktif=read_sheet("PAKET_UJIAN")
        if not aktif.empty and "Aktif" in aktif:
            aktif=aktif[aktif["Aktif"].astype(str).str.upper()=="YA"]
        if aktif.empty: st.info("Belum ada paket ujian yang diaktifkan.")
        else:
            paket_id=st.selectbox("Pilih paket",aktif["ID Paket"].astype(str).unique())
            p=aktif[aktif["ID Paket"].astype(str)==str(paket_id)]
            ids=p["ID Soal"].astype(str).tolist()
            q=soal[soal["ID Soal"].astype(str).isin(ids)].copy()
            if q.empty: st.warning("Soal paket belum tersedia.")
            else:
                if "answers" not in st.session_state: st.session_state.answers={}
                for _,r in q.iterrows():
                    st.markdown(f"### Soal {r['ID Soal']}")
                    st.write(r["Pertanyaan"])
                    typ=str(r["Jenis Soal"]).upper()
                    if typ=="PG":
                        opts=[r["Pilihan A"],r["Pilihan B"],r["Pilihan C"],r["Pilihan D"]]
                        st.session_state.answers[r["ID Soal"]]=st.radio(
                            "Jawaban",opts,key="q_"+str(r["ID Soal"]),index=None)
                    else:
                        st.session_state.answers[r["ID Soal"]]=st.text_area(
                            "Jawaban",key="q_"+str(r["ID Soal"]))
                if st.button("Kirim Jawaban",type="primary"):
                    score=0; total=0
                    for _,r in q.iterrows():
                        b=float(r["Bobot"] or 1); total+=b
                        a=str(st.session_state.answers.get(r["ID Soal"],"")).strip().lower()
                        k=str(r["Kunci"]).strip().lower()
                        if str(r["Jenis Soal"]).upper()=="PG":
                            letters={"a":r["Pilihan A"],"b":r["Pilihan B"],"c":r["Pilihan C"],"d":r["Pilihan D"]}
                            correct=letters.get(k,k)
                            if a==str(correct).strip().lower(): score+=b
                        elif str(r["Jenis Soal"]).upper()=="ISIAN":
                            if a==k: score+=b
                        # ESSAI intentionally stored for teacher/manual scoring
                    nilai=round(score/total*100,2) if total else 0
                    if any(str(x["Jenis Soal"]).upper()=="ESSAI" for _,x in q.iterrows()):
                        st.warning("Paket memuat essai. Nilai essai perlu diverifikasi guru/admin.")
                    st.metric("Nilai otomatis",nilai)
                    st.write("Predikat:",predikat(nilai))
                    append_row("HASIL",[
                        datetime.now().strftime("%Y%m%d%H%M%S"),s["NISN"],s["Nama"],s["Kelas"],
                        str(p.iloc[0]["Mata Pelajaran"]),paket_id,datetime.now().isoformat(),
                        "",nilai,"","","",nilai,predikat(nilai)
                    ])
                    st.session_state.answers={}

else:
    st.title("🔐 Admin")
    dfadm=read_sheet("ADMIN")
    user=st.text_input("Username")
    pw=st.text_input("Password",type="password")
    if st.button("Masuk Admin",type="primary"):
        hit=dfadm[(dfadm["Username"].astype(str)==user)&(dfadm["Password"].astype(str)==pw)]
        if hit.empty: st.error("Username/password salah.")
        else: st.session_state.admin=True; st.rerun()

    if st.session_state.get("admin"):
        tab=st.tabs(["Dashboard","Siswa","Bank Soal","Paket Ujian","Hasil & Rekap","Admin"])
        with tab[0]:
            st.metric("Jumlah siswa",len(read_sheet("SISWA")))
            st.metric("Jumlah soal",len(read_sheet("BANK_SOAL")))
            st.metric("Hasil ujian",len(read_sheet("HASIL")))
        with tab[1]:
            st.subheader("Tambah siswa")
            with st.form("siswa"):
                kelas=st.text_input("Kelas","1A")
                no=st.number_input("No",1,100,1)
                nisn2=st.text_input("NISN")
                nama=st.text_input("Nama")
                ok=st.form_submit_button("Simpan")
            if ok: append_row("SISWA",[kelas,no,nisn2,nama,"AKTIF"]); st.cache_data.clear(); st.success("Siswa tersimpan.")
            st.dataframe(read_sheet("SISWA"),use_container_width=True)
        with tab[2]:
            st.subheader("Input bank soal")
            with st.form("soal"):
                sid=st.text_input("ID Soal")
                mp=st.selectbox("Mata Pelajaran",SUBJECTS)
                materi=st.text_input("Materi")
                typ=st.selectbox("Jenis Soal",["PG","ISIAN","ESSAI"])
                pert=st.text_area("Pertanyaan")
                a=st.text_input("Pilihan A"); b=st.text_input("Pilihan B"); c=st.text_input("Pilihan C"); d=st.text_input("Pilihan D")
                k=st.text_input("Kunci (A/B/C/D atau kata jawaban)")
                bob=st.number_input("Bobot",1.0,100.0,1.0)
                ok=st.form_submit_button("Simpan soal")
            if ok:
                append_row("BANK_SOAL",[sid,mp,materi,typ,pert,a,b,c,d,k,bob,""])
                st.cache_data.clear(); st.success("Soal tersimpan.")
        with tab[3]:
            st.subheader("Membuat paket ujian")
            with st.form("paket"):
                pid=st.text_input("ID Paket")
                pn=st.text_input("Nama Paket")
                pmp=st.selectbox("Mata Pelajaran",SUBJECTS,key="pmp")
                per=st.selectbox("Periode",PERIODS)
                pt=st.selectbox("Jenis Soal",["PG","ISIAN","ESSAI","PG+ISIAN","PG+ISIAN+ESSAI"])
                qid=st.text_input("ID Soal (pisahkan koma)")
                ok=st.form_submit_button("Simpan paket")
            if ok:
                for i,x in enumerate([x.strip() for x in qid.split(",") if x.strip()],1):
                    append_row("PAKET_UJIAN",[pid,pn,pmp,per,pt,x,i,"TIDAK"])
                st.cache_data.clear(); st.success("Paket tersimpan. Aktifkan dengan mengubah kolom Aktif menjadi YA di Google Sheets.")
        with tab[4]:
            st.subheader("Hasil ujian")
            st.dataframe(read_sheet("HASIL"),use_container_width=True)
            st.subheader("Rekap")
            st.dataframe(read_sheet("REKAP_NILAI"),use_container_width=True)
        with tab[5]:
            st.subheader("Admin")
            st.info("Username/password dapat diubah langsung pada sheet ADMIN. Untuk keamanan produksi, gunakan password hash dan secrets.")

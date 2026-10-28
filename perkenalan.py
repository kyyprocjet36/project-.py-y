import cv2
import mediapipe as mp
import pygame
import time
import os
import threading
from gtts import gTTS

# Inisialisasi suara
pygame.mixer.init()

# Inisialisasi MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Pesan perkenalan
pesan = {
    5: ("HALO,SEMUANYA!", "Halosemuanya !"),
    2: ("PERKENALKAN NAMA SAYA...", "perkenalkan Nama saya..."),
    1: ("IKY!", "Iky!"),
    3: ("SENANG BERKENALAN DENGAN ANDA!",
        "Senang berkenalan dengan Anda!")
}

# Membuat folder suara
os.makedirs("suara", exist_ok=True)

# Membuat suara Google
for jumlah, (teks, ucapan) in pesan.items():
    file_suara = f"suara/{jumlah}.mp3"

    tts = gTTS(text=ucapan, lang="id")
    tts.save(file_suara)
    
# Variabel program
tampilan = "SELAMAT DATANG!"
gerakan_sebelumnya = None
waktu_terakhir = 0
sedang_bicara = False


def putar_suara(jumlah):
    global sedang_bicara

    sedang_bicara = True

    try:
        pygame.mixer.music.load(f"suara/{jumlah}.mp3")
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    finally:
        sedang_bicara = False


def hitung_jari(landmarks):
    titik = landmarks.landmark

    # Jempol
    jari = []

    if titik[4].x < titik[3].x:
        jari.append(1)
    else:
        jari.append(0)

    # Telunjuk, tengah, manis, kelingking
    for ujung, sendi in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        if titik[ujung].y < titik[sendi].y:
            jari.append(1)
        else:
            jari.append(0)

    return sum(jari)


# Membuka kamera
kamera = cv2.VideoCapture(0)

if not kamera.isOpened():
    print("Kamera tidak dapat dibuka.")
    exit()

print("Program perkenalan Iky berjalan!")
print("Tekan Q untuk keluar.")

try:
    while True:
        berhasil, frame = kamera.read()

        if not berhasil:
            break

        # Membalik kamera seperti cermin
        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hasil = hands.process(rgb)

        jumlah_jari = None

        if hasil.multi_hand_landmarks:
            for landmark in hasil.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, landmark, mp_hands.HAND_CONNECTIONS
                )

                jumlah_jari = hitung_jari(landmark)

        waktu_sekarang = time.time()

        if jumlah_jari is not None:
            if jumlah_jari in pesan:
                tampilan = pesan[jumlah_jari][0]

                if (
                    jumlah_jari != gerakan_sebelumnya
                    and waktu_sekarang - waktu_terakhir > 2
                    and not sedang_bicara
                ):
                    threading.Thread(
                        target=putar_suara,
                        args=(jumlah_jari,),
                        daemon=True
                    ).start()

                    gerakan_sebelumnya = jumlah_jari
                    waktu_terakhir = waktu_sekarang

            elif jumlah_jari == 0:
                tampilan = "SELAMAT DATANG!"
                gerakan_sebelumnya = None

        # Tampilan tulisan
        cv2.rectangle(frame, (0, 0), (640, 100), (30, 30, 30), -1)

        cv2.putText(
            frame,
            tampilan,
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Tekan Q untuk keluar",
            (20, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.imshow("Perkenalan Iky", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    kamera.release()
    hands.close()
    cv2.destroyAllWindows()
    pygame.mixer.quit()
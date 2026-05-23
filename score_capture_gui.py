import configparser
import os
import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import cv2
import mss
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as compare_ssim


APP_NAME = "ScoreCapture"


def get_app_data_dir():
    """Return a writable folder that is easy to find in a packaged app."""
    base_dir = Path.home() / "Documents" / APP_NAME
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


APP_DATA_DIR = get_app_data_dir()
CONFIG_FILE = APP_DATA_DIR / "config.ini"
OUTPUT_FOLDER = APP_DATA_DIR / "captured_scores"
PDF_FILENAME = APP_DATA_DIR / "final_sheet_music_stitched.pdf"


def open_screen_recording_settings():
    if sys.platform != "darwin":
        return

    subprocess.Popen(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        ]
    )


class ScoreCaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("악보 자동 캡처")
        self.root.geometry("360x240")
        self.root.resizable(False, False)

        self.capture_area = None
        self.is_capturing = False
        self.last_captured_image_gray = None
        self.captured_image_files = []

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="민감도 (0.0-1.0):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.similarity_var = tk.StringVar(value="0.9")
        self.similarity_entry = ttk.Entry(frame, textvariable=self.similarity_var, width=10)
        self.similarity_entry.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(frame, text="시작 지연 (초):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.delay_var = tk.StringVar(value="3")
        self.delay_entry = ttk.Entry(frame, textvariable=self.delay_var, width=10)
        self.delay_entry.grid(row=1, column=1, sticky=tk.W)

        self.select_button = ttk.Button(frame, text="1. 캡처 영역 선택", command=self.select_capture_area)
        self.select_button.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.start_button = ttk.Button(frame, text="2. 캡처 시작", command=self.start_capture, state=tk.DISABLED)
        self.start_button.grid(row=3, column=0, sticky=(tk.W, tk.E))

        self.stop_button = ttk.Button(frame, text="종료 및 PDF 생성", command=self.stop_and_create_pdf, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, sticky=(tk.W, tk.E))

        self.output_label = ttk.Label(frame, text=f"저장 위치: {APP_DATA_DIR}", wraplength=330)
        self.output_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        self.status_var = tk.StringVar(value="먼저 캡처 영역을 선택하세요.")
        status_label = ttk.Label(self.root, textvariable=self.status_var, padding="10 5", relief=tk.SUNKEN)
        status_label.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.S))

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def load_config(self):
        config = configparser.ConfigParser()
        if CONFIG_FILE.exists():
            config.read(CONFIG_FILE, encoding="utf-8")
            threshold = config.get("Settings", "similarity_threshold", fallback="0.9")
            self.similarity_var.set(threshold)

    def save_config(self):
        config = configparser.ConfigParser()
        config["Settings"] = {"similarity_threshold": self.similarity_var.get()}
        with CONFIG_FILE.open("w", encoding="utf-8") as configfile:
            config.write(configfile)

    def select_capture_area(self):
        self.update_status("캡처할 영역을 드래그하세요...")
        self.root.withdraw()
        time.sleep(0.5)

        try:
            with mss.mss() as sct:
                sct_img = sct.grab(sct.monitors[1])
                screenshot = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
        except Exception as exc:
            self.root.deiconify()
            message = (
                "화면을 캡처할 수 없습니다.\n\n"
                "macOS에서는 처음 한 번 화면 기록 권한을 허용해야 합니다.\n"
                f"시스템 설정이 열리면 {APP_NAME}을 허용한 뒤 앱을 다시 실행하세요.\n\n"
                f"{exc}"
            )
            if sys.platform == "darwin":
                if messagebox.askyesno("화면 기록 권한 필요", f"{message}\n\n지금 설정을 열까요?"):
                    open_screen_recording_settings()
            else:
                messagebox.showerror("화면 캡처 권한 필요", message)
            self.update_status("화면 캡처 권한을 확인하세요.")
            return

        selector = AreaSelector(screenshot)
        self.capture_area = selector.select_area("Drag the full score area. ESC: cancel")

        self.root.deiconify()

        if self.capture_area:
            self.update_status("영역 선택 완료. 캡처를 시작하세요.")
            self.start_button.config(state=tk.NORMAL)
        else:
            self.update_status("영역 선택이 취소되었습니다.")

    def start_capture(self):
        try:
            delay = int(self.delay_var.get())
            threshold = float(self.similarity_var.get())
            if not 0.0 <= threshold <= 1.0:
                raise ValueError
        except ValueError:
            messagebox.showerror("입력 오류", "민감도는 0.0부터 1.0 사이, 지연 시간은 숫자로 입력하세요.")
            return

        self.save_config()
        self.is_capturing = True
        self.start_button.config(state=tk.DISABLED)
        self.select_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        def countdown(count):
            if count > 0:
                self.update_status(f"{count}초 후 캡처를 시작합니다...")
                self.root.after(1000, countdown, count - 1)
            else:
                self.update_status("캡처 진행 중...")
                self.capture_loop()

        countdown(delay)

    def capture_loop(self):
        if not self.is_capturing:
            return

        try:
            with mss.mss() as sct:
                sct_img = sct.grab(self.capture_area)
                current_image_bgra = np.array(sct_img)
                current_image_gray = cv2.cvtColor(current_image_bgra, cv2.COLOR_BGRA2GRAY)
        except Exception as exc:
            self.is_capturing = False
            messagebox.showerror("캡처 오류", f"화면 캡처 중 오류가 발생했습니다.\n\n{exc}")
            self.reset_state()
            return

        if self.last_captured_image_gray is None:
            self.update_status("첫 악보 감지. 캡처합니다.")
            self.last_captured_image_gray = current_image_gray
            self.save_image(current_image_bgra)
        else:
            score, _ = compare_ssim(self.last_captured_image_gray, current_image_gray, full=True)
            if score < float(self.similarity_var.get()):
                self.update_status(f"새 악보 감지. 유사도: {score:.2f}")
                self.last_captured_image_gray = current_image_gray
                self.save_image(current_image_bgra)

        self.root.after(1000, self.capture_loop)

    def save_image(self, image_bgra):
        OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        filename = OUTPUT_FOLDER / f"score_page_{len(self.captured_image_files) + 1:03d}.png"
        cv2.imwrite(str(filename), cv2.cvtColor(image_bgra, cv2.COLOR_BGRA2BGR))
        self.captured_image_files.append(filename)

    def stop_and_create_pdf(self):
        self.is_capturing = False
        self.update_status("PDF 생성 중입니다...")

        if self.captured_image_files:
            image_list = [Image.open(path).convert("RGB") for path in self.captured_image_files]
            widths, heights = zip(*(image.size for image in image_list))
            total_height = sum(heights)
            max_width = max(widths)
            stitched_image = Image.new("RGB", (max_width, total_height), "white")
            y_offset = 0
            for image in image_list:
                stitched_image.paste(image, (0, y_offset))
                y_offset += image.size[1]

            stitched_image.save(PDF_FILENAME, "PDF", resolution=100.0)
            messagebox.showinfo("완료", f"PDF가 생성되었습니다.\n\n{PDF_FILENAME}")
        else:
            messagebox.showwarning("알림", "캡처한 이미지가 없어 PDF를 생성하지 않았습니다.")

        self.reset_state()

    def reset_state(self):
        self.last_captured_image_gray = None
        self.captured_image_files = []
        self.start_button.config(state=tk.NORMAL if self.capture_area else tk.DISABLED)
        self.select_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("준비 완료. 영역을 선택하거나 캡처를 시작하세요.")


class AreaSelector:
    def __init__(self, screen_shot):
        self.image = screen_shot
        self.point1 = None
        self.point2 = None
        self.rect_done = False

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.point1 = (x, y)
            self.rect_done = False
        elif event == cv2.EVENT_MOUSEMOVE and self.point1:
            img_copy = self.image.copy()
            cv2.rectangle(img_copy, self.point1, (x, y), (0, 255, 0), 2)
            cv2.imshow("Area Selector", img_copy)
        elif event == cv2.EVENT_LBUTTONUP:
            self.point2 = (x, y)
            self.rect_done = True

    def select_area(self, instructions):
        self.point1 = None
        self.point2 = None
        self.rect_done = False
        cv2.namedWindow("Area Selector", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Area Selector", self.mouse_callback)
        img_with_text = self.image.copy()
        cv2.putText(
            img_with_text,
            instructions,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow("Area Selector", img_with_text)
        while not self.rect_done:
            if cv2.waitKey(1) & 0xFF == 27:
                cv2.destroyAllWindows()
                return None
        cv2.destroyAllWindows()
        left = min(self.point1[0], self.point2[0])
        top = min(self.point1[1], self.point2[1])
        width = abs(self.point1[0] - self.point2[0])
        height = abs(self.point1[1] - self.point2[1])
        return {"top": top, "left": left, "width": width, "height": height}


if __name__ == "__main__":
    if sys.platform == "darwin":
        os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

    root = tk.Tk()
    app = ScoreCaptureApp(root)
    root.mainloop()

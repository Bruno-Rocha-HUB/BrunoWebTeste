import threading
import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
import time
import requests
from concurrent.futures import ThreadPoolExecutor

class TesteAutomatizadoGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Teste Automatizado")
        self.master.geometry("500x350")

        self.url_label = ttk.Label(self.master, text="URL:")
        self.url_label.grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.url_entry = ttk.Entry(self.master, width=40)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10, sticky='w', columnspan=2)

        self.iter_label = ttk.Label(self.master, text="Número de Iterações:")
        self.iter_label.grid(row=1, column=0, padx=10, pady=10, sticky='e')
        self.iter_entry = ttk.Entry(self.master, width=40)
        self.iter_entry.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        self.delay_label = ttk.Label(self.master, text="Delay (segundos):")
        self.delay_label.grid(row=2, column=0, padx=10, pady=10, sticky='e')
        self.delay_entry = ttk.Entry(self.master, width=40)
        self.delay_entry.grid(row=2, column=1, padx=10, pady=10, sticky='w')

        self.scroll_var = tk.IntVar()
        self.scroll_checkbutton = ttk.Checkbutton(self.master, text="Ativar Scroll Automático", variable=self.scroll_var)
        self.scroll_checkbutton.grid(row=3, column=0, padx=10, pady=10, columnspan=2)

        self.start_button = ttk.Button(self.master, text="Iniciar", command=self.start_test_async)
        self.start_button.grid(row=4, column=0, padx=10, pady=10, columnspan=2)

        self.stop_button = ttk.Button(self.master, text="Parar", command=self.stop_test)
        self.stop_button.grid(row=4, column=1, padx=10, pady=10)

        self.progress_label = ttk.Label(self.master, text="Progresso:")
        self.progress_label.grid(row=5, column=0, padx=10, pady=10, sticky='e')
        self.progress_var = tk.StringVar()
        self.progress_entry = ttk.Entry(self.master, textvariable=self.progress_var, state='readonly', width=40)
        self.progress_entry.grid(row=5, column=1, padx=10, pady=10, sticky='w', columnspan=2)

        self.time_label = ttk.Label(self.master, text="Tempo Decorrido:")
        self.time_label.grid(row=6, column=0, padx=10, pady=10, sticky='e')
        self.time_var = tk.StringVar()
        self.time_entry = ttk.Entry(self.master, textvariable=self.time_var, state='readonly', width=40)
        self.time_entry.grid(row=6, column=1, padx=10, pady=10, sticky='w')

        self.driver = None
        self.testing = False
        self.check_internet_thread = None
        self.check_internet_interval = 10  # segundos
        self.executor = ThreadPoolExecutor(max_workers=1)  # Para executar a função start_test em uma thread separada

    def start_test_async(self):
        # Submete a função start_test para execução assíncrona na ThreadPoolExecutor
        self.future = self.executor.submit(self.start_test)

    def start_test(self):
        if self.testing:
            return

        url = self.url_entry.get()
        if not url:
            messagebox.showwarning("URL Vazio", "Por favor, insira um URL antes de iniciar o teste.")
            return

        iterations = int(self.iter_entry.get())
        delay = float(self.delay_entry.get())

        self.testing = True
        self.check_internet_thread = threading.Thread(target=self.check_internet, daemon=True)
        self.check_internet_thread.start()

        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get(url)

            start_time = time.time()

            def update_gui():
                if not self.testing:
                    return
                elapsed_time = time.time() - start_time
                self.update_time(elapsed_time)
                self.master.after(1000, update_gui)

            update_gui()

            for i in range(1, iterations + 1):
                if not self.testing:
                    break

                if self.check_condition():
                    self.update_progress(f"Condição satisfeita na iteração {i}")
                    break

                self.driver.refresh()
                self.update_progress(f"Iteração {i}/{iterations}")
                self.master.update()

                time.sleep(delay)

                if self.scroll_var.get():
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        except Exception as e:
            self.update_progress(f"Erro: {str(e)}")
        finally:
            self.testing = False
            self.check_internet_thread.join()
            if self.driver:
                self.driver.quit()

    def stop_test(self):
        self.testing = False

    def check_internet(self):
        while self.testing:
            if not self.is_internet_available():
                messagebox.showinfo("Sem Conexão", "Conexão perdida. Teste continuando.")
                continue

            if not self.testing:
                break

            time.sleep(self.check_internet_interval)

    def is_internet_available(self):
        try:
            response = requests.get("http://www.google.com", timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            return False

    def check_condition(self):
        return False

    def update_progress(self, message):
        self.progress_var.set(message)

    def update_time(self, elapsed_time):
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        self.time_var.set(time_str)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("+%d+%d" % ((root.winfo_screenwidth() - root.winfo_reqwidth()) / 3,
                               (root.winfo_screenheight() - root.winfo_reqheight()) / 3))
    app = TesteAutomatizadoGUI(root)
    root.mainloop()

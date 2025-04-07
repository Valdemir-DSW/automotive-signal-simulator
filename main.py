
import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

class FullApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador e gerador de sinais automotivos By Valdemir")
        self.root.state("zoomed")

        self.serial_conn = None
        self.reading = False
        self.buffer_size = 100
        self.paused = False
        self.max_amostras = 2000
        self.analog_data = [[0] * self.buffer_size for _ in range(6)]
        self.pwm_data = [{"enabled": False, "freq": 1000, "duty": 50} for _ in range(2)]

        self.total_dentes = 10
        self.falhas = 1
        self.simular_fase_var = tk.BooleanVar(value=False)
        self.fase_pos = 0

        self.channel_vars = [tk.BooleanVar(value=False) for _ in range(6)]

        self.ports = []

        self.build_gui()

        self.update_ports()

    def build_gui(self):
        self.tabControl = ttk.Notebook(self.root)

        self.rpm_tab = ttk.Frame(self.tabControl)
        self.pwm_tab = ttk.Frame(self.tabControl)
        self.tab_analisagem = ttk.Frame(self.tabControl)
        self.tab_serial = ttk.Frame(self.tabControl)

        self.tabControl.add(self.rpm_tab, text="RPM")
        self.tabControl.add(self.pwm_tab, text="PWM")
        self.tabControl.add(self.tab_analisagem, text="Analisagem")
        self.tabControl.add(self.tab_serial, text="Conexão Serial e CAN")
        self.tabControl.pack(expand=1, fill="both")

        self.setup_rpm_tab()
        self.setup_pwm_tab()
        self.setup_tab_analisagem()
        self.setup_tab_serial()

    def setup_rpm_tab(self):
        self.dentes_totais = tk.IntVar(value=36)
        self.falhas = tk.IntVar(value=1)
        self.simular_fase_var = tk.BooleanVar(value=False)
        self.fase_valor = tk.IntVar(value=0)
        self.rpm_valor = tk.IntVar(value=74)

        # DENTES TOTAIS
        ttk.Label(self.rpm_tab, text="DENTES TOTAIS:").pack(anchor='w', padx=10, pady=(10, 0))
        self.dentes_label = ttk.Label(self.rpm_tab, text=str(self.dentes_totais.get()))
        self.dentes_label.pack(anchor='w', padx=20)
        ttk.Scale(self.rpm_tab, from_=10, to=80, orient='horizontal', variable=self.dentes_totais,
                command=lambda val: self.update_dentes()).pack(fill='x', padx=10)

        # FALHAS
        ttk.Label(self.rpm_tab, text="FALHAS:").pack(anchor='w', padx=10, pady=(10, 0))
        self.falhas_label = ttk.Label(self.rpm_tab, text=str(self.falhas.get()))
        self.falhas_label.pack(anchor='w', padx=20)
        ttk.Scale(self.rpm_tab, from_=1, to=10, orient='horizontal', variable=self.falhas,
                command=lambda val: self.update_falhas()).pack(fill='x', padx=10)

        # SIMULAR FASE
        self.fase_check = ttk.Checkbutton(self.rpm_tab, text="SIMULAR FASE",
                                        variable=self.simular_fase_var,
                                        command=self.atualizar_fase_slider)
        self.fase_check.pack(anchor='w', padx=10, pady=(10, 0))

        # Slider da Fase
        ttk.Label(self.rpm_tab, text="FASE:").pack(anchor='w', padx=10, pady=(0, 0))
        self.fase_valor_label = ttk.Label(self.rpm_tab, text=str(self.fase_valor.get()))
        self.fase_valor_label.pack(anchor='w', padx=20)

        self.fase_slider = ttk.Scale(self.rpm_tab, from_=1, to=35, orient='horizontal',
                                    variable=self.fase_valor,
                                    command=lambda val: self.fase_valor_label.config(text=str(int(float(val)))))
        self.fase_slider.pack(fill='x', padx=10, pady=(0, 10))
        self.fase_slider.configure(state='disabled')

        # Slider do RPM
        ttk.Label(self.rpm_tab, text="RPM:").pack(anchor='w', padx=10, pady=(10, 0))
        self.rpm_valor_label = ttk.Label(self.rpm_tab, text=str(self.rpm_valor.get()))
        self.rpm_valor_label.pack(anchor='w', padx=20)
        ttk.Scale(self.rpm_tab, from_=600, to=14000, orient='horizontal', variable=self.rpm_valor,
                command=self.on_rpm_change ).pack(fill='x', padx=10)
    def on_rpm_change(self,val):
        self.rpm_valor_label.config(text=str(int(float(val))))
        self.send_all_data2()

    def update_dentes(self):
        self.dentes_label.config(text=str(self.dentes_totais.get()))
        self.atualizar_fase_slider()
        self.send_all_data2()

    def update_falhas(self):
        self.falhas_label.config(text=str(self.falhas.get()))
        self.atualizar_fase_slider()
        self.send_all_data2()

    def atualizar_fase_slider(self):
        total_dentes = self.dentes_totais.get()
        falhas = self.falhas.get()
        dentes_reais = max(total_dentes - falhas, 1)

        if self.simular_fase_var.get():
            self.fase_slider.configure(to=dentes_reais - 1, state='normal')
        else:
            self.fase_slider.configure(state='disabled')
        self.send_all_data2()    


    def setup_pwm_tab(self):
        for i in range(2):
            frame = ttk.LabelFrame(self.pwm_tab, text=f"PWM {i+1}")
            frame.pack(fill='x', padx=10, pady=10)

            ativo_var = tk.BooleanVar(value=False)

            # Armazenar o checkbox no dicionário existente
            self.pwm_data[i]["ativo"] = ativo_var

            checkbox = ttk.Checkbutton(
                frame, text="Ativar PWM", variable=ativo_var,
                command=lambda var=ativo_var, i=i: self.toggle_pwm(i, var)
            )
            checkbox.pack(anchor='w', padx=10, pady=5)

            ttk.Label(frame, text="Frequência (Hz):").pack(anchor='w', padx=10)
            freq_val_label = ttk.Label(frame, text="1000 Hz")
            freq_val_label.pack(anchor='w', padx=20)

            freq_slider = ttk.Scale(
                frame, from_=1, to=1000, orient='horizontal',
                command=lambda val, lbl=freq_val_label, i=i: self.update_pwm_freq(i, val, lbl)
            )
            freq_slider.set(1000)
            freq_slider.pack(fill='x', padx=10)

            ttk.Label(frame, text="Duty Cycle (%):").pack(anchor='w', padx=10)
            duty_val_label = ttk.Label(frame, text="50 %")
            duty_val_label.pack(anchor='w', padx=20)

            duty_slider = ttk.Scale(
                frame, from_=0, to=100, orient='horizontal',
                command=lambda val, lbl=duty_val_label, i=i: self.update_pwm_duty(i, val, lbl)
            )
            duty_slider.set(50)
            duty_slider.pack(fill='x', padx=10)



    def toggle_pwm(self, index, var):
      self.pwm_data[index]["ativo"] = var
      self.send_all_data()


    def update_pwm_freq(self, index, value, label):
        val_int = int(float(value))
        label.config(text=f"{val_int} Hz")
        self.pwm_data[index]["freq"] = val_int
        self.send_all_data()

    def update_pwm_duty(self, index, value, label):
        val_int = int(float(value))
        label.config(text=f"{val_int} %")
        self.pwm_data[index]["duty"] = val_int
        self.send_all_data()

    def setup_tab_analisagem(self):
        top_frame = ttk.Frame(self.tab_analisagem)
        top_frame.pack(side='top', fill='x')

        for i, var in enumerate(self.channel_vars):
            cb = ttk.Checkbutton(top_frame, text=f"Canal A{i}", variable=var)
            cb.pack(side='left', padx=5)

        ttk.Label(top_frame, text="Amostras:").pack(side='left', padx=10)
        self.sample_scale = ttk.Scale(top_frame, from_=50, to=self.max_amostras, orient='horizontal',
                                      command=self.on_sample_scale_change)
        self.sample_scale.set(self.buffer_size)
        self.sample_scale.pack(side='left', padx=5)

        self.pause_button = ttk.Button(top_frame, text="Pausar", command=self.toggle_pause)
        self.pause_button.pack(side='left', padx=10)

        self.fig, self.ax = plt.subplots()
        self.lines = [self.ax.plot([], [])[0] for _ in range(6)]
        self.ax.set_ylim(-10, 1033)
        self.ax.set_xlim(0, self.buffer_size)
        self.ax.set_title("Osciloscópio - Entradas Analógicas")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_analisagem)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=100)

    def on_sample_scale_change(self, value):
        self.buffer_size = int(float(value))
        self.ax.set_xlim(0, self.buffer_size)

    def toggle_pause(self):
        if self.paused:
            self.ani.event_source.start()
            self.pause_button.config(text="Pausar")
        else:
            self.ani.event_source.stop()
            self.pause_button.config(text="Continuar")
        self.paused = not self.paused

    def update_plot(self, i):
        for ch in range(6):
            if self.channel_vars[ch].get():
                data = self.analog_data[ch][-self.buffer_size:]
                x = range(len(data))
                self.lines[ch].set_data(x, data)
            else:
                self.lines[ch].set_data([], [])
        self.ax.relim()
        self.ax.autoscale_view(scaley=True, scalex=False)
        self.canvas.draw()

    def setup_tab_serial(self):
        frm = self.tab_serial

        self.port_combo = ttk.Combobox(frm, values=self.ports)
        self.port_combo.pack(pady=5)

        self.btn_connect = ttk.Button(frm, text="Conectar", command=self.toggle_connection)
        self.btn_connect.pack(pady=5)

        self.log_box = tk.Text(frm, height=10)
        self.log_box.pack(padx=10, pady=10, fill='both', expand=True)

      
        self.manual_entry = ttk.Entry(self.tab_serial)
        self.manual_entry.pack(fill='x', padx=10)
        self.manual_entry.bind("<Return>", self.send_manual_command)

    def update_ports(self):
        self.ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = self.ports

    def toggle_connection(self):
        if self.serial_conn:
            self.reading = False
            time.sleep(0.5)
            self.serial_conn.close()
            self.serial_conn = None
            self.btn_connect.config(text="Conectar")
            self.log("Desconectado.")
        else:
            port = self.port_combo.get()
            if port:
                try:
                    self.serial_conn = serial.Serial(port, 115200, timeout=1)
                    self.reading = True
                    threading.Thread(target=self.read_serial, daemon=True).start()
                    self.btn_connect.config(text="Desconectar")
                    self.log(f"Conectado em {port}")
                    self.send_all_data()
                    self.send_all_data2()
                except Exception as e:
                    self.log(f"Erro ao conectar: {e}")

    def read_serial(self):
        while self.reading and self.serial_conn:
            try:
                line = self.serial_conn.readline().decode().strip()
                if line.startswith("A="):
                    payload = line[2:]  # Remove "A="
                    parts = payload.split(",")
                    if len(parts) == 6 and all(p.isdigit() for p in parts):
                        for i in range(6):
                            self.analog_data[i].append(int(parts[i]))
                            if len(self.analog_data[i]) > self.buffer_size:
                                self.analog_data[i].pop(0)
                    else:
                        self.log(f"< Formato A= inválido: {line}")
                elif line:
                    self.log(f"< {line}")
            except Exception as e:
                self.log(f"Erro leitura: {e}")


    def send_manual_command(self, event=None):
        if self.serial_conn and self.serial_conn.is_open:
            msg = self.manual_entry.get()
            if msg:
                self.serial_conn.write((msg + "\n").encode())
                self.log(f"> {msg}")
                self.manual_entry.delete(0, tk.END)
    def send_all_data(self):
        for i, pwm in enumerate(self.pwm_data):
            freq = pwm.get("freq", 1000)
            duty = pwm.get("duty", 50)
            ativo = int(pwm["ativo"].get())
            print(f"PWM{i+1}: FREQ={freq}, DUTY={duty}, ATIVO={ativo}")
            self.serial_conn.write(f"PWM{i+1}_FREQ:{freq}\n".encode())
            self.serial_conn.write(f"PWM{i+1}_DUTY:{duty}\n".encode())
            self.serial_conn.write(f"PWM{i+1}_ON:{ativo}\n".encode())
    def send_all_data2(self):
 
            dentes = self.dentes_totais.get()
            falhas = self.falhas.get()
            fase = self.fase_valor.get()
            rpm = self.rpm_valor.get()
            fase_on = 1 if self.simular_fase_var.get() else 0

            comandos = [
                f"DENTES:{dentes}\n",
                f"RPM:{rpm}\n",
                f"FALHAS:{falhas}\n",
                f"FASE:{fase}\n",
                f"FASE_ON:{fase_on}\n"
            ]

            for cmd in comandos:
                self.serial_conn.write(cmd.encode())
                print("Enviado:", cmd.strip())
        

    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FullApp(root)
    root.mainloop()

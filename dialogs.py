import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox

class ScaleDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Fator de escala X:").grid(row=0, column=0, sticky="e")
        tk.Label(master, text="Fator de escala Y:").grid(row=1, column=0, sticky="e")
        self.entry_sx = tk.Entry(master)
        self.entry_sy = tk.Entry(master)
        self.entry_sx.grid(row=0, column=1, padx=5, pady=3)
        self.entry_sy.grid(row=1, column=1, padx=5, pady=3)
        return self.entry_sx  # foco inicial

    def validate(self):
        try:
            self.sx = float(self.entry_sx.get())
            self.sy = float(self.entry_sy.get())
            if self.sx < 0 or self.sy < 0:
                raise ValueError("Valores devem ser ≥ 0")
        except Exception as e:
            messagebox.showerror("Entrada inválida", str(e), parent=self)
            return False
        return True

    def apply(self):
        # atributos self.sx e self.sy já definidos em validate()
        pass

class ShearDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="shx:").grid(row=0, column=0, sticky="e")
        tk.Label(master, text="shy:").grid(row=1, column=0, sticky="e")
        self.entry_sx = tk.Entry(master)
        self.entry_sy = tk.Entry(master)
        self.entry_sx.grid(row=0, column=1, padx=5, pady=3)
        self.entry_sy.grid(row=1, column=1, padx=5, pady=3)
        return self.entry_sx  # foco inicial

    def validate(self):
        try:
            self.sx = float(self.entry_sx.get())
            self.sy = float(self.entry_sy.get())
            if self.sx < 0 or self.sy < 0:
                raise ValueError("Valores devem ser ≥ 0")
        except Exception as e:
            messagebox.showerror("Entrada inválida", str(e), parent=self)
            return False
        return True

    def apply(self):
        # atributos self.sx e self.sy já definidos em validate()
        pass

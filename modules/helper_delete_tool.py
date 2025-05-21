import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np

class MeshClipperApp(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyVista Interactive Clipping Tool")
        self.setGeometry(100, 100, 1200, 900)

        # 1. Configuração da interface PySide6
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # PyVistaQt interactor
        self.plotter = QtInteractor(self.central_widget)
        self.layout.addWidget(self.plotter.interactor)

        # Controles
        self.controls_layout = QVBoxLayout()
        self.instruction_label = QLabel(
            "Pressione 'Ativar Recorte' para mostrar a caixa. "
            "Use as setas para mover a caixa (X,Z). W/S para mover Y. "
            "'A/D' para X-size, 'Z/X' para Y-size, 'Q/E' para Z-size. "
            "Pressione 'Enter' para aplicar o recorte. 'R' para resetar. 'C' para alternar o modo de recorte."
        )
        self.controls_layout.addWidget(self.instruction_label)

        button_layout = QHBoxLayout()

        self.activate_clip_button = QPushButton("Ativar Recorte")
        self.activate_clip_button.clicked.connect(self.activate_clip_mode)
        button_layout.addWidget(self.activate_clip_button)

        self.reset_button = QPushButton("Resetar Malha")
        self.reset_button.clicked.connect(self.reset_mesh)
        button_layout.addWidget(self.reset_button)
        
        self.toggle_clip_mode_button = QPushButton("Inverter Recorte (Atual: Interno)")
        self.toggle_clip_mode_button.clicked.connect(self.toggle_clip_inversion)
        button_layout.addWidget(self.toggle_clip_mode_button)

        self.layout.addLayout(button_layout)
        self.layout.addLayout(self.controls_layout)

        # 2. Criar uma malha de exemplo
        self.original_mesh = pv.examples.load_airplane()
        self.current_mesh = self.original_mesh.copy()
        self.add_initial_mesh()

        # Variáveis de estado para o recorte
        # Corrigido: Agora armazenamos centro e comprimentos separadamente
        self.roi_center = [0.0, 0.0, 0.0] 
        self.roi_lengths = [100.0, 100.0, 100.0]
        self.clip_roi: pv.PolyData | None = None # O objeto PolyData do cubo
        self.clip_actor = None # O ator da caixa de recorte no plotter
        self.clip_mode_active = False
        self.clip_invert = False # Se o recorte é interno (False) ou externo (True)

        # Parâmetros de controle da caixa (ajuste conforme necessário)
        self.move_step = 10.0 # Quão longe a caixa se move por tecla
        self.resize_step = 10.0 # Quão rápido a caixa muda de tamanho por tecla

        # 3. Adicionar eventos de teclado para controle da caixa
        self.plotter.add_key_event('Up', lambda: self.move_clip_roi(z=self.move_step))
        self.plotter.add_key_event('Down', lambda: self.move_clip_roi(z=-self.move_step))
        self.plotter.add_key_event('Left', lambda: self.move_clip_roi(x=-self.move_step))
        self.plotter.add_key_event('Right', lambda: self.move_clip_roi(x=self.move_step))
        self.plotter.add_key_event('w', lambda: self.move_clip_roi(y=self.move_step))
        self.plotter.add_key_event('s', lambda: self.move_clip_roi(y=-self.move_step))
        
        self.plotter.add_key_event('a', lambda: self.resize_clip_roi(x=-self.resize_step))
        self.plotter.add_key_event('d', lambda: self.resize_clip_roi(x=self.resize_step))
        self.plotter.add_key_event('q', lambda: self.resize_clip_roi(z=-self.resize_step))
        self.plotter.add_key_event('e', lambda: self.resize_clip_roi(z=self.resize_step))
        self.plotter.add_key_event('z', lambda: self.resize_clip_roi(y=-self.resize_step)) # Z para diminuir Y
        self.plotter.add_key_event('x', lambda: self.resize_clip_roi(y=self.resize_step)) # X para aumentar Y

        self.plotter.add_key_event('Return', self.apply_clip) # Tecla Enter
        self.plotter.add_key_event('r', self.reset_mesh) # Tecla R para resetar
        self.plotter.add_key_event('c', self.toggle_clip_inversion) # Tecla C para alternar modo de recorte

    def add_initial_mesh(self):
        """Adiciona a malha inicial ao plotter."""
        self.plotter.add_mesh(self.current_mesh, show_edges=True, color='lightblue', name='main_mesh')
        self.plotter.show_grid()
        self.plotter.reset_camera()
        self.plotter.render()

    def _update_roi_actor(self):
        """Recria o pv.Cube e atualiza seu ator no plotter."""
        if self.clip_actor:
            self.plotter.remove_actor('clip_roi_actor') # Remove o ator antigo
            self.clip_actor = None # Limpa a referência
            
        # Recria o cubo com os parâmetros atualizados
        self.clip_roi = pv.Cube(
            center=self.roi_center,
            x_length=self.roi_lengths[0],
            y_length=self.roi_lengths[1],
            z_length=self.roi_lengths[2]
        )
        # Adiciona o novo cubo ao plotter
        self.clip_actor = self.plotter.add_mesh(self.clip_roi, opacity=0.3, color='red', name='clip_roi_actor')
        self.plotter.render()

    def activate_clip_mode(self):
        """Ativa o modo de recorte, mostrando a caixa ROI."""
        if not self.clip_mode_active:
            self.clip_mode_active = True
            # Inicializa a ROI no centro da malha original
            bounds = self.original_mesh.bounds
            x_length = bounds[1] - bounds[0]
            y_length = bounds[3] - bounds[2]
            z_length = bounds[5] - bounds[4]
            
            # Define o centro inicial como o centro da malha
            self.roi_center = list(self.current_mesh.center) 
            # Define os comprimentos iniciais como uma fração das dimensões da malha
            self.roi_lengths = [x_length * 0.5, y_length * 0.5, z_length * 0.5]
            
            self._update_roi_actor() # Cria e adiciona a ROI ao plotter
            
            self.instruction_label.setText(
                "Modo de recorte ATIVO. "
                "Use as setas para mover (X,Z), W/S para mover Y. "
                "'A/D' para X-size, 'Z/X' para Y-size, 'Q/E' para Z-size. "
                "Pressione 'Enter' para aplicar."
            )
            print("Modo de recorte ativado.")
        else:
            print("Modo de recorte já está ativo.")

    def move_clip_roi(self, x=0.0, y=0.0, z=0.0):
        """Move a caixa de recorte (ROI) em uma direção."""
        if self.clip_mode_active and self.clip_roi:
            self.roi_center[0] += x
            self.roi_center[1] += y
            self.roi_center[2] += z
            self._update_roi_actor() # Recria e atualiza o ator
            print(f"ROI movida para {self.roi_center}")

    def resize_clip_roi(self, x=0.0, y=0.0, z=0.0):
        """Redimensiona a caixa de recorte (ROI)."""
        if self.clip_mode_active and self.clip_roi:
            self.roi_lengths[0] = max(1.0, self.roi_lengths[0] + x)
            self.roi_lengths[1] = max(1.0, self.roi_lengths[1] + y)
            self.roi_lengths[2] = max(1.0, self.roi_lengths[2] + z)
            self._update_roi_actor() # Recria e atualiza o ator
            print(f"ROI redimensionada para L_x={self.roi_lengths[0]}, L_y={self.roi_lengths[1]}, L_z={self.roi_lengths[2]}")

    def toggle_clip_inversion(self):
        """Alterna o modo de recorte (interno vs. externo)."""
        self.clip_invert = not self.clip_invert
        mode_text = "Externo (fora da caixa)" if self.clip_invert else "Interno (dentro da caixa)"
        self.toggle_clip_mode_button.setText(f"Inverter Recorte (Atual: {mode_text})")
        self.instruction_label.setText(f"Modo de recorte atual: {mode_text}. Pressione 'Enter' para aplicar.")
        print(f"Modo de recorte invertido para: {mode_text}")
        self.plotter.render() # Força renderização para atualizar o texto do botão imediatamente.

    def apply_clip(self):
        """Aplica o recorte da malha usando a caixa ROI."""
        if self.clip_mode_active and self.clip_roi:
            print(f"Aplicando recorte. Modo de inversão: {self.clip_invert}")
            try:
                # Remove a malha antiga e o ator da caixa
                self.plotter.remove_actor('main_mesh')
                self.plotter.remove_actor('clip_roi_actor')

                # Aplica o recorte
                # IMPORTANTE: self.clip_roi é o PolyData do cubo, que é o que clip_box espera
                self.current_mesh = self.current_mesh.clip_box(self.clip_roi, invert=self.clip_invert)
                
                # Adiciona a nova malha recortada
                self.plotter.add_mesh(self.current_mesh, show_edges=True, color='lightgray', name='main_mesh_clipped')
                self.plotter.reset_camera()
                self.plotter.render()

                self.clip_mode_active = False
                self.clip_roi = None
                self.clip_actor = None
                self.instruction_label.setText("Recorte aplicado! Pressione 'Ativar Recorte' novamente para novo recorte.")
                self.toggle_clip_mode_button.setText("Inverter Recorte (Atual: Interno)") # Reseta o texto do botão
                print("Recorte aplicado com sucesso.")
            except Exception as e:
                print(f"Erro ao aplicar o recorte: {e}")
                self.instruction_label.setText(f"Erro ao aplicar o recorte: {e}")
        else:
            print("Modo de recorte não está ativo ou ROI não definida.")
            self.instruction_label.setText("Ative o modo de recorte primeiro para aplicar.")

    def reset_mesh(self):
        """Reseta a malha para seu estado original e remove a caixa ROI."""
        self.current_mesh = self.original_mesh.copy()
        self.add_initial_mesh() # Isso já chama remove_all_actors()
        
        if self.clip_actor: # Garante que a ROI também seja removida se o reset ocorrer sem ter aplicado o clip
            self.plotter.remove_actor('clip_roi_actor')
            self.clip_actor = None
            self.clip_roi = None
        
        # Reseta as variáveis de estado da ROI também
        self.roi_center = [0.0, 0.0, 0.0]
        self.roi_lengths = [100.0, 100.0, 100.0]

        self.clip_mode_active = False
        self.clip_invert = False 
        self.toggle_clip_mode_button.setText("Inverter Recorte (Atual: Interno)") 
        self.instruction_label.setText("Malha resetada. Pressione 'Ativar Recorte' para começar.")
        print("Malha resetada para o estado original.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MeshClipperApp()
    window.show()
    sys.exit(app.exec())
import sys
import os
from halfEdge import HalfEdgeMesh, Vertex, HalfEdge
import tkinter as tk
from tkinter import filedialog
from utils import component_from_face
import MatrizResultante as MR
import numpy as np
from tkinter import simpledialog
from dialogs import ScaleDialog, ShearDialog

# Configuration\ nWINDOW_WIDTH = 800
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
MENU_HEIGHT = 50
INPUT_HEIGHT = 30
BG_COLOR = (30, 30, 30)
MENU_COLOR = (50, 50, 50)
VERTEX_COLOR = (255, 200, 0)
EDGE_COLOR = (200, 200, 200)
BUTTON_COLOR = (80, 80, 80)
BUTTON_HOVER_COLOR = (100, 100, 100)
TEXT_COLOR = (255, 255, 255)
FPS = 60
INPUT_BG_COLOR = (40, 40, 40)
INPUT_BORDER_COLOR = (100, 100, 100)
MARGIN = 20

SCALE_FACTOR = (WINDOW_HEIGHT - MENU_HEIGHT - INPUT_HEIGHT - 2 * MARGIN)/max(WINDOW_HEIGHT-MARGIN, WINDOW_WIDTH - 2 * MARGIN)

# Primitive buttons configuration\ n

MENU_ITEMS = ["View", "Open", "Triangle", "Rectangle", "Translate", "Polygon"]

BUTTON_PADDING = 10
BUTTON_SPACING = 10





class Interface():
    def __init__(self, pygame, font):
        self.pygame = pygame
        self.file_path = ""
        self.mode = 'view'       # modos: 'view', 'translate'
        self._drag_start = None  # armazenar screen_pos no início do drag
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self._view_units_x = 3       # 800 por exemplo
        self._view_units_y = 3
        self._view_min_x = 0.0
        self._view_min_y = 0.0
        self._view_bottom = self._view_min_y + self._view_units_y
        usable_w = WINDOW_WIDTH  - 2*MARGIN
        usable_h = (WINDOW_HEIGHT - MENU_HEIGHT - INPUT_HEIGHT) - 2*MARGIN
        self._view_usable_w = usable_w
        self._view_usable_h = usable_h
        self._view_top    = MENU_HEIGHT   + MARGIN
        self._view_bottom = WINDOW_HEIGHT - INPUT_HEIGHT - MARGIN

        # 4) Malha HalfEdge vazia
        self.mesh = HalfEdgeMesh()

        self.project = None
        self.menu_options = [
            "Digite um ângulo...",
            "Rotacionar 90°",
            "Inverter Vertical",
            "Inverter Horizontal",
            "Escalar",
            "Cisalhar"
        ]
        self.font = font

        self.input_values = {'UX': f"{3}", 'UY': f"{3}"}

        # Campos de input (unidades)
        self.input_rects = {
            'UX': pygame.Rect(10, WINDOW_HEIGHT - INPUT_HEIGHT + 5, 120, INPUT_HEIGHT - 10),
            'UY': pygame.Rect(140, WINDOW_HEIGHT - INPUT_HEIGHT + 5, 120, INPUT_HEIGHT - 10)
        }

        self.menu_rects = []
        self.menu_position = (0, 0)
        self.root = tk.Tk()
        self.root.withdraw()
        

        self.buttons = None

        self.menu_active = False

        
        
    def toggle_translate_mode(self):
        """Troca entre view e translate."""
        self.mode = 'translate' if self.mode != 'translate' else 'view'
    
    def switch_mode(self, mode):
        self.mode = mode

    def load_mesh(self, filepath):
        mesh = HalfEdgeMesh()
        mesh.load_obj(filepath)
        return mesh

    def compute_extents(self, vertices, units_x = None, units_y = None):
        xs = [v.position[0] for v in vertices]
        ys = [v.position[1] for v in vertices]
        if not xs or not ys:
            return 3.0, 3.0
        
        span_x = max(xs) - min(xs) or 3.0
        span_y = max(ys) - min(ys) or 3.0
        
        if units_x and units_y:
            if span_x > units_x or span_y > units_y:
                return span_x, span_y
            else:
                return units_x, units_y
        return span_x, span_y

    def open_obj(self):
        self.file_path = filedialog.askopenfilename(title="Open OBJ File",
                                               filetypes=[("OBJ Files", "*.obj")])
        
        if self.file_path:
            try:
                mesh = self.load_mesh(self.file_path)
                return mesh
            except Exception as e:
                print(f"Failed to load mesh: {e}")

    def compute_projection(self, vertices, width, height, units_x, units_y):
        # 1) extrai min/max do modelo
        xs = [v.position[0] for v in vertices]
        ys = [v.position[1] for v in vertices]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # 2) espaço útil
        usable_w = width  - 2*MARGIN
        usable_h = (height - MENU_HEIGHT - INPUT_HEIGHT) - 2*MARGIN

        # 3) armazena para usar na inversão
        self._view_min_x = min_x
        self._view_min_y = min_y
        self._view_units_x = units_x
        self._view_units_y = units_y
        self._view_usable_w = usable_w
        self._view_usable_h = usable_h
        self._view_top    = MENU_HEIGHT   + MARGIN
        self._view_bottom = height - INPUT_HEIGHT - MARGIN

        # 4) cria o project
        def project(v):
            sx = MARGIN + ( (v.position[0] - min_x) / units_x ) * usable_w
            sy = self._view_bottom - ( (v.position[1] - min_y) / units_y ) * usable_h
            return (sx, sy)
        return project

    def screen_to_model(self, screen_pos):
        """
        Inverte exatamente o compute_projection acima:
        limpa qualquer desvio constante.
        """
        mx, my = screen_pos

        # 1) X: tira margin, converte proporção, soma min_x
        model_x = ((mx - MARGIN) 
                   / self._view_usable_w 
                   * self._view_units_x) + self._view_min_x

        # 2) Y: mede em pixels acima da linha de base do viewport,
        #    converte proporção, soma min_y
        pixel_above_bottom = self._view_bottom - my
        model_y = (pixel_above_bottom 
                   / self._view_usable_h 
                   * self._view_units_y) + self._view_min_y

        return (model_x, model_y)


    #def screen_to_model(self, screen_pos, units_x=3, units_y=3, width=WINDOW_WIDTH, #height=WINDOW_HEIGHT, margin=MARGIN):
    #    mx, my = screen_pos
    #    scale_x = (width - 2*margin)/units_x
    #    scale_y = (height - MENU_HEIGHT - INPUT_HEIGHT - 2*margin)/units_y
    #    model_x = (mx - margin)/scale_x
    #    raw_y = (height - INPUT_HEIGHT - MENU_HEIGHT) - my
    #    model_y = raw_y/scale_y
    #    return (model_x, model_y)


    def create_buttons(self, font):
        buttons = []
        x = BUTTON_PADDING
        y = (MENU_HEIGHT - font.get_height()) // 2
        for name in MENU_ITEMS:
            text_surf = font.render(name, True, TEXT_COLOR)
            btn_rect = self.pygame.Rect(x, 0, text_surf.get_width() + 2 * BUTTON_PADDING, MENU_HEIGHT)
            buttons.append((name, btn_rect, text_surf))
            x += btn_rect.width + BUTTON_SPACING
        return buttons
    
    def create_rect(self, pA, pB, mesh):
        """
        Adiciona um retângulo à mesh a partir de dois cantos opostos pA e pB,
        em qualquer ordem de clique/arraste.

        pA, pB: tuplas (x, y) de dois cantos opostos do retângulo.
        mesh: instância de HalfEdgeMesh que receberá o retângulo.
        """
        # 1) Descobre as coordenadas min/max em x e y
        x_min = min(pA[0], pB[0])
        x_max = max(pA[0], pB[0])
        y_min = min(pA[1], pB[1])
        y_max = max(pA[1], pB[1])

        # 2) Reconstrói as 4 esquinas na ordem BL, BR, TR, TL
        bl = (x_min, y_min)  # bottom-left
        br = (x_max, y_min)  # bottom-right
        tr = (x_max, y_max)  # top-right
        tl = (x_min, y_max)  # top-left

        # 3) Chama a função genérica de criação
        mesh.create_rectangle([bl, br, tr, tl])
        self.reproject()

    def create_triangle(self, pA, pB, mesh):
        """
        Adiciona um triângulo retângulo à mesh considerando pA e pB como extremidades da hipotenusa.

        pA, pB: tuplas (x, y) dos vértices da hipotenusa.
        mesh: instância de HalfEdgeMesh que receberá o triângulo.
        """
        # calcula o vértice do ângulo reto alinhado aos eixos: (pA.x, pB.y)
        xA, yA = pA
        xB, yB = pB
        pC = (xA, yB)  # ponto com coordenadas de A.x e B.y
        # chama a função genérica para criar o triângulo
        mesh.create_triangle([pA, pC, pB])
        self.reproject()

    def draw_menu(self):
        # desenha fundo e texto do menu
        for rect, _, surf in self.menu_rects:
            self.pygame.draw.rect(self.screen, (50, 50, 50), rect.inflate(4, 4))
        for rect, _, surf in self.menu_rects:
            self.screen.blit(surf, rect)
    
    def handle_left_click(self, pos):
        print("handle_left_click")
        pos = self.screen_to_model(pos)
        # seleção de componente sem abrir menu
        face = self.mesh.pick_face(pos)
        if face:
            comp = component_from_face(self.mesh, face)
            self.selected_vertices = comp["vertices"]
            self.menu_active = False

    def handle_right_click(self, pos):
        # abre menu de contexto apenas se clicar em um face
        model_pos = self.screen_to_model(pos)
        face = self.mesh.pick_face(model_pos)
        if face:
            comp = component_from_face(self.mesh, face)
            self.selected_vertices = comp['vertices']
            self.menu_active = True
            self.menu_position = pos
            self._prepare_menu()
        else:
            self.menu_active = False

    def _prepare_menu(self):
        # cria um rect para cada opção de menu
        font = self.pygame.font.SysFont(None, 24)
        x, y = self.menu_position
        self.menu_rects.clear()
        for i, text in enumerate(self.menu_options):
            surf = font.render(text, True, (255, 255, 255))
            rect = surf.get_rect(topleft=(x + 5, y + 5 + i * 30))
            self.menu_rects.append((rect, text, surf))

    def handle_menu_click(self, pos):
        print("handle_menu_click")
        for rect, text, _ in self.menu_rects:
            if rect.collidepoint(pos):
                self.apply_transform(text)
                self.menu_active = False
                break
        self.handle_left_click(pos)
        


    def apply_transform(self, option: str):
        # calcula centróide do componente selecionado
        xs = [v.position[0] for v in self.selected_vertices]
        ys = [v.position[1] for v in self.selected_vertices]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        M = None
                # define matriz de transformação M usando funções de MatrizResultante
        if option == "Digite um ângulo...":
            try:
                angle = simpledialog.askfloat(
                    "Rotação",
                    "Digite o ângulo de rotação (em graus):",
                    minvalue=-360, maxvalue=360
                )

                if angle is None:
                    # Usuário cancelou
                    return
            except ValueError:
                return
            rad = np.deg2rad(angle)
            # transladar ao centro, rotacionar, transladar de volta
            M = (MR.matriz_translacao(cx, cy) @
                 MR.matriz_rotacao(rad) @
                 MR.matriz_translacao(-cx, -cy))
        elif option == "Rotacionar 90°":
            rad = np.deg2rad(90.0)
            M = (MR.matriz_translacao(cx, cy) @
                 MR.matriz_rotacao(rad) @
                 MR.matriz_translacao(-cx, -cy))
        elif option == "Inverter Vertical":
            # reflexão em y: eixo horizontal passa por cy
            M = (MR.matriz_translacao(cx, cy) @
                 MR.matriz_reflexao('x') @
                 MR.matriz_translacao(-cx, -cy))
        elif option == "Inverter Horizontal":
            # reflexão em x: eixo vertical passa por cx
            M = (MR.matriz_translacao(cx, cy) @
                 MR.matriz_reflexao('y') @
                 MR.matriz_translacao(-cx, -cy))
        elif option == "Escalar":
            dlg = ScaleDialog(self.root, title="Escala em X e Y")
            # após fechar, se dlg.sx e dlg.sy existem, aplica
            if hasattr(dlg, "sx") and hasattr(dlg, "sy"):
                M = (MR.matriz_translacao(cx, cy) @
                     MR.matriz_escalacao(dlg.sx, dlg.sy) @ 
                     MR.matriz_translacao(-cx, -cy))
        elif option == "Cisalhar":
            dlg = ShearDialog(self.root, title="Fatores em shx e shy")
            # após fechar, se dlg.sx e dlg.sy existem, aplica
            if hasattr(dlg, "sx") and hasattr(dlg, "sy"):
                M = (
                    MR.matriz_translacao(cx, cy) @
                    MR.matriz_cisalhamento(dlg.sx, dlg.sy) @
                    MR.matriz_translacao(-cx, -cy)
                )
        else:
            return

        # aplica transformação homogênea
        for v in self.selected_vertices:
            x_old, y_old, z_old = v.position
            p = np.array([x_old, y_old, 1.0])
            x_new, y_new, _ = M @ p
            # atualiza de fato o position do vértice
            v.position = (x_new, y_new, z_old)

        self.reproject()
    

    def reproject(self):
        desired_x = float(self.input_values['UX'])
        desired_y = float(self.input_values['UY'])
        # 3) recomputa projeção para redesenhar
        span_x, span_y = self.compute_extents(self.mesh.vertices, desired_x, desired_y)
        self.project = self.compute_projection(
            self.mesh.vertices,
            WINDOW_WIDTH, WINDOW_HEIGHT,
            span_x, span_y
        )

        self.input_values['UX'] = f"{span_x:.2f}"
        self.input_values['UY'] = f"{span_y:.2f}"

    def draw_interface(self, mouse_pos, posicoes_polygon):
        # Draw background
        self.screen.fill(BG_COLOR)

        if self.mesh:
            if self.menu_active:
                self.draw_menu()
            # Draw edges
            drawn_edges = set()
            for (o_idx, d_idx), he in self.mesh.edge_map.items():
                edge = tuple(sorted((o_idx, d_idx)))
                if edge in drawn_edges:
                    continue
                drawn_edges.add(edge)

                v1 = self.mesh.vertices[edge[0] - 1]
                v2 = self.mesh.vertices[edge[1] - 1]
                p1 = self.project(v1)
                p2 = self.project(v2)
                self.pygame.draw.line(self.screen, EDGE_COLOR, p1, p2, 2)

            # Draw vertices
            for v in self.mesh.vertices:
                p = self.project(v)
                self.pygame.draw.circle(self.screen, VERTEX_COLOR, p, 5)

            for p in posicoes_polygon:
                self.pygame.draw.circle(self.screen, VERTEX_COLOR, p, 5)
            

            # Draw input area
            self.pygame.draw.rect(self.screen, INPUT_BG_COLOR, (0, WINDOW_HEIGHT - INPUT_HEIGHT, WINDOW_WIDTH, INPUT_HEIGHT))
            for key, rect in self.input_rects.items():
                self.pygame.draw.rect(self.screen, INPUT_BORDER_COLOR, rect, 2)
                txt = self.font.render(f"{key}: {self.input_values[key]}", True, TEXT_COLOR)
                self.screen.blit(txt, (rect.x + 5, rect.y + (rect.height - txt.get_height()) // 2))

        # Draw menu bar
        self.pygame.draw.rect(self.screen, MENU_COLOR, (0, 0, WINDOW_WIDTH, MENU_HEIGHT))
        for name, rect, text_surf in self.buttons:
            color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_COLOR
            self.pygame.draw.rect(self.screen, color, rect)
            self.screen.blit(text_surf, (rect.x + BUTTON_PADDING, (MENU_HEIGHT - text_surf.get_height()) // 2))
    
    
        self.pygame.display.flip()
        self.clock.tick(FPS)

    def on_save(self):
        # 1) Se ainda não temos um caminho de arquivo definido ou ele não existe, pede ao usuário
        if not self.file_path or not os.path.exists(self.file_path):
            # abre diálogo “Salvar como .obj”
            path = filedialog.asksaveasfilename(
                parent=self.root,
                defaultextension=".obj",
                filetypes=[("Wavefront OBJ", "*.obj")],
                title="Salvar modelo como OBJ"
            )
            # se o usuário cancelou, aborta sem destruir nada
            if not path:
                return
            self.file_path = path
            self.mesh.export_obj(self.file_path)  # ou o método que você usa para exportar
           




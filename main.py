import pygame
from interface import *
from MatrizResultante import matriz_translacao  # ou de onde você definiu
import numpy as np
from utils import component_from_face


EVENTS = {
    "rect": False,
    "triangle": False,
    "polygon": False
}

class MouseEvent:
    
    def __init__(self):
        self.count = 0
        self.clickPositions = []
        pass
    
    def start_rect_event(self, event):
        self.clickPositions = []
        if event == "rect":
            self.count = 2
        if event == "triangle":
            self.count = 3    
    
    def add_click(self, click_position):
        if self.count > 0:
            self.clicks_positions.append(click_position)
            self.count-=1

    
    def showEvent(self):
        for i, point in self.clickPositions:
            print(f"ponto {i}: {point}")

        



def main():

    

    

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Half-Edge Mesh Viewer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    
    interface = Interface(pygame, font)
    posicoes = [None]*2
    posicoes_polygon = []
    arrastando = False

    interface.buttons = interface.create_buttons(font)

    #if mesh:
    first_focus = {'UX': True, 'UY': True}
    active_input = True
    #project = compute_projection(mesh.vertices, WINDOW_WIDTH, WINDOW_HEIGHT)
    first_focus = {'SX': True, 'SY': True}
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # ao clicar no botão esquerdo
             # Inicia drag só no modo translate e com o botão esquerdo
            elif (event.type == pygame.MOUSEBUTTONDOWN and
                  event.button == 1 and
                  interface.mode == 'translate' and
                  MENU_HEIGHT <= event.pos[1] <= (WINDOW_HEIGHT - INPUT_HEIGHT)):
                interface._drag_start = event.pos  # GUARDA aqui

            elif event.type == pygame.MOUSEBUTTONDOWN and interface.menu_active and MENU_HEIGHT <= event.pos[1] <= (WINDOW_HEIGHT - INPUT_HEIGHT):
                    # clique dentro do menu de contexto
                    interface.handle_menu_click(event.pos)

            # ao soltar, aplica translação
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and interface.mode == 'translate'and MENU_HEIGHT <= event.pos[1] <= (WINDOW_HEIGHT - INPUT_HEIGHT):
                start = interface._drag_start
                end   = event.pos
                interface._drag_start = None

                # converte screen→model usando seu método (sem params extras):
                # lembre-se: você já salvou os parâmetros no compute_projection
                p0 = interface.screen_to_model(start)
                p1 = interface.screen_to_model(end)

                face = interface.mesh.pick_face(p0)
                if face:
                    comp = component_from_face(interface.mesh, face)
                    # agora comp['vertices'] é o conjunto de vértices do objeto clicado
                    interface.selected_vertices = comp['vertices']
                else:
                    interface.selected_vertices = set()

                # delta em modelo
                dx = p1[0] - p0[0]
                dy = p1[1] - p0[1]

                # 1) cria matriz de translação
                M = matriz_translacao(dx, dy)

                # 2) aplica a todos os vértices
                for v in interface.selected_vertices:
                    x, y, z = v.position
                    x_new, y_new, _ = M @ np.array([x, y, 1])
                    v.position = (x_new, y_new, z)
                desired_x = float(interface.input_values['UX'])
                desired_y = float(interface.input_values['UY'])
                # 3) recomputa projeção para redesenhar
                span_x, span_y = interface.compute_extents(interface.mesh.vertices, desired_x, desired_y)
                interface.project = interface.compute_projection(
                    interface.mesh.vertices,
                    WINDOW_WIDTH, WINDOW_HEIGHT,
                    span_x, span_y
                )

                interface.input_values['UX'] = f"{span_x:.2f}"
                interface.input_values['UY'] = f"{span_y:.2f}"

                print(f"Objeto transladado por ({dx:.3f}, {dy:.3f})")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if event.button == 1 and interface.mode == "rect" and MENU_HEIGHT <= y <= (WINDOW_HEIGHT - INPUT_HEIGHT):
                    posicoes[0] = event.pos
                    posicoes[1] = event.pos
                    arrastando = True

                elif event.button == 1 and interface.mode == "triangle" and MENU_HEIGHT <= y <= (WINDOW_HEIGHT - INPUT_HEIGHT):
                    posicoes[0] = event.pos
                    posicoes[1] = event.pos
                    arrastando = True
                
                elif event.button == 1 and interface.mode == "polygon" and MENU_HEIGHT <= y <= (WINDOW_HEIGHT - INPUT_HEIGHT):
                    if len(posicoes_polygon) > 0:
                        dx = event.pos[0] - posicoes_polygon[0][0]
                        dy = event.pos[1] - posicoes_polygon[0][1]
                    
                        distance = (dx ** 2 + dy ** 2)**(1/2)
                    
                        if (distance < 10):
                            posicoes_polygon.append(posicoes_polygon[0])
                            interface.switch_mode("view")
                            model_positions = []
                            for pos in posicoes_polygon:
                                model_positions.append(interface.screen_to_model(pos))
                            interface.mesh.create_polygon(model_positions)
                            posicoes_polygon = []
                            interface.reproject()
                            
                        else:
                            posicoes_polygon.append(event.pos)
                    else:
                        posicoes_polygon.append(event.pos)

                    
                    
                
                # botão esquerdo
                if event.button == 1 and MENU_HEIGHT <= event.pos[1] <= (WINDOW_HEIGHT - INPUT_HEIGHT) and interface.mode != "rect":
                    interface.handle_left_click(event.pos)
                # botão direito
                elif event.button == 3 and MENU_HEIGHT <= event.pos[1] <= (WINDOW_HEIGHT - INPUT_HEIGHT): 
                    interface.handle_right_click(event.pos)
                

                
                for name, rect, _ in interface.buttons:
                    if rect.collidepoint(mouse_pos):
                        match name:
                            case "View":
                                interface.switch_mode("view")
                            case "Open":
                                interface.mesh = interface.open_obj()
                                span_x, span_y = interface.compute_extents(interface.mesh.vertices, float(interface.input_values['UX']), float(interface.input_values['UY']))
                                desired_x, desired_y = span_x, span_y
                                interface.input_values['UX'] = f"{desired_x:.2f}"
                                interface.input_values['UY'] = f"{desired_y:.2f}"
                                first_focus = {'UX': True, 'UY': True}
                                
                                interface.project = interface.compute_projection(interface.mesh.vertices, WINDOW_WIDTH, WINDOW_HEIGHT,desired_x, desired_y)
                            case "Triangle":
                                interface.switch_mode("triangle")
                                print(f"Button '{name}' clicked - functionality not yet implemented")
                            case "Rectangle":
                                interface.switch_mode("rect")
                                print(f"Button '{name}' clicked - functionality not yet implemented")
                            case "Translate":
                                interface.switch_mode("translate")
                                print("Modo:", interface.mode)
                            case "Polygon":
                                interface.switch_mode("polygon")

                # Input field focus
                active_input = None
                for key, rect in interface.input_rects.items():
                    if rect.collidepoint(mouse_pos):
                        active_input = key
            
             # Input field focus
                active_input = None
                for key, rect in interface.input_rects.items():
                    if rect.collidepoint(mouse_pos):
                        active_input = key
                        # Clear on first focus
                        if first_focus[key]:
                            interface.input_values[key] = ''
                            first_focus[key] = False
            elif event.type == pygame.KEYDOWN and active_input:
                if event.key in [pygame.K_BACKSPACE, pygame.K_KP_ENTER]:
                    interface.input_values[active_input] = interface.input_values[active_input][:-1]
                    
                elif event.unicode.isdigit() or event.unicode == '.':
                    interface.input_values[active_input] += event.unicode
                elif event.key == pygame.K_RETURN:
                    try:
                        desired_x = float(interface.input_values['UX'])
                        desired_y = float(interface.input_values['UY'])
                        if interface.mesh:
                            interface.project = interface.compute_projection(interface.mesh.vertices, WINDOW_WIDTH, WINDOW_HEIGHT, desired_x, desired_y)
                    except ValueError:
                        pass  # ignore invalid input
            #print(input_values)

            elif event.type == pygame.MOUSEMOTION and (interface.mode == "rect" or interface.mode == "triangle"):
                if arrastando:
                    posicoes[1] = event.pos  # Atualiza posição final
                
            
            elif event.type == pygame.MOUSEBUTTONUP and (interface.mode == "rect" or interface.mode == "triangle") :
                if arrastando:
                    arrastando = False

                    # converte usando o método inverso, sem parâmetros extras:
                    p1 = interface.screen_to_model(posicoes[0])
                    p2 = interface.screen_to_model(posicoes[1])

                    if (interface.mode == "rect"):
                        # cria o retângulo
                        interface.create_rect(p1, p2, interface.mesh)
                    elif (interface.mode == "triangle"):
                        interface.create_triangle(p1, p2, interface.mesh)
                    
                    
            # Verifica se uma tecla foi pressionada
            if event.type == pygame.KEYDOWN:
                # Verifica se a tecla 's' foi pressionada
                if event.key == pygame.K_s:
                    # Verifica se o CTRL está sendo segurado
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_CTRL:
                        print("salvando")
                        interface.on_save()

        interface.draw_interface(mouse_pos, posicoes_polygon)


                    
        

    pygame.quit()


if __name__ == '__main__':
    main()
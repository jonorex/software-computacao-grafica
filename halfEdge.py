

class Vertex:
    def __init__(self, idx, position):
        self.idx = idx            # index in OBJ (1-based)
        self.position = position  # (x, y, z)
        self.half_edge = None     # one outgoing half-edge

class HalfEdge:
    def __init__(self):
        self.origin = None        # Vertex
        self.twin = None          # HalfEdge
        self.next = None          # HalfEdge
        self.face = None          # Face

class Face:
    def __init__(self, idx):
        self.idx = idx            # face ID (1-based)
        self.half_edge = None     # one half-edge on its boundary

class HalfEdgeMesh:
    def __init__(self):
        self.vertices = []        # list of Vertex
        self.faces = []           # list of Face
        self.half_edges = []      # list of HalfEdge
        self.edge_map = {}        # map (origin, dest) -> half-edge
        self.face_layer = []
        self.layer = 0

    def load_obj(self, filepath):
        positions = []
        face_indices = []
        with open(filepath, 'r') as f:
            for line in f:
                # remove comments
                line = line.split('#', 1)[0].strip()
                if not line:
                    continue
                parts = line.split()
                if parts[0] == 'v' and len(parts) >= 4:
                    x, y, z = map(float, parts[1:4])
                    positions.append((x, y, z))
                elif parts[0] == 'f' and len(parts) >= 4:
                    idxs = []
                    for p in parts[1:]:
                        idx = p.split('/')[0] if '/' in p else p
                        idxs.append(int(idx))
                    face_indices.append(idxs)

        # Create vertices
        self.vertices = [Vertex(i+1, pos) for i, pos in enumerate(positions)]

        # Build faces and half-edges
        for f_idx, idx_list in enumerate(face_indices, start=1):
            face = Face(f_idx)
            self.faces.append(face)
            self.face_layer.append(self.layer)
            n = len(idx_list)
            face_half_edges = [HalfEdge() for _ in range(n)]
            for he in face_half_edges:
                self.half_edges.append(he)
                he.face = face

            for i, he in enumerate(face_half_edges):
                origin_idx = idx_list[i]
                dest_idx = idx_list[(i+1) % n]
                v_origin = self.vertices[origin_idx-1]
                he.origin = v_origin
                if v_origin.half_edge is None:
                    v_origin.half_edge = he
                he.next = face_half_edges[(i+1) % n]

                key = (origin_idx, dest_idx)
                twin_key = (dest_idx, origin_idx)
                self.edge_map[key] = he
                if twin_key in self.edge_map:
                    twin_he = self.edge_map[twin_key]
                    he.twin = twin_he
                    twin_he.twin = he

            face.half_edge = face_half_edges[0]

    def faces_sharing_vertex(self, v_idx):
        v = self.vertices[v_idx-1]
        faces = []
        he = v.half_edge
        if not he:
            return faces
        start = he
        while True:
            faces.append(he.face)
            he = he.twin.next if he.twin else None
            if he == start or he is None:
                break
        return faces

    def edges_sharing_vertex(self, v_idx):
        v = self.vertices[v_idx-1]
        edges = []
        he = v.half_edge
        if not he:
            return edges
        start = he
        while True:
            edges.append((he.origin.idx, he.next.origin.idx))
            he = he.twin.next if he.twin else None
            if he == start or he is None:
                break
        return edges

    def faces_sharing_edge(self, origin_idx, dest_idx):
        he = self.edge_map.get((origin_idx, dest_idx))
        if not he:
            return []
        faces = [he.face]
        if he.twin:
            faces.append(he.twin.face)
        return faces

    def edges_sharing_face(self, f_idx):
        face = self.faces[f_idx-1]
        edges = []
        he = face.half_edge
        start = he
        while True:
            edges.append((he.origin.idx, he.next.origin.idx))
            he = he.next
            if he == start:
                break
        return edges

    def adjacent_faces(self, f_idx):
        face = self.faces[f_idx-1]
        neighbors = []
        he = face.half_edge
        start = he
        while True:
            if he.twin:
                neighbors.append(he.twin.face)
            he = he.next
            if he == start:
                break
        return neighbors

    def summary(self):
        num_he = len(self.half_edges)
        # Unique undirected edges
        unique = set(tuple(sorted(k)) for k in self.edge_map.keys())
        num_edges = len(unique)
        print(f"Loaded mesh with {len(self.vertices)} vertices, {len(self.faces)} faces, {num_he} half-edges ({num_edges} undirected edges).")

    
    def create_rectangle(self, positions2d):
        """
        Cria um único face quadrilateral a partir de 4 posições 2D.
        positions2d: lista/tupla de 4 tuplas (x, y), na ordem:
                      [BL, BR, TR, TL] (bottom-left, bottom-right, top-right, top-left)
        Todas as novas vértices terão z = 0.
        """
        self.layer+=1
        if len(positions2d) != 4:
            raise ValueError("É preciso exatamente 4 posições para definir o retângulo.")

        # 1) Criar vértices
        start_idx = len(self.vertices) + 1
        new_verts = []
        for i, (x, y) in enumerate(positions2d):
            v = Vertex(start_idx + i, (x, y, 0.0))
            self.vertices.append(v)
            new_verts.append(v)

        # 2) Criar um novo face
        f_idx = len(self.faces) + 1
        face = Face(f_idx)
        self.faces.append(face)
        self.face_layer.append(self.layer)

        # 3) Criar 4 half-edges e vinculá-los ao face
        face_hes = [HalfEdge() for _ in range(4)]
        for he in face_hes:
            he.face = face
            self.half_edges.append(he)

        # 4) Configurar origin, next e atualizar vertex.half_edge
        for i, he in enumerate(face_hes):
            v_origin = new_verts[i]
            v_dest   = new_verts[(i+1) % 4]
            he.origin = v_origin
            he.next   = face_hes[(i+1) % 4]
            # se o vértice ainda não tinha um half_edge, aponta para este:
            if v_origin.half_edge is None:
                v_origin.half_edge = he

            # registrar no edge_map
            key = (v_origin.idx, v_dest.idx)
            twin_key = (v_dest.idx, v_origin.idx)
            self.edge_map[key] = he
            # conectar twin se já existir o oposto
            if twin_key in self.edge_map:
                twin_he = self.edge_map[twin_key]
                he.twin = twin_he
                twin_he.twin = he

        face.half_edge = face_hes[0]

        return face
    

    def create_triangle(self, positions2d):
        """
        Cria um único face triangular a partir de 3 posições 2D.
        positions2d: lista/tupla de 3 tuplas (x, y).
        Todas as novas vértices terão z = 0.
        """
        self.layer += 1
        if len(positions2d) != 3:
            raise ValueError("É preciso exatamente 3 posições para definir o triângulo.")

        # 1) Criar vértices
        start_idx = len(self.vertices) + 1
        new_verts = []
        for i, (x, y) in enumerate(positions2d):
            v = Vertex(start_idx + i, (x, y, 0.0))
            self.vertices.append(v)
            new_verts.append(v)

        # 2) Criar um novo face
        f_idx = len(self.faces) + 1
        face = Face(f_idx)
        self.faces.append(face)
        self.face_layer.append(self.layer)

        # 3) Criar 3 half-edges e vinculá-los ao face
        face_hes = [HalfEdge() for _ in range(3)]
        for he in face_hes:
            he.face = face
            self.half_edges.append(he)

        # 4) Configurar origin, next e atualizar vertex.half_edge
        for i, he in enumerate(face_hes):
            v_origin = new_verts[i]
            v_dest   = new_verts[(i+1) % 3]
            he.origin = v_origin
            he.next   = face_hes[(i+1) % 3]
            if v_origin.half_edge is None:
                v_origin.half_edge = he

            key = (v_origin.idx, v_dest.idx)
            twin_key = (v_dest.idx, v_origin.idx)
            self.edge_map[key] = he
            if twin_key in self.edge_map:
                twin_he = self.edge_map[twin_key]
                he.twin = twin_he
                twin_he.twin = he

        face.half_edge = face_hes[0]
        return face
    
    def pick_face(self, p_model):
        """
        Retorna a Face que contém p_model, ou None se não encontrar.
        """
        # extrai só x,y do ponto clicado (supondo p_model = (x, y, z))
        x_click, y_click, _ = p_model[0], p_model[1], 0

        hits = []
        # percorre faces e camadas juntas
        for face, layer in zip(self.faces, self.face_layer):
            # coleta os vértices 2D da face
            pts = []
            he = face.half_edge
            start = he
            while True:
                x, y, _ = he.origin.position
                pts.append((x, y))
                he = he.next
                if he == start:
                    break

            # testa colisão
            if point_in_poly((x_click, y_click), pts):
                hits.append((face, layer))

        if not hits:
            print("Nenhuma face encontrada nesse ponto.")
            return None

        # retorna a face de maior layer
        faceR, _ = max(hits, key=lambda fl: fl[1])
        print(f"faces testadas: {hits}")
        print(f"face retornada: {faceR}")
        return faceR

    def create_polygon(self, positions2d):
        """
        Cria um único face poligonal (n vértices) a partir de posições 2D fornecidas
        na ordem de clique do usuário. Fecha o polígono usando o último ponto igual ao primeiro.
        positions2d: lista de tuplas (x, y), com pelo menos 4 entradas se incluir repetição
        do primeiro ponto no final (ou n>=3 sem repetição).
        """
        # Remove possível repetição final do primeiro ponto para processar corretamente
        pts = list(positions2d)
        if len(pts) >= 2 and pts[0] == pts[-1]:
            pts = pts[:-1]
        n = len(pts)
        if n < 3:
            raise ValueError("É preciso pelo menos 3 pontos para definir um polígono.")

        # Atualiza camada
        self.layer += 1

        # 1) Criar vértices
        start_idx = len(self.vertices) + 1
        new_verts = []
        for i, (x, y) in enumerate(pts):
            v = Vertex(start_idx + i, (x, y, 0.0))
            self.vertices.append(v)
            new_verts.append(v)

        # 2) Criar face
        f_idx = len(self.faces) + 1
        face = Face(f_idx)
        self.faces.append(face)
        self.face_layer.append(self.layer)

        # 3) Criar half-edges
        face_hes = [HalfEdge() for _ in range(n)]
        for he in face_hes:
            he.face = face
            self.half_edges.append(he)

        # 4) Vincular origins, next e twins
        for i, he in enumerate(face_hes):
            v_origin = new_verts[i]
            v_dest = new_verts[(i + 1) % n]
            he.origin = v_origin
            he.next = face_hes[(i + 1) % n]
            # define half_edge do vértice se não houver ainda
            if v_origin.half_edge is None:
                v_origin.half_edge = he

            # registra no mapa de arestas e conecta twins
            key = (v_origin.idx, v_dest.idx)
            twin_key = (v_dest.idx, v_origin.idx)
            self.edge_map[key] = he
            if twin_key in self.edge_map:
                twin_he = self.edge_map[twin_key]
                he.twin = twin_he
                twin_he.twin = he

        # 5) Aresta inicial do face
        face.half_edge = face_hes[0]
        return face

    def export_obj(self, filepath: str):
        """
        Exporta a malha atual para um arquivo .obj.
        Cada vértice é escrito como 'v x y z'.
        Cada face é escrito como 'f i j k ...', indexando vértices a partir de 1.
        """
        # Mapeia cada vértice ao seu índice no arquivo OBJ (1-based)
        with open(filepath, 'w') as f:
            # 1) Escreve comentários e cabeçalho
            f.write(f"# OBJ export generated by HalfEdgeMesh\n")

            # 2) Lista de vértices
            # Supondo self.vertices é lista de Vertex com .position = (x,y,z)
            for v in self.vertices:
                x, y, z = v.position
                f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")

            # 3) Lista de faces
            # Cada face: percorre os half-edges em volta até voltar ao inicial
            for face in self.faces:
                # coleta vértices em ordem cíclica
                verts_idx = []
                start_he = face.half_edge
                he = start_he
                while True:
                    # origin.idx deve corresponder à posição em self.vertices
                    # Se necessário, ajusta: supõe que idx é 1-based
                    verts_idx.append(he.origin.idx)
                    he = he.next
                    if he == start_he:
                        break
                # escreve a face: f idx1 idx2 idx3 ...
                # OBJ espera índices 1-based
                idxs = " ".join(str(i) for i in verts_idx)
                f.write(f"f {idxs}\n")
        print(f"Malha exportada para {filepath}")



def point_in_poly(point, poly_pts):
    """
    Ray‑casting algorithm para polígono convexo ou côncavo.
    point: (x,y)
    poly_pts: lista de (x,y) dos vértices em ordem.
    Retorna True se point estiver dentro.
    """
    x, y = point
    inside = False
    n = len(poly_pts)
    for i in range(n):
        x0, y0 = poly_pts[i]
        x1, y1 = poly_pts[(i+1) % n]
        # verifica cruzamento da aresta com o semi‑eixo positivo em Y
        if ((y0 > y) != (y1 > y)) and \
           (x < (x1 - x0) * (y - y0) / (y1 - y0) + x0):
            inside = not inside
    return inside




if __name__ == '__main__':
    mesh = HalfEdgeMesh()
    path = 'cube.obj'
    mesh.load_obj(path)
    mesh.summary()

    menu = '''\nEscolha uma opção:
1. Faces que compartilham um vértice
2. Arestas que compartilham um vértice
3. Faces que compartilham uma aresta
4. Arestas que compartilham uma face
5. Faces adjacentes a uma face
0. Sair\n'''
    while True:
        choice = input(menu)
        if choice == '0':
            break
        elif choice == '1':
            v = int(input("Índice do vértice: "))
            print([f.idx for f in mesh.faces_sharing_vertex(v)])
        elif choice == '2':
            v = int(input("Índice do vértice: "))
            print(mesh.edges_sharing_vertex(v))
        elif choice == '3':
            o = int(input("Origem da aresta: "))
            d = int(input("Destino da aresta: "))
            print([f.idx for f in mesh.faces_sharing_edge(o, d)])
        elif choice == '4':
            f = int(input("Índice da face: "))
            print(mesh.edges_sharing_face(f))
        elif choice == '5':
            f = int(input("Índice da face: "))
            print([nf.idx for nf in mesh.adjacent_faces(f)])
        else:
            print("Opção inválida.")




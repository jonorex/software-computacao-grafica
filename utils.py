from collections import deque

def component_from_face(mesh, start_face):
    """
    Devolve todas as faces, arestas e vértices conectados a start_face.
    """
    faces_seen = set()
    verts_seen = set()
    edges_seen = set()

    queue = deque([start_face])
    while queue:
        face = queue.popleft()
        if face in faces_seen:
            continue
        faces_seen.add(face)

        # itera half-edges do face
        he = face.half_edge
        start = he
        while True:
            # registra vértice e aresta
            verts_seen.add(he.origin)
            v0, v1 = he.origin.idx, he.next.origin.idx
            edges_seen.add(tuple(sorted((v0, v1))))

            # adiciona face vizinha pela twin
            if he.twin and he.twin.face not in faces_seen:
                queue.append(he.twin.face)

            he = he.next
            if he == start:
                break
    a = {
        'faces':    faces_seen,
        'vertices': verts_seen,
        'edges':    edges_seen
    }

    print(f"dicionário {a}")


    return {
        'faces':    faces_seen,
        'vertices': verts_seen,
        'edges':    edges_seen
    }
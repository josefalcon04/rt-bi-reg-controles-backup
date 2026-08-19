from app.servicios.bases.connection_manager import conectar_netezza
from app.servicios.embedding_service import EmbeddingService


class MemoriaService:

    # ============================================================
    # GUARDAR MEMORIA
    # ============================================================

    def guardar(
        self,
        tipo_memoria,
        alcance,
        contenido,
        categoria=None,
        confianza=0,
        utilidad=0,
        id_usuario_origen=None,
        roles=None
    ):

        conn = None
        cursor = None

        try:

            conn = conectar_netezza()
            cursor = conn.cursor()

            # ----------------------------------------------------
            # GENERAR ID
            # ----------------------------------------------------

            cursor.execute("""
                SELECT COALESCE(
                    MAX(ID_MEMORIA),
                    0
                ) + 1
                FROM CONTROL_MAKO..TABLERO_MEMORIA
            """)

            id_memoria = cursor.fetchone()[0]

            # ----------------------------------------------------
            # INSERTAR MEMORIA
            # ----------------------------------------------------

            cursor.execute("""
                INSERT INTO CONTROL_MAKO..TABLERO_MEMORIA
                (
                    ID_MEMORIA,
                    TIPO_MEMORIA,
                    ALCANCE,
                    CONTENIDO,
                    CATEGORIA,
                    CONFIANZA,
                    UTILIDAD,
                    ID_USUARIO_ORIGEN,
                    ESTADO
                )
                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    'P'
                )
            """, (
                id_memoria,
                tipo_memoria,
                alcance,
                contenido,
                categoria,
                confianza,
                utilidad,
                id_usuario_origen
            ))

            # ----------------------------------------------------
            # ASIGNAR ROLES
            # ----------------------------------------------------

            if (
                alcance == "ROL"
                and roles
            ):

                for id_rol in roles:

                    cursor.execute("""
                        INSERT INTO
                            CONTROL_MAKO..TABLERO_MEMORIA_ROLES
                        (
                            ID_MEMORIA,
                            ID_ROL
                        )
                        VALUES
                        (
                            ?,
                            ?
                        )
                    """, (
                        id_memoria,
                        id_rol
                    ))

            conn.commit()

            print(
                "=========================================="
            )

            print(
                "[MEMORIA] Memoria guardada"
            )

            print(
                "ID:",
                id_memoria
            )

            print(
                "TIPO:",
                tipo_memoria
            )

            print(
                "ALCANCE:",
                alcance
            )

            print(
                "ESTADO: PENDIENTE"
            )

            print(
                "=========================================="
            )

            # ==========================================
            # GENERAR EMBEDDING
            # ==========================================

            try:

                self.guardar_embedding(
                    id_memoria,
                    contenido
                )

            except Exception as e:

                print(
                    f"[MEMORIA] Advertencia: "
                    f"no se pudo generar embedding: {e}"
                )

            return id_memoria

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "[ERROR MEMORIA GUARDAR]:",
                str(e)
            )

            return None

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()


    # ============================================================
    # APROBAR MEMORIA
    # ============================================================

    def aprobar(
        self,
        id_memoria,
        id_usuario_validacion
    ):

        conn = None
        cursor = None

        try:

            conn = conectar_netezza()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE CONTROL_MAKO..TABLERO_MEMORIA

                SET
                    ESTADO = 'A',
                    ID_USUARIO_VALIDACION = ?,
                    FECHA_VALIDACION =
                        CURRENT_TIMESTAMP

                WHERE ID_MEMORIA = ?
                  AND ESTADO = 'P'
            """, (
                id_usuario_validacion,
                id_memoria
            ))

            conn.commit()

            print(
                "[MEMORIA] Memoria aprobada:",
                id_memoria
            )

            return True

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "[ERROR MEMORIA APROBAR]:",
                str(e)
            )

            return False

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()


    # ============================================================
    # RECHAZAR MEMORIA
    # ============================================================

    def rechazar(
        self,
        id_memoria,
        id_usuario_validacion,
        observacion=None
    ):

        conn = None
        cursor = None

        try:

            conn = conectar_netezza()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE CONTROL_MAKO..TABLERO_MEMORIA

                SET
                    ESTADO = 'R',
                    ID_USUARIO_VALIDACION = ?,
                    FECHA_VALIDACION =
                        CURRENT_TIMESTAMP,
                    OBSERVACION_VALIDACION = ?

                WHERE ID_MEMORIA = ?
                  AND ESTADO = 'P'
            """, (
                id_usuario_validacion,
                observacion,
                id_memoria
            ))

            conn.commit()

            print(
                "[MEMORIA] Memoria rechazada:",
                id_memoria
            )

            return True

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "[ERROR MEMORIA RECHAZAR]:",
                str(e)
            )

            return False

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()


    # ============================================================
    # DESACTIVAR MEMORIA
    # ============================================================

    def desactivar(
        self,
        id_memoria
    ):

        conn = None
        cursor = None

        try:

            conn = conectar_netezza()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE CONTROL_MAKO..TABLERO_MEMORIA

                SET
                    ESTADO = 'I'

                WHERE ID_MEMORIA = ?
                  AND ESTADO = 'A'
            """, (
                id_memoria,
            ))

            conn.commit()

            print(
                "[MEMORIA] Memoria desactivada:",
                id_memoria
            )

            return True

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "[ERROR MEMORIA DESACTIVAR]:",
                str(e)
            )

            return False

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()


    # ============================================================
    # BUSCAR MEMORIAS DISPONIBLES PARA EL USUARIO
    # ============================================================

    def buscar(
        self,
        id_usuario,
        pregunta=None
    ):

        conn = None
        cursor = None

        try:

            conn = conectar_netezza()
            cursor = conn.cursor()

            # ----------------------------------------------------
            # OBTENER ROL DEL USUARIO
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    ID_ROL
                FROM CONTROL_MAKO..TABLERO_USUARIOS
                WHERE ID_USUARIO = ?
                  AND ESTADO = 'A'
            """, (
                id_usuario,
            ))

            fila_usuario = cursor.fetchone()

            if not fila_usuario:

                print(
                    "[MEMORIA] Usuario no encontrado:",
                    id_usuario
                )

                return []

            id_rol = fila_usuario[0]

            # ----------------------------------------------------
            # BUSCAR MEMORIAS PERMITIDAS
            #
            # GLOBAL:
            #   todos los usuarios
            #
            # USUARIO:
            #   solamente el propietario
            #
            # ROL:
            #   solamente el rol asignado
            # ----------------------------------------------------

            sql = """
                SELECT

                    M.ID_MEMORIA,
                    M.TIPO_MEMORIA,
                    M.ALCANCE,
                    M.CONTENIDO,
                    M.CATEGORIA,
                    M.CONFIANZA,
                    M.UTILIDAD,
                    M.ID_USUARIO_ORIGEN,
                    M.VECES_USADA,
                    M.FECHA_CREACION

                FROM CONTROL_MAKO..TABLERO_MEMORIA M

                LEFT JOIN
                    CONTROL_MAKO..TABLERO_MEMORIA_ROLES MR

                    ON
                        M.ID_MEMORIA = MR.ID_MEMORIA
                        AND
                        MR.ID_ROL = ?

                WHERE
                    M.ESTADO = 'A'

                    AND

                    (
                        M.ALCANCE = 'GLOBAL'

                        OR

                        (
                            M.ALCANCE = 'USUARIO'
                            AND
                            M.ID_USUARIO_ORIGEN = ?
                        )

                        OR

                        (
                            M.ALCANCE = 'ROL'
                            AND
                            MR.ID_MEMORIA IS NOT NULL
                        )
                    )

                ORDER BY
                    M.UTILIDAD DESC,
                    M.CONFIANZA DESC,
                    M.FECHA_CREACION DESC
            """

            cursor.execute(
                sql,
                (
                    id_rol,
                    id_usuario
                )
            )

            filas = cursor.fetchall()

            # ----------------------------------------------------
            # CONVERTIR RESULTADO
            # ----------------------------------------------------

            memorias = []

            ids_procesados = set()

            for fila in filas:

                id_memoria = fila[0]

                # Evitar duplicados

                if id_memoria in ids_procesados:

                    continue

                ids_procesados.add(
                    id_memoria
                )

                memorias.append({

                    "id_memoria":
                        fila[0],

                    "tipo_memoria":
                        fila[1],

                    "alcance":
                        fila[2],

                    "contenido":
                        fila[3],

                    "categoria":
                        fila[4],

                    "confianza":
                        float(
                            fila[5]
                        )
                        if fila[5] is not None
                        else 0,

                    "utilidad":
                        float(
                            fila[6]
                        )
                        if fila[6] is not None
                        else 0,

                    "id_usuario_origen":
                        fila[7],

                    "veces_usada":
                        fila[8],

                    "fecha_creacion":
                        fila[9]

                })

            # ----------------------------------------------------
            # LOG DE CONTROL
            # ----------------------------------------------------

            print(
                "=========================================="
            )

            print(
                "[MEMORIA] BUSQUEDA"
            )

            print(
                "ID_USUARIO:",
                id_usuario
            )

            print(
                "ID_ROL:",
                id_rol
            )

            print(
                "MEMORIAS DISPONIBLES:",
                len(memorias)
            )

            for memoria in memorias:

                print(
                    "MEMORIA:",
                    memoria["id_memoria"],
                    "| ALCANCE:",
                    memoria["alcance"],
                    "| CATEGORIA:",
                    memoria["categoria"]
                )

            print(
                "=========================================="
            )

            return memorias

        except Exception as e:

            print(
                "=========================================="
            )

            print(
                "[ERROR MEMORIA BUSCAR]:",
                str(e)
            )

            print(
                "=========================================="
            )

            return []

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()

        # ============================================================
    # BUSCAR MEMORIAS RELEVANTES
    # ============================================================

    def buscar_relevantes(
        self,
        id_usuario,
        pregunta,
        limite=5
    ):

        # --------------------------------------------------------
        # Primero obtenemos solamente las memorias que el usuario
        # tiene permitido consultar.
        #
        # IMPORTANTE:
        # El RBAC se mantiene antes de calcular relevancia.
        # Una memoria no autorizada nunca entra al ranking.
        # --------------------------------------------------------

        memorias = self.buscar(
            id_usuario=id_usuario,
            pregunta=pregunta
        )

        if not memorias:
            return []

        if not pregunta or not pregunta.strip():
            return []

        # --------------------------------------------------------
        # SERVICIO DE EMBEDDINGS
        # --------------------------------------------------------

        embedding_service = EmbeddingService()

        # --------------------------------------------------------
        # NORMALIZAR PREGUNTA
        # --------------------------------------------------------

        import re

        palabras = re.findall(
            r"\w+",
            pregunta.lower()
        )

        # --------------------------------------------------------
        # PALABRAS QUE NO APORTAN RELEVANCIA
        # --------------------------------------------------------

        stopwords = {
            "el",
            "la",
            "los",
            "las",
            "un",
            "una",
            "unos",
            "unas",
            "de",
            "del",
            "al",
            "en",
            "por",
            "para",
            "con",
            "sin",
            "que",
            "como",
            "qué",
            "cómo",
            "es",
            "son",
            "tiene",
            "tienen",
            "hay",
            "me",
            "se",
            "y",
            "o",
            "a",
            "actualmente"
        }

        palabras = [
            palabra
            for palabra in palabras
            if palabra not in stopwords
            and len(palabra) > 2
        ]

        # --------------------------------------------------------
        # EMBEDDING DE LA PREGUNTA
        # --------------------------------------------------------

        embedding_pregunta = embedding_service.generar(
            pregunta
        )

        resultados = []

        for memoria in memorias:

            contenido = (
                memoria.get(
                    "contenido",
                    ""
                )
                or ""
            ).strip()

            categoria = (
                memoria.get(
                    "categoria",
                    ""
                )
                or ""
            ).strip()

            texto = (
                contenido
                + " "
                + categoria
            ).lower()

            # ----------------------------------------------------
            # COINCIDENCIAS LÉXICAS
            # ----------------------------------------------------

            coincidencias = 0

            for palabra in palabras:

                if palabra in texto:
                    coincidencias += 1

            if palabras:
                porcentaje_coincidencia = (
                    coincidencias / len(palabras)
                )
            else:
                porcentaje_coincidencia = 0.0

            # ----------------------------------------------------
            # SIMILITUD SEMÁNTICA
            #
            # Si Ollama/embedding falla, conservamos la lógica
            # léxica como fallback para no romper la memoria.
            # ----------------------------------------------------

            similitud_semantica = 0.0

            if embedding_pregunta:

                try:

                    embedding_memoria = (
                        embedding_service.generar(
                            contenido
                        )
                    )

                    if embedding_memoria:

                        import numpy as np

                        a = np.array(
                            embedding_pregunta,
                            dtype=float
                        )

                        b = np.array(
                            embedding_memoria,
                            dtype=float
                        )

                        norma_a = np.linalg.norm(a)
                        norma_b = np.linalg.norm(b)

                        if (
                            norma_a > 0
                            and norma_b > 0
                        ):

                            similitud_semantica = (
                                float(
                                    np.dot(a, b)
                                    / (
                                        norma_a
                                        * norma_b
                                    )
                                )
                            )

                except Exception as e:

                    print(
                        "[MEMORIA] Error calculando "
                        f"similitud semántica: {str(e)}"
                    )

            # ----------------------------------------------------
            # SCORE FINAL
            #
            # 70%  -> similitud semántica
            # 15%  -> coincidencias léxicas
            # 7.5% -> confianza
            # 7.5% -> utilidad
            #
            # La semántica es ahora el factor principal.
            # ----------------------------------------------------

            score = (
                similitud_semantica * 0.70
                +
                porcentaje_coincidencia * 0.15
                +
                memoria["confianza"] * 0.075
                +
                memoria["utilidad"] * 0.075
            )

            memoria_resultado = memoria.copy()

            memoria_resultado[
                "score_relevancia"
            ] = round(
                score,
                4
            )

            memoria_resultado[
                "similitud_semantica"
            ] = round(
                similitud_semantica,
                4
            )

            memoria_resultado[
                "porcentaje_coincidencia"
            ] = round(
                porcentaje_coincidencia,
                4
            )

            memoria_resultado[
                "coincidencias"
            ] = coincidencias

            # ----------------------------------------------------
            # UMBRAL MÍNIMO
            #
            # 0.35 es solamente un filtro inicial.
            # Lo podremos calibrar con más pruebas reales.
            # ----------------------------------------------------

            if score < 0.35:
                continue

            resultados.append(
                memoria_resultado
            )

        # --------------------------------------------------------
        # ORDENAR POR RELEVANCIA
        # --------------------------------------------------------

        resultados.sort(
            key=lambda x: (
                x["score_relevancia"],
                x["similitud_semantica"],
                x["confianza"],
                x["utilidad"]
            ),
            reverse=True
        )

        # --------------------------------------------------------
        # TOP N
        # --------------------------------------------------------

        resultados = resultados[
            :limite
        ]

        # --------------------------------------------------------
        # LOG DE CONTROL
        # --------------------------------------------------------

        print(
            "=========================================="
        )

        print(
            "[MEMORIA] BUSQUEDA RELEVANTE"
        )

        print(
            "ID_USUARIO:",
            id_usuario
        )

        print(
            "PREGUNTA:",
            pregunta
        )

        print(
            "MEMORIAS RELEVANTES:",
            len(resultados)
        )

        for memoria in resultados:

            print(
                "MEMORIA:",
                memoria["id_memoria"],
                "| SCORE:",
                memoria["score_relevancia"],
                "| SEMANTICA:",
                memoria["similitud_semantica"],
                "| COINCIDENCIAS:",
                memoria["coincidencias"]
            )

        print(
            "=========================================="
        )

        return resultados

    # ============================================================
    # CONSTRUIR CONTEXTO PARA LA IA
    # ============================================================

    def construir_contexto(
        self,
        memorias
    ):

        if not memorias:

            return ""

        bloques = []

        for memoria in memorias:

            contenido = (
                memoria.get(
                    "contenido",
                    ""
                )
                or ""
            ).strip()

            if not contenido:

                continue

            bloques.append(
                "[MEMORIA]\n"
                + contenido
                + "\n[/MEMORIA]"
            )

        return "\n\n".join(
            bloques
        )

    def guardar_embedding(self, id_memoria, contenido):
        """
        Genera y guarda el embedding de una memoria.
        """

        import json

        conn = None
        cursor = None

        try:

            # -----------------------------------------
            # GENERAR EMBEDDING
            # -----------------------------------------

            from app.servicios.embedding_service import EmbeddingService

            embedding_service = EmbeddingService()

            vector = embedding_service.generar(
                contenido
            )

            if not vector:
                print("[MEMORIA] No se pudo generar embedding")
                return False

            dimension = len(vector)

            vector_json = json.dumps(
                vector,
                separators=(",", ":")
            )

            print(
                f"[MEMORIA] Embedding generado | "
                f"ID: {id_memoria} | "
                f"DIMENSION: {dimension}"
            )

            # -----------------------------------------
            # CONEXIÓN
            # -----------------------------------------

            conn = conectar_netezza()
            cursor = conn.cursor()

            # -----------------------------------------
            # INSERT / UPDATE
            # -----------------------------------------

            cursor.execute(
                """
                DELETE FROM CONTROL_MAKO..TABLERO_MEMORIA_EMBEDDING
                WHERE ID_MEMORIA = ?
                """,
                (id_memoria,)
            )

            cursor.execute(
                """
                INSERT INTO CONTROL_MAKO..TABLERO_MEMORIA_EMBEDDING
                (
                    ID_MEMORIA,
                    MODELO,
                    DIMENSION,
                    VECTOR
                )
                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?
                )
                """,
                (
                    id_memoria,
                    embedding_service.MODELO,
                    dimension,
                    vector_json
                )
            )

            conn.commit()

            print(
                f"[MEMORIA] Embedding guardado | "
                f"ID: {id_memoria}"
            )

            return True

        except Exception as e:

            print(
                f"[MEMORIA] Error guardando embedding: {e}"
            )

            if conn:
                try:
                    conn.rollback()
                except:
                    pass

            return False

        finally:

            if cursor:
                try:
                    cursor.close()
                except:
                    pass

            if conn:
                try:
                    conn.close()
                except:
                    pass



    def buscar_memorias_semanticas(self, pregunta, limite=5):
        
        """
        Busca memorias semánticamente similares a una pregunta.

        Flujo:
            pregunta
                ↓
            EmbeddingService
                ↓
            embeddings almacenados en BD
                ↓
            similitud coseno
                ↓
            ranking
        """
        UMBRAL_SIMILITUD = 0.50
        
        import json
        import numpy as np

        conn = None
        cursor = None

        try:

            # ==========================================
            # GENERAR EMBEDDING DE LA PREGUNTA
            # ==========================================

            from app.servicios.embedding_service import EmbeddingService

            embedding_service = EmbeddingService()

            vector_pregunta = embedding_service.generar(
                pregunta
            )

            if not vector_pregunta:

                print(
                    "[MEMORIA] No se pudo generar embedding "
                    "de la pregunta"
                )

                return []

            vector_pregunta = np.array(
                vector_pregunta,
                dtype=float
            )

            # ==========================================
            # CONEXIÓN A NETEZZA
            # ==========================================

            conn = conectar_netezza()
            cursor = conn.cursor()

            # ==========================================
            # OBTENER EMBEDDINGS
            # ==========================================

            cursor.execute(
                """
                SELECT
                    E.ID_MEMORIA,
                    E.MODELO,
                    E.DIMENSION,
                    E.VECTOR,
                    M.TIPO_MEMORIA,
                    M.ALCANCE,
                    M.CONTENIDO,
                    M.CATEGORIA,
                    M.CONFIANZA,
                    M.UTILIDAD,
                    M.ID_USUARIO_ORIGEN,
                    M.VECES_USADA,
                    M.FECHA_CREACION,
                    M.ESTADO
                FROM CONTROL_MAKO..TABLERO_MEMORIA_EMBEDDING E
                INNER JOIN CONTROL_MAKO..TABLERO_MEMORIA M
                    ON E.ID_MEMORIA = M.ID_MEMORIA
                WHERE M.ESTADO = 'A'
                """
            )

            filas = cursor.fetchall()

            resultados = []

            # ==========================================
            # CALCULAR SIMILITUD
            # ==========================================

            for fila in filas:

                (
                    id_memoria,
                    modelo,
                    dimension,
                    vector_json,
                    tipo_memoria,
                    alcance,
                    contenido,
                    categoria,
                    confianza,
                    utilidad,
                    id_usuario_origen,
                    veces_usada,
                    fecha_creacion,
                    estado
                ) = fila

                try:

                    vector_memoria = np.array(
                        json.loads(vector_json),
                        dtype=float
                    )

                    # ----------------------------------
                    # Validar dimensiones
                    # ----------------------------------

                    if len(vector_memoria) != len(vector_pregunta):

                        print(
                            f"[MEMORIA] Dimensión incorrecta "
                            f"ID={id_memoria}: "
                            f"{len(vector_memoria)}"
                        )

                        continue

                    # ----------------------------------
                    # Cosine similarity
                    # ----------------------------------

                    denominador = (
                        np.linalg.norm(vector_pregunta)
                        *
                        np.linalg.norm(vector_memoria)
                    )

                    if denominador == 0:

                        continue

                    similitud = (
                        np.dot(
                            vector_pregunta,
                            vector_memoria
                        )
                        /
                        denominador
                    )

                    if similitud < UMBRAL_SIMILITUD:

                        print(
                            f"[MEMORIA] Descartada por baja similitud | "
                            f"ID={id_memoria} | "
                            f"SIM={round(float(similitud), 4)}"
                        )

                        continue

                    resultados.append(
                        {
                            "id_memoria": id_memoria,
                            "tipo_memoria": tipo_memoria,
                            "alcance": alcance,
                            "contenido": contenido,
                            "categoria": categoria,
                            "confianza": float(confianza)
                            if confianza is not None
                            else 0.0,
                            "utilidad": float(utilidad)
                            if utilidad is not None
                            else 0.0,
                            "id_usuario_origen": id_usuario_origen,
                            "veces_usada": veces_usada,
                            "fecha_creacion": str(fecha_creacion)
                            if fecha_creacion
                            else None,
                            "estado": estado,
                            "similitud_semantica": round(
                                float(similitud),
                                4
                            )
                        }
                    )

                except Exception as e:

                    print(
                        f"[MEMORIA] Error procesando "
                        f"embedding ID={id_memoria}: {e}"
                    )

            # ==========================================
            # ORDENAR
            # ==========================================

            resultados.sort(
                key=lambda x: x["similitud_semantica"],
                reverse=True
            )

            resultados = resultados[:limite]

            print(
                f"[MEMORIA] Búsqueda semántica: "
                f"{len(resultados)} resultados"
            )

            for resultado in resultados:

                print(
                    f"[MEMORIA] "
                    f"ID={resultado['id_memoria']} | "
                    f"SIM={resultado['similitud_semantica']} | "
                    f"CONTENIDO={resultado['contenido']}"
                )

            return resultados

        except Exception as e:

            print(
                f"[MEMORIA] Error en búsqueda semántica: {e}"
            )

            return []

        finally:

            if cursor:

                try:
                    cursor.close()
                except:
                    pass

            if conn:

                try:
                    conn.close()
                except:
                    pass                    

    def evaluar_memoria(self, memoria):
        """
        Evalúa si una memoria es suficientemente relevante
        y confiable para utilizarse como respuesta directa.

        Fórmula:

            score_final =
                similitud_semantica * 0.60
                + confianza * 0.25
                + utilidad * 0.15
        """

        try:

            # ==========================================
            # VALIDAR MEMORIA
            # ==========================================

            if not memoria:

                return {
                    "aprobada": False,
                    "motivo": "No existe memoria"
                }

            # ==========================================
            # ESTADO
            # ==========================================

            estado = memoria.get("estado")

            if estado != "A":

                return {
                    "aprobada": False,
                    "motivo": "Memoria no aprobada",
                    "estado": estado
                }

            # ==========================================
            # OBTENER VALORES
            # ==========================================

            similitud = float(
                memoria.get(
                    "similitud_semantica",
                    0
                )
            )

            confianza = float(
                memoria.get(
                    "confianza",
                    0
                )
            )

            utilidad = float(
                memoria.get(
                    "utilidad",
                    0
                )
            )

            # ==========================================
            # CALCULAR SCORE
            # ==========================================

            score_final = (
                (similitud * 0.60)
                +
                (confianza * 0.25)
                +
                (utilidad * 0.15)
            )

            score_final = round(
                score_final,
                4
            )

            # ==========================================
            # UMBRAL
            # ==========================================

            UMBRAL = 0.50

            aprobada = (
                score_final >= UMBRAL
            )

            # ==========================================
            # RESULTADO
            # ==========================================

            resultado = {
                "aprobada": aprobada,
                "score_final": score_final,
                "umbral": UMBRAL,
                "similitud_semantica": similitud,
                "confianza": confianza,
                "utilidad": utilidad,
                "id_memoria": memoria.get(
                    "id_memoria"
                ),
                "contenido": memoria.get(
                    "contenido"
                )
            }

            print(
                "[MEMORIA] Evaluación:"
            )

            print(
                f"ID: {resultado['id_memoria']}"
            )

            print(
                f"Similitud: {similitud}"
            )

            print(
                f"Confianza: {confianza}"
            )

            print(
                f"Utilidad: {utilidad}"
            )

            print(
                f"Score final: {score_final}"
            )

            print(
                f"Umbral: {UMBRAL}"
            )

            print(
                f"Respuesta directa: {aprobada}"
            )

            return resultado

        except Exception as e:

            print(
                f"[MEMORIA] Error evaluando memoria: {e}"
            )

            return {
                "aprobada": False,
                "motivo": str(e)
            }                    
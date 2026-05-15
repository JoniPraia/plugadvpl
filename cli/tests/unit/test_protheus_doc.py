"""Tests do extrator de blocos Protheus.doc (Universo 3 / Feature C v0.4.2)."""
from __future__ import annotations

from plugadvpl.parsing.protheus_doc import (
    extract_protheus_docs,
    infer_module,
)


# --- Block parsing --------------------------------------------------------


class TestBlockParsing:
    def test_minimal_block(self) -> None:
        """Bloco mínimo: abertura + fechamento, sem tags."""
        src = (
            '/*/{Protheus.doc} MinhaFn\n'
            'Resumo livre.\n'
            '/*/\n'
            'User Function MinhaFn()\n'
            'Return\n'
        )
        docs = extract_protheus_docs(src)
        assert len(docs) == 1
        d = docs[0]
        assert d["funcao_id"] == "MinhaFn"
        assert "Resumo livre" in (d["summary"] or "")
        assert d["linha_bloco_inicio"] == 1

    def test_block_with_id_method_double_colon(self) -> None:
        """Method de classe usa Classe::Metodo no <id>."""
        src = (
            '/*/{Protheus.doc} TQuad::new\n'
            'Construtor.\n'
            '@type method\n'
            '/*/\n'
        )
        docs = extract_protheus_docs(src)
        assert len(docs) == 1
        assert docs[0]["funcao_id"] == "TQuad::new"
        assert docs[0]["tipo"] == "method"

    def test_two_blocks_in_same_source(self) -> None:
        """Dois blocos seguidos."""
        src = (
            '/*/{Protheus.doc} FnA\nA.\n/*/\n'
            'User Function FnA()\nReturn\n'
            '/*/{Protheus.doc} FnB\nB.\n/*/\n'
            'User Function FnB()\nReturn\n'
        )
        docs = extract_protheus_docs(src)
        assert len(docs) == 2
        ids = sorted(d["funcao_id"] for d in docs)
        assert ids == ["FnA", "FnB"]

    def test_linha_funcao_resolved_after_close(self) -> None:
        """linha_funcao = linha da próxima decl após /*/ fechamento."""
        src = (
            '/*/{Protheus.doc} MinhaFn\n'  # linha 1
            'Resumo.\n'                     # linha 2
            '/*/\n'                         # linha 3
            'User Function MinhaFn()\n'     # linha 4
            'Return\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["linha_bloco_inicio"] == 1
        assert d["linha_bloco_fim"] == 3
        assert d["linha_funcao"] == 4

    def test_block_without_id(self) -> None:
        """Bloco sem <id> — funcao_id=None, ainda extrai."""
        src = '/*/{Protheus.doc}\nSem id.\n/*/\n'
        docs = extract_protheus_docs(src)
        assert len(docs) == 1
        assert docs[0]["funcao_id"] is None


# --- Tag extraction -------------------------------------------------------


class TestTagExtraction:
    def test_full_canonical_block(self) -> None:
        """Bloco canônico com 9 tags principais."""
        src = (
            '/*/{Protheus.doc} MT460FIM\n'
            'Ponto de Entrada apos faturamento.\n'
            'Envia ao Kafka.\n'
            '@type user function\n'
            '@author Fernando Vernier\n'
            '@since 18/10/2025\n'
            '@version 2.0\n'
            '@param cNumNF, character, "Numero da NF"\n'
            '@return logical, ".T. se sucesso"\n'
            '@example\n'
            '   Local lOk := MT460FIM("000001")\n'
            '@see OutraFn\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["tipo"] == "user function"
        assert d["author"] == "Fernando Vernier"
        assert d["since"] == "18/10/2025"
        assert d["version"] == "2.0"
        assert "Ponto de Entrada" in d["summary"]
        assert "Envia ao Kafka" in d["summary"]
        assert d["params"][0]["name"] == "cNumNF"
        assert d["params"][0]["type"] == "character"
        assert "Numero da NF" in d["params"][0]["desc"]
        assert d["params"][0]["optional"] is False
        assert d["returns"][0]["type"] == "logical"
        assert "MT460FIM" in d["examples"][0]
        assert d["see"] == ["OutraFn"]

    def test_param_optional_brackets(self) -> None:
        """[nArg2] em colchetes = optional=True."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            '@param cArg1, character, "obrigatorio"\n'
            '@param [nArg2], numeric, "opcional"\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["params"][0]["optional"] is False
        assert d["params"][0]["name"] == "cArg1"
        assert d["params"][1]["optional"] is True
        assert d["params"][1]["name"] == "nArg2"  # sem colchetes no name final

    def test_param_minimal_no_type_no_desc(self) -> None:
        """@param só com name."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            '@param cArg\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["params"][0]["name"] == "cArg"
        assert d["params"][0]["type"] is None
        assert d["params"][0]["desc"] is None

    def test_deprecated_flag_no_value(self) -> None:
        """@deprecated sem valor = flag bool."""
        src = '/*/{Protheus.doc} Fn\n@deprecated\n/*/\n'
        d = extract_protheus_docs(src)[0]
        assert d["deprecated"] is True
        assert d["deprecated_reason"] is None

    def test_deprecated_with_reason(self) -> None:
        """@deprecated <texto> = flag + reason."""
        src = '/*/{Protheus.doc} Fn\n@deprecated Use OutraFn no lugar\n/*/\n'
        d = extract_protheus_docs(src)[0]
        assert d["deprecated"] is True
        assert "OutraFn" in (d["deprecated_reason"] or "")

    def test_multi_value_tags(self) -> None:
        """@param/@example/@history acumulam em lista."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            '@param a, character, "primeiro"\n'
            '@param b, numeric, "segundo"\n'
            '@param c, logical, "terceiro"\n'
            '@example uso 1\n'
            '@example uso 2\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert len(d["params"]) == 3
        assert len(d["examples"]) == 2

    def test_table_tag_extracted(self) -> None:
        """@table acumula (cross-ref com tabelas)."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            '@table SF2\n'
            '@table SD2\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["tables"] == ["SF2", "SD2"]

    def test_unknown_tag_goes_to_raw(self) -> None:
        """Tag fora da whitelist vai pro raw_tags."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            '@meuTag valor custom\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert "meuTag" in d["raw_tags"]
        assert "valor custom" in d["raw_tags"]["meuTag"]


# --- Module inference -----------------------------------------------------


class TestModuleInference:
    def test_module_from_path_sigafat(self) -> None:
        assert infer_module("src/SIGAFAT/MT460FIM.tlpp", None) == "SIGAFAT"

    def test_module_from_path_case_insensitive(self) -> None:
        assert infer_module("src/sigafin/X.prw", None) == "SIGAFIN"

    def test_module_from_routine_prefix(self) -> None:
        """Sem path-hint mas funcao MATA410 → SIGAFAT (via catalogo execauto)."""
        assert infer_module("src/CustomA/X.prw", "MATA410") == "SIGAFAT"

    def test_module_from_routine_prefix_finA(self) -> None:
        assert infer_module("X.prw", "FINA050") == "SIGAFIN"

    def test_module_unknown_returns_none(self) -> None:
        assert infer_module("X.prw", "UDC123") is None

    def test_module_path_takes_precedence_over_prefix(self) -> None:
        """Path SIGAFIN deve vencer prefixo MATA*."""
        assert infer_module("src/SIGAFIN/MATA410.prw", "MATA410") == "SIGAFIN"

    def test_module_ambiguous_prefix_returns_none(self) -> None:
        """v0.4.3 (C5): prefix `MATA` casa rotinas de SIGAEST/SIGAFAT/SIGACOM.

        Antes: retornava SIGAEST silenciosamente (sort alfabético favorecia).
        Agora: ambiguidade real → None (não inventar). MATA999 não existe no
        catálogo e o prefixo é ambíguo entre 3 módulos.
        """
        assert infer_module("X.prw", "MATA999") is None

    def test_module_unambiguous_prefix_still_resolves(self) -> None:
        """Prefixo `FINA` mapeia 100% pra SIGAFIN — sem ambiguidade, resolve."""
        assert infer_module("X.prw", "FINA999") == "SIGAFIN"


# --- Edge cases -----------------------------------------------------------


class TestEdgeCases:
    def test_block_without_close_ignored(self) -> None:
        """Bloco sem /*/ até EOF — não casa, ignora."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            'Resumo sem fechar.\n'
            'User Function Fn()\n'
            'Return\n'
        )
        docs = extract_protheus_docs(src)
        assert docs == []

    def test_orphan_block_no_function(self) -> None:
        """Bloco sem função associada (bloco no final do arquivo)."""
        src = '/*/{Protheus.doc} Soltinho\nSem fn depois.\n/*/\n'
        docs = extract_protheus_docs(src)
        assert len(docs) == 1
        assert docs[0]["linha_funcao"] is None

    def test_orphan_block_with_distant_function_treated_as_orphan(self) -> None:
        """v0.4.3 (C4): bloco órfão NÃO deve "puxar" função muito longe.

        Cap: max 80 linhas entre /*/ fechamento e próxima decl. Acima disso
        funcao=None, linha_funcao=None (preserva sinal de "órfão" e impede
        que a função seguinte ganhe doc errada).
        """
        # 100 linhas vazias entre /*/ e a decl
        spacer = "\n".join(["// linha de filler"] * 100)
        src = (
            '/*/{Protheus.doc} Soltinho\nDoc.\n/*/\n'
            f'{spacer}\n'
            'User Function MuitoDepois()\n'
            'Return\n'
        )
        docs = extract_protheus_docs(src)
        assert len(docs) == 1
        d = docs[0]
        assert d["funcao"] is None, (
            "Esperado funcao=None pra bloco com decl 100+ linhas adiante"
        )
        assert d["linha_funcao"] is None

    def test_block_with_function_within_cap_resolves(self) -> None:
        """Sanity: decl dentro do cap (5 linhas) ainda resolve."""
        src = (
            '/*/{Protheus.doc} Fn\nDoc.\n/*/\n'
            '// 1\n// 2\n// 3\n'
            'User Function Fn()\nReturn\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["funcao"] == "Fn"
        assert d["linha_funcao"] is not None

    def test_summary_stops_at_first_tag(self) -> None:
        """Summary = linhas até primeira @tag, não inclui tags."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            'Linha 1 do summary.\n'
            'Linha 2 do summary.\n'
            '@type function\n'
            '@author X\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert "Linha 1" in d["summary"]
        assert "Linha 2" in d["summary"]
        assert "@type" not in d["summary"]

    def test_tag_continuation_multiline(self) -> None:
        """@param desc multi-linha greedy até próxima @tag."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            '@param cArg, character, "primeira linha\n'
            '   segunda linha da descricao"\n'
            '@return logical, "ok"\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert "primeira linha" in d["params"][0]["desc"]
        assert "segunda linha" in d["params"][0]["desc"]

    def test_history_structured(self) -> None:
        """@history parseia date,user,desc."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            '@history 18/10/2025, fvernier, "Refactor inicial"\n'
            '@history 20/10/2025, joao, "Bugfix"\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        assert len(d["history"]) == 2
        assert d["history"][0]["date"] == "18/10/2025"
        assert d["history"][0]["user"] == "fvernier"
        assert "Refactor" in d["history"][0]["desc"]

    def test_example_with_inline_close_marker_does_not_close(self) -> None:
        """v0.4.3 (C2): `/*/` literal em meio de comentário no @example NÃO
        deve fechar o bloco prematuramente.

        Antes (bug): regex non-greedy `(?P<body>.*?)/\\*/` casava o primeiro
        `/*/` que aparecesse — mesmo dentro do exemplo. Agora o fechamento
        exige start-of-line (padrão oficial TOTVS — `/*/` fica sozinho na
        própria linha).
        """
        src = (
            '/*/{Protheus.doc} Fn\n'
            'Doc.\n'
            '@example\n'
            '   //  /*/ exemplo dentro do comentario\n'
            '   Local x := 1\n'
            '/*/\n'
            'User Function Fn()\n'
            'Return\n'
        )
        docs = extract_protheus_docs(src)
        assert len(docs) == 1
        d = docs[0]
        assert d["funcao"] == "Fn"
        # O exemplo deve incluir o código completo (incluindo a linha do `/*/` interno).
        assert d["examples"], "esperado pelo menos 1 example"
        ex = d["examples"][0]
        assert "Local x" in ex
        assert "exemplo dentro" in ex

    def test_example_with_at_inside_code(self) -> None:
        """@example com '@' dentro do código não conta como nova tag."""
        src = (
            '/*/{Protheus.doc} Fn\n'
            '@example\n'
            '   // bloco @ inicio de comment não é tag\n'
            '   Local x := 1\n'
            '@author Joao\n'
            '/*/\n'
        )
        d = extract_protheus_docs(src)[0]
        # Author deve ser detectado (start-of-line @ é tag)
        assert d["author"] == "Joao"
        # Example deve incluir o bloco completo
        assert "Local x" in d["examples"][0]


# --- Resolution to function -----------------------------------------------


class TestFunctionResolution:
    def test_funcao_extracted_from_decl_after_close(self) -> None:
        """funcao = nome da próxima decl (User/Static/Main Function ou Method)."""
        src = (
            '/*/{Protheus.doc} MinhaFn\nResumo.\n/*/\n'
            'Static Function MinhaFn(cArg)\n'
            'Return\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["funcao"] == "MinhaFn"

    def test_funcao_method_decl(self) -> None:
        """Method MyClass:MyMethod() — extrai 'MyMethod' como funcao."""
        src = (
            '/*/{Protheus.doc} TQuad::new\n@type method\n/*/\n'
            'Method new() Class TQuad\n'
            'Return Self\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["funcao"] == "new"

    def test_funcao_id_preserved_when_mismatch(self) -> None:
        """funcao_id no header pode diferir de funcao real (copy-paste)."""
        src = (
            '/*/{Protheus.doc} OldName\nResumo.\n/*/\n'
            'User Function NewName()\n'
            'Return\n'
        )
        d = extract_protheus_docs(src)[0]
        assert d["funcao_id"] == "OldName"
        assert d["funcao"] == "NewName"

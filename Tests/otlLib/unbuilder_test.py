import pytest
from fontTools.otlLib import builder, unbuilder
from fontTools.ttLib.tables import otTables


class UnbuilderTest(object):
    GLYPHS = (
        ".notdef space zero one two three four five six "
        "A B C a b c grave acute cedilla f_f_i f_i c_t"
    ).split()
    GLYPHMAP = {name: num for num, name in enumerate(GLYPHS)}

    ANCHOR1 = builder.buildAnchor(11, -11)
    ANCHOR2 = builder.buildAnchor(22, -22)
    ANCHOR3 = builder.buildAnchor(33, -33)

    def test_unbuildAnchor_format1(self):
        kwargs = {"x": 23, "y": 42}
        anchor = builder.buildAnchor(**kwargs)
        unbuilt_anchor = unbuilder.unbuildAnchor(anchor)
        assert kwargs == unbuilt_anchor

    def test_unbuildAnchor_format2(self):
        kwargs = {"x": 24, "y": 42, "point": 17}
        anchor = builder.buildAnchor(**kwargs)
        unbuilt_anchor = unbuilder.unbuildAnchor(anchor)
        assert kwargs == unbuilt_anchor

    def test_unbuildAnchor_format3(self):
        kwargs = {
            "x": 23,
            "y": 42,
            "deviceX": builder.buildDevice({1: 1, 0: 0}),
            "deviceY": builder.buildDevice({7: 7}),
        }
        anchor = builder.buildAnchor(**kwargs)
        unbuilt_kwargs = unbuild_args(kwargs)
        unbuilt_anchor = unbuilder.unbuildAnchor(anchor)
        assert unbuilt_kwargs == unbuilt_anchor

    def test_unbuildAttachList(self):
        args = {"zero": [7, 23], "one": [1]}
        attachList = builder.buildAttachList(args, self.GLYPHMAP)
        unbuilt_attachList = unbuilder.unbuildAttachList(attachList)
        assert args == unbuilt_attachList

    def test_unbuildAttachList_empty(self):
        args = {}
        attachList = builder.buildAttachList(args, self.GLYPHMAP)
        unbuilt_attachList = unbuilder.unbuildAttachList(attachList)
        assert not unbuilt_attachList

    def test_unbuildAttachPoint(self):
        args = [7, 3]
        attachPoint = builder.buildAttachPoint(args)
        unbuilt_attachPoint = unbuilder.unbuildAttachPoint(attachPoint)
        assert sorted(args) == unbuilt_attachPoint

    def test_unbuildAttachPoint_empty(self):
        args = []
        attachPoint = builder.buildAttachPoint(args)
        unbuilt_attachPoint = unbuilder.unbuildAttachPoint(attachPoint)
        assert not unbuilt_attachPoint

    def test_unbuildAttachPoint_duplicate(self):
        args = [7, 3, 7]
        attachPoint = builder.buildAttachPoint(args)
        unbuilt_attachPoint = unbuilder.unbuildAttachPoint(attachPoint)
        assert sorted(args[:-1]) == unbuilt_attachPoint

    def test_unbuildBaseArray(self):
        anchor = builder.buildAnchor
        args = {
            "a": {2: anchor(300, 80)},
            "c": {1: anchor(300, 80), 2: anchor(300, -20)},
        }
        # buildBaseArray doesn't store any glyph names so we can't compare
        # it against unbuilding the function argseter.
        baseArray = builder.buildBaseArray(
            args, numMarkClasses=4, glyphMap=self.GLYPHMAP
        )
        unbuilt_baseArray = unbuilder.unbuildBaseArray(baseArray)
        assert [
            [None, None, {"x": 300, "y": 80}, None],
            [None, {"x": 300, "y": 80}, {"x": 300, "y": -20}, None],
        ] == unbuilt_baseArray

    def test_unbuildBaseRecord(self):
        a = builder.buildAnchor
        args = [a(500, -20), None, a(300, -15)]
        rec = builder.buildBaseRecord(args)
        unbuilt_args = unbuild_args(args)
        unbuilt_rec = unbuilder.unbuildBaseRecord(rec)
        assert unbuilt_args == unbuilt_rec

    def test_unbuildCaretValueForCoord(self):
        args = 500
        caret = builder.buildCaretValueForCoord(args)
        unbuilt_caret = unbuilder.unbuildCaretValueForCoord(caret)
        assert args == unbuilt_caret

    def test_unbuildCaretValueForPoint(self):
        args = 23
        caret = builder.buildCaretValueForPoint(args)
        unbuilt_caret = unbuilder.unbuildCaretValueForPoint(caret)
        assert unbuilt_caret == args

    def test_unbuildComponentRecord(self):
        a = builder.buildAnchor
        args = [a(500, -20), None, a(300, -15)]
        rec = builder.buildComponentRecord(args)
        unbuilt_args = unbuild_args(args)
        unbuilt_rec = unbuilder.unbuildComponentRecord(rec)
        assert unbuilt_args == unbuilt_rec

    def test_unbuildComponentRecord_empty(self):
        args = []
        rec = builder.buildComponentRecord(args)
        unbuilt_rec = unbuilder.unbuildComponentRecord(rec)
        assert unbuilt_rec is None

    def test_unbuildComponentRecord_None(self):
        args = None
        rec = builder.buildComponentRecord(args)
        unbuilt_rec = unbuilder.unbuildComponentRecord(rec)
        assert unbuilt_rec is None

    def test_unbuildCoverage(self):
        args1 = {"two", "four"}
        glyphMap = {"two": 2, "four": 4}
        cov = builder.buildCoverage(args1, glyphMap)
        unbuilt_cov = unbuilder.unbuildCoverage(cov)
        # buildCoverage assembles a list of glyphs which are sorted by
        # the glyphMap so we need to do the same sorting to args1.
        assert sorted(args1, key=lambda k: glyphMap[k]) == unbuilt_cov

    def test_unbuildCursivePosSubtable(self):
        args = {
            "two": (self.ANCHOR1, self.ANCHOR2),
            "four": (self.ANCHOR3, self.ANCHOR1),
        }
        unbuilt_args = unbuild_args(args)
        pos = builder.buildCursivePosSubtable(args, self.GLYPHMAP)

        unbuilt_subtable = unbuilder.unbuildCursivePosSubtable(pos)
        assert unbuilt_args == unbuilt_subtable

    def test_unbuildDevice_format1(self):
        args = {1: 1, 0: 0}
        device = builder.buildDevice(args)
        unbuilt_device = unbuilder.unbuildDevice(device)
        for k in args:
            assert args[k] == unbuilt_device[k]

    def test_unbuildDevice_format2(self):
        args = {2: 2, 0: 1, 1: 0}
        device = builder.buildDevice(args)
        unbuilt_device = unbuilder.unbuildDevice(device)
        for k in args:
            assert args[k] == unbuilt_device[k]

    def test_unbuildDevice_format3(self):
        args = {5: 3, 1: 77}
        device = builder.buildDevice(args)
        unbuilt_device = unbuilder.unbuildDevice(device)
        for k in args:
            assert args[k] == unbuilt_device[k]

    def test_unbuildLigatureArray(self):
        anchor = builder.buildAnchor
        args = {
            "f_i": [{2: anchor(300, -20)}, {}],
            "c_t": [{}, {1: anchor(500, 350), 2: anchor(1300, -20)}],
        }
        ligatureArray = builder.buildLigatureArray(
            args, numMarkClasses=4, glyphMap=self.GLYPHMAP
        )
        unbuilt_args = unbuild_args(args)
        unbuilt_ligatureArray = unbuilder.unbuildLigatureArray(ligatureArray)
        # buildLigtureArray doesn't store any glyph names so we can't compare
        # it against unbuilding the function args.
        assert [
            [[None, None, {"x": 300, "y": -20}, None], [None, None, None, None]],
            [
                [None, None, None, None],
                [None, {"x": 500, "y": 350}, {"x": 1300, "y": -20}, None],
            ],
        ] == unbuilt_ligatureArray

    def test_unbuildLigatureAttach(self):
        anchor = builder.buildAnchor
        args = [[anchor(500, -10), None], [None, anchor(300, -20), None]]
        attach = builder.buildLigatureAttach(args)
        unbuilt_args = unbuild_args(args)
        unbuilt_attach = unbuilder.unbuildLigatureAttach(attach)
        assert unbuilt_args == unbuilt_attach

    def test_unbuildLigatureAttach_emptyComponents(self):
        args = [[], None]
        attach = builder.buildLigatureAttach(args)
        unbuilt_attach = unbuilder.unbuildLigatureAttach(attach)
        # buildLigatureAttach can't distinguish between [] and None
        # the function outputs the following XML.
        #    "<LigatureAttach>",
        #    "  <!-- ComponentCount=2 -->",
        #    '  <ComponentRecord index="0" empty="1"/>',
        #    '  <ComponentRecord index="1" empty="1"/>',
        #    "</LigatureAttach>",
        #
        # Due to this output, we cannot compare it against the
        # function args.
        assert [None, None] == unbuilt_attach

    def test_unbuildLigatureAttach_noComponents(self):
        args = []
        attach = builder.buildLigatureAttach(args)
        unbuilt_args = unbuild_args(args)
        unbuilt_attach = unbuilder.unbuildLigatureAttach(attach)
        assert unbuilt_args == unbuilt_attach

    def test_unbuildLigCaretList(self):
        args1 = {"f_f_i": [300, 600]}
        args2 = {"c_t": [42]}
        carets = builder.buildLigCaretList(args1, args2, self.GLYPHMAP)
        unbuilt_carets = unbuilder.unbuildLigCaretList(carets)
        args = args1
        args.update(args2)
        assert args == unbuilt_carets

    def test_unbuildLigCaretList_bothCoordsAndPointsForSameGlyph(self):
        args1 = {"f_f_i": [300]}
        args2 = {"f_f_i": [7]}
        carets = builder.buildLigCaretList(args1, args2, self.GLYPHMAP)
        unbuilt_carets = unbuilder.unbuildLigCaretList(carets)
        assert {"f_f_i": [300, 7]} == unbuilt_carets

    def test_unbuildLigCaretList_empty(self):
        ligCaretList = builder.buildLigCaretList({}, {}, self.GLYPHMAP)
        unbuilt_ligCaretList = unbuilder.unbuildLigCaretList(ligCaretList)
        assert unbuilt_ligCaretList is None

    def test_unbuildLigCaretList_None(self):
        ligCaretList = builder.buildLigCaretList(None, None, self.GLYPHMAP)
        unbuilt_ligCaretList = unbuilder.unbuildLigCaretList(ligCaretList)
        assert unbuilt_ligCaretList is None

    def test_unbuildLigGlyph_coords(self):
        args = [500, 800]
        lig = builder.buildLigGlyph([500, 800], None)
        unbuilt_lig = unbuilder.unbuildLigGlyph(lig)
        assert args == unbuilt_lig

    def test_unbuildLigGlyph_empty(self):
        args = []
        lig = builder.buildLigGlyph(args, args)
        unbuilt_lig = unbuilder.unbuildLigGlyph(lig)
        assert unbuilt_lig is None

    def test_unbuildLigGlyph_None(self):
        args = None
        lig = builder.buildLigGlyph(args, args)
        unbuilt_lig = unbuilder.unbuildLigGlyph(lig)
        assert args == unbuilt_lig

    def test_unbuildLigGlyph_points(self):
        args = (None, [2])
        lig = builder.buildLigGlyph(*args)
        unbuilt_lig = unbuilder.unbuildLigGlyph(lig)
        # TODO check this
        # assert args == unbuilt_lig

    def test_unbuildLookup(self):
        args1 = {"one": "two"}
        args2 = {"three": "four"}
        s1 = builder.buildSingleSubstSubtable(args1)
        s2 = builder.buildSingleSubstSubtable(args2)
        lookup = builder.buildLookup([s1, s2], flags=7)
        unbuilt_lookup, unbuilt_flag = unbuilder.unbuildLookup(lookup)
        assert unbuilt_lookup[0] == args1 and unbuilt_lookup[1] == args2

    def test_unbuildMarkArray(self):
        args = {
            "acute": (7, builder.buildAnchor(300, 800)),
            "grave": (2, builder.buildAnchor(10, 80)),
        }
        markArray = builder.buildMarkArray(args, self.GLYPHMAP)
        unbuilt_args = unbuild_args(args)
        unbuilt_markArray = unbuilder.unbuildMarkArray(markArray)
        # MarkArray is similar to BaseArray. It does not contain any glyph names 
        assert sorted(unbuilt_args.values(), key=lambda k: k[0]) == unbuilt_markArray

    def test_unbuildMarkBasePosSubtable(self):
        anchor = builder.buildAnchor
        marks = {
            "acute": (0, anchor(300, 700)),
            "cedilla": (1, anchor(300, -100)),
            "grave": (0, anchor(300, 700)),
        }
        unbuilt_marks = unbuild_args(marks)
        bases = {
            # Make sure we can handle missing entries.
            "A": {},  # no entry for any markClass
            "B": {0: anchor(500, 900)},  # only markClass 0 specified
            "C": {1: anchor(500, -10)},  # only markClass 1 specified
            "a": {0: anchor(500, 400), 1: anchor(500, -20)},
            "b": {0: anchor(500, 800), 1: anchor(500, -20)},
        }
        unbuilt_bases = unbuild_args(bases)
        subtable = builder.buildMarkBasePosSubtable(marks, bases, self.GLYPHMAP)
        unbuilt_subtable = unbuilder.unbuildMarkBasePosSubtable(subtable)
        assert unbuilt_marks == unbuilt_subtable["marks"]
        assert unbuilt_bases == unbuilt_subtable["bases"]

    def test_unbuildMarkGlyphSetsDef(self):
        args = [{"acute", "grave"}, {"cedilla", "grave"}]
        marksets = builder.buildMarkGlyphSetsDef(args, self.GLYPHMAP)
        unbuilt_marksets = unbuilder.unbuildMarkGlyphSetsDef(marksets)
        assert args == unbuilt_marksets

    def test_unbuildMarkGlyphSetsDef_empty(self):
        args = []
        markGlyphs = builder.buildMarkGlyphSetsDef(args, self.GLYPHMAP)
        unbuilt_markGlyphs = unbuilder.unbuildMarkGlyphSetsDef(markGlyphs)
        assert unbuilt_markGlyphs is None

    def test_unbuildMarkGlyphSetsDef_None(self):
        args = None
        markGlyphs = builder.buildMarkGlyphSetsDef(args, self.GLYPHMAP)
        unbuilt_markGlyphs = unbuilder.unbuildMarkGlyphSetsDef(markGlyphs)
        assert unbuilt_markGlyphs is None

    def test_unbuildMarkLigPosSubtable(self):
        anchor = builder.buildAnchor
        marks = {
            "acute": (0, anchor(300, 700)),
            "cedilla": (1, anchor(300, -100)),
            "grave": (0, anchor(300, 700)),
        }
        unbuilt_marks = unbuild_args(marks)
        ligs = {
            "f_i": [{}, {0: anchor(200, 400)}],  # nothing on f; only 1 on i
            "c_t": [
                {0: anchor(500, 600), 1: anchor(500, -20)},  # c
                {0: anchor(1300, 800), 1: anchor(1300, -20)},  # t
            ],
        }
        subtable = builder.buildMarkLigPosSubtable(marks, ligs, self.GLYPHMAP)
        unbuilt_subtable = unbuilder.unbuildMarkLigPosSubtable(subtable)
        unbuilt_ligs = unbuild_args(ligs)
        assert unbuilt_marks == unbuilt_subtable["marks"]
        assert unbuilt_ligs == unbuilt_subtable["ligs"]

    def test_unbuildMarkRecord(self):
        args = (17, builder.buildAnchor(500, -20))
        rec = builder.buildMarkRecord(*args)
        unbuilt_args = unbuild_args(args)
        unbuilt_rec = unbuilder.unbuildMarkRecord(rec)
        assert unbuilt_args == unbuilt_rec

    def test_unbuildMark2Record(self):
        a = builder.buildAnchor
        args = [a(500, -20), None, a(300, -15)]
        rec = builder.buildMark2Record(args)
        unbuilt_args = unbuild_args(args)
        unbuilt_rec = unbuilder.unbuildMark2Record(rec)
        assert unbuilt_args == unbuilt_rec

    def test_unbuildPairPosClassesSubtable(self):
        d20 = builder.buildValue({"XPlacement": -20})
        d50 = builder.buildValue({"XPlacement": -50})
        d0 = builder.buildValue({})
        d8020 = builder.buildValue({"XPlacement": -80, "YPlacement": -20})
        args = {
            (tuple("A"), tuple(["zero"])): (d0, d50),
            (tuple("A"), tuple(["one", "two"])): (None, d20),
            (tuple(["B", "C"]), tuple(["zero"])): (d8020, d50),
        }
        unbuilt_args = unbuild_args(args)
        subtable = builder.buildPairPosClassesSubtable(args, self.GLYPHMAP)
        unbuilt_subtable = unbuilder.unbuildPairPosClassesSubtable(subtable)
        assert unbuilt_args == unbuilt_subtable

    def test_unbuildPairPosGlyphsSubtable(self):
        d20 = builder.buildValue({"XPlacement": -20})
        d50 = builder.buildValue({"XPlacement": -50})
        d0 = builder.buildValue({})
        d8020 = builder.buildValue({"XPlacement": -80, "YPlacement": -20})
        args = {
            ("A", "zero"): (d0, d50),
            ("A", "one"): (None, d20),
            ("B", "five"): (d8020, d50),
        }
        subtable = builder.buildPairPosGlyphsSubtable(args, self.GLYPHMAP)
        unbuilt_args = unbuild_args(args)
        unbuilt_subtable = unbuilder.unbuildPairPosSubtable(subtable)
        assert unbuilt_args == unbuilt_subtable

    def test_unbuildSinglePosSubtable_ValueFormat0(self):
        args = {"zero": builder.buildValue({})}
        unbuilt_args = unbuild_args(args)
        subtables = builder.buildSinglePosSubtable(args, self.GLYPHMAP)
        assert unbuilt_args == unbuilder.unbuildSinglePosSubtable(subtables)

    def test_unbuildSinglePosSubtable_format1(self):
        args = {
            "one": builder.buildValue({"XPlacement": 777}),
            "two": builder.buildValue({"XPlacement": 777}),
        }
        unbuilt_args = unbuild_args(args)
        subtable = builder.buildSinglePosSubtable(args, self.GLYPHMAP)
        assert unbuilt_args == unbuilder.unbuildSinglePosSubtable(subtable)

    def test_unbuildSinglePosSubtable_format2(self):
        args = {
            "one": builder.buildValue({"XPlacement": 777}),
            "two": builder.buildValue({"YPlacement": -888}),
        }
        unbuilt_args = unbuild_args(args)
        subtable = builder.buildSinglePosSubtable(args, self.GLYPHMAP)
        assert unbuilt_args == unbuilder.unbuildSinglePosSubtable(subtable)

    def test_unbuildValue(self):
        args = {"XPlacement": 7, "YPlacement": 23}
        value = builder.buildValue(args)
        unbuilt_value = unbuilder.unbuildValue(value)
        assert unbuilt_value == args


def test_unbuild_args():
    anchor = builder.buildAnchor
    args = {1: {2: {3: [anchor(1, 1), anchor(2, 2)], 4: anchor(3, 3)}}}
    assert unbuild_args(args) == {
        1: {2: {3: [{"x": 1, "y": 1}, {"x": 2, "y": 2}], 4: {"x": 3, "y": 3}}}
    }


def unbuild_args(item):
    """Helper function to recursively unbuild function arguments which contain
    either otTables.Anchor or otTables.Value.
    
    anc = Anchor
    [anc(10, 10), anc(20,20)] --> [{"x": 10, "y": 10}, {"x": 20, "y": 20}

    {1: {2: [anc(10, 10)]}} --> {1: {2: [{"x": 10, "y": 10}]}}
    """
    if isinstance(item, list):
        item = [unbuild_args(_unbuild_item(item[idx])) for idx in range(len(item))]
    elif isinstance(item, tuple):
        item = tuple([unbuild_args(_unbuild_item(item[idx])) for idx in range(len(item))])
    elif isinstance(item, dict):
        item = {k: unbuild_args(_unbuild_item(item[k])) for k, v in item.items()}
    return item


def _unbuild_item(item):
    if isinstance(item, otTables.Anchor):
        item = unbuilder.unbuildAnchor(item)
    elif isinstance(item, otTables.ValueRecord):
        item = unbuilder.unbuildValue(item)
    return item
